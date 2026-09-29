# AgentVerse

A modular multi-agent research, compliance, and simulation ecosystem.

## 📁 Repository Structure

```
agentverse/
├── gdpr/                     # Cross-Border A2A Governance & GDPR Compliance Module
│   ├── backend/              # FastAPI server, Europe & India Agents, GlassBox compliance evaluators
│   ├── demo-ui/              # Next.js interactive telemetry & audit dashboard
│   ├── docs/                 # Test cases & compliance specifications
│   ├── DESIGN.md             # UI/UX design specifications
│   └── README.md             # GDPR module documentation & quickstart
├── FEMA/                     # Foreign Exchange Management Act (FEMA) Compliance Module
│   └── README.md             # FEMA module documentation
└── (Upcoming Modules)        # Future agent systems with dedicated frontend and backend services
```

## 🚀 Modules

### 🛡️ [GDPR Cross-Border A2A Compliance](./gdpr)
An autonomous agent-to-agent protocol under cross-border data protection regulations (such as GDPR Chapter V), featuring independent GlassBox telemetry monitoring and real-time compliance evaluation.
- **Backend:** FastAPI + Python (Europe Agent, India Agent, GlassBox Evaluator)
- **Frontend:** Next.js + React + Tailwind CSS
- See [`gdpr/README.md`](./gdpr/README.md) for full setup instructions and architecture details.

### 💼 [FEMA Compliance Framework](./FEMA)
Autonomous agent-to-agent architecture and regulatory evaluation for cross-border financial transactions and reporting under FEMA guidelines.
- See [`FEMA/README.md`](./FEMA/README.md) for module outline and upcoming services.
