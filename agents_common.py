"""Shared setup for the agent1/agent2 automation scripts (Claude Agent SDK + paperclip).

Not used by agent3 (pure-Python library, no LLM) or agent4 (deterministic benchmark script).
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent

load_dotenv(REPO_ROOT / ".env")


def paperclip_mcp_config() -> dict:
    """MCP server config for paperclip, authenticated via API key (not OAuth) so it
    works headlessly — see docs at https://paperclip.gxl.ai/docs."""
    api_key = os.environ.get("PAPERCLIP_API_KEY")
    if not api_key:
        sys.exit("PAPERCLIP_API_KEY not set — add it to .env (get one at https://paperclip.gxl.ai/keys)")
    return {
        "paperclip": {
            "type": "http",
            "url": "https://paperclip.gxl.ai/mcp",
            "headers": {"X-API-Key": api_key},
        }
    }


def require_anthropic_key() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY not set — add it to .env")
