import os
import shutil
from typing import List, Optional
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_openai import OpenAIEmbeddings


class RAGManager:
    def __init__(self):
        # Gemini Embedding Model (Free Tier Available)
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=os.environ.get("GEMINI_API_KEY"))
        self.index_name = "capstone-agent-index-gemini" # Dimension 768
        self._vector_store = None
        
        # Initialize Pinecone check
        self._ensure_index_exists()

    def _ensure_index_exists(self):
        pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
        if self.index_name not in pc.list_indexes().names():
            pc.create_index(
                name=self.index_name,
                dimension=768, # models/embedding-001 dimension
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )

    @property
    def vector_store(self):
        if self._vector_store is None:
            self._vector_store = PineconeVectorStore(
                index_name=self.index_name,
                embedding=self.embeddings
            )
        return self._vector_store

    def _batch_add_documents(self, documents):
        """Helper to split and add documents with rate limiting."""
        import time
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1024,
            chunk_overlap=256
        )
        chunks = text_splitter.split_documents(documents)
        
        # Batch processing to prevent 429 Quota Exceeded
        batch_size = 5
        total_chunks = len(chunks)
        
        print(f"Total chunks to process: {total_chunks}. Batch size: {batch_size}")
        
        for i in range(0, total_chunks, batch_size):
            batch = chunks[i:i + batch_size]
            try:
                print(f"Processing batch {i//batch_size + 1}/{(total_chunks + batch_size - 1)//batch_size}...")
                self.vector_store.add_documents(batch)
                time.sleep(5) 
            except Exception as e:
                print(f"Error processing batch {i}-{i+batch_size}: {e}")
                time.sleep(30)
                try:
                    self.vector_store.add_documents(batch)
                except Exception as e2:
                    print(f"Failed retry for batch {i}-{i+batch_size}: {e2}")
                    raise e2
        
        return total_chunks

    def process_pdf(self, file_path: str):
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        return self._batch_add_documents(documents)

    def process_text(self, file_path: str):
        from langchain_community.document_loaders import TextLoader
        loader = TextLoader(file_path)
        documents = loader.load()
        return self._batch_add_documents(documents)

    def process_docx(self, file_path: str):
        from langchain_community.document_loaders import Docx2txtLoader
        loader = Docx2txtLoader(file_path)
        documents = loader.load()
        return self._batch_add_documents(documents)

    def search(self, query: str, k: int = 3):
        return self.vector_store.similarity_search(query, k=k)

rag_manager = RAGManager()
