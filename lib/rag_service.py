from __future__ import annotations

import re
from typing import Any

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "can",
    "do",
    "does",
    "for",
    "from",
    "get",
    "how",
    "i",
    "if",
    "in",
    "is",
    "it",
    "me",
    "my",
    "need",
    "of",
    "on",
    "or",
    "our",
    "should",
    "so",
    "the",
    "their",
    "to",
    "use",
    "what",
    "when",
    "where",
    "who",
    "why",
    "with",
    "you",
    "your",
}


def tokenize(text: str) -> set[str]:
    """Convert text into a set of searchable lowercase tokens.

    TODO:
    - Lowercase the text.
    - Extract word-like values.
    - Remove leading/trailing apostrophes.
    - Remove tokens with length <= 1.
    - Remove tokens in STOPWORDS.
    - Return a set of searchable terms.
    """
    # TODO: 
    words = re.findall(r"[a-z0-9']+", text.lower())
    cleaned = {word.strip("'") for word in words}
    return {word for word in cleaned if len(word) > 1 and word not in STOPWORDS}
   


def document_search_text(document: dict[str, Any]) -> str:
    """Combine searchable document fields into one text value.

    TODO:
    Include title, category, tags, and text.
    """
    return " ".join(
        [
            document["title"],
            document["category"],
            " ".join(document["tags"]),
            document["text"]
        ]
    )


def score_document(query: str, document: dict[str, Any]) -> dict[str, Any]:

    query_tokens = tokenize(query)
    document_tokens = tokenize(document_search_text(document))
    title_tokens = tokenize(document["title"])

    matched_terms = query_tokens & document_tokens
    title_matches = query_tokens & title_tokens

    score = len(matched_terms) + 0.5 * len(title_matches)
    return {
        "document": document,
        "score": score,
        "matched_terms": sorted(matched_terms),
    }


def retrieve_context(
    query: str,
    documents: list[dict[str, Any]],
    limit: int = 2,
    minimum_score: float = 1.0,
) -> list[dict[str, Any]]:
    """Select the most relevant documents for the query.

    TODO:
    - Score all documents.
    - Keep only matches with score >= minimum_score.
    - Sort by score from highest to lowest.
    - Return only the top `limit` matches.

    The selected context must depend on the user's query. Do not return the same
    hardcoded document for every request.
    """
    scored = [score_document(query, document) for document in documents]
    relevant = [match for match in scored if match["score"] >= minimum_score]
    relevant.sort(key=lambda match: match["score"], reverse=True)
    return relevant[:limit]


def format_context(context_matches: list[dict[str, Any]]) -> str:
    """Format retrieved documents into a context block for the prompt.

    TODO:
    - If no matches exist, return a short no-context message.
    - For each match, include Source ID, Title, Category, and Content.
    - Separate document blocks clearly.
    """
    if not context_matches:
        return "No relevant context was found in the approved company documents."

    blocks = []
    for match in context_matches:
        document = match["document"]
        blocks.append(
            f"Source ID: {document['id']}\n"
            f"Title: {document['title']}\n"
            f"Category: {document['category']}\n"
            f"Content: {document['text']}"
        )

    return "\n\n---\n\n".join(blocks)

def build_prompt(query: str, context_matches: list[dict[str, Any]]) -> str:
    """Build a structured prompt with instructions, context, question, and requirements.

    TODO:
    The prompt should include these sections:
    - Instructions
    - Context
    - Question
    - Response requirements

    The prompt should tell the model to use only the provided context and avoid
    inventing unsupported details.
    """
    context = format_context(context_matches)
    return (
        "Instructions:\n"
        "You are a helpful assistant for company employees. "
        "Use only the information in the Context section to answer. "
        "Do not invent details that are not supported by the context.\n\n"
        f"Context:\n{context}\n\n"
        f"Question:\n{query}\n\n"
        "Response requirements:\n"
        "- Answer clearly and briefly.\n"
        "- Mention the Source ID of each document you used.\n"
        "- If the context does not answer the question, say so.\n"
        )


def source_metadata(match: dict[str, Any]) -> dict[str, str]:
    """Return source information that is safe to expose in the API response.

    TODO:
    Return only the document id and title.
    """
    document = match["document"]
    return {
        "id": document["id"],
        "title": document["title"]
    }
