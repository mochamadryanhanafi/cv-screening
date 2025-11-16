import chromadb
import os
from django.conf import settings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.vectorstores import Chroma

from core.application.interfaces import IVectorStore


class ChromaVectorStore(IVectorStore):
    def __init__(self):
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

        # Configure host/port from environment if available
        host = os.getenv('CHROMA_HOST', 'localhost')
        port = int(os.getenv('CHROMA_PORT', '8003'))

        # Create a Chroma HTTP client and wrap with LangChain's Chroma vectorstore
        # chromadb.HttpClient expects host/port kwargs
        self.chroma_client = chromadb.HttpClient(host=host, port=port)

        self.vector_store = Chroma(
            client=self.chroma_client,
            embedding_function=self.embeddings,
        )

    def get_retriever(self):
        return self.vector_store.as_retriever()
