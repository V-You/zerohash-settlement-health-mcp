# zerohash Settlement Health MCP

**Pitch:** *The MCP server encodes zerohash's settlement logic and API runbooks. By using a terminal-based client like [mcp-shell](https://github.com/Prat011/mcp-shell), a support engineer can diagnose 'Trade & Transact' issues in seconds, directly where they are already viewing logs.*

*This is an MCP server for terminal use that takes a transaction\_id, queries the (mocked) Zero Hash API, and performs a "pre-flight" or "post-mortem" check. Instead of just showing raw JSON, the tool maps the error to a "Runbook" (referencing Alerting requirements). For example: "Transaction failed due to insufficient liquidity in the participant's sub-account. Action: Trigger rebalance via the /accounts/rebalance endpoint."*

*Pros:*

* **Context is king:** Just as developers shouldn't have to leave their IDE, TSEs shouldn't have to leave the terminal/command line to diagnose a [Settlement](https://zerohash.com/) failure. The tool lives where the logs are, allowing the TSE to pipe an error directly into a tool that interpretes the zerohash settlement logic and suggests an action.*
* **Bridging the gap:** It moves the user from API docs that are “somewhere”, to "Docs as Action". The user gets a tool that validates an API state against those docs.*
* **Direct tool execution:** run specific diagnostic tools as one-off commands (e.g., `mcp-terminal tool check_settlement --id 0x123...`). This is exactly how a TSE would want to interact with a troubleshooting script during a live incident.*
* **Chat for complex analysis:** If a single tool output isn't enough, TSE can switch to the interactive chat mode: "I see a settlement failure in the previous tool output; check the last 5 minutes of logs for this customer to see if there's a pattern" \- the AI can coordinate multiple MCP tools to find the answer.*
* **Multi-provider upport:** LiteLLM \= not locked into one model. Claude/GPT-4/local via Ollama*

\------------------------------------------------


# Install

Install the client  
pip install mcp-shell

Add the server  
mcp-terminal server add  
\# Name: zerohash-settlement-health-mcp  
\# Command: uvx  
\# Args: \--from git+https://github.com/V-You/zerohash-settlement-health-mcp

# Usage

mcp-terminal chat   
"Check the settlement health for transaction `0xabc...`"

# Distribute
pip install mcp-shell  
mcp-terminal server add; \# Name: zerohash-settlement-health-mcp; \# Command: uvx; \# Args: \--from git+https://github.com/V-You/zerohash-settlement-health-mcp  
mcp-terminal chat 

# Workflow

**Execution:** The CLI client sends a `call_tool` request to your local script. Your script hits the [Zero Hash API](https://zerohash.com/), parses the "Trade" or "Transact" status, and sends the result back to the terminal.

\-------------------------------------------------


