import os
from django.core.management.base import BaseCommand
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv
from core.infra.vector_store.chroma import ChromaVectorStore # Import the updated ChromaVectorStore

load_dotenv()

class Command(BaseCommand):
    help = 'Ingests documents into the vector store'

    def handle(self, *args, **options):
        self.stdout.write("Starting document ingestion...")

        # Load documents
        loader = DirectoryLoader(
            './documents',
            glob="**/*.txt",
            loader_cls=TextLoader,
            show_progress=True,
            use_multithreading=True
        )
        documents = loader.load()

        # Split documents
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        texts = text_splitter.split_documents(documents)

        # Initialize the ChromaVectorStore (which uses HttpClient)
        chroma_vector_store = ChromaVectorStore()
        
        # Add documents to the vector store
        chroma_vector_store.vector_store.add_documents(texts)

        self.stdout.write(self.style.SUCCESS('Successfully ingested documents.'))
