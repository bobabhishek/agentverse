import logging
from fastapi import APIRouter, HTTPException, Response
from fpdf import FPDF
from app.services.database import db_service
import datetime

logger = logging.getLogger("fema.routes.banking")
router = APIRouter(prefix="/api/banking", tags=["banking"])

class StatementPDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 16)
        self.cell(0, 10, 'BANK STATEMENT', border=False, align='C', fill=False)
        self.ln(20)

    def footer(self):
        self.set_y(-25)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 5, 'SIMULATION ONLY', border=False, align='C', fill=False)
        self.ln(4)
        self.cell(0, 5, 'Synthetic Data - No Real Funds', border=False, align='C', fill=False)
        self.ln(4)
        self.cell(0, 5, 'FEMA Guardrail Test Bench Simulation Environment', border=False, align='C', fill=False)
        self.ln(4)
        self.cell(0, 5, f'Page {self.page_no()}', border=False, align='C', fill=False)

@router.get("/{person_id}/statement/pdf")
async def get_statement_pdf(person_id: str):
    db_record = db_service.get_full_person_details(person_id)
    if not db_record:
        raise HTTPException(status_code=404, detail="Person not found")

    owner_id = db_record.get("customer_id") or db_record.get("recipient_id")
    txs = db_service.get_recent_transactions(owner_id, limit=200)

    accounts = db_record.get("accounts", [])
    if not accounts:
        raise HTTPException(status_code=404, detail="No accounts found for person")

    acc = accounts[0]
    balance = acc.get("balance", 0)
    currency = acc.get("currency", "INR")
    
    # generate PDF
    pdf = StatementPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=30)
    pdf.set_font("helvetica", size=10)
    
    # Account Info
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, "Account Information", ln=True)
    pdf.set_font("helvetica", size=10)
    
    pdf.cell(40, 6, "Account Holder:", border=0)
    pdf.cell(0, 6, str(db_record.get("customer_name") or db_record.get("recipient_name", "")), border=0, ln=True)
    pdf.cell(40, 6, "Bank Name:", border=0)
    pdf.cell(0, 6, str(acc.get("bank_name", "")), border=0, ln=True)
    pdf.cell(40, 6, "Account Number:", border=0)
    pdf.cell(0, 6, str(acc.get("account_number", "")), border=0, ln=True)
    pdf.cell(40, 6, "Account Type:", border=0)
    pdf.cell(0, 6, "Savings Account", border=0, ln=True)
    pdf.cell(40, 6, "Currency:", border=0)
    pdf.cell(0, 6, str(currency), border=0, ln=True)
    pdf.ln(8)
    
    # Statement Summary
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, "Statement Summary", ln=True)
    pdf.set_font("helvetica", size=10)
    
    pdf.cell(40, 6, "Statement Date:", border=0)
    pdf.cell(0, 6, datetime.datetime.now().strftime("%Y-%m-%d"), border=0, ln=True)
    pdf.cell(40, 6, "Closing Balance:", border=0)
    pdf.cell(0, 6, f"{balance:,.2f} {currency}", border=0, ln=True)
    pdf.ln(10)
    
    # Transactions
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, "Transaction History", ln=True)
    pdf.set_font("helvetica", size=8)
    
    # Table Header
    col_widths = [25, 40, 50, 25, 25, 25]
    headers = ["Date", "Transaction ID", "Description", "Debit", "Credit", "Balance"]
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 8, h, border=1, align='C')
    pdf.ln()
    
    pdf.set_font("helvetica", size=8)
    
    # Calculate running balances backwards from current balance
    running_balance = float(balance)
    
    # Create list of formatted rows
    rows = []
    # txs is newest to oldest
    for t in txs:
        is_sender = (t.get("sender_id") == owner_id)
        
        debit = ""
        credit = ""
        
        # Current row's closing balance is running_balance
        row_balance = running_balance
        
        if is_sender:
            amt = float(t.get("total_debit", t.get("amount_sent", 0)))
            debit = f"{amt:,.2f}"
            running_balance += amt  # before this debit, balance was higher
            desc = f"Transfer to {t.get('recipient_id')}"
        else:
            amt = float(t.get("recipient_amount", t.get("amount_sent", 0)))
            credit = f"{amt:,.2f}"
            running_balance -= amt  # before this credit, balance was lower
            desc = f"Transfer from {t.get('sender_id')}"
            
        purpose = t.get("purpose")
        if purpose and purpose != "None":
            desc = desc[:30] + "..." if len(desc) > 30 else desc
        else:
            desc = desc[:45] + "..." if len(desc) > 45 else desc

        rows.append({
            "date": str(t.get("timestamp", ""))[:10],
            "tx_id": str(t.get("transaction_id", "")),
            "desc": desc,
            "debit": debit,
            "credit": credit,
            "balance": f"{row_balance:,.2f}"
        })
        
    for r in reversed(rows):
        pdf.cell(col_widths[0], 8, r["date"], border=1, align='C')
        pdf.cell(col_widths[1], 8, r["tx_id"], border=1, align='C')
        pdf.cell(col_widths[2], 8, r["desc"], border=1, align='L')
        pdf.cell(col_widths[3], 8, r["debit"], border=1, align='R')
        pdf.cell(col_widths[4], 8, r["credit"], border=1, align='R')
        pdf.cell(col_widths[5], 8, r["balance"], border=1, align='R')
        pdf.ln()

    if not rows:
        pdf.cell(sum(col_widths), 8, "No transactions available for this account.", border=1, align='C', ln=True)

    pdf_bytes = pdf.output()
    person_name = db_record.get("customer_name") or db_record.get("recipient_name", "Unknown")
    filename_name = person_name.replace(" ", "_")
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = f"{filename_name}_Bank_Statement_{date_str}.pdf"
    
    headers_dict = {
        'Content-Disposition': f'attachment; filename="{filename}"',
        'Content-Type': 'application/pdf'
    }
    return Response(content=bytes(pdf_bytes), headers=headers_dict)
