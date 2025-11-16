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

    # 3. Execute the use case with fallback logic.
    try:
        use_case.execute(job_id)
    except Exception as exc:
        logger.exception("LLM provider %s failed during evaluation for job %s: %s", LLM_PROVIDER, job_id, exc)
        # metric increment (if cache configured)
        try:
            cache.incr(f"metrics:llm:{LLM_PROVIDER.lower()}:failures")
        except Exception:
            # ignore cache errors
            pass

        # If we tried Groq, fallback to HuggingFace
        if LLM_PROVIDER == 'GROQ':
            try:
                logger.info("Attempting fallback to HuggingFace for job %s", job_id)
                from core.infra.llm.huggingface import HuggingFaceLLMService

                fallback_llm = HuggingFaceLLMService()
                use_case.llm_service = fallback_llm
                use_case.execute(job_id)
                try:
                    cache.incr("metrics:llm:groq:fallbacks")
                except Exception:
                    pass
            except Exception:
                logger.exception("Fallback to HuggingFace failed for job %s", job_id)
                # final failure handling: repository update to mark failed
                try:
                    job = evaluation_repo.get_by_id(job_id)
                    job.status = 'failed'
                    job.overall_summary = f"LLM evaluation failed: {str(exc)}"
                    evaluation_repo.update(job)
                except Exception:
                    logger.exception("Failed to mark job %s as failed", job_id)
        else:
            # Non-Groq provider failed — mark job failed
            try:
                job = evaluation_repo.get_by_id(job_id)
                job.status = 'failed'
                job.overall_summary = f"LLM evaluation failed: {str(exc)}"
                evaluation_repo.update(job)
            except Exception:
                logger.exception("Failed to mark job %s as failed", job_id)