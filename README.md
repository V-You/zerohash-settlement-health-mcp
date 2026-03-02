# zerohash Settlement Health MCP

**Pitch:** *The MCP server encodes zerohash's settlement logic and API runbooks. A support engineer can diagnose 'Trade & Transact' issues in seconds, directly in the terminal where they are already viewing logs — using [mcp-cli](https://github.com/IBM/mcp-cli) for interactive LLM-powered chat, or `fastmcp` for instant tool invocation with no setup required.*

*This is an MCP server for terminal use that takes a trade\_id, queries the (mocked) Zero Hash API, and performs a "pre-flight" or "post-mortem" check. Instead of just showing raw JSON, the tool maps the trade state to a Runbook. For example: "Trade defaulted. Action: Escalate to the settlement operations team and file an incident report."*

*Pros:*

* **Context is king:** Just as developers shouldn't have to leave their IDE, TSEs shouldn't have to leave the terminal/command line to diagnose a [Settlement](https://zerohash.com/) failure. The tool lives where the logs are, allowing the TSE to pipe an error directly into a tool that interprets the zerohash settlement logic and suggests an action.*
* **Bridging the gap:** It moves the user from API docs that are "somewhere", to "Docs as Action". The user gets a tool that validates an API state against those docs.*
* **Direct tool execution:** `fastmcp call ... --target check_settlement_health trade_id=trade_002` — a one-liner that returns a structured diagnosis. This is exactly how a TSE would interact with a troubleshooting script during a live incident.*
* **Chat for complex analysis:** Switch to `mcp-cli chat` for multi-step analysis: "Check settlement health for trade\_005 and then verify the participant's account balance" — the AI chains the tools and returns a unified answer.*
* **Multi-provider support:** `mcp-cli` supports Groq, Gemini, OpenAI, Anthropic, and Ollama — not locked into one model.*

\------------------------------------------------


# Quick Demo — no LLM, no API key needed

Requires: Python 3.10+, [uv](https://docs.astral.sh/uv/)

```bash
# 1. Clone and install
git clone https://github.com/V-You/zerohash-settlement-health-mcp
cd zerohash-settlement-health-mcp
uv sync

# 2. List available tools
fastmcp list src/zerohash_settlement_health/server.py

# 3. Call a tool directly — returns structured JSON diagnosis in the terminal
fastmcp call src/zerohash_settlement_health/server.py \
  --target check_settlement_health trade_id=trade_002

# 4. (Optional) Launch the web-based MCP Inspector for interactive use
fastmcp dev inspector src/zerohash_settlement_health/server.py
```

**Mock trade IDs:** `trade_001` (healthy/settled), `trade_002` (defaulted/CRITICAL), `trade_003` (counterparty default), `trade_004`–`trade_008` (various states and severity levels).


# Terminal Chat with LLM — mcp-cli

```bash
# Install mcp-cli
pip install mcp-cli
# or zero-footprint: uvx mcp-cli

# Set ONE free-tier LLM provider key (see .env.example for all options)
export GROQ_API_KEY=your_key_here   # Groq: generous free tier, very fast

# Start interactive chat (uses server_config.json in this directory)
mcp-cli chat --config server_config.json --server zerohash-settlement-health --provider groq

# Example queries:
# "Check the settlement health for trade trade_002"
# "Look up trade_005 and check the account balance for its participant"
```

Supported providers: `groq`, `gemini`, `openai`, `anthropic`, `ollama`.


# Distribute — zero footprint

To share with a teammate who doesn't have the repo:

```bash
# Install mcp-cli (one-time)
pip install mcp-cli

# Edit server_config.json to use the remote (uvx) command variant, then:
mcp-cli chat --config server_config.json --server zerohash-settlement-health --provider groq
```

See `server_config.json` in this repo for the local dev and remote (uvx from GitHub) config variants.


# Workflow

**Execution:** The CLI client sends a `call_tool` request to the server process. The server queries the Zero Hash API (or mock), maps the trade state to a runbook, and returns a structured diagnosis to the terminal.

\-------------------------------------------------
