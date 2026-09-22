# AgentVerse

**Cross-Border Agent-to-Agent (A2A) Governance & GDPR Compliance Framework**

AgentVerse demonstrates an autonomous agent-to-agent protocol under cross-border data protection regulations (such as GDPR Chapter V). It features external requesting nodes, data-holding European nodes, independent GlassBox telemetry monitoring, and real-time compliance evaluation.

---

## 🏛️ Architecture Overview

```
User → Agent 2 (India Node) ──[A2A Request]──► Agent 1 (Europe Node) ──► Synthetic DB
                                                     │
                                                     ▼ [Observed Independently]
                                                  GlassBox ──► Compliance Flagging
```

- **Agent 2 (India Node):** External requesting agent with no direct database access. Translates user queries and initiates cross-border A2A requests.
- **Agent 1 (Europe Node):** Synthetic customer database owner. Validates incoming requests, applies data minimization policies, and independently decides compliance responses.
- **GlassBox (Independent Monitor):** External observer that passively analyzes telemetry between nodes to detect and flag statutory non-compliance in real-time.

---

## 📂 Project Structure

```
agentverse/
├── backend/                  # FastAPI backend server
│   ├── app/
│   │   ├── a2a/              # Agent-to-Agent protocol & message bus
│   │   ├── agents/           # Agent 1 (Europe) & Agent 2 (India) logic
│   │   ├── compliance/       # GDPR compliance evaluators & rules
│   │   ├── audit/            # Forensic audit logs & telemetry
│   │   └── data/             # Synthetic European customer records
│   ├── tests/                # Accuracy, GDPR, and security test suites
│   └── requirements.txt
├── demo-ui/                  # Next.js 16 + Tailwind CSS frontend
│   ├── src/
│   │   ├── app/              # Dashboard, audit trail, and docs
│   │   └── components/       # Architecture visualizer & Mermaid diagrams
│   └── package.json
├── docs/                     # Test case specifications & GDPR docs
│   └── gdpr-a2a-glassbox-test-case.md
├── DESIGN.md                 # Design system & tokens
└── .gitignore
```

---

## 🚀 Quick Start

### 1. Backend (FastAPI)
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate       # Linux/macOS
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 2. Frontend (Next.js)
```bash
cd demo-ui
npm install
npm run dev
```
Visit `http://localhost:3000` for the interactive dashboard and `http://localhost:3000/docs` for architecture specifications.

---

## 🧪 Testing & Verification

Run automated test suites from the `backend/` directory:
```bash
pytest tests/ -v
```
