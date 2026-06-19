# RAG Engine - ChromaDB vector store
"""RAG engine using ChromaDB"""
import hashlib
import json
import os
import chromadb
from chromadb.config import Settings
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
from langchain_mistralai.embeddings import MistralAIEmbeddings
from pathlib import Path

class MistralLangChainEmbeddingFunction(EmbeddingFunction):
    def __init__(self):
        self._mistral_embedder = MistralAIEmbeddings(mistral_api_key=os.environ.get("MISTRAL_API_KEY"))

    def __call__(self, texts: Documents) -> Embeddings:
        return self._mistral_embedder.embed_documents(texts)

class RAGEngine:
    """Retrieval Augmented Generation engine"""
    
    def __init__(self, knowledge_path="knowledge_docs/faqs.json",
                 persist_dir="chroma_db"):
        self.knowledge_path = knowledge_path
        self.client = chromadb.Client(Settings(
            persist_directory=persist_dir,
            anonymized_telemetry=False
        ))

        embedding_function = MistralLangChainEmbeddingFunction()

        # Use get_or_create_collection to preserve existing collection
        self.collection = self.client.get_or_create_collection(
            name="dbs_banking",
            embedding_function=embedding_function,
            metadata={"description": "DBS Banking knowledge base"}
        )

        # Only re-index if knowledge source has changed
        if self._knowledge_changed():
            self._reindex_knowledge()

    def _load_knowledge(self, knowledge_path: str):
        """Load FAQs and policies into ChromaDB"""
        try:
            with open(knowledge_path, 'r') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # If file doesn't exist or is corrupted, log and return
            return

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

    def _compute_knowledge_hash(self) -> str:
        """Compute SHA256 hash of knowledge file contents."""
        path = Path(self.knowledge_path)
        if not path.exists():
            return ""
        
        with open(path, 'rb') as f:
            content = f.read()
        
        return hashlib.sha256(content).hexdigest()

    def _get_stored_hash(self) -> str:
        """Retrieve stored knowledge hash from collection metadata."""
        try:
            # Check if we have a stored hash in the collection's own metadata
            if "knowledge_hash" in self.collection.metadata:
                return self.collection.metadata["knowledge_hash"]
        except Exception:
            pass
        return ""

    def _store_knowledge_hash(self, knowledge_hash: str):
        """Store knowledge hash in collection metadata."""
        try:
            # Update collection metadata with new hash
            self.collection.modify(
                name="dbs_banking",
                metadata={
                    **self.collection.metadata,
                    "knowledge_hash": knowledge_hash
                }
            )
        except Exception:
            # Fallback: log but don't fail
            pass

    def _knowledge_changed(self) -> bool:
        """Check if knowledge source has changed since last indexing."""
        current_hash = self._compute_knowledge_hash()
        stored_hash = self._get_stored_hash()
        
        # If no stored hash, this is first run - need to index
        if not stored_hash:
            return True
        
        return current_hash != stored_hash

    def _reindex_knowledge(self):
        """Clear existing collection and re-index all documents."""
        # Clear existing documents
        try:
            self.collection.delete(where={})  # Delete all documents
        except Exception:
            pass  # Collection may be empty, that's fine
        
        # Load fresh knowledge
        self._load_knowledge(self.knowledge_path)
        
        # Store new hash
        new_hash = self._compute_knowledge_hash()
        self._store_knowledge_hash(new_hash)
    
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