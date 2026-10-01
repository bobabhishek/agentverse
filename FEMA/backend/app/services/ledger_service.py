import io
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from app.services.database import db_service

class LedgerService:
    """
    Maintains simulated ledger accounts backed by the persistent SQLite database.
    Provides per-conversation audit trails and PDF export.
    """

    def __init__(self):
        self._db = db_service

    def get_customer_balance(self, customer_id: Optional[str] = None, currency: str = "INR") -> float:
        if customer_id and customer_id.strip():
            cid = customer_id.strip().upper()
        else:
            recent = self._db.get_all_transactions()
            if recent:
                cid = recent[0].get("sender_id", "CUST-0001")
            else:
                cid = "CUST-0001"
        return self._db.get_balance("CUSTOMER", cid, currency)

    def get_sender_balance(self, currency: str = "INR", customer_id: Optional[str] = None) -> float:
        return self.get_customer_balance(customer_id, currency)

    def get_recipient_balance(self, recipient_id: Optional[str] = None, currency: str = "USD") -> float:
        if recipient_id and recipient_id.strip():
            rid = recipient_id.strip().upper()
        else:
            recent = self._db.get_all_transactions()
            if recent:
                rid = recent[0].get("recipient_id", "REC-0001")
            else:
                rid = "REC-0001"
        return self._db.get_balance("RECIPIENT", rid, currency)

    def has_sufficient_balance(self, *args, **kwargs) -> Tuple[bool, float]:
        target_customer_id = kwargs.get("customer_id")
        amount = 0.0
        currency = "INR"

        if len(args) == 1:
            if isinstance(args[0], (int, float)):
                amount = float(args[0])
        elif len(args) == 2:
            if isinstance(args[0], (int, float)):
                amount = float(args[0])
                currency = str(args[1])
            else:
                target_customer_id = str(args[0])
                amount = float(args[1])
        elif len(args) >= 3:
            if isinstance(args[0], (int, float)):
                amount = float(args[0])
                currency = str(args[1])
                target_customer_id = str(args[2])
            else:
                target_customer_id = str(args[0])
                amount = float(args[1])
                currency = str(args[2])

        if "amount" in kwargs:
            amount = float(kwargs["amount"])
        if "currency" in kwargs:
            currency = str(kwargs["currency"])

        current = self.get_customer_balance(target_customer_id, currency)
        return (current >= amount, current)


    def record_successful_transfer(
        self,
        transaction_id: str,
        conversation_id: str,
        sender_id: Optional[str] = None,
        sender_name: Optional[str] = None,
        recipient_id: Optional[str] = None,
        recipient_name: Optional[str] = None,
        source_country: str = "India",
        destination_country: str = "United States",
        amount_sent: float = 0.0,
        source_currency: str = "INR",
        recipient_amount: float = 0.0,
        destination_currency: str = "USD",
        transfer_fee: float = 0.0,
        total_debit: float = 0.0,
        status: str = "Completed",
        environment: str = "Simulation",
        sender: Optional[str] = None,
        recipient: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Deducts sender's balance, credits recipient's balance, and writes a permanent
        transaction row to the persistent SQLite database.
        """
        s_name = (sender_name or sender or "").strip()
        r_name = (recipient_name or recipient or "").strip()

        cid = (sender_id or "").strip().upper()
        if s_name:
            p = self._db.find_person(s_name)
            if p:
                if not cid:
                    cid = p["id"]
                s_name = p["name"]
        elif cid:
            p = self._db.find_person(cid)
            if p:
                s_name = p["name"]

        if not cid:
            cid = "CUST-0001"
        if not s_name:
            s_name = "Sender"

        rid = (recipient_id or "").strip().upper()
        if r_name:
            p = self._db.find_person(r_name)
            if p:
                if not rid:
                    rid = p["id"]
                r_name = p["name"]
        elif rid:
            p = self._db.find_person(rid)
            if p:
                r_name = p["name"]

        if not rid:
            rid = "REC-0001"
        if not r_name:
            r_name = "Recipient"

        return self._db.record_transfer(
            transaction_id=transaction_id,
            conversation_id=conversation_id,
            sender_id=cid,
            sender_name=s_name,
            recipient_id=rid,
            recipient_name=r_name,
            source_country=source_country,
            destination_country=destination_country,
            amount_sent=amount_sent,
            source_currency=source_currency,
            recipient_amount=recipient_amount,
            destination_currency=destination_currency,
            transfer_fee=transfer_fee,
            total_debit=total_debit,
            status=status,
            environment=environment
        )


    def get_audit_trail(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        return self._db.get_transaction_by_conversation(conversation_id)

    def get_completed_conversation_ids(self) -> List[str]:
        return self._db.get_completed_conversation_ids()

    def get_summary_balances(self, customer_id: Optional[str] = None) -> Dict[str, Any]:
        if customer_id and customer_id.strip():
            cid = customer_id.strip().upper()
        else:
            recent = self._db.get_all_transactions()
            if recent:
                cid = recent[0].get("sender_id", "CUST-0001")
            else:
                cid = "CUST-0001"

        sender_inr = self.get_customer_balance(cid, "INR")
        sender_usd = self.get_customer_balance(cid, "USD")

        # Build customer and recipient balances dictionaries from SQLite
        all_accounts = self._db.get_all_accounts()
        cust_bals: Dict[str, Dict[str, float]] = {}
        recip_bals: Dict[str, Dict[str, float]] = {}

        for acc in all_accounts:
            otype = acc["owner_type"]
            oid = acc["owner_id"]
            curr = acc["currency"]
            bal = round(float(acc["balance"]), 2)
            if otype == "CUSTOMER":
                if oid not in cust_bals:
                    cust_bals[oid] = {}
                cust_bals[oid][curr] = bal
            elif otype == "RECIPIENT":
                if oid not in recip_bals:
                    recip_bals[oid] = {}
                recip_bals[oid][curr] = bal

        return {
            "customer_id": cid,
            "sender": {
                "INR": round(sender_inr, 2),
                "USD": round(sender_usd, 2)
            },
            "customer_balances": cust_bals,
            "recipient_balances": recip_bals,
            "completed_conversations": self.get_completed_conversation_ids()
        }

    def generate_audit_trail_pdf(self, conversation_id: str) -> Optional[bytes]:
        entry = self.get_audit_trail(conversation_id)
        if not entry:
            return None

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=45,
            leftMargin=45,
            topMargin=45,
            bottomMargin=45
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'AuditTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=18,
            leading=22,
            textColor=colors.HexColor('#0f172a'),
            alignment=0,
            spaceAfter=4
        )

        subtitle_style = ParagraphStyle(
            'AuditSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#64748b'),
            spaceAfter=15
        )

        section_heading = ParagraphStyle(
            'AuditSection',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=14,
            textColor=colors.HexColor('#1e293b'),
            spaceBefore=10,
            spaceAfter=6
        )

        cell_label = ParagraphStyle(
            'CellLabel',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#475569')
        )

        cell_value = ParagraphStyle(
            'CellValue',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#0f172a')
        )

        story = []

        # Header Badge & Title
        story.append(Paragraph("AGENTVERSE · FEMA COMPLIANCE TEST BENCH", subtitle_style))
        story.append(Paragraph("TRANSACTION AUDIT TRAIL", title_style))
        story.append(Paragraph(f"Official transaction audit record generated for session {entry.get('conversation_id', '')}", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#cbd5e1'), spaceBefore=2, spaceAfter=14))

        # Core Metadata Table
        data_overview = [
            [
                Paragraph("Transaction ID", cell_label),
                Paragraph(str(entry.get('transaction_id', 'N/A')), cell_value),
                Paragraph("Date / Time", cell_label),
                Paragraph(str(entry.get('timestamp', 'N/A')), cell_value)
            ],
            [
                Paragraph("Status", cell_label),
                Paragraph(f"<font color='#059669'><b>{entry.get('status', 'Completed')}</b></font>", cell_value),
                Paragraph("Environment", cell_label),
                Paragraph(str(entry.get('environment', 'Simulation')), cell_value)
            ]
        ]

        t_overview = Table(data_overview, colWidths=[110, 150, 110, 150])
        t_overview.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(t_overview)
        story.append(Spacer(1, 14))

        # Parties & Routing Section
        story.append(Paragraph("TRANSACTION PARTIES & ROUTING", section_heading))
        sender_account_text = str(entry.get('sender_name') or entry.get('sender') or 'Customer')
        if entry.get('sender_id'):
            sender_account_text = f"<b>{sender_account_text}</b><br/><font color='#64748b' size='8'>Account / ID: {entry.get('sender_id')}</font>"
        else:
            sender_account_text = f"<b>{sender_account_text}</b>"

        recipient_account_text = str(entry.get('recipient_name') or entry.get('recipient') or 'Recipient')
        if entry.get('recipient_id'):
            recipient_account_text = f"<b>{recipient_account_text}</b><br/><font color='#64748b' size='8'>Account / ID: {entry.get('recipient_id')}</font>"
        else:
            recipient_account_text = f"<b>{recipient_account_text}</b>"

        data_parties = [
            [
                Paragraph("Source Customer (Sender)", cell_label),
                Paragraph(sender_account_text, cell_value),
                Paragraph("Source Country", cell_label),
                Paragraph(str(entry.get('source_country', 'India')), cell_value)
            ],
            [
                Paragraph("Beneficiary (Recipient)", cell_label),
                Paragraph(recipient_account_text, cell_value),
                Paragraph("Destination Country", cell_label),
                Paragraph(str(entry.get('destination_country', 'United States')), cell_value)
            ]
        ]

        t_parties = Table(data_parties, colWidths=[130, 130, 110, 150])
        t_parties.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(t_parties)
        story.append(Spacer(1, 14))

        # Financial Summary Section
        story.append(Paragraph("FINANCIAL DETAILS & LEDGER IMPACT", section_heading))
        src_curr = entry.get('source_currency', 'INR')
        dst_curr = entry.get('destination_currency', 'USD')
        amt_sent = f"{src_curr} {entry.get('amount_sent', 0):,.2f}"
        recip_amt = f"{dst_curr} {entry.get('recipient_amount', 0):,.2f}"
        fee_str = f"{src_curr} {entry.get('transfer_fee', 0):,.2f}"
        debit_str = f"{src_curr} {entry.get('total_debit', 0):,.2f}"

        sender_before = f"{src_curr} {entry.get('sender_balance_before', 0):,.2f}"
        sender_after = f"{src_curr} {entry.get('sender_balance_after', 0):,.2f}"
        recip_before = f"{dst_curr} {entry.get('recipient_balance_before', 0):,.2f}"
        recip_after = f"{dst_curr} {entry.get('recipient_balance_after', 0):,.2f}"

        data_financials = [
            [Paragraph("Amount Sent", cell_label), Paragraph(amt_sent, cell_value)],
            [Paragraph("Recipient Received", cell_label), Paragraph(recip_amt, cell_value)],
            [Paragraph("Transfer Fee", cell_label), Paragraph(fee_str, cell_value)],
            [Paragraph("Total Debited", cell_label), Paragraph(f"<b>{debit_str}</b>", cell_value)],
            [Paragraph("Sender Balance (Before → After)", cell_label), Paragraph(f"{sender_before} → <b>{sender_after}</b>", cell_value)],
            [Paragraph("Recipient Balance (Before → After)", cell_label), Paragraph(f"{recip_before} → <b>{recip_after}</b>", cell_value)],
            [Paragraph("Simulated Payment Gateway", cell_label), Paragraph("WireMock (Simulation Endpoint)", cell_value)]
        ]

        t_financials = Table(data_financials, colWidths=[200, 320])
        t_financials.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ffffff')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#f1f5f9')),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(t_financials)
        story.append(Spacer(1, 24))

        # Security & Audit Footnote
        story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor('#e2e8f0'), spaceBefore=6, spaceAfter=8))
        note_style = ParagraphStyle(
            'AuditFootnote',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=8,
            leading=11,
            textColor=colors.HexColor('#94a3b8'),
            alignment=1
        )
        story.append(Paragraph("This document is a certified simulated audit trail generated by the FEMA Autonomous Payment Agent Test Bench. Backed by persistent database storage.", note_style))

        doc.build(story)
        return buffer.getvalue()

ledger_service = LedgerService()
