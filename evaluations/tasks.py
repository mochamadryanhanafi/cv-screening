from celery import shared_task
from dotenv import load_dotenv
import logging
import os

from django.core.cache import cache

from core.application.use_cases.evaluate_candidate import EvaluateCandidateUseCase
from core.infra.persistence.django_repository import DjangoEvaluationRepository
from core.infra.file_parser import PdfParser
from core.infra.vector_store.chroma import ChromaVectorStore

load_dotenv()

# Select LLM provider by environment variable LLM_PROVIDER. Supported: HUGGINGFACE (default), GROQ
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'HUGGINGFACE').upper()
if LLM_PROVIDER == 'GROQ':
    from core.infra.llm.groq import GroqLLMService as SelectedLLMService
else:
    from core.infra.llm.huggingface import HuggingFaceLLMService as SelectedLLMService

logger = logging.getLogger(__name__)

@shared_task
def evaluate_documents(job_id):
    """
    Celery task to evaluate a candidate's documents.
    This task acts as the Composition Root for the evaluation use case.
    """
    try:
        # 1. Initialize concrete implementations
        evaluation_repo = DjangoEvaluationRepository()
        pdf_parser = PdfParser()
        # Initialize chosen LLM service
        llm_service = SelectedLLMService()
        vector_store = ChromaVectorStore()

        # 2. Initialize the use case with concrete dependencies
        use_case = EvaluateCandidateUseCase(
            evaluation_repository=evaluation_repo,
            cv_parser=pdf_parser,
            project_parser=pdf_parser,
            llm_service=llm_service,
            vector_store=vector_store,
        )

        # 3. Execute the use case
        use_case.execute(job_id)

    except Exception as exc:
        logger.exception("An error occurred during the evaluation for job %s: %s", job_id, exc)
        
        # Generic failure handling
        evaluation_repo = DjangoEvaluationRepository()
        try:
            job = evaluation_repo.get_by_id(job_id)
            if job and job.status != 'completed':
                job.status = 'failed'
                job.overall_summary = f"An unexpected error occurred during evaluation: {str(exc)}"
                evaluation_repo.update(job)
        except Exception as update_exc:
            logger.exception("Failed to update job %s status to failed: %s", job_id, update_exc)

        # Fallback logic (optional, can be simplified or removed if not needed)
        # For this example, we'll keep the original fallback logic inside the generic handler
        if LLM_PROVIDER == 'GROQ':
            try:
                logger.info("Attempting fallback to HuggingFace for job %s", job_id)
                from core.infra.llm.huggingface import HuggingFaceLLMService

                # Re-initialize dependencies for fallback
                pdf_parser = PdfParser()
                vector_store = ChromaVectorStore()
                fallback_llm = HuggingFaceLLMService()
                
                # Re-initialize use case with fallback LLM
                use_case = EvaluateCandidateUseCase(
                    evaluation_repository=evaluation_repo,
                    cv_parser=pdf_parser,
                    project_parser=pdf_parser,
                    llm_service=fallback_llm,
                    vector_store=vector_store,
                )
                use_case.execute(job_id)
                
                try:
                    cache.incr("metrics:llm:groq:fallbacks")
                except Exception:
                    pass # ignore cache errors

            except Exception as fallback_exc:
                logger.exception("Fallback to HuggingFace also failed for job %s: %s", job_id, fallback_exc)
                # Final failure update after fallback failure
                try:
                    job = evaluation_repo.get_by_id(job_id)
                    job.status = 'failed'
                    job.overall_summary = f"Primary LLM failed and fallback also failed: {str(fallback_exc)}"
                    evaluation_repo.update(job)
                except Exception as final_update_exc:
                    logger.exception("Failed to mark job %s as failed after fallback failure: %s", job_id, final_update_exc)