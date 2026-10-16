from __future__ import annotations

from flask import Flask, jsonify, request

from lib.ai_client import generate_response
from lib.company_documents import COMPANY_DOCUMENTS
from lib.rag_service import build_prompt, retrieve_context, source_metadata


def create_app():
    app = Flask(__name__)

    @app.get("/api/health")
    def health_check():
        return jsonify({"status": "ok"})

    @app.post("/api/ask")
    def ask_question():
        """Accept a query and return a source-backed generated answer.

        TODO:
        1. Read JSON request data safely.
        2. Validate that `query` is a non-empty string.
        3. Retrieve relevant context from COMPANY_DOCUMENTS.
        4. If no context is found, return a safe fallback with an empty sources list.
        5. Build a structured prompt from the selected context.
        6. Call generate_response(prompt).
        7. Return query, answer, and sources as JSON.
        8. If generate_response raises RuntimeError, return a 503 service error.
        """
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            data = {}

        query = data.get("query")
        if not isinstance(query, str) or not query.strip():
            return jsonify({"error": "A non-empty 'query' string is required."}), 400

        matches = retrieve_context(query, COMPANY_DOCUMENTS)

        if not matches:
            return jsonify(
                {
                    "query": query,
                    "answer": (
                        "The approved company documents do not contain "
                        "enough information to answer that question."
                    ),
                    "sources": [],
                }
            ), 200

        prompt = build_prompt(query, matches)

        try:
            answer = generate_response(prompt)
        except RuntimeError as error:
            return jsonify({"error": f"The model service is unavailable: {error}"}), 503

        sources = [source_metadata(match) for match in matches]

        return jsonify({"query": query, "answer": answer, "sources": sources}), 200

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
