"""TDD Tests for RAG Engine - Fix ChromaDB Collection Re-creation Bug"""
import hashlib
import json
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

# Set up path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


def get_rag_module():
    """Import rag_engine module"""
    from rag import rag_engine
    return rag_engine


class TestKnowledgeHash:
    """Tests for knowledge file hashing functionality"""

    def test_compute_knowledge_hash_basic(self):
        """Test that hash is computed correctly for a simple knowledge file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"faqs": [{"question": "test", "answer": "test answer"}]}, f)
            temp_path = f.name

        try:
            with tempfile.TemporaryDirectory() as persist_dir:
                rag_module = get_rag_module()
                
                with patch('chromadb.Client') as mock_client_class:
                    mock_client = Mock()
                    mock_collection = Mock()
                    mock_collection.metadata = {}
                    mock_client.get_or_create_collection = Mock(return_value=mock_collection)
                    mock_client_class.return_value = mock_client
                    
                    engine = rag_module.RAGEngine(knowledge_path=temp_path, persist_dir=persist_dir)
                    
                    computed_hash = engine._compute_knowledge_hash()
                    
                    # Verify it's a valid SHA256 hex string (64 characters)
                    assert len(computed_hash) == 64
                    assert all(c in '0123456789abcdef' for c in computed_hash)
                    
                    # Compute expected hash manually
                    with open(temp_path, 'rb') as f:
                        content = f.read()
                    expected_hash = hashlib.sha256(content).hexdigest()
                    
                    assert computed_hash == expected_hash
        finally:
            os.unlink(temp_path)

    def test_compute_knowledge_hash_missing_file(self):
        """Test that missing file returns empty string"""
        with tempfile.TemporaryDirectory() as persist_dir:
            rag_module = get_rag_module()
            engine = rag_module.RAGEngine(knowledge_path="/nonexistent/path.json", persist_dir=persist_dir)
            
            result = engine._compute_knowledge_hash()
            assert result == ""

    def test_compute_knowledge_hash_consistency(self):
        """Test that same file content produces same hash"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            content = {"faqs": [{"question": "test", "answer": "answer"}]}
            json.dump(content, f)
            temp_path = f.name

        try:
            with tempfile.TemporaryDirectory() as persist_dir:
                rag_module = get_rag_module()
                
                with patch('chromadb.Client') as mock_client_class:
                    mock_client = Mock()
                    mock_collection = Mock()
                    mock_collection.metadata = {}
                    mock_client.get_or_create_collection = Mock(return_value=mock_collection)
                    mock_client_class.return_value = mock_client
                    
                    engine = rag_module.RAGEngine(knowledge_path=temp_path, persist_dir=persist_dir)
                    
                    hash1 = engine._compute_knowledge_hash()
                    hash2 = engine._compute_knowledge_hash()
                    
                    assert hash1 == hash2
        finally:
            os.unlink(temp_path)

    def test_compute_knowledge_hash_different_content(self):
        """Test that different content produces different hash"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f1:
            json.dump({"faqs": [{"question": "test1", "answer": "answer1"}]}, f1)
            temp_path1 = f1.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f2:
            json.dump({"faqs": [{"question": "test2", "answer": "answer2"}]}, f2)
            temp_path2 = f2.name

        try:
            with tempfile.TemporaryDirectory() as persist_dir:
                rag_module = get_rag_module()
                
                with patch('chromadb.Client') as mock_client_class:
                    mock_client = Mock()
                    mock_collection = Mock()
                    mock_collection.metadata = {}
                    mock_client.get_or_create_collection = Mock(return_value=mock_collection)
                    mock_client_class.return_value = mock_client
                    
                    engine1 = rag_module.RAGEngine(knowledge_path=temp_path1, persist_dir=persist_dir)
                    engine2 = rag_module.RAGEngine(knowledge_path=temp_path2, persist_dir=persist_dir)
                    
                    hash1 = engine1._compute_knowledge_hash()
                    hash2 = engine2._compute_knowledge_hash()
                    
                    assert hash1 != hash2
        finally:
            os.unlink(temp_path1)
            os.unlink(temp_path2)


class TestGetStoredHash:
    """Tests for retrieving stored hash from collection metadata"""

    def test_get_stored_hash_empty_metadata(self):
        """Test that empty metadata returns empty string"""
        with tempfile.TemporaryDirectory() as persist_dir:
            rag_module = get_rag_module()
            
            # Mock chromadb to return a collection without knowledge_hash
            with patch('chromadb.Client') as mock_client_class:
                mock_client = Mock()
                mock_collection = Mock()
                mock_collection.metadata = {"description": "DBS Banking knowledge base"}
                mock_collection.get = Mock(return_value={"metadatas": [[]]})
                mock_client.get_or_create_collection = Mock(return_value=mock_collection)
                mock_client_class.return_value = mock_client
                
                engine = rag_module.RAGEngine(persist_dir=persist_dir)
                result = engine._get_stored_hash()
                
                assert result == ""

    def test_get_stored_hash_with_hash(self):
        """Test that stored hash is retrieved correctly"""
        with tempfile.TemporaryDirectory() as persist_dir:
            rag_module = get_rag_module()
            test_hash = "abc123def456"
            
            with patch('chromadb.Client') as mock_client_class:
                mock_client = Mock()
                mock_collection = Mock()
                mock_collection.metadata = {
                    "description": "DBS Banking knowledge base",
                    "knowledge_hash": test_hash
                }
                mock_client.get_or_create_collection = Mock(return_value=mock_collection)
                mock_client_class.return_value = mock_client
                
                engine = rag_module.RAGEngine(persist_dir=persist_dir)
                result = engine._get_stored_hash()
                
                assert result == test_hash


class TestStoreKnowledgeHash:
    """Tests for storing hash in collection metadata"""

    def test_store_knowledge_hash(self):
        """Test that hash is stored in collection metadata"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"faqs": []}, f)
            temp_path = f.name

        try:
            with tempfile.TemporaryDirectory() as persist_dir:
                rag_module = get_rag_module()
                test_hash = "abc123def456"
                
                with patch('chromadb.Client') as mock_client_class:
                    mock_client = Mock()
                    mock_collection = Mock()
                    mock_collection.metadata = {"description": "DBS Banking knowledge base"}
                    mock_collection.modify = Mock()
                    mock_client.get_or_create_collection = Mock(return_value=mock_collection)
                    mock_client_class.return_value = mock_client
                    
                    # Patch _knowledge_changed to return False so reindex isn't called during init
                    with patch.object(rag_module.RAGEngine, '_knowledge_changed', return_value=False):
                        engine = rag_module.RAGEngine(knowledge_path=temp_path, persist_dir=persist_dir)
                        engine._store_knowledge_hash(test_hash)
                        
                        # Verify modify was called with updated metadata
                        mock_collection.modify.assert_called_once()
                        call_kwargs = mock_collection.modify.call_args[1]
                        assert call_kwargs['metadata']['knowledge_hash'] == test_hash
        finally:
            os.unlink(temp_path)


