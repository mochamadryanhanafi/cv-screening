import os
import time
import requests
from typing import Optional

from core.application.interfaces import ILLMService


class GroqLLMService(ILLMService):
    """Simple Groq API adapter implementing ILLMService.

    This adapter uses HTTP requests to call a Groq model endpoint. It includes
    a lightweight retry backoff and attempts to parse common response shapes.
    Configure via environment variables:
      - GROQ_API_KEY
      - GROQ_API_URL (e.g. https://api.groq.com/v1/models)
      - GROQ_MODEL
      - GROQ_TIMEOUT (seconds)
    """

    def __init__(self, api_key: Optional[str] = None, api_url: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        self.api_url = api_url or os.getenv('GROQ_API_URL')
        self.model = model or os.getenv('GROQ_MODEL')
        self.timeout = int(os.getenv('GROQ_TIMEOUT', '60'))
        if not (self.api_key and self.api_url and self.model):
            raise ValueError('GROQ_API_KEY, GROQ_API_URL and GROQ_MODEL must be set for GroqLLMService')

    def _call(self, prompt: str, max_tokens: int = 512, temperature: float = 0.0, retries: int = 3) -> str:
        url = f"{self.api_url.rstrip('/')}/{self.model}/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        backoff = 1.0
        for attempt in range(1, retries + 1):
            try:
                resp = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
                resp.raise_for_status()
                data = resp.json()
                # Common response shapes: `choices` list with `text`, or `output`/`results` fields
                if isinstance(data, dict):
                    if 'choices' in data and isinstance(data['choices'], list) and data['choices']:
                        choice = data['choices'][0]
                        return choice.get('text') or choice.get('message') or str(choice)
                    if 'output' in data:
                        # Some APIs return output as list of objects or text
                        out = data['output']
                        if isinstance(out, list):
                            return ' '.join([o.get('text', str(o)) if isinstance(o, dict) else str(o) for o in out])
                        return str(out)
                    # Fallback: try top-level text
                    if 'text' in data:
                        return data['text']

                # If response is unexpected, return raw text
                return resp.text

            except requests.RequestException as e:
                if attempt == retries:
                    raise
                time.sleep(backoff)
                backoff *= 2

    def evaluate_cv(self, cv_content: str, retriever) -> str:
        job_docs = []
        rubric_docs = []
        try:
            if retriever:
                job_docs = retriever.get_relevant_documents("Backend Developer Job Description")
                rubric_docs = retriever.get_relevant_documents("CV Evaluation Scoring Rubric")
        except Exception:
            # If retriever fails, continue with minimal context
            job_docs = []
            rubric_docs = []

        context = ' '.join([d.page_content for d in job_docs])
        rubric = ' '.join([d.page_content for d in rubric_docs])

        prompt = (
            f"Context: {context}\n\nCV Rubric: {rubric}\n\n"
            f"Evaluate the following CV and provide:\n"
            f"Match Rate: a number between 0.0 and 1.0\nFeedback: actionable feedback\n\nCV:\n{cv_content}\n"
        )
        return self._call(prompt, max_tokens=1024, temperature=0.0)

    def evaluate_project(self, project_content: str, retriever) -> str:
        case_docs = []
        rubric_docs = []
        try:
            if retriever:
                case_docs = retriever.get_relevant_documents("Case Study Brief")
                rubric_docs = retriever.get_relevant_documents("Project Deliverable Evaluation Scoring Rubric")
        except Exception:
            case_docs = []
            rubric_docs = []

        context = ' '.join([d.page_content for d in case_docs])
        rubric = ' '.join([d.page_content for d in rubric_docs])

        prompt = (
            f"Context: {context}\n\nProject Rubric: {rubric}\n\n"
            f"Evaluate the following project report and provide:\n"
            f"Score: a number between 1.0 and 5.0\nFeedback: actionable feedback\n\nProject Report:\n{project_content}\n"
        )
        return self._call(prompt, max_tokens=1024, temperature=0.0)

    def generate_summary(self, cv_evaluation: str, project_evaluation: str) -> str:
        prompt = (
            f"Given the CV evaluation:\n{cv_evaluation}\n\nAnd the project evaluation:\n{project_evaluation}\n\n"
            "Write a concise overall summary of the candidate in 3-5 sentences."
        )
        return self._call(prompt, max_tokens=512, temperature=0.0)
