"""
Query Expansion Prompt for Better Retrieval
Expands user queries to improve vector search results.
"""

RETRIEVER_PROMPT = """You are a query expansion specialist for Constitutional queries.

Your task: Transform the user's question into optimized search queries for retrieving relevant Constitutional articles.

**Instructions:**
1. Identify key constitutional concepts
2. Expand abbreviations (FR → Fundamental Rights, DPSP → Directive Principles)
3. Identify potential Article numbers
4. Add constitutional context (Part, Schedule names)
5. Generate 3-5 search variations

**User Question:** {question}

**User Type:** {user_type}

**Output Format (JSON):**
{{
  "expanded_queries": ["query1", "query2", "query3"],
  "potential_articles": ["Article 21", "Article 22"],
  "constitutional_context": ["Part III", "Fundamental Rights"],
  "search_strategy": "brief explanation"
}}

Generate the JSON now:"""

def create_retriever_prompt(question: str, user_type: str = "Student") -> str:
    """Create retriever prompt with user context."""
    return RETRIEVER_PROMPT.format(question=question, user_type=user_type)
