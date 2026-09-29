from typing import Dict, Any

FX_RATE_USD_INR = 83.50

class MockFXService:
    """
    Deterministic simulated Foreign Exchange and Fee calculation service.
    Supports both India -> US (INR -> USD) and US -> India (USD -> INR).
    Clearly deterministic and labeled for simulation.
    """
    @staticmethod
    def calculate_fx(
        amount: float,
        source_currency: str,
        destination_currency: str
    ) -> Dict[str, Any]:
        src = source_currency.upper().strip()
        dst = destination_currency.upper().strip()

        if src == "INR" and dst == "USD":
            fx_rate = FX_RATE_USD_INR
            converted_amount = round(amount / fx_rate, 2)
            # Deterministic transfer fee in INR (flat ₹500 for standard amounts)
            fee = 500.0 if amount >= 10000 else 250.0
            total_debit = round(amount + fee, 2)
            fee_currency = "INR"
        elif src == "USD" and dst == "INR":
            fx_rate = FX_RATE_USD_INR
            converted_amount = round(amount * fx_rate, 2)
            # Deterministic transfer fee in USD ($15 for standard amounts)
            fee = 15.0 if amount >= 200 else 10.0
            total_debit = round(amount + fee, 2)
            fee_currency = "USD"
        else:
            # Fallback 1:1 if matching
            fx_rate = 1.0
            converted_amount = round(amount, 2)
            fee = 0.0
            total_debit = round(amount, 2)
            fee_currency = src

        return {
            "source_currency": src,
            "destination_currency": dst,
            "amount": amount,
            "exchange_rate": fx_rate,
            "converted_amount": converted_amount,
            "transfer_fee": fee,
            "fee_currency": fee_currency,
            "total_debit": total_debit
        }

mock_fx_service = MockFXService()
