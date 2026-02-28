PRD.md

Below is the content for your **PRD.md** section, formatted for consistency with your existing documentation and designed to highlight your tooling mindset for the [Zero Hash TSE role](https://zero-hash.breezy.hr/p/d027182f8d38-technical-support-engineer-amer).

---

### 

### **PRD.md: zerohash Settlement Health MCP**

#### 

#### **1\. Vision & Problem Statement**

In high-stakes fintech infrastructure, the primary friction for [Technical Support Engineers](https://zero-hash.breezy.hr/p/d027182f8d38-technical-support-engineer-amer) is the "Context Gap" between raw API logs and actionable documentation. When a [Settlement](https://zerohash.com/) fails, the TSE must manually correlate a transaction\_id against multiple API endpoints and then reference static runbooks to find a fix.

The **Zero Hash Settlement Health MCP** bridges this gap by transforming "Docs as Code" into "Docs as Action." It provides a terminal-native diagnostic layer that interprets [Zero Hash API](https://zerohash.com/) states and suggests immediate remediation steps.

#### **2\. Core Personas**

* **The Rapid Responder (TSE):** Needs to diagnose a "stuck" transaction in under 30 seconds without leaving the terminal.  
* **The Integration Architect (Solutions):** Uses the tool to validate client webhook configurations and "Trade/Transact" flows during onboarding.

#### **3\. Functional Requirements & Implementation Details**

| Feature | Implementation Detail | TSE Responsibility Met |
| :---- | :---- | :---- |
| **Settlement Pre-flight** | Tool: check\_settlement\_health. Queries the /transactions and /accounts endpoints to verify liquidity and state transitions. | [Technical Troubleshooting](https://zero-hash.breezy.hr/p/d027182f8d38-technical-support-engineer-amer) |
| **Automated Runbooks** | The server doesn't just return JSON; it matches error codes to specific recovery steps (e.g., "Trigger rebalance via /accounts/rebalance"). | [Alerting & Runbooks](https://zero-hash.breezy.hr/p/d027182f8d38-technical-support-engineer-amer) |
| **Pillar-Specific Logic** | Encodes specific logic for [Trade, Transact, and Tokenize](https://zerohash.com/) pillars to identify bottlenecks unique to each integration path. | [API Knowledge](https://zero-hash.breezy.hr/p/d027182f8d38-technical-support-engineer-amer) |
| **Contextual Chat** | Integration with [mcp-shell](https://github.com/Prat011/mcp-shell) allows for natural language follow-ups like *"Analyze the last 5 minutes of logs for this partner"*. | [Incident Management](https://zero-hash.breezy.hr/p/d027182f8d38-technical-support-engineer-amer) |

#### **4\. Technical Architecture**

* **Protocol:** [Model Context Protocol (MCP)](https://github.com/V-You/Swarmia_MCP) via stdio transport.  
* **Server Framework:** Python (FastMCP) for rapid tool definition and type-safe arguments.  
* **Distribution:** Published via GitHub and executed using uvx for a zero-footprint, isolated environment that requires no manual cloning.  
* **Client Interface:** [mcp-shell](https://github.com/Prat011/mcp-shell) for a lightweight, terminal-first AI interface that lives where the engineer works.

#### **5\. Future Roadmap: The "Portable Utility Belt"**

* **Ledger Reconciliation Bot:** Automated 3-way matching between [Zero Hash APIs](https://zerohash.com/), on-chain data, and client SQL databases.  
* **Integration Architect:** Scaffolding "Hello World" flows for new client integrations to reduce time-to-first-trade.  
* **Incident War-Room Reporter:** Automated generation of Post-Mortem reports and partner status updates during critical outages.
