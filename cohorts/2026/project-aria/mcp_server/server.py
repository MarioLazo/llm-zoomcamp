"""BONUS: MCP server exposing ARIA to Claude Desktop / any MCP client.

Turns the corpus into a first-class tool for Claude: search transcripts and
pull auditable evidence without leaving the chat. This is the "something
extra" bonus and a strong Claude Architect portfolio signal (MCP + tool design).

Run:  python -m mcp_server.server      (stdio transport)
Add to Claude Desktop's mcp config to use it.
"""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP  # from the `mcp` PyPI package (Anthropic's MCP SDK)

from app.rerank import rerank
from app.search import InterviewSearch

mcp = FastMCP("aria")
_search = InterviewSearch()


@mcp.tool()
def search_interviews(query: str, k: int = 5) -> list[dict]:
    """Search the interview transcripts (hybrid + rerank). Returns top passages."""
    results = rerank(query, _search.hybrid_search(query, limit=k * 4), top_k=k)
    return [{"source": r["source"], "speaker": r["speaker"], "text": r["text"]} for r in results]


@mcp.tool()
def pull_evidence(theme: str, k: int = 8) -> list[dict]:
    """Return verbatim candidate passages for a theme, for an auditable evidence trail."""
    results = rerank(theme, _search.hybrid_search(theme, limit=k * 4), top_k=k)
    return [{"source": r["source"], "speaker": r["speaker"], "text": r["text"]} for r in results]


if __name__ == "__main__":
    mcp.run()
