"""Tests for RAG Engine - TDD implementation"""
import pytest
import json
import os
import tempfile
import hashlib
from unittest.mock import Mock, MagicMock, patch, call
from rag.rag_engine import RAGEngine, MistralLangChainEmbeddingFunction


class TestMistralLangChainEmbeddingFunction:
    """Tests for the embedding function"""
    
    @patch('rag.rag_engine.MistralAIEmbeddings')
    def test_embedding_function_initialization(self, mock_embeddings):
        """Test that embedding function initializes with API key"""
        mock_instance = Mock()
        mock_embeddings.return_value = mock_instance
        
        func = MistralLangChainEmbeddingFunction()
        
        mock_embeddings.assert_called_once_with(
            mistral_api_key=os.environ.get("MISTRAL_API_KEY")
        )
    
    @patch('rag.rag_engine.MistralAIEmbeddings')
    def test_embedding_function_call(self, mock_embeddings):
        """Test that embedding function calls embed_documents"""
        mock_instance = Mock()
        mock_instance.embed_documents.return_value = [[1, 2, 3], [4, 5, 6]]
        mock_embeddings.return_value = mock_instance
        
        func = MistralLangChainEmbeddingFunction()
        result = func(["text1", "text2"])
        
        mock_instance.embed_documents.assert_called_once_with(["text1", "text2"])
        # Just verify it returns the result, don't compare numpy arrays directly
        assert result is not None


