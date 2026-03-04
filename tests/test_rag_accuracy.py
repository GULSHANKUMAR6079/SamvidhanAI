"""
Automated RAG Accuracy Tests
Tests citation presence, article accuracy, and response quality.
"""

import pytest
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.rag_chain import ConstitutionRAGChain


# Fixtures
@pytest.fixture(scope="module")
def rag_chain():
    """Initialize RAG chain once for all tests"""
    return ConstitutionRAGChain()


@pytest.fixture(scope="module")
def test_queries():
    """Load test queries"""
    test_file = Path(__file__).parent / "test_queries.json"
    with open(test_file, 'r') as f:
        return json.load(f)


# Test Suite
class TestRAGAccuracy:
    """Test RAG system accuracy"""
    
    def test_basic_queries(self, rag_chain, test_queries):
        """Test basic constitutional queries"""
        for test_case in test_queries['basic_queries']:
            query = test_case['query']
            user_type = test_case['user_type']
            
            result = rag_chain.query(query, user_type)
            answer = result['answer']
            
            # Check answer is not empty
            assert len(answer) > 100, f"Answer too short for: {query}"
            
            # Check expected content
            for expected_term in test_case.get('expected_contains', []):
                assert expected_term.lower() in answer.lower(), \
                    f"Missing '{expected_term}' in answer for: {query}"
            
            # Check citations present
            if test_case.get('expected_citations', False):
                assert '[Source:' in answer or 'Article' in answer, \
                    f"Missing citations for: {query}"
    
    def test_citation_presence(self, rag_chain, test_queries):
        """Test that all responses have citations"""
        for test_case in test_queries['basic_queries']:
            result = rag_chain.query(test_case['query'], test_case['user_type'])
            answer = result['answer']
            
            # Should have source references
            assert ('[Source:' in answer or 
                    'Article' in answer or
                    'Part' in answer), \
                f"No citations found in response to: {test_case['query']}"
    
    def test_out_of_scope_refusal(self, rag_chain, test_queries):
        """Test that out-of-scope queries are refused"""
        for test_case in test_queries['out_of_scope']:
            result = rag_chain.query(test_case['query'], test_case['user_type'])
            answer = result['answer'].lower()
            
            # Should indicate refusal or limitation
            refusal_indicators = [
                'could not find',
                'out of scope',
                'cannot help',
                'only answer questions about'
            ]
            
            has_refusal = any(indicator in answer for indicator in refusal_indicators)
            assert has_refusal, \
                f"Should refuse out-of-scope query: {test_case['query']}"
    
    def test_retrieval_relevance(self, rag_chain):
        """Test that retrieval returns relevant documents"""
        query = "What is Article 21?"
        
        docs, context = rag_chain.retrieve_context(query)
        
        # Should retrieve some documents
        assert len(docs) > 0, "No documents retrieved"
        
        # At least one should mention Article 21
        article_21_found = any(
            '21' in doc.metadata.get('article_number', '') or
            '21' in doc.page_content
            for doc in docs
        )
        
        assert article_21_found, "Retrieved docs don't mention Article 21"
    
    def test_user_type_adaptation(self, rag_chain):
        """Test that responses adapt to user type"""
        query = "What is Article 21?"
        
        student_result = rag_chain.query(query, "Student")
        lawyer_result = rag_chain.query(query, "Lawyer")
        
        student_answer = student_result['answer']
        lawyer_answer = lawyer_result['answer']
        
        # Both should answer
        assert len(student_answer) > 100
        assert len(lawyer_answer) > 100
        
        # Should be somewhat different (not identical)
        # This is a soft check - just ensure they're not exactly the same
        assert student_answer != lawyer_answer, \
            "Student and Lawyer responses should differ"


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
