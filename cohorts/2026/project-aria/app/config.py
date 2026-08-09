"""Central configuration, loaded from environment (.env)."""
import os

# --- LLM ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
PRIMARY_LLM = os.getenv("PRIMARY_LLM", "claude")  # claude | gemini
CLAUDE_FAST_MODEL = os.getenv("CLAUDE_FAST_MODEL", "claude-3-5-haiku-20241022")
CLAUDE_SMART_MODEL = os.getenv("CLAUDE_SMART_MODEL", "claude-3-5-sonnet-20241022")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# --- Infra ---
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "interviews")
POSTGRES_DSN = os.getenv("POSTGRES_DSN", "postgresql://vault:vault@localhost:5432/vault")

# --- Ingestion ---
TRANSCRIPTS_DIR = os.getenv("TRANSCRIPTS_DIR", "data/sample")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "2000"))
CHUNK_STEP = int(os.getenv("CHUNK_STEP", "1000"))

# --- Retrieval ---
EMBEDDING_DIM = 384  # all-MiniLM-L6-v2
RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
