"""
RAG Chain Implementation
Orchestrates the complete Retrieval-Augmented Generation pipeline.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from config import ModelConfig, GOOGLE_API_KEY, logger

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import HumanMessage, SystemMessage
except ImportError as e:
    logger.error(f"Required libraries not installed: {e}")
    sys.exit(1)

from src.vector_store import ConstitutionVectorStore
from src.prompts.retriever_prompt import create_retriever_prompt
from src.prompts.answer_prompt import create_answer_prompt
from src.prompts.citation_validator_prompt import create_citation_validator_prompt
from src.prompts.refusal_prompt import create_refusal_prompt


class ConstitutionRAGChain:
    """
    Complete RAG pipeline for Constitutional queries.
    
    Pipeline:
    1. Query Expansion (optional, for complex queries)
    2. Retrieval from Vector Store
    3. Context Assembly
    4. Answer Generation with Gemini
    5. Citation Validation (optional, for production)
    6. Structured Response Formatting
    """
    
    def __init__(self):
        logger.info("🔗 Initializing RAG Chain...")
        
        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model=ModelConfig.GEMINI_MODEL,
            google_api_key=GOOGLE_API_KEY,
            temperature=ModelConfig.TEMPERATURE,
            max_output_tokens=ModelConfig.MAX_OUTPUT_TOKENS
        )
        
        # Initialize Vector Store
        self.vector_store = ConstitutionVectorStore()
        self.vector_store.initialize_chromadb()
        
        logger.info("✅ RAG Chain initialized")
    
    def query_expansion(self, question: str, user_type: str) -> Dict[str, Any]:
        """
        Expand query for better retrieval (optional step).
        """
        logger.info("🔄 Expanding query...")
        
        try:
            prompt = create_retriever_prompt(question, user_type)
            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            # Parse JSON response
            content = response.content.strip()
            
            # Extract JSON from markdown if needed
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            expansion = json.loads(content)
            logger.info(f"   Expanded to {len(expansion.get('expanded_queries', []))} queries")
            
            return expansion
            
        except Exception as e:
            logger.warning(f"Query expansion failed: {e}, using original query")
            return {
                "expanded_queries": [question],
                "potential_articles": [],
                "constitutional_context": []
            }
    
    def retrieve_context(
        self, 
        question: str, 
        expanded_queries: List[str] = None,
        k: int = 5
    ) -> tuple:
        """
        Retrieve relevant documents from vector store.
        
        Returns:
            (retrieved_documents, formatted_context_string)
        """
        logger.info("📚 Retrieving context...")
        
        # Use expanded queries or original
        queries = expanded_queries if expanded_queries else [question]
        
        # Retrieve for each query and deduplicate
        all_docs = []
        seen_texts = set()
        
        for query in queries[:3]:  # Limit to top 3 queries
            docs = self.vector_store.hybrid_search(query, k=k)
            
            for doc in docs:
                # Deduplicate by text content
                text_hash = hash(doc.page_content[:100])
                if text_hash not in seen_texts:
                    all_docs.append(doc)
                    seen_texts.add(text_hash)
        
        # Limit total docs
        all_docs = all_docs[:k]
        
        logger.info(f"   Retrieved {len(all_docs)} unique documents")
        
        # Format context
        context_parts = []
        for i, doc in enumerate(all_docs, 1):
            metadata = doc.metadata
            context_parts.append(
                f"[Document {i}]\n"
                f"Article: {metadata.get('article_number', 'N/A')}\n"
                f"Part: {metadata.get('part', 'N/A')}\n"
                f"Title: {metadata.get('title', 'N/A')}\n"
                f"Content: {doc.page_content}\n"
            )
        
        formatted_context = "\n---\n".join(context_parts)
        
        return all_docs, formatted_context
    
    def generate_answer(
        self, 
        question: str, 
        context: str, 
        user_type: str
    ) -> str:
        """
        Generate structured answer using Gemini.
        """
        logger.info("✍️ Generating answer...")
        
        try:
            prompt = create_answer_prompt(question, context, user_type)
            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            answer = response.content.strip()
            logger.info(f"   Generated {len(answer)} characters")
            
            return answer
            
        except Exception as e:
            logger.error(f"❌ Answer generation failed: {e}")
            return self._generate_error_response(question, str(e))
    
    def validate_citations(self, answer: str, context: str) -> Dict[str, Any]:
        """
        Validate that answer has proper citations.
        """
        logger.info("🔍 Validating citations...")
        
        try:
            prompt = create_citation_validator_prompt(answer, context)
            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            content = response.content.strip()
            
            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            validation = json.loads(content)
            
            if validation.get("validation_passed", True):
                logger.info("   ✅ Citations validated")
            else:
                logger.warning(f"   ⚠️ Validation issues: {len(validation.get('issues', []))}")
            
            return validation
            
        except Exception as e:
            logger.warning(f"Citation validation failed: {e}")
            return {"validation_passed": True, "issues": []}
    
    def check_if_out_of_scope(self, question: str, context: str) -> tuple:
        """
        Check if question is out of scope or has insufficient context.
        
        Returns:
            (is_out_of_scope: bool, refusal_message: str)
        """
        # Simple heuristics
        out_of_scope_keywords = [
            "who to vote", "which party", "political opinion",
            "recommend", "prediction", "future"
        ]
        
        question_lower = question.lower()
        for keyword in out_of_scope_keywords:
            if keyword in question_lower:
                logger.info("⛔ Question detected as out-of-scope")
                
                # Generate refusal message
                prompt = create_refusal_prompt(question, context)
                response = self.llm.invoke([HumanMessage(content=prompt)])
                return True, response.content.strip()
        
        # Check if context is too sparse
        if len(context) < 200:
            logger.warning("⚠️ Retrieved context is sparse")
            # Might want to generate refusal here too
        
        return False, ""
    
    def query(
        self, 
        question: str, 
        user_type: str = "Student",
        use_query_expansion: bool = False,
        validate_citations: bool = False
    ) -> Dict[str, Any]:
        """
        Complete query method - the main entry point.
        
        Args:
            question: User's question
            user_type: Student, Lawyer, Citizen, or Competitive Exam
            use_query_expansion: Whether to use query expansion
            validate_citations: Whether to validate citations
        
        Returns:
            Dictionary with answer, context, metadata
        """
        logger.info("=" * 50)
        logger.info(f"🏛️ Query: {question}")
        logger.info(f"👤 User Type: {user_type}")
        logger.info("=" * 50)
        
        try:
            # Step 1: Query Expansion (optional)
            expanded_queries = None
            if use_query_expansion:
                expansion = self.query_expansion(question, user_type)
                expanded_queries = expansion.get('expanded_queries')
            
            # Step 2: Retrieve Context
            retrieved_docs, formatted_context = self.retrieve_context(
                question, 
                expanded_queries
            )
            
            # Step 3: Check if out of scope
            is_out_of_scope, refusal_msg = self.check_if_out_of_scope(
                question, 
                formatted_context
            )
            
            if is_out_of_scope:
                return {
                    "answer": refusal_msg,
                    "context": formatted_context,
                    "retrieved_docs": retrieved_docs,
                    "user_type": user_type,
                    "out_of_scope": True
                }
            
            # Step 4: Generate Answer
            answer = self.generate_answer(question, formatted_context, user_type)
            
            # Step 5: Validate Citations (optional)
            validation_result = None
            if validate_citations:
                validation_result = self.validate_citations(answer, formatted_context)
            
            # Step 6: Return structured response
            result = {
                "answer": answer,
                "context": formatted_context,
                "retrieved_docs": retrieved_docs,
                "user_type": user_type,
                "out_of_scope": False,
                "validation": validation_result
            }
            
            logger.info("✅ Query completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"❌ Query failed: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "answer": self._generate_error_response(question, str(e)),
                "context": "",
                "retrieved_docs": [],
                "user_type": user_type,
                "error": str(e)
            }
    
    def _generate_error_response(self, question: str, error: str) -> str:
        """Generate user-friendly error message."""
        return f"""❌ I encountered an error while processing your question.

**Your Question:** {question}

**Error:** {error}

**Suggestions:**
- Please try rephrasing your question
- Make sure your question is about the Constitution of India
- Check that the system is properly initialized

If the problem persists, please contact support."""


def main():
    """
    Test the RAG chain with sample queries.
    """
    logger.info("🧪 Testing RAG Chain...")
    
    # Initialize chain
    rag_chain = ConstitutionRAGChain()
    
    # Test queries
    test_queries = [
        ("What is Article 21?", "Student"),
        ("Explain Fundamental Rights", "Citizen"),
        ("Who should I vote for?", "Student"),  # Out of scope
    ]
    
    for question, user_type in test_queries:
        print("\n" + "=" * 50)
        print(f"Q: {question}")
        print(f"User Type: {user_type}")
        print("=" * 50)
        
        result = rag_chain.query(question, user_type)
        
        print(result['answer'])
        print("\n")


if __name__ == "__main__":
    main()
