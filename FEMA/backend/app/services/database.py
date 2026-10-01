import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger("fema.database")

DB_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DB_DIR / "fema_simulation.db"
SEED_JSON_PATH = DB_DIR / "fema_transfer_recipients_150.json"



class DatabaseService:
    """
    Persistent SQLite database service for the FEMA Payment Agent Test Bench.
    Acts as the single source of truth for customers, recipients, account balances, and transactions.
    """

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._ensure_db_dir()
        self.init_db()

    def _ensure_db_dir(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=15.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_db(self):
        """Creates tables if they do not exist and seeds initial data if database is empty."""
        conn = self.get_connection()
        try:
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            with conn:
                # 1. Customers Table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS customers (
                        customer_id TEXT PRIMARY KEY,
                        customer_name TEXT NOT NULL,
                        sender_residency TEXT NOT NULL,
                        sender_state TEXT,
                        source_country TEXT NOT NULL,
                        source_currency TEXT NOT NULL
                    )
                """)

                # 2. Recipients Table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS recipients (
                        recipient_id TEXT PRIMARY KEY,
                        recipient_name TEXT NOT NULL,
                        recipient_country TEXT NOT NULL,
                        destination_country TEXT NOT NULL,
                        destination_currency TEXT NOT NULL
                    )
                """)

                # 3. Accounts / Balances Table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS accounts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        owner_type TEXT NOT NULL CHECK(owner_type IN ('CUSTOMER', 'RECIPIENT')),
                        owner_id TEXT NOT NULL,
                        currency TEXT NOT NULL CHECK(currency IN ('INR', 'USD')),
                        balance REAL NOT NULL DEFAULT 0.0,
                        last_updated TEXT NOT NULL,
                        UNIQUE(owner_type, owner_id, currency)
                    )
                """)

                # 4. Completed Transactions Table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS transactions (
                        transaction_id TEXT PRIMARY KEY,
                        conversation_id TEXT NOT NULL,
                        sender_id TEXT NOT NULL,
                        sender_name TEXT NOT NULL,
                        recipient_id TEXT NOT NULL,
                        recipient_name TEXT NOT NULL,
                        source_country TEXT NOT NULL,
                        destination_country TEXT NOT NULL,
                        amount_sent REAL NOT NULL,
                        source_currency TEXT NOT NULL,
                        recipient_amount REAL NOT NULL,
                        destination_currency TEXT NOT NULL,
                        transfer_fee REAL NOT NULL,
                        total_debit REAL NOT NULL,
                        sender_balance_before REAL NOT NULL,
                        sender_balance_after REAL NOT NULL,
                        recipient_balance_before REAL NOT NULL,
                        recipient_balance_after REAL NOT NULL,
                        timestamp TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'Completed',
                        environment TEXT NOT NULL DEFAULT 'Simulation'
                    )
                """)

                # Check if seed data needs to be populated
                cursor = conn.execute("SELECT COUNT(*) FROM customers")
                count = cursor.fetchone()[0]

                if count == 0:
                    logger.info("Initializing persistent SQLite database from seed dataset...")
                    self._seed_data(conn)
                else:
                    logger.info(f"Persistent database active at {self.db_path} with {count} customers.")
        finally:
            conn.close()

    def _seed_data(self, conn: sqlite3.Connection):
        """Seeds initial 150 customers, recipients, and starting balances from the dataset."""
        if not SEED_JSON_PATH.is_file():
            logger.warning(f"Seed dataset file not found at {SEED_JSON_PATH}")
            return

        with open(SEED_JSON_PATH, "r", encoding="utf-8") as f:
            seed_cases = json.load(f)

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for tc in seed_cases:
            cid = tc.get("customer_id") or tc.get("person_id")
            cname = tc.get("customer_name") or tc.get("name")
            cres = tc.get("sender_residency", "India")
            cstate = tc.get("sender_state")
            src_country = tc.get("source_country", "India")
            src_curr = tc.get("source_currency", "INR")

            rid = tc.get("recipient_id")
            rname = tc.get("recipient_name")
            rcountry = tc.get("recipient_country") or tc.get("destination_country", "United States")
            dst_country = tc.get("destination_country", "United States")
            dst_curr = tc.get("destination_currency", "USD")

            if cid and cname:
                conn.execute("""
                    INSERT OR IGNORE INTO customers (customer_id, customer_name, sender_residency, sender_state, source_country, source_currency)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (cid, cname, cres, cstate, src_country, src_curr))

                # Customer initial balances: 100,000 INR and 10,000 USD
                conn.execute("""
                    INSERT OR IGNORE INTO accounts (owner_type, owner_id, currency, balance, last_updated)
                    VALUES (?, ?, ?, ?, ?)
                """, ('CUSTOMER', cid, 'INR', 100000.0, now_str))

                conn.execute("""
                    INSERT OR IGNORE INTO accounts (owner_type, owner_id, currency, balance, last_updated)
                    VALUES (?, ?, ?, ?, ?)
                """, ('CUSTOMER', cid, 'USD', 10000.0, now_str))

            if rid and rname:
                conn.execute("""
                    INSERT OR IGNORE INTO recipients (recipient_id, recipient_name, recipient_country, destination_country, destination_currency)
                    VALUES (?, ?, ?, ?, ?)
                """, (rid, rname, rcountry, dst_country, dst_curr))

                # Recipient initial balances: 500 USD and 50,000 INR
                conn.execute("""
                    INSERT OR IGNORE INTO accounts (owner_type, owner_id, currency, balance, last_updated)
                    VALUES (?, ?, ?, ?, ?)
                """, ('RECIPIENT', rid, 'USD', 500.0, now_str))

                conn.execute("""
                    INSERT OR IGNORE INTO accounts (owner_type, owner_id, currency, balance, last_updated)
                    VALUES (?, ?, ?, ?, ?)
                """, ('RECIPIENT', rid, 'INR', 50000.0, now_str))

        logger.info(f"Seeded {len(seed_cases)} records into SQLite persistent database.")

    # ---------------------------------------------------------
    # CUSTOMER QUERIES
    # ---------------------------------------------------------

    def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        if not customer_id:
            return None
        clean_id = customer_id.strip().upper()
        conn = self.get_connection()
        try:
            row = conn.execute("""
                SELECT c.*,
                       COALESCE(ai.balance, 100000.0) as inr_balance,
                       COALESCE(au.balance, 10000.0) as usd_balance
                FROM customers c
                LEFT JOIN accounts ai ON ai.owner_id = c.customer_id AND ai.currency = 'INR'
                LEFT JOIN accounts au ON au.owner_id = c.customer_id AND au.currency = 'USD'
                WHERE c.customer_id = ?
            """, (clean_id,)).fetchone()
            if row:
                d = dict(row)
                d["person_id"] = d["customer_id"]
                d["name"] = d["customer_name"]
                return d
            return None
        finally:
            conn.close()

    def get_all_customers(self) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        try:
            rows = conn.execute("""
                SELECT c.*,
                       COALESCE(ai.balance, 100000.0) as inr_balance,
                       COALESCE(au.balance, 10000.0) as usd_balance
                FROM customers c
                LEFT JOIN accounts ai ON ai.owner_id = c.customer_id AND ai.currency = 'INR'
                LEFT JOIN accounts au ON au.owner_id = c.customer_id AND au.currency = 'USD'
                ORDER BY c.customer_id ASC
            """).fetchall()
            results = []
            for r in rows:
                d = dict(r)
                cid = d["customer_id"]
                d["person_id"] = cid
                d["name"] = d["customer_name"]
                d["currency"] = d["source_currency"]
                d["policy_violations"] = []
                d["amount"] = 25000
                d["purpose"] = "Family support"
                results.append(d)
            return results
        finally:
            conn.close()

    def find_customer(self, query: str) -> Optional[Dict[str, Any]]:
        if not query or not query.strip():
            return None
        clean_q = query.strip().lower().rstrip(".").rstrip(",")
        conn = self.get_connection()
        try:
            # 1. By ID (exact match)
            row = conn.execute("SELECT customer_id FROM customers WHERE LOWER(customer_id) = ?", (clean_q,)).fetchone()
            if row:
                return self.get_customer(row["customer_id"])

            # 2. By exact full name
            row = conn.execute("SELECT customer_id FROM customers WHERE LOWER(customer_name) = ?", (clean_q,)).fetchone()
            if row:
                return self.get_customer(row["customer_id"])

            # If not found in customers table, check recipients table to support role reversal
            recip = self.get_recipient(clean_q)
            if not recip:
                row = conn.execute("SELECT recipient_id FROM recipients WHERE LOWER(recipient_name) = ?", (clean_q,)).fetchone()
                if row:
                    recip = self.get_recipient(row["recipient_id"])
            if not recip:
                rows = conn.execute("SELECT recipient_id, recipient_name FROM recipients WHERE LOWER(recipient_name) LIKE ?", (f"%{clean_q}%",)).fetchall()
                if len(rows) == 1:
                    recip = self.get_recipient(rows[0]["recipient_id"])
                elif len(rows) > 1:
                    for r in rows:
                        if r["recipient_name"].strip().lower() == clean_q:
                            recip = self.get_recipient(r["recipient_id"])
                            break

            if recip:
                country = recip.get("recipient_country") or recip.get("destination_country", "India")
                curr = "INR" if "india" in country.lower() else "USD"
                return {
                    "customer_id": recip["recipient_id"],
                    "customer_name": recip["recipient_name"],
                    "person_id": recip["recipient_id"],
                    "name": recip["recipient_name"],
                    "sender_residency": country,
                    "sender_state": None,
                    "source_country": country,
                    "source_currency": curr,
                    "inr_balance": recip.get("inr_balance", 100000.0),
                    "usd_balance": recip.get("usd_balance", 10000.0),
                    "policy_violations": [],
                    "amount": 25000,
                    "purpose": "Family support"
                }

            return None
        finally:
            conn.close()

    def get_customer_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        return self.find_customer(name)

    def get_customer_by_id(self, customer_id: str) -> Optional[Dict[str, Any]]:
        return self.get_customer(customer_id)

    # ---------------------------------------------------------
    # RECIPIENT QUERIES
    # ---------------------------------------------------------

    def get_recipient(self, recipient_id: str) -> Optional[Dict[str, Any]]:
        if not recipient_id:
            return None
        clean_id = recipient_id.strip().upper()
        conn = self.get_connection()
        try:
            row = conn.execute("""
                SELECT r.*,
                       COALESCE(au.balance, 500.0) as usd_balance,
                       COALESCE(ai.balance, 50000.0) as inr_balance
                FROM recipients r
                LEFT JOIN accounts au ON au.owner_id = r.recipient_id AND au.currency = 'USD'
                LEFT JOIN accounts ai ON ai.owner_id = r.recipient_id AND ai.currency = 'INR'
                WHERE r.recipient_id = ?
            """, (clean_id,)).fetchone()
            if row:
                return dict(row)
            return None
        finally:
            conn.close()

    def get_all_recipients(self) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        try:
            rows = conn.execute("""
                SELECT r.*,
                       COALESCE(au.balance, 500.0) as usd_balance,
                       COALESCE(ai.balance, 50000.0) as inr_balance
                FROM recipients r
                LEFT JOIN accounts au ON au.owner_id = r.recipient_id AND au.currency = 'USD'
                LEFT JOIN accounts ai ON ai.owner_id = r.recipient_id AND ai.currency = 'INR'
                ORDER BY r.recipient_id ASC
            """).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def find_recipient(self, query: str) -> Optional[Dict[str, Any]]:
        if not query or not query.strip():
            return None
        clean_q = query.strip().lower().rstrip(".").rstrip(",")
        if clean_q.startswith("to "):
            clean_q = clean_q[3:].strip()

        conn = self.get_connection()
        try:
            # 1. By ID (exact match)
            row = conn.execute("SELECT recipient_id FROM recipients WHERE LOWER(recipient_id) = ?", (clean_q,)).fetchone()
            if row:
                return self.get_recipient(row["recipient_id"])

            # 2. By exact name
            row = conn.execute("SELECT recipient_id FROM recipients WHERE LOWER(recipient_name) = ?", (clean_q,)).fetchone()
            if row:
                return self.get_recipient(row["recipient_id"])

            # If not found in recipients table, check customers table to support role reversal
            cust = self.get_customer(clean_q)
            if not cust:
                row = conn.execute("SELECT customer_id FROM customers WHERE LOWER(customer_name) = ?", (clean_q,)).fetchone()
                if row:
                    cust = self.get_customer(row["customer_id"])
            if not cust:
                rows = conn.execute("SELECT customer_id, customer_name FROM customers WHERE LOWER(customer_name) LIKE ?", (f"%{clean_q}%",)).fetchall()
                if len(rows) == 1:
                    cust = self.get_customer(rows[0]["customer_id"])
                elif len(rows) > 1:
                    for r in rows:
                        if r["customer_name"].strip().lower() == clean_q:
                            cust = self.get_customer(r["customer_id"])
                            break

            if cust:
                country = cust.get("source_country", "India")
                curr = "INR" if "india" in country.lower() else "USD"
                return {
                    "recipient_id": cust["customer_id"],
                    "recipient_name": cust["customer_name"],
                    "recipient_country": country,
                    "destination_country": country,
                    "destination_currency": curr,
                    "inr_balance": cust.get("inr_balance", 100000.0),
                    "usd_balance": cust.get("usd_balance", 10000.0)
                }

            return None
        finally:
            conn.close()

    def get_recipient_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        return self.find_recipient(name)

    def get_recipient_by_id(self, recipient_id: str) -> Optional[Dict[str, Any]]:
        return self.get_recipient(recipient_id)

    def find_person(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Unified identity lookup across both customers and recipients.
        Enables role flexibility: anyone can be a sender or recipient.
        """
        if not query or not query.strip():
            return None
        c = self.find_customer(query)
        if c:
            return {
                "id": c["customer_id"],
                "name": c["customer_name"],
                "country": c.get("source_country", "India"),
                "currency": c.get("source_currency", "INR"),
                "inr_balance": c.get("inr_balance", 100000.0),
                "usd_balance": c.get("usd_balance", 10000.0),
                "type": "CUSTOMER"
            }
        r = self.find_recipient(query)
        if r:
            return {
                "id": r["recipient_id"],
                "name": r["recipient_name"],
                "country": r.get("recipient_country", "United States"),
                "currency": r.get("destination_currency", "USD"),
                "inr_balance": r.get("inr_balance", 50000.0),
                "usd_balance": r.get("usd_balance", 500.0),
                "type": "RECIPIENT"
            }
        return None

    def find_name_candidates(self, query: str) -> List[str]:
        """
        Searches customers and recipients for people matching the query.
        Returns unique matched names.
        If an exact match on full name exists, returns just [exact_full_name].
        If query is a first name (e.g. 'Bhavya'), returns all matches e.g. ['Bhavya Patel', 'Bhavya Desai', ...].
        """
        if not query or not query.strip():
            return []
        clean_q = query.strip().lower().rstrip(".").rstrip(",")
        conn = self.get_connection()
        try:
            # 1. Exact match in customers or recipients
            row = conn.execute("SELECT customer_name FROM customers WHERE LOWER(customer_name) = ?", (clean_q,)).fetchone()
            if row:
                return [row["customer_name"]]
            row = conn.execute("SELECT recipient_name FROM recipients WHERE LOWER(recipient_name) = ?", (clean_q,)).fetchone()
            if row:
                return [row["recipient_name"]]

            # 2. Search by prefix / word boundary (e.g. 'Bhavya' matching 'Bhavya Patel', 'Bhavya Desai')
            matches = set()
            rows_c = conn.execute(
                "SELECT customer_name FROM customers WHERE LOWER(customer_name) LIKE ? OR LOWER(customer_name) LIKE ?",
                (f"{clean_q} %", f"% {clean_q}%")
            ).fetchall()
            for r in rows_c:
                matches.add(r["customer_name"])

            rows_r = conn.execute(
                "SELECT recipient_name FROM recipients WHERE LOWER(recipient_name) LIKE ? OR LOWER(recipient_name) LIKE ?",
                (f"{clean_q} %", f"% {clean_q}%")
            ).fetchall()
            for r in rows_r:
                matches.add(r["recipient_name"])

            # 3. If still nothing, try substring
            if not matches:
                rows_c = conn.execute("SELECT customer_name FROM customers WHERE LOWER(customer_name) LIKE ?", (f"%{clean_q}%",)).fetchall()
                for r in rows_c:
                    matches.add(r["customer_name"])
                rows_r = conn.execute("SELECT recipient_name FROM recipients WHERE LOWER(recipient_name) LIKE ?", (f"%{clean_q}%",)).fetchall()
                for r in rows_r:
                    matches.add(r["recipient_name"])

            return sorted(list(matches))
        finally:
            conn.close()

    # ---------------------------------------------------------
    # ACCOUNT / BALANCE OPERATIONS
    # ---------------------------------------------------------

    def get_balance(self, owner_type: str, owner_id: str, currency: str) -> float:
        clean_type = (owner_type or "").strip().upper()
        clean_id = (owner_id or "").strip().upper()
        curr = "INR" if currency.upper() in ("INR", "₹") else "USD"

        conn = self.get_connection()
        try:
            # First check with both owner_type and owner_id if owner_type provided
            if clean_type:
                row = conn.execute(
                    "SELECT balance FROM accounts WHERE owner_type = ? AND owner_id = ? AND currency = ?",
                    (clean_type, clean_id, curr)
                ).fetchone()
            else:
                row = None

            # Fallback to query by owner_id and currency directly
            if row is None:
                row = conn.execute(
                    "SELECT balance FROM accounts WHERE owner_id = ? AND currency = ? LIMIT 1",
                    (clean_id, curr)
                ).fetchone()

            if row is not None:
                return round(float(row["balance"]), 2)

            # Insert default if not present
            default_bal = 100000.0 if curr == "INR" else 10000.0
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.execute(
                "INSERT OR IGNORE INTO accounts (owner_type, owner_id, currency, balance, last_updated) VALUES (?, ?, ?, ?, ?)",
                (clean_type or "CUSTOMER", clean_id, curr, default_bal, now_str)
            )
            conn.commit()
            return default_bal
        finally:
            conn.close()

    def update_balance(self, owner_type: str, owner_id: str, currency: str, new_balance: float):
        clean_type = (owner_type or "CUSTOMER").strip().upper()
        clean_id = owner_id.strip().upper()
        curr = "INR" if currency.upper() in ("INR", "₹") else "USD"
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = self.get_connection()
        try:
            with conn:
                conn.execute("""
                    INSERT INTO accounts (owner_type, owner_id, currency, balance, last_updated)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(owner_type, owner_id, currency) DO UPDATE SET
                        balance = excluded.balance,
                        last_updated = excluded.last_updated
                """, (clean_type, clean_id, curr, round(new_balance, 2), now_str))
        finally:
            conn.close()

    def get_all_accounts(self) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        try:
            rows = conn.execute("""
                SELECT 
                    a.id,
                    a.owner_type,
                    a.owner_id,
                    a.currency,
                    a.balance,
                    a.last_updated,
                    CASE 
                        WHEN a.owner_type = 'CUSTOMER' THEN c.customer_name
                        WHEN a.owner_type = 'RECIPIENT' THEN r.recipient_name
                        ELSE a.owner_id
                    END AS owner_name
                FROM accounts a
                LEFT JOIN customers c ON a.owner_type = 'CUSTOMER' AND a.owner_id = c.customer_id
                LEFT JOIN recipients r ON a.owner_type = 'RECIPIENT' AND a.owner_id = r.recipient_id
                ORDER BY a.owner_type ASC, a.owner_id ASC, a.currency ASC
            """).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ---------------------------------------------------------
    # TRANSACTION PERSISTENCE & LEDGER
    # ---------------------------------------------------------

    def record_transfer(
        self,
        transaction_id: str,
        conversation_id: str,
        sender_id: str,
        sender_name: str,
        recipient_id: str,
        recipient_name: str,
        source_country: str,
        destination_country: str,
        amount_sent: float,
        source_currency: str,
        recipient_amount: float,
        destination_currency: str,
        transfer_fee: float,
        total_debit: float,
        status: str = "Completed",
        environment: str = "Simulation"
    ) -> Dict[str, Any]:
        """
        Executes an atomic database transaction:
        1. Debits sender account in source currency (works for any customer or recipient).
        2. Credits recipient account in destination currency (works for any recipient or customer).
        3. Inserts transaction record into transactions table.
        """
        cid = sender_id.strip().upper()
        rid = recipient_id.strip().upper()
        src_curr = "INR" if source_currency.upper() in ("INR", "₹") else "USD"
        dst_curr = "INR" if destination_currency.upper() in ("INR", "₹") else "USD"
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

        conn = self.get_connection()
        try:
            with conn:
                # 1. Get and update sender balance (supports role reversal)
                row = conn.execute(
                    "SELECT owner_type, balance FROM accounts WHERE owner_id = ? AND currency = ? LIMIT 1",
                    (cid, src_curr)
                ).fetchone()

                if row:
                    s_owner_type = row["owner_type"]
                    prev_sender_bal = round(float(row["balance"]), 2)
                else:
                    is_cust = conn.execute("SELECT 1 FROM customers WHERE customer_id = ?", (cid,)).fetchone()
                    s_owner_type = 'CUSTOMER' if is_cust else 'RECIPIENT'
                    prev_sender_bal = 100000.0 if src_curr == "INR" else 10000.0

                new_sender_bal = max(0.0, prev_sender_bal - total_debit)
                conn.execute("""
                    INSERT INTO accounts (owner_type, owner_id, currency, balance, last_updated)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(owner_type, owner_id, currency) DO UPDATE SET
                        balance = excluded.balance,
                        last_updated = excluded.last_updated
                """, (s_owner_type, cid, src_curr, round(new_sender_bal, 2), now_str))

                # 2. Get and update recipient balance (supports role reversal)
                row = conn.execute(
                    "SELECT owner_type, balance FROM accounts WHERE owner_id = ? AND currency = ? LIMIT 1",
                    (rid, dst_curr)
                ).fetchone()

                if row:
                    r_owner_type = row["owner_type"]
                    prev_recip_bal = round(float(row["balance"]), 2)
                else:
                    is_recip = conn.execute("SELECT 1 FROM recipients WHERE recipient_id = ?", (rid,)).fetchone()
                    r_owner_type = 'RECIPIENT' if is_recip else 'CUSTOMER'
                    prev_recip_bal = 50000.0 if dst_curr == "INR" else 500.0

                new_recip_bal = prev_recip_bal + recipient_amount
                conn.execute("""
                    INSERT INTO accounts (owner_type, owner_id, currency, balance, last_updated)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(owner_type, owner_id, currency) DO UPDATE SET
                        balance = excluded.balance,
                        last_updated = excluded.last_updated
                """, (r_owner_type, rid, dst_curr, round(new_recip_bal, 2), now_str))

                # 3. Insert transaction record
                conn.execute("""
                    INSERT OR REPLACE INTO transactions (
                        transaction_id, conversation_id, sender_id, sender_name,
                        recipient_id, recipient_name, source_country, destination_country,
                        amount_sent, source_currency, recipient_amount, destination_currency,
                        transfer_fee, total_debit, sender_balance_before, sender_balance_after,
                        recipient_balance_before, recipient_balance_after, timestamp, status, environment
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    transaction_id, conversation_id, cid, sender_name,
                    rid, recipient_name, source_country, destination_country,
                    amount_sent, src_curr, recipient_amount, dst_curr,
                    transfer_fee, total_debit, prev_sender_bal, round(new_sender_bal, 2),
                    prev_recip_bal, round(new_recip_bal, 2), now_str, status, environment
                ))

            entry = {
                "transaction_id": transaction_id,
                "conversation_id": conversation_id,
                "sender_id": cid,
                "sender_name": sender_name,
                "recipient_id": rid,
                "recipient_name": recipient_name,
                "source_country": source_country,
                "destination_country": destination_country,
                "amount_sent": amount_sent,
                "source_currency": src_curr,
                "recipient_amount": recipient_amount,
                "destination_currency": dst_curr,
                "transfer_fee": transfer_fee,
                "total_debit": total_debit,
                "sender_balance_before": prev_sender_bal,
                "sender_balance_after": round(new_sender_bal, 2),
                "recipient_balance_before": prev_recip_bal,
                "recipient_balance_after": round(new_recip_bal, 2),
                "timestamp": now_str,
                "status": status,
                "environment": environment,
                "sender": sender_name,
                "recipient": recipient_name
            }
            logger.info(f"Recorded transaction {transaction_id} for {cid} -> {rid} in SQLite database.")
            return entry
        finally:
            conn.close()

    def get_transaction_by_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        conn = self.get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM transactions WHERE conversation_id = ? ORDER BY rowid DESC LIMIT 1",
                (conversation_id,)
            ).fetchone()
            if row:
                d = dict(row)
                d["sender"] = d["sender_name"]
                d["recipient"] = d["recipient_name"]
                return d
            return None
        finally:
            conn.close()

    def get_all_transactions(self) -> List[Dict[str, Any]]:
        """Returns all completed transactions ordered by newest first (timestamp DESC, rowid DESC)."""
        conn = self.get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM transactions ORDER BY rowid DESC, timestamp DESC"
            ).fetchall()
            results = []
            for r in rows:
                d = dict(r)
                d["sender"] = d["sender_name"]
                d["recipient"] = d["recipient_name"]
                results.append(d)
            return results
        finally:
            conn.close()

    def get_completed_conversation_ids(self) -> List[str]:
        conn = self.get_connection()
        try:
            rows = conn.execute("SELECT DISTINCT conversation_id FROM transactions ORDER BY rowid DESC").fetchall()
            return [r["conversation_id"] for r in rows]
        finally:
            conn.close()

    def get_database_summary(self) -> Dict[str, Any]:
        conn = self.get_connection()
        try:
            cust_count = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
            recip_count = conn.execute("SELECT COUNT(*) FROM recipients").fetchone()[0]
            acct_count = conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
            tx_count = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
            
            latest_tx = conn.execute("SELECT timestamp FROM transactions ORDER BY rowid DESC LIMIT 1").fetchone()
            last_updated = latest_tx[0] if latest_tx else datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            return {
                "total_customers": cust_count,
                "total_recipients": recip_count,
                "total_accounts": acct_count,
                "total_transactions": tx_count,
                "last_updated": last_updated,
                "database_type": "SQLite Persistent",
                "database_file": str(self.db_path.name)
            }
        finally:
            conn.close()

    def add_synthetic_person(
        self,
        name: str,
        residency: str = "India",
        source_country: str = "India",
        initial_inr: float = 100000.0,
        initial_usd: float = 10000.0
    ) -> Dict[str, Any]:
        """
        Dynamically adds a new synthetic person to the SQLite database.
        Creates customer record, recipient record, and persistent accounts for INR and USD.
        """
        clean_name = name.strip()
        country = "India" if "india" in (residency or source_country).lower() else "United States"
        curr = "INR" if country == "India" else "USD"
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = self.get_connection()
        try:
            with conn:
                # Find maximum numeric ID among CUST-XXXX
                rows = conn.execute("SELECT customer_id FROM customers WHERE customer_id LIKE 'CUST-%'").fetchall()
                max_num = 150
                for r in rows:
                    try:
                        num = int(r["customer_id"].split("-")[1])
                        if num > max_num:
                            max_num = num
                    except Exception:
                        pass
                next_num = max_num + 1
                new_cid = f"CUST-{next_num:04d}"
                new_rid = f"REC-{next_num:04d}"

                conn.execute("""
                    INSERT INTO customers (customer_id, customer_name, sender_residency, sender_state, source_country, source_currency)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (new_cid, clean_name, country, None, country, curr))

                conn.execute("""
                    INSERT INTO accounts (owner_type, owner_id, currency, balance, last_updated)
                    VALUES ('CUSTOMER', ?, 'INR', ?, ?)
                """, (new_cid, round(float(initial_inr), 2), now_str))

                conn.execute("""
                    INSERT INTO accounts (owner_type, owner_id, currency, balance, last_updated)
                    VALUES ('CUSTOMER', ?, 'USD', ?, ?)
                """, (new_cid, round(float(initial_usd), 2), now_str))

                conn.execute("""
                    INSERT OR IGNORE INTO recipients (recipient_id, recipient_name, recipient_country, destination_country, destination_currency)
                    VALUES (?, ?, ?, ?, ?)
                """, (new_rid, clean_name, country, country, curr))

                conn.execute("""
                    INSERT OR IGNORE INTO accounts (owner_type, owner_id, currency, balance, last_updated)
                    VALUES ('RECIPIENT', ?, 'INR', ?, ?)
                """, (new_rid, round(float(initial_inr), 2), now_str))

                conn.execute("""
                    INSERT OR IGNORE INTO accounts (owner_type, owner_id, currency, balance, last_updated)
                    VALUES ('RECIPIENT', ?, 'USD', ?, ?)
                """, (new_rid, round(float(initial_usd), 2), now_str))

            return {
                "customer_id": new_cid,
                "customer_name": clean_name,
                "recipient_id": new_rid,
                "recipient_name": clean_name,
                "person_id": new_cid,
                "name": clean_name,
                "source_country": country,
                "source_currency": curr,
                "inr_balance": round(float(initial_inr), 2),
                "usd_balance": round(float(initial_usd), 2)
            }
        finally:
            conn.close()

db_service = DatabaseService()
