class FundamentalService:
    """Extracts, validates and scores fundamental financial metrics."""

    @staticmethod
    def extract_fundamentals(info_dict):
        if not info_dict or not isinstance(info_dict, dict):
            return {
                "available": False,
                "reason": "Fundamental data is not available"
            }

        try:
            info = info_dict

            def safe_float(val, default=None):
                if val is None:
                    return default
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return default

            def safe_pct(val):
                f = safe_float(val)
                if f is None:
                    return "Not available"
                return f"{f * 100:.2f}%"

            def safe_currency(val):
                f = safe_float(val)
                if f is None:
                    return "Not available"
                if abs(f) >= 1_000_000_000_000:
                    return f"₹{f / 1_000_000_000_000:.2f} T"
                if abs(f) >= 1_000_000_000:
                    return f"₹{f / 1_000_000_000:.2f} B"
                if abs(f) >= 10_000_000:
                    return f"₹{f / 10_000_000:.2f} Cr"
                if abs(f) >= 100_000:
                    return f"₹{f / 100_000:.2f} L"
                return f"₹{f:,.2f}"

            pe = safe_float(info.get("trailingPE") or info.get("forwardPE"))
            pb = safe_float(info.get("priceToBook"))
            roe = safe_float(info.get("returnOnEquity"))
            roa = safe_float(info.get("returnOnAssets"))
            debt_to_equity = safe_float(info.get("debtToEquity"))
            profit_margin = safe_float(info.get("profitMargins"))
            operating_margin = safe_float(info.get("operatingMargins"))
            revenue_growth = safe_float(info.get("revenueGrowth"))
            earnings_growth = safe_float(info.get("earningsGrowth"))
            dividend_yield = safe_float(info.get("dividendYield"))
            free_cash_flow = safe_float(info.get("freeCashflow"))
            ebitda = safe_float(info.get("ebitda"))
            market_cap = safe_float(info.get("marketCap"))
            eps = safe_float(info.get("trailingEps") or info.get("forwardEps"))
            total_revenue = safe_float(info.get("totalRevenue"))

            # Calculate deterministic Fundamental Score (0-100)
            score = 50.0
            factors_evaluated = 0

            # 1. Profitability (ROE / ROA)
            if roe is not None:
                factors_evaluated += 1
                if roe > 0.20:
                    score += 15
                elif roe > 0.12:
                    score += 8
                elif roe < 0.05:
                    score -= 10

            # 2. Operating Margins
            if operating_margin is not None:
                factors_evaluated += 1
                if operating_margin > 0.20:
                    score += 10
                elif operating_margin > 0.10:
                    score += 5
                elif operating_margin < 0:
                    score -= 12

            # 3. Debt-to-Equity (Solvency)
            if debt_to_equity is not None:
                factors_evaluated += 1
                if debt_to_equity < 50:
                    score += 12 # Very low debt
                elif debt_to_equity < 120:
                    score += 5  # Manageable debt
                elif debt_to_equity > 250:
                    score -= 15 # High leverage risk

            # 4. Revenue / Earnings Growth
            if revenue_growth is not None:
                factors_evaluated += 1
                if revenue_growth > 0.15:
                    score += 12
                elif revenue_growth > 0.05:
                    score += 5
                elif revenue_growth < -0.05:
                    score -= 10

            # 5. Free Cash Flow
            if free_cash_flow is not None:
                factors_evaluated += 1
                if free_cash_flow > 0:
                    score += 8
                else:
                    score -= 6

            # 6. Valuation sanity (P/E)
            if pe is not None:
                factors_evaluated += 1
                if 5 <= pe <= 28:
                    score += 8  # Fair / attractive valuation
                elif pe > 75:
                    score -= 8  # Premium / expensive valuation
                elif pe < 0:
                    score -= 10 # Negative earnings

            fundamental_score = int(round(max(10, min(95, score)))) if factors_evaluated >= 2 else 50

            return {
                "available": True,
                "pe_ratio": f"{pe:.2f}" if pe is not None else "Not available",
                "pb_ratio": f"{pb:.2f}" if pb is not None else "Not available",
                "roe": safe_pct(roe),
                "roa": safe_pct(roa),
                "debt_to_equity": f"{debt_to_equity:.2f}" if debt_to_equity is not None else "Not available",
                "profit_margin": safe_pct(profit_margin),
                "operating_margin": safe_pct(operating_margin),
                "revenue_growth": safe_pct(revenue_growth),
                "earnings_growth": safe_pct(earnings_growth),
                "dividend_yield": safe_pct(dividend_yield),
                "free_cash_flow": safe_currency(free_cash_flow),
                "ebitda": safe_currency(ebitda),
                "total_revenue": safe_currency(total_revenue),
                "market_cap": safe_currency(market_cap),
                "eps": f"₹{eps:.2f}" if eps is not None else "Not available",
                "sector": info.get("sector", "Not available"),
                "industry": info.get("industry", "Not available"),
                "fundamental_score": fundamental_score,
                "raw_metrics": {
                    "pe": pe,
                    "pb": pb,
                    "roe": roe,
                    "debt_to_equity": debt_to_equity,
                    "revenue_growth": revenue_growth,
                    "dividend_yield": dividend_yield,
                    "market_cap": market_cap
                }
            }

        except Exception as e:
            return {
                "available": False,
                "reason": f"Fundamental calculation error: {str(e)}"
            }
