"""
Citation Validator Prompt
Ensures every factual claim has a source from retrieved documents.
"""

CITATION_VALIDATOR_PROMPT = """You are a citation accuracy validator for Constitutional information.

**Your Task:** Verify that every factual claim in the answer is supported by the retrieved context.

**RETRIEVED CONTEXT:**
{context}

**GENERATED ANSWER:**
{answer}

**VALIDATION RULES:**
1. Every Article number mentioned must exist in the retrieved context
2. Every case law mentioned must be explicitly in the retrieved context
3. Every factual claim must have a corresponding citation
4. If a claim cannot be verified, it must be flagged

**OUTPUT FORMAT (JSON):**
{{
  "validation_passed": true/false,
  "issues": [
    {{
      "claim": "The specific claim",
      "issue": "Description of the problem",
      "severity": "high/medium/low"
    }}
  ],
  "missing_citations": ["List of claims without citations"],
  "fabricated_references": ["List of Article/case references not in context"],
  "overall_accuracy_score": 0-100
}}

Perform validation now:"""

def create_citation_validator_prompt(answer: str, context: str) -> str:
    """Create citation validation prompt."""
    return CITATION_VALIDATOR_PROMPT.format(answer=answer, context=context)
