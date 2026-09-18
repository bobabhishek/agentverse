# A2A Guard: Frontend Implementation & Architecture Summary

## Overview & Objective
The **A2A Guard Frontend** is an interactive, real-time simulation platform built to model and audit **Agent-to-Agent (A2A)** communications. Its primary objective is to demonstrate data sovereignty enforcement, track unencrypted or non-compliant PII (Personally Identifiable Information) transfers, and provide an immutable telemetry log for security audits.

---

## 🛠️ Technology Stack & Architecture

| Layer / Aspect | Technology Used | Rationale & Usage |
| :--- | :--- | :--- |
| **Core Framework** | Next.js 14+ (App Router), React 18+ | Client-side dynamic state rendering (`'use client'`), stateful transitions, component modularity. |
| **Styling & Theme** | Tailwind CSS v3+ | Dark mode aesthetic (`#030712`), custom borders (`border-slate-800`), telemetry grid background. |
| **Design System** | Shadcn UI | Accessible design primitives (`Card`, `Badge`, `ScrollArea`, `Button`, `Input`). |
| **Iconography** | Lucide React | Visual state indicators (`Shield`, `ShieldAlert`, `Database`, `Send`, `ArrowRight`, `ArrowLeft`, `Download`, `FileText`). |
| **State & Storage** | React Hooks & Web Storage API | `useState`, `useEffect`, `useRef` for animation step delays, plus `localStorage` for session persistence. |
| **Synthetic Database** | JSON Dataset (`synthetic-customers.json`) | 100 synthetic European customer profiles containing PII fields (ID, Name, Country, City, Phone, Address, GPS, Order Status). |

---

## 🧠 System Logic & Workflow Architecture

### 1. Visual Node Canvas & Connection Telemetry
The UI features a top visualizer tracking data flow between two node types:
*   **Agent 2 (India Node - `IN`) [Left Box]**: Marked as **Non-Compliant / External Node**. Lacks direct database access and must route queries to Agent 1 via A2A protocols.
*   **Agent 1 (Europe Node - `EU`) [Right Box]**: Marked as **Attested / GDPR Compliant** with exclusive local database access. In rogue scenarios, it fails compliance rules by transmitting raw PII outside EU borders.
*   **Dual-Track Connection Visualizer**:
    *   **Top Track (Request Path)**: `Request ->` (flows from Agent 2 [IN] on the left to Agent 1 [EU] on the right).
    *   **Bottom Track (Data Path)**: `<- Data` (flows from Agent 1 [EU] on the right to Agent 2 [IN] on the left).

### 2. Simulation Execution Logic (`runSimulation`)
When a user submits a prompt, the following execution steps take place:
1.  **Exact ID & Name Matching Engine**: First checks for explicit customer ID patterns (`SYN-CUST-1003` or `1003`) or exact names present in `synthetic-customers.json`.
2.  **Full Profile Display on ID Lookup**: When a user queries `"give details of id SYN-CUST-1006"`, `fetchAll` is automatically enabled, displaying ID, Name, Region, Phone, Address, GPS, and Order Status.
3.  **Expanded Follow-up Context**: Supports follow-up phrases like `"give me additional details of that id"`, `"more details"`, and `"her address"` using `lastContext`.
4.  **Polite Closing & Thank You Handler**: Responds warmly to `"thanks"`, `"thank you"`, and `"cheers"`.
5.  **Strict Dataset Validation (Zero Dummy Fallbacks)**: If a requested entity (e.g. "Bob") does not exist in `synthetic-customers.json`, returns `"No customer record matching 'Bob' was found in the European database."` (never hallucinates dummy data).
6.  **Step 1: Agent 2 Dispatch (India Node)**: Agent 2 logs no direct DB access and dispatches an A2A request to Agent 1 (Europe Node). UI highlights top request track in orange.
7.  **Step 2: Agent 1 DB Query & Transfer (Europe Node)**: Agent 1 queries local DB, retrieves PII, and transmits requested attributes to Agent 2. UI highlights bottom data track in emerald green.
8.  **Step 3: Response Delivery & Audit Log Export**: Agent 2 receives the data and renders the structured profile card. Pure Agent-to-Agent audit trail logs are captured and can be exported as structured JSON.

---

## 🎯 Use Cases

### Use Case 1: Full Profile Details by ID
*   **Description**: User requests all details using a specific Customer ID.
*   **Example Prompt**: `"give details of id SYN-CUST-1006"`
*   **Behavior**: Retrieves and displays all profile fields for Emma García (ID, Region, Phone, Address, GPS, Order Status).

### Use Case 2: Follow-up Details on Previous Subject
*   **Description**: User requests additional details on the previously searched customer.
*   **Example Prompt**: `"give me additional details of that id"` (after querying SYN-CUST-1007)
*   **Behavior**: Uses `lastContext` to resolve `SYN-CUST-1007` (Olivia Dubois) and displays full profile card.

### Use Case 3: Polite Closing / Thank You
*   **Description**: User sends a thank-you message.
*   **Example Prompt**: `"thanks"` or `"thank you"`
*   **Behavior**: Agent 2 responds with a warm polite response: `"You're welcome! Let me know if you need any more European customer records or telemetry checks."`

### Use Case 4: Pure Agent-to-Agent Audit Log JSON Export
*   **Description**: User exports active A2A telemetry logs.
*   **Action**: Click `JSON` button in Audit Trail header.
*   **Behavior**: Downloads a formatted `.json` file containing all A2A hop events and timestamps.

---

## 🧪 Test Cases & Verification Matrix

| Test Case ID | Feature / Logic | Input / Action | Expected Result | Pass Criteria |
| :--- | :--- | :--- | :--- | :--- |
| **TC-01** | Full Details by ID | Prompt: `"give details of id SYN-CUST-1006"` | Agent 2 routes to Agent 1 $\rightarrow$ Agent 1 retrieves Emma García (`SYN-CUST-1006`). | Displays full profile card (ID, Region, Phone, Address, GPS, Order Status). |
| **TC-02** | Follow-up Context | Prompt: `"give me additional details of that id"` | Resolves `lastContext` (`SYN-CUST-1007` - Olivia Dubois). | Displays full profile card for Olivia Dubois. |
| **TC-03** | Thank You Handler | Prompt: `"thanks"` | Agent 2 returns polite closing message. | Displays: `"You're welcome! Let me know if you need any more..."` |
| **TC-04** | Clean Target Error | Prompt: `"what about id 4nm21ai072"` | Agent 1 queries local DB, finds 0 records. | Displays: `"No customer record matching '4nm21ai072' was found in the European database."` |
