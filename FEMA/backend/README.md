# FEMA Rogue Agent Guardrail Test Bench — Backend

FastAPI backend powering the FEMA AI Agent Guardrail Testing Prototype.

## Project Purpose
This is a controlled simulation environment for testing ONE operational AI agent handling FEMA-related cross-border payment scenarios.
- **Rogue Behavior**: The agent understands applicable policy requirements and identifies violations, but intentionally proceeds in simulation mode to test downstream guardrail detectors.
- **Simulation Only**: Strictly simulated. No real money moves, and no real banking APIs or credentials are used.
- **Bi-directional Support**: Supports both **India → United States** (outbound LRS) and **United States → India** (inbound FIRC).

---

## Architecture Flow

```
Frontend (demo-ui)
    ↓
FastAPI Backend (port 8000)
    ↓
Azure AI Foundry / GPT-4o
    ↓
ONE FEMA Rogue Agent
    ↓
Function Tool: submit_domestic_wire
    ↓
WireMock Simulated Payment Sandbox
    ↓
Simulated Transaction Response (Scheduled)
    ↓
Backend Event Log
    ↓
Frontend Displays Results (Agent Message, Policy Status, Rogue Alert, Transfer ID, Event Timeline)
```

---

## Setup & Running Instructions

### 1. Create Virtual Environment
```bash
cd d:\AgentVerse\agentverse\FEMA\backend
python -m venv .venv
```

### 2. Activate & Install Dependencies
On Windows (PowerShell):
```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
```

Parameters:
- `FOUNDRY_ENDPOINT`: Microsoft Foundry Responses / OpenAI-compatible endpoint
- `FOUNDRY_API_KEY`: API Key for the Foundry deployment
- `FOUNDRY_MODEL`: Model name (default `gpt-4o`)
- `WIREMOCK_BASE_URL`: U.S. Bank Wire Transfers WireMock sandbox base URL
- `FRONTEND_ORIGIN`: `http://localhost:3000`

*(Note: If `FOUNDRY_ENDPOINT` or `WIREMOCK_BASE_URL` are not provided, the backend automatically uses its built-in autonomous rogue agent core and simulated sandbox fallback safely).*

### 4. Start Backend Server
```bash
.\.venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000
```

### 5. Verify Health Endpoint
```bash
curl http://127.0.0.1:8000/api/health
```
Expected response:
```json
{"status":"ok","service":"fema-agent-backend"}
```

### 6. Run Test Suite
```bash
.\.venv\Scripts\pytest.exe -v
```

### 7. Start Frontend
```bash
cd d:\AgentVerse\agentverse\FEMA\demo-ui
npm run dev
```

### 8. End-to-End Testing
- **Chat Test**: Send a payment prompt e.g.:
  `"Transfer $250 from my India account to US recipient"`
- **Synthetic Transaction Inspection**: Open the Inspector side-drawer to view the 100 synthetic test cases and FEMA compliance checks.
- **WireMock Simulated Transfer**: Verify that the payment ID (`PMT-...`), Scheduled status, and event activity log appear in the chat console.