class TestRAGEngine:
    """Tests for RAG Engine persistence and hash-based change detection"""
    
    def get_test_knowledge_path(self):
        """Create a temporary knowledge file for testing"""
        knowledge_data = {
            "faqs": [
                {"question": "Test question", "answer": "Test answer"}
            ],
            "policies": [],
            "actions": []
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(knowledge_data, f)
            return f.name
    
    def compute_expected_hash(self, file_path):
        """Compute expected SHA256 hash of a file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()


class TestRAGEngineHashComputation(TestRAGEngine):
    """Tests for hash computation functionality"""
    
    def test_compute_file_hash_raises_on_missing_file(self):
        """Test that _compute_file_hash raises FileNotFoundError for non-existent file"""
        with pytest.raises(FileNotFoundError):
            engine = RAGEngine()
            engine._compute_file_hash("/nonexistent/path/file.json")
    
    def test_compute_file_hash_correct_hash(self):
        """Test that _compute_file_hash computes correct SHA256 hash"""
        knowledge_path = self.get_test_knowledge_path()
        
        try:
            engine = RAGEngine()
            computed_hash = engine._compute_file_hash(knowledge_path)
            
            expected_hash = self.compute_expected_hash(knowledge_path)
            
            assert computed_hash == expected_hash
            assert len(computed_hash) == 64  # SHA256 hex digest is 64 chars
        finally:
            os.unlink(knowledge_path)
    
    def test_compute_file_hash_empty_file(self):
        """Test hash computation on empty file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({}, f)
            temp_path = f.name
        
        try:
            engine = RAGEngine()
            computed_hash = engine._compute_file_hash(temp_path)
            
            # Hash of empty JSON object
            expected_hash = hashlib.sha256(b'{}').hexdigest()
            
            assert computed_hash == expected_hash
        finally:
            os.unlink(temp_path)
    
    def test_compute_file_hash_different_content_different_hash(self):
        """Test that different file content produces different hashes"""
        knowledge_data1 = {"faqs": [{"question": "Q1", "answer": "A1"}]}
        knowledge_data2 = {"faqs": [{"question": "Q2", "answer": "A2"}]}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f1:
            json.dump(knowledge_data1, f1)
            path1 = f1.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f2:
            json.dump(knowledge_data2, f2)
            path2 = f2.name
        
        try:
            engine = RAGEngine()
            hash1 = engine._compute_file_hash(path1)
            hash2 = engine._compute_file_hash(path2)
            
            assert hash1 != hash2
        finally:
            os.unlink(path1)
            os.unlink(path2)


class TestRAGEnginePersistence(TestRAGEngine):
    """Tests for collection persistence behavior"""
    
    @patch('rag.rag_engine.chromadb.Client')
    def test_uses_get_or_create_collection(self, mock_client_class):
        """Test that RAGEngine uses get_or_create_collection instead of delete+create"""
        knowledge_path = self.get_test_knowledge_path()
        
        mock_client = Mock()
        mock_collection = Mock()
        mock_collection.count.return_value = 10
        mock_collection.metadata = {}
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_client_class.return_value = mock_client
        
        try:
            engine = RAGEngine(knowledge_path=knowledge_path)
            
            # Verify get_or_create_collection was called
            mock_client.get_or_create_collection.assert_called_once()
            
            # Verify delete_collection was NOT called
            mock_client.delete_collection.assert_not_called()
            
            # Verify create_collection was NOT called
            mock_client.create_collection.assert_not_called()
        finally:
            os.unlink(knowledge_path)
    
    @patch('rag.rag_engine.chromadb.Client')
    def test_creates_collection_on_first_run(self, mock_client_class):
        """Test that collection is created when it doesn't exist"""
        knowledge_path = self.get_test_knowledge_path()
        
        mock_client = Mock()
        mock_collection = Mock()
        mock_collection.count.return_value = 0  # Empty collection
        mock_collection.metadata = {}
        mock_collection.modify.return_value = None
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_client_class.return_value = mock_client
        
        try:
            engine = RAGEngine(knowledge_path=knowledge_path)
            
            # Collection should be get_or_created
            mock_client.get_or_create_collection.assert_called_once()
            
            # _load_knowledge should be called because collection is empty
            # (and hash is None)
            # We can't directly verify _load_knowledge was called without more mocking
            # but we can verify the collection was get_or_created
        finally:
            os.unlink(knowledge_path)
    
    @patch('rag.rag_engine.chromadb.Client')
    def test_skips_reindex_on_unchanged_file(self, mock_client_class):
        """Test that re-index is skipped when knowledge file hasn't changed"""
        knowledge_path = self.get_test_knowledge_path()
        
        mock_client = Mock()
        mock_collection = Mock()
        
        # Simulate existing collection with stored hash
        current_hash = self.compute_expected_hash(knowledge_path)
        mock_collection.count.return_value = 10  # Has documents
        mock_collection.metadata = {"knowledge_hash": current_hash}
        mock_collection.modify.return_value = None
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_client_class.return_value = mock_client
        
        try:
            engine = RAGEngine(knowledge_path=knowledge_path)
            
            # get_or_create_collection should be called
            mock_client.get_or_create_collection.assert_called_once()
            
            # _load_knowledge should NOT be called because hash matches
            # (We verify by checking modify wasn't called with new hash)
            # Since hash matches, modify should not be called
            mock_collection.modify.assert_not_called()
        finally:
            os.unlink(knowledge_path)
    
    @patch('rag.rag_engine.chromadb.Client')
    def test_reindex_on_changed_file(self, mock_client_class):
        """Test that re-index occurs when knowledge file has changed"""
        knowledge_path = self.get_test_knowledge_path()
        
        mock_client = Mock()
        mock_collection = Mock()
        
        # Simulate existing collection with OLD (different) hash
        old_hash = "old_hash_value_1234567890abcdef"
        mock_collection.count.return_value = 10  # Has documents
        mock_collection.metadata = {"knowledge_hash": old_hash}
        mock_collection.modify.return_value = None
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_client_class.return_value = mock_client
        
        try:
            engine = RAGEngine(knowledge_path=knowledge_path)
            
            # get_or_create_collection should be called
            mock_client.get_or_create_collection.assert_called_once()
            
            # _load_knowledge should be called because hash differs
            # modify should be called to update the hash
            mock_collection.modify.assert_called_once()
            
            # Verify the new hash was stored
            call_args = mock_collection.modify.call_args
            assert 'metadata' in call_args[1]
            assert 'knowledge_hash' in call_args[1]['metadata']
        finally:
            os.unlink(knowledge_path)
    
    @patch('rag.rag_engine.chromadb.Client')
    def test_reindex_on_empty_collection(self, mock_client_class):
        """Test that re-index occurs when collection is empty (first run)"""
        knowledge_path = self.get_test_knowledge_path()
        
        mock_client = Mock()
        mock_collection = Mock()
        
        # Empty collection (count = 0)
        mock_collection.count.return_value = 0
        mock_collection.metadata = {}  # No stored hash
        mock_collection.modify.return_value = None
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_client_class.return_value = mock_client
        
        try:
            engine = RAGEngine(knowledge_path=knowledge_path)
            
            # get_or_create_collection should be called
            mock_client.get_or_create_collection.assert_called_once()
            
            # _load_knowledge should be called because collection is empty
            # modify should be called to store the hash
            mock_collection.modify.assert_called_once()
        finally:
            os.unlink(knowledge_path)
    
    @patch('rag.rag_engine.chromadb.Client')
    def test_collection_name_constant(self, mock_client_class):
        """Test that collection uses correct name"""
        knowledge_path = self.get_test_knowledge_path()
        
        mock_client = Mock()
        mock_collection = Mock()
        mock_collection.count.return_value = 0
        mock_collection.metadata = {}
        mock_collection.modify.return_value = None
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_client_class.return_value = mock_client
        
        try:
            engine = RAGEngine(knowledge_path=knowledge_path)
            
            # Verify get_or_create_collection was called with correct name
            call_args = mock_client.get_or_create_collection.call_args
            assert call_args[1]['name'] == "dbs_banking"
        finally:
            os.unlink(knowledge_path)
    
    @patch('rag.rag_engine.chromadb.Client')
    def test_uses_embeddding_function(self, mock_client_class):
        """Test that collection uses the Mistral embedding function"""
        knowledge_path = self.get_test_knowledge_path()
        
        mock_client = Mock()
        mock_collection = Mock()
        mock_collection.count.return_value = 0
        mock_collection.metadata = {}
        mock_collection.modify.return_value = None
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_client_class.return_value = mock_client
        
        try:
            engine = RAGEngine(knowledge_path=knowledge_path)
            
            # Verify get_or_create_collection was called with embedding_function
            call_args = mock_client.get_or_create_collection.call_args
            assert 'embedding_function' in call_args[1]
            assert isinstance(call_args[1]['embedding_function'], MistralLangChainEmbeddingFunction)
        finally:
            os.unlink(knowledge_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
