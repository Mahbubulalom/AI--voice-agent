"""
Knowledge base implementation for storing and retrieving dental practice information.
"""

import os
import uuid
import shutil
from typing import List, Dict, Any, Tuple, Optional
import logging

import numpy as np
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.document_loaders import (
    TextLoader,
    PyPDFLoader,
    Docx2txtLoader,
    CSVLoader,
    UnstructuredHTMLLoader,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KnowledgeBase:
    """
    Knowledge base for storing and retrieving dental practice information.
    Uses embeddings and vector search to find relevant information.
    """
    
    def __init__(self, knowledge_dir: str, vector_db_path: str):
        """
        Initialize the knowledge base.
        
        Args:
            knowledge_dir (str): Directory to store uploaded documents
            vector_db_path (str): Directory to store vector database
        """
        self.knowledge_dir = knowledge_dir
        self.vector_db_path = vector_db_path
        
        # Create directories if they don't exist
        os.makedirs(knowledge_dir, exist_ok=True)
        os.makedirs(vector_db_path, exist_ok=True)
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings()
        
        # Initialize vector store if it exists
        if os.path.exists(os.path.join(vector_db_path, "index.faiss")):
            self.vector_store = FAISS.load_local(vector_db_path, self.embeddings)
        else:
            # Create an empty vector store
            self.vector_store = FAISS.from_texts(["Initial empty document"], self.embeddings)
            self.vector_store.save_local(vector_db_path)
        
        # Initialize text splitter for chunking documents
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        # Map file extensions to loaders
        self.file_loaders = {
            ".txt": TextLoader,
            ".pdf": PyPDFLoader,
            ".docx": Docx2txtLoader,
            ".doc": Docx2txtLoader,
            ".csv": CSVLoader,
            ".html": UnstructuredHTMLLoader,
            ".htm": UnstructuredHTMLLoader,
        }
    
    def add_document(self, file_path: str, description: Optional[str] = None) -> str:
        """
        Add a document to the knowledge base.
        
        Args:
            file_path (str): Path to the document file
            description (str, optional): Description of the document
            
        Returns:
            str: Document ID
        """
        try:
            # Generate a unique document ID
            document_id = str(uuid.uuid4())
            
            # Get file extension
            _, file_extension = os.path.splitext(file_path)
            file_extension = file_extension.lower()
            
            # Check if file type is supported
            if file_extension not in self.file_loaders:
                raise ValueError(f"Unsupported file type: {file_extension}")
            
            # Load the document
            loader_class = self.file_loaders[file_extension]
            loader = loader_class(file_path)
            documents = loader.load()
            
            # Add metadata
            for doc in documents:
                doc.metadata["source"] = os.path.basename(file_path)
                doc.metadata["document_id"] = document_id
                if description:
                    doc.metadata["description"] = description
            
            # Split into chunks
            text_chunks = self.text_splitter.split_documents(documents)
            
            # Add to vector store
            self.vector_store.add_documents(text_chunks)
            
            # Save the vector store
            self.vector_store.save_local(self.vector_db_path)
            
            # Copy the file to the knowledge directory
            destination = os.path.join(self.knowledge_dir, f"{document_id}{file_extension}")
            shutil.copy2(file_path, destination)
            
            logger.info(f"Added document {os.path.basename(file_path)} with ID {document_id}")
            
            return document_id
            
        except Exception as e:
            logger.error(f"Error adding document: {str(e)}")
            raise
    
    def query(self, query: str, top_k: int = 5) -> List[Tuple[str, Dict[str, Any], float]]:
        """
        Query the knowledge base for relevant information.
        
        Args:
            query (str): Query string
            top_k (int): Number of results to return
            
        Returns:
            List[Tuple[str, Dict, float]]: List of (text, metadata, score) tuples
        """
        try:
            # Perform similarity search
            docs_with_scores = self.vector_store.similarity_search_with_score(query, k=top_k)
            
            # Format results
            results = []
            for doc, score in docs_with_scores:
                results.append((doc.page_content, doc.metadata, score))
            
            return results
            
        except Exception as e:
            logger.error(f"Error querying knowledge base: {str(e)}")
            return []
    
    def remove_document(self, document_id: str) -> bool:
        """
        Remove a document from the knowledge base.
        
        Args:
            document_id (str): Document ID to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Find all files with the document ID prefix
            document_files = [f for f in os.listdir(self.knowledge_dir) 
                            if f.startswith(document_id)]
            
            if not document_files:
                logger.warning(f"No files found for document ID {document_id}")
                return False
            
            # Remove the files
            for file_name in document_files:
                file_path = os.path.join(self.knowledge_dir, file_name)
                os.remove(file_path)
            
            # Re-index the vector store
            # This is a simplified approach; a more efficient implementation
            # would selectively remove only the relevant vectors
            self._rebuild_index()
            
            logger.info(f"Removed document with ID {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing document: {str(e)}")
            return False
    
    def _rebuild_index(self):
        """Rebuild the vector index from all documents in the knowledge directory."""
        try:
            # Clear the vector store
            self.vector_store = FAISS.from_texts(["Temporary placeholder"], self.embeddings)
            
            # Process all files in the knowledge directory
            for file_name in os.listdir(self.knowledge_dir):
                # Skip .gitkeep and other hidden files
                if file_name.startswith('.'):
                    continue
                
                file_path = os.path.join(self.knowledge_dir, file_name)
                if os.path.isfile(file_path):
                    # Extract document ID and file extension
                    document_id = os.path.splitext(file_name)[0]
                    _, file_extension = os.path.splitext(file_name)
                    
                    # Check if file type is supported
                    if file_extension.lower() in self.file_loaders:
                        # Load and process the document
                        loader_class = self.file_loaders[file_extension.lower()]
                        loader = loader_class(file_path)
                        documents = loader.load()
                        
                        # Add metadata
                        for doc in documents:
                            doc.metadata["source"] = file_name
                            doc.metadata["document_id"] = document_id
                        
                        # Split into chunks
                        text_chunks = self.text_splitter.split_documents(documents)
                        
                        # Add to vector store
                        self.vector_store.add_documents(text_chunks)
            
            # Save the vector store
            self.vector_store.save_local(self.vector_db_path)
            logger.info("Vector index rebuilt successfully")
            
        except Exception as e:
            logger.error(f"Error rebuilding index: {str(e)}")
            raise
