import chromadb
import os
from django.conf import settings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma

from core.application.interfaces import IVectorStore


class ChromaVectorStore(IVectorStore):
    def __init__(self):
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

# Reverting to HttpClient and hardcoding the port to force the correct connection.
        host = os.getenv("CHROMA_HOST", "localhost")
        port = 8003  # Hardcode the port to prevent environment issues in Celery
        self.chroma_client = chromadb.HttpClient(host=host, port=port)

        self.vector_store = Chroma(
            client=self.chroma_client,
            embedding_function=self.embeddings,
        )

    def get_retriever(self):
        return self.vector_store.as_retriever()