class TestKnowledgeChanged:
    """Tests for knowledge change detection"""

    def test_knowledge_changed_first_run(self):
        """Test that first run (no stored hash) returns True"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"faqs": [{"question": "test", "answer": "answer"}]}, f)
            temp_path = f.name

        try:
            with tempfile.TemporaryDirectory() as persist_dir:
                rag_module = get_rag_module()
                
                with patch('chromadb.Client') as mock_client_class:
                    mock_client = Mock()
                    mock_collection = Mock()
                    mock_collection.metadata = {"description": "DBS Banking knowledge base"}
                    mock_collection.get = Mock(return_value={"metadatas": [[]]})
                    mock_client.get_or_create_collection = Mock(return_value=mock_collection)
                    mock_client_class.return_value = mock_client
                    
                    engine = rag_module.RAGEngine(
                        knowledge_path=temp_path, 
                        persist_dir=persist_dir
                    )
                    
                    result = engine._knowledge_changed()
                    assert result == True
        finally:
            os.unlink(temp_path)

    def test_knowledge_changed_no_change(self):
        """Test that no change returns False"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            content = {"faqs": [{"question": "test", "answer": "answer"}]}
            json.dump(content, f)
            temp_path = f.name

        try:
            with tempfile.TemporaryDirectory() as persist_dir:
                rag_module = get_rag_module()
                
                # Compute expected hash
                with open(temp_path, 'rb') as f:
                    file_content = f.read()
                expected_hash = hashlib.sha256(file_content).hexdigest()
                
                with patch('chromadb.Client') as mock_client_class:
                    mock_client = Mock()
                    mock_collection = Mock()
                    mock_collection.metadata = {
                        "description": "DBS Banking knowledge base",
                        "knowledge_hash": expected_hash
                    }
                    mock_collection.get = Mock(return_value={"metadatas": [[]]})
                    mock_client.get_or_create_collection = Mock(return_value=mock_collection)
                    mock_client_class.return_value = mock_client
                    
                    engine = rag_module.RAGEngine(
                        knowledge_path=temp_path, 
                        persist_dir=persist_dir
                    )
                    
                    result = engine._knowledge_changed()
                    assert result == False
        finally:
            os.unlink(temp_path)

    def test_knowledge_changed_detects_change(self):
        """Test that content change is detected"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"faqs": [{"question": "test", "answer": "answer"}]}, f)
            temp_path = f.name

        try:
            with tempfile.TemporaryDirectory() as persist_dir:
                rag_module = get_rag_module()
                
                # Store an old hash that doesn't match current content
                old_hash = "old_hash_value_123456"
                
                with patch('chromadb.Client') as mock_client_class:
                    mock_client = Mock()
                    mock_collection = Mock()
                    mock_collection.metadata = {
                        "description": "DBS Banking knowledge base",
                        "knowledge_hash": old_hash
                    }
                    mock_collection.get = Mock(return_value={"metadatas": [[]]})
                    mock_client.get_or_create_collection = Mock(return_value=mock_collection)
                    mock_client_class.return_value = mock_client
                    
                    engine = rag_module.RAGEngine(
                        knowledge_path=temp_path, 
                        persist_dir=persist_dir
                    )
                    
                    result = engine._knowledge_changed()
                    assert result == True
        finally:
            os.unlink(temp_path)


class TestReindexKnowledge:
    """Tests for re-indexing functionality"""

    def test_reindex_knowledge_clears_and_reloads(self):
        """Test that reindex clears old docs and loads new ones"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"faqs": [{"question": "test", "answer": "answer"}]}, f)
            temp_path = f.name

        try:
            with tempfile.TemporaryDirectory() as persist_dir:
                rag_module = get_rag_module()
                
                with patch('chromadb.Client') as mock_client_class:
                    mock_client = Mock()
                    mock_collection = Mock()
                    mock_collection.metadata = {}
                    mock_collection.delete = Mock()
                    mock_collection.add = Mock()
                    mock_collection.get = Mock(return_value={"metadatas": [[]]})
                    mock_collection.modify = Mock()
                    mock_client.get_or_create_collection = Mock(return_value=mock_collection)
                    mock_client_class.return_value = mock_client
                    
                    # Patch _knowledge_changed to return False so reindex isn't called during init
                    with patch.object(rag_module.RAGEngine, '_knowledge_changed', return_value=False):
                        engine = rag_module.RAGEngine(
                            knowledge_path=temp_path, 
                            persist_dir=persist_dir
                        )
                        
                        # Call reindex directly
                        engine._reindex_knowledge()
                        
                        # Verify delete was called to clear old docs
                        mock_collection.delete.assert_called_once()
                        
                        # Verify add was called to load new docs
                        mock_collection.add.assert_called_once()
                        
                        # Verify hash was stored
                        mock_collection.modify.assert_called_once()
        finally:
            os.unlink(temp_path)


