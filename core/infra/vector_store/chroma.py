import os
import chromadb
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from core.application.interfaces import IVectorStore

class ChromaVectorStore(IVectorStore):
    def __init__(self):
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        
        # Setup ChromaDB client for client-server mode
        chroma_client = chromadb.HttpClient(
            host=os.getenv("CHROMA_HOST", "localhost"),
            port=os.getenv("CHROMA_PORT", "8003")
        )
        
        self.vector_store = Chroma(
            client=chroma_client,
            embedding_function=self.embeddings
        )

    def get_retriever(self):
        return self.vector_store.as_retriever()
