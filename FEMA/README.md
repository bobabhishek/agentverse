# FEMA Module

Cross-border financial transactions and regulatory compliance framework under the Foreign Exchange Management Act (FEMA).

## 📂 Module Structure

```
FEMA/
├── demo-ui/                  # Frontend prototype: Guardrail Test Bench (Vite + React + TS + Tailwind)
├── backend/                  # (Upcoming) FastAPI backend service & financial compliance agents
└── docs/                     # Regulatory specifications & compliance documentation
```

## 🚀 Guardrail Test Bench (Frontend Prototype)

A controlled simulation prototype for testing an autonomous AI agent's compliance behavior under simulated FEMA cross-border regulations.

### Features
- **Single Rogue AI Agent**: Evaluates policy requirements (authorization, documentation, eligibility) but intentionally proceeds with simulated remittances despite guardrail violations for security testing.
- **100 Synthetic Test Cases (`Fema_synthetic_100`)**: Complete benchmark dataset with filter views for `All 100`, `Policy failures 69`, and `Valid-looking 31`.
- **Live Compliance & Telemetry Panels**:
  - Structured policy check matrix (pass/fail status)
  - Simulated WireMock transfer output with payment IDs
  - Glassbox behavioral monitoring telemetry placeholder
  - Real-time agent event activity timeline
- **Technical Documentation**: Comprehensive 10-section test case specification with visual flow pipelines and future integration architecture.

### Running the Frontend
```bash
cd demo-ui
npm install
npm run dev
```
Navigate to `http://localhost:3000`.

