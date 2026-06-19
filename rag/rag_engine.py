# RAG Engine - ChromaDB vector store
"""RAG engine using ChromaDB"""
import json
import os
import hashlib
import chromadb
from chromadb.config import Settings
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
from langchain_mistralai.embeddings import MistralAIEmbeddings
from pathlib import Path

# Collection name constant
COLLECTION_NAME = "dbs_banking"

# Metadata key for storing knowledge hash
KNOWLEDGE_HASH_KEY = "knowledge_hash"

class MistralLangChainEmbeddingFunction(EmbeddingFunction):
    def __init__(self):
        self._mistral_embedder = MistralAIEmbeddings(mistral_api_key=os.environ.get("MISTRAL_API_KEY"))

    def __call__(self, texts: Documents) -> Embeddings:
        return self._mistral_embedder.embed_documents(texts)

class RAGEngine:
    """Retrieval Augmented Generation engine"""
    
    def __init__(self, knowledge_path="knowledge_docs/faqs.json",
                 persist_dir="chroma_db"):
        self.client = chromadb.Client(Settings(
            persist_directory=persist_dir,
            anonymized_telemetry=False
        ))

        embedding_function = MistralLangChainEmbeddingFunction()

        # Use get_or_create_collection instead of delete+create
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=embedding_function,
            metadata={"description": "DBS Banking knowledge base"}
        )

        # Check if knowledge file has changed before re-indexing
        current_hash = self._compute_file_hash(knowledge_path)
        metadata = self.collection.metadata or {}
        
        # Re-index only if collection is empty OR knowledge file changed
        stored_hash = metadata.get(KNOWLEDGE_HASH_KEY)
        if self.collection.count() == 0 or stored_hash != current_hash:
            self._load_knowledge(knowledge_path)
            # Update the hash in collection metadata
            try:
                self.collection.modify(
                    name=COLLECTION_NAME,
                    metadata={**metadata, KNOWLEDGE_HASH_KEY: current_hash}
                )
            except Exception:
                # Log warning but don't fail if metadata update fails
                pass

    def _load_knowledge(self, knowledge_path: str):
        """Load FAQs and policies into ChromaDB"""
        with open(knowledge_path, 'r') as f:
            data = json.load(f)

        documents = []
        metadatas = []
        ids = []

        # Add FAQs
        for i, faq in enumerate(data.get("faqs", [])):
            doc = f"Q: {faq['question']}\nA: {faq['answer']}"
            documents.append(doc)
            # Serialize metadata to a JSON string
            metadatas.append({"metadata": json.dumps({"type": "faq", "question": faq["question"]})})
            ids.append(f"faq_{i}")

        # Add policies
        for i, policy in enumerate(data.get("policies", [])):
            doc = f"Policy - {policy['topic']}: {policy['content']}"
            documents.append(doc)
            # Serialize metadata to a JSON string
            metadatas.append({"metadata": json.dumps({"type": "policy", "topic": policy["topic"]})})
            ids.append(f"policy_{i}")

        # Add action descriptions
        for i, action in enumerate(data.get("actions", [])):
            doc = f"Action: {action['name']}\n{action['description']}"
            documents.append(doc)
            # Serialize metadata to a JSON string
            metadatas.append({"metadata": json.dumps({"type": "action", "name": action["name"]})})
            ids.append(f"action_{i}")

        # Add to collection
        if documents:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
    
    def _compute_file_hash(self, file_path: str) -> str:
        """Compute SHA256 hash of a file for change detection."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            # Read file in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def retrieve(self, query: str, n_results: int = 3) -> list:
        """Retrieve relevant documents"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        retrieved = []
        if results['documents']:
            for doc, metadata in zip(results['documents'][0], 
                                    results['metadatas'][0]):
                retrieved.append({
                    "content": doc,
                    "metadata": json.loads(metadata["metadata"]) if metadata and "metadata" in metadata else {}
                })
        
        return retrieved
    
    def get_context(self, query: str, n_results: int = 3) -> str:
        """Get formatted context for LLM"""
        results = self.retrieve(query, n_results)
        
        if not results:
            return "No relevant information found in knowledge base."
        
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(f"[{i}] {result['content']}")
        
        return "\n\n".join(context_parts)
    
    def search_actions(self, action_name: str) -> dict:
        """Search for specific action details"""
        results = self.collection.query(
            query_texts=[f"action {action_name}"],
            n_results=1,
            where={"type": "action"}
        )
        
        if results['documents'] and results['documents'][0]:
            return {
                "found": True,
                "content": results['documents'][0][0],
                "metadata": results['metadatas'][0][0]
            }
        
        return {"found": False}