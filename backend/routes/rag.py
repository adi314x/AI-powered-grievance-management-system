"""RAG chatbot route — registers the rag_module Flask blueprint into the main app."""

from __future__ import annotations

import os
import traceback
from pathlib import Path

from flask import Blueprint, jsonify, request, current_app

# ---------------------------------------------------------------------------
# Lazy initialisation so the RAG engine is built only once per process.
# ---------------------------------------------------------------------------
_rag_engine = None
_rag_init_error: str | None = None


def _get_engine():
    global _rag_engine, _rag_init_error
    if _rag_engine is not None:
        return _rag_engine, None
    if _rag_init_error is not None:
        return None, _rag_init_error

    try:
        from rag_module.config import RagConfig
        from rag_module.engine import RagEngine
        from rag_module.providers import GeminiProvider
        from rag_module.store import SQLiteVectorStore

        config = RagConfig.from_env()
        config.validate()

        provider = GeminiProvider(
            config.api_key,
            embedding_model=config.embedding_model,
            generation_model=config.generation_model,
            timeout_seconds=config.request_timeout_seconds,
            retry_attempts=config.retry_attempts,
        )
        store = SQLiteVectorStore(config.index_path)
        _rag_engine = RagEngine(config, provider, store)
        return _rag_engine, None
    except Exception as exc:
        _rag_init_error = str(exc)
        return None, _rag_init_error


# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------
rag_bp = Blueprint("rag", __name__)


@rag_bp.post("/query")
def rag_query():
    """Public chatbot endpoint — no auth required for citizen chatbot."""
    if request.content_length is not None and request.content_length > 16_384:
        return jsonify({"error": "request body exceeds 16 KB"}), 413
    if not request.is_json:
        return jsonify({"error": "request must be JSON"}), 415

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "request body must be a JSON object"}), 400

    question = payload.get("question")
    department = payload.get("department")
    top_k = payload.get("top_k")

    if not isinstance(question, str) or not question.strip():
        return jsonify({"error": "question must be a non-empty string"}), 400
    if department is not None and not isinstance(department, str):
        return jsonify({"error": "department must be a string"}), 400
    if top_k is not None and (isinstance(top_k, bool) or not isinstance(top_k, int)):
        return jsonify({"error": "top_k must be an integer"}), 400

    engine, err = _get_engine()
    if engine is None:
        current_app.logger.error("RAG engine not available: %s", err)
        return jsonify({"error": "RAG service is not configured. Set GEMINI_API_KEY and run the indexer."}), 503

    try:
        from rag_module.providers import ProviderError
        result = engine.answer(question, department=department, top_k=top_k)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        tb = traceback.format_exc()
        current_app.logger.error("RAG query failed:\n%s", tb)
        print("[RAG ERROR]", tb)  # also prints to terminal
        return jsonify({"error": f"RAG query failed: {exc}"}), 500

    return jsonify({
        "answer": result.answer,
        "supported": result.supported,
        "reason": result.reason,
        "citations": [
            {
                "source": c.source_path,
                "title": c.title,
                "department": c.department,
                "page": c.page_number,
            }
            for c in result.citations
        ],
    })