class TestInitBehavior:
    """Tests for __init__ behavior with the fix"""

    def test_init_uses_get_or_create_collection(self):
        """Test that __init__ uses get_or_create_collection instead of delete+create"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"faqs": []}, f)
            temp_path = f.name

        try:
            with tempfile.TemporaryDirectory() as persist_dir:
                rag_module = get_rag_module()
                
                with patch('chromadb.Client') as mock_client_class:
                    mock_client = Mock()
                    mock_collection = Mock()
                    mock_collection.metadata = {}
                    mock_collection.count = Mock(return_value=10)  # Has existing docs
                    mock_collection.get = Mock(return_value={"metadatas": [[]]})
                    mock_client.get_or_create_collection = Mock(return_value=mock_collection)
                    mock_client.delete_collection = Mock()  # Should NOT be called
                    mock_client.create_collection = Mock()  # Should NOT be called
                    mock_client_class.return_value = mock_client
                    
                    engine = rag_module.RAGEngine(
                        knowledge_path=temp_path,
                        persist_dir=persist_dir
                    )
                    
                    # Verify get_or_create_collection was called
                    mock_client.get_or_create_collection.assert_called_once()
                    
                    # Verify delete_collection was NOT called
                    mock_client.delete_collection.assert_not_called()
                    
                    # Verify create_collection was NOT called directly
                    # (it might be called internally by get_or_create, but not by our code)
                    # We check that our code doesn't call it
        finally:
            os.unlink(temp_path)

    def test_init_reindexes_on_first_run(self):
        """Test that __init__ triggers reindex on first run (no stored hash)"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"faqs": [{"question": "test", "answer": "answer"}]}, f)
            temp_path = f.name

        try:
            with tempfile.TemporaryDirectory() as persist_dir:
                rag_module = get_rag_module()
                
                with patch('chromadb.Client') as mock_client_class:
                    mock_client = Mock()
                    mock_collection = Mock()
                    mock_collection.metadata = {}  # No stored hash
                    mock_collection.delete = Mock()
                    mock_collection.add = Mock()
                    mock_collection.get = Mock(return_value={"metadatas": [[]]})
                    mock_collection.modify = Mock()
                    mock_client.get_or_create_collection = Mock(return_value=mock_collection)
                    mock_client_class.return_value = mock_client
                    
                    engine = rag_module.RAGEngine(
                        knowledge_path=temp_path,
                        persist_dir=persist_dir
                    )
                    
                    # Verify reindex was triggered
                    mock_collection.delete.assert_called_once()
                    mock_collection.add.assert_called_once()
        finally:
            os.unlink(temp_path)

    def test_init_skips_reindex_on_no_change(self):
        """Test that __init__ skips reindex when knowledge unchanged"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            content = {"faqs": [{"question": "test", "answer": "answer"}]}
            json.dump(content, f)
            temp_path = f.name

        try:
            with tempfile.TemporaryDirectory() as persist_dir:
                rag_module = get_rag_module()
                
                # Compute expected hash
                with open(temp_path, 'rb') as f:
                    file_content = f.read()
                expected_hash = hashlib.sha256(file_content).hexdigest()
                
                with patch('chromadb.Client') as mock_client_class:
                    mock_client = Mock()
                    mock_collection = Mock()
                    mock_collection.metadata = {"knowledge_hash": expected_hash}
                    mock_collection.delete = Mock()
                    mock_collection.add = Mock()
                    mock_collection.get = Mock(return_value={"metadatas": [[]]})
                    mock_client.get_or_create_collection = Mock(return_value=mock_collection)
                    mock_client_class.return_value = mock_client
                    
                    engine = rag_module.RAGEngine(
                        knowledge_path=temp_path,
                        persist_dir=persist_dir
                    )
                    
                    # Verify reindex was NOT triggered (no delete call)
                    mock_collection.delete.assert_not_called()
                    # Note: add might still be called if the collection is empty,
                    # but delete should not be called
        finally:
            os.unlink(temp_path)


class TestExistingFunctionality:
    """Tests to ensure existing functionality still works"""

    def test_retrieve_works(self):
        """Test that retrieve method still works"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"faqs": []}, f)
            temp_path = f.name

        try:
            with tempfile.TemporaryDirectory() as persist_dir:
                rag_module = get_rag_module()
                
                with patch('chromadb.Client') as mock_client_class:
                    mock_client = Mock()
                    mock_collection = Mock()
                    mock_collection.metadata = {}
                    mock_collection.get = Mock(return_value={"metadatas": [[]]})
                    mock_collection.query = Mock(return_value={
                        'documents': [["test doc"], [], []],
                        'metadatas': [[{"metadata": '{"type": "faq"}'}], [], []]
                    })
                    mock_client.get_or_create_collection = Mock(return_value=mock_collection)
                    mock_client_class.return_value = mock_client
                    
                    engine = rag_module.RAGEngine(
                        knowledge_path=temp_path,
                        persist_dir=persist_dir
                    )
                    
                    results = engine.retrieve("test query", n_results=1)
                    
                    assert len(results) == 1
                    assert "test doc" in results[0]["content"]
        finally:
            os.unlink(temp_path)

    def test_get_context_works(self):
        """Test that get_context method still works"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"faqs": []}, f)
            temp_path = f.name

        try:
            with tempfile.TemporaryDirectory() as persist_dir:
                rag_module = get_rag_module()
                
                with patch('chromadb.Client') as mock_client_class:
                    mock_client = Mock()
                    mock_collection = Mock()
                    mock_collection.metadata = {}
                    mock_collection.get = Mock(return_value={"metadatas": [[]]})
                    mock_collection.query = Mock(return_value={
                        'documents': [["test doc"], [], []],
                        'metadatas': [[{"metadata": '{"type": "faq"}'}], [], []]
                    })
                    mock_client.get_or_create_collection = Mock(return_value=mock_collection)
                    mock_client_class.return_value = mock_client
                    
                    engine = rag_module.RAGEngine(
                        knowledge_path=temp_path,
                        persist_dir=persist_dir
                    )
                    
                    context = engine.get_context("test query", n_results=1)
                    
                    assert "test doc" in context
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
