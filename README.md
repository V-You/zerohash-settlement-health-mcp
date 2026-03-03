# zerohash Settlement Health MCP

This is an MCP server for the command line. It takes a **trade\_id**, queries the (mocked) Zero Hash API, and performs a *pre-flight* or a *post-mortem* check. It shows the JSON response, and maps the trade state to a Runbook. Example: "Trade defaulted. Action: Escalate to the settlement operations team and file an incident report. 

The MCP server encodes zerohash's settlement logic and API runbooks. A technical support engineer (TSE) can diagnose 'Trade & Transact' issues in seconds, directly in the terminal where they are already viewing logs. Using [mcp-cli](https://github.com/IBM/mcp-cli) for interactive LLM-powered chat, or `fastmcp` for instant tool invocation with no setup required. Advantages:

* **Context is king:** TSEs shouldn't have to leave the terminal/command line to diagnose a [Settlement](https://zerohash.com/) failure. The tool lives where the logs are, allowing the TSE to pipe an error directly into a tool that interprets the zerohash settlement logic and suggests an action.
* **Bridging the gap:** The tool moves the user from API docs that are "somewhere", to "Docs as Action". The TSE gets a tool that validates an API state against those docs.
* **Direct tool execution:** `fastmcp call ... --target check_settlement_health trade_id=trade_002` — a one-liner that returns a structured diagnosis. Mimics interaction with a troubleshooting script during a prod incident.
* **Chat for complex analysis:** Switch to `mcp-cli chat` for multi-step analysis: "Check settlement health for trade\_005 and then verify the participant's account balance" — the AI chains the applicable MCP tools and returns a unified answer.
* **Multi-provider support:** `mcp-cli` supports Groq, Gemini, OpenAI, Anthropic, and Ollama — not locked into one model.

# Quick demo (no LLM)

Requires: Python 3.10+, [uv](https://docs.astral.sh/uv/)

```bash
# 1. Clone and install
git clone https://github.com/V-You/zerohash-settlement-health-mcp
cd zerohash-settlement-health-mcp
uv sync

# 2. List available tools
uv run fastmcp list src/zerohash_settlement_health/server.py

# 3. Call a tool directly — returns structured JSON diagnosis in the terminal
uv run fastmcp call src/zerohash_settlement_health/server.py \
  --target check_settlement_health trade_id=trade_002

# 4. (Optional) Launch the web-based MCP Inspector for interactive use
uv run fastmcp dev inspector src/zerohash_settlement_health/server.py
```

**Mock trade IDs:** 
- `trade_001` (healthy/settled)
- `trade_002` (defaulted/CRITICAL)
- `trade_003` (counterparty default)
- `trade_004`–`trade_008` (various states and severity levels)


# Terminal Chat with LLM — mcp-cli

```bash
# Install dev dependencies (includes mcp-cli) — skip if you already ran uv sync --extra dev
uv sync --extra dev

# Export API keys from .env into the current shell session
set -a; source .env; set +a

# Start interactive chat (server_config.json is the default config file)
uv run mcp-cli chat --config-file server_config.json --server zerohash-settlement-health --provider groq

# Example queries:
# "Check the settlement health for trade trade_002"
# "Look up trade_005 and check the account balance for its participant"
```

Supported providers: `groq`, `gemini`, `openai`, `anthropic`, `ollama`.

> **Keys:** Add your `GROQ_API_KEY` (or `OPENROUTER_API_KEY`) to `.env`. Run `set -a; source .env; set +a` once per shell session before chatting. `mcp-cli` does not auto-load `.env`.


# Distribute — zero footprint

To share with a teammate who doesn't have the repo:

```bash
# Install mcp-cli (one-time)
pip install mcp-cli

# Copy server_config.json to your working directory
# Edit it to use the "zerohash-settlement-health-remote" server entry (uvx variant)

# Export your LLM key, then chat:
export GROQ_API_KEY=your_key_here
mcp-cli chat --config-file server_config.json --server zerohash-settlement-health-remote --provider groq
```

> The Distribute path uses a standalone `pip install mcp-cli` since there is no project venv available.

See `server_config.json` in this repo for the local dev and remote (uvx from GitHub) config variants.


# Workflow

**Execution:** The CLI client sends a `call_tool` request to the server process. The server queries the Zero Hash API (or mock), maps the trade state to a runbook, and returns a structured diagnosis to the terminal.

\-------------------------------------------------
