import os
import json
import requests
from config import Config
from services.cache_service import CacheService

class LLMService:
    """Enterprise AI Service with secure backend tool executions and explainable finance intelligence."""

    @staticmethod
    def get_api_key():
        return os.getenv("OPENROUTER_API_KEY") or getattr(Config, "OPENROUTER_API_KEY", None)

    @classmethod
    def ask_financial_assistant(cls, question, user_id=None, current_stock_context=None):
        if not question or not question.strip():
            return {
                "success": False,
                "answer": "Please ask a financial or stock market question."
            }

        api_key = cls.get_api_key()
        if not api_key:
            return {
                "success": False,
                "answer": "AI service is currently offline. Please configure OPENROUTER_API_KEY in your .env file."
            }

        # Retrieve real backend data context based on intent
        tool_context = cls._resolve_tools_context(question, user_id, current_stock_context)

        system_prompt = (
            "You are InvestIQ AI, an elite financial research assistant and investment intelligence strategist. "
            "You provide data-backed, institutional-grade analysis for Indian and global equities. "
            "Rules you must strictly obey:\n"
            "1. ALWAYS use the provided verified live market/portfolio context below. NEVER fabricate prices, numbers, or metrics.\n"
            "2. If requested data is missing from context, state that data is unavailable instead of inventing it.\n"
            "3. Support queries in English, Hindi, or Hinglish based on the user's language.\n"
            "4. Clearly explain financial concepts (like P/E, ROE, RSI, ATR, Support/Resistance) simply and practically.\n"
            "5. Never guarantee returns or predict exact future stock prices. Always maintain risk awareness.\n"
            "6. Keep responses clear, professional, structured, and easy to read."
        )

        models = [
            "openai/gpt-4o-mini",
            "openai/gpt-4o",
            "anthropic/claude-3.5-haiku",
            "google/gemini-2.5-flash"
        ]

        user_content = f"Verified Live Data Context:\n{tool_context}\n\nUser Question:\n{question}"

        for model in models:
            try:
                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                        "X-Title": "InvestIQ",
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_content},
                        ],
                        "temperature": 0.3,
                        "max_tokens": 500,
                    },
                    timeout=20,
                )

                if response.status_code == 200:
                    ai_data = response.json()
                    answer = (
                        ai_data.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")
                        .strip()
                    )
                    if answer:
                        return {"success": True, "answer": answer}
            except Exception as e:
                print(f"LLM Model {model} error:", e)

        return {
            "success": False,
            "answer": "InvestIQ AI assistant is temporarily busy. Please review the live metrics on your dashboard and try again in a few moments."
        }

    @classmethod
    def analyze_portfolio_ai(cls, portfolio_summary):
        if not portfolio_summary or not portfolio_summary.get("has_holdings"):
            return {
                "success": True,
                "summary": "Your portfolio currently has no holdings. Add stocks or transactions to receive personalized AI diversification insights and risk analysis.",
                "strengths": ["Clean slate ready for structured capital allocation"],
                "risks": ["No active market exposure"],
                "recommendations": ["Start by selecting quality companies across diversified sectors like Technology, Banking, and FMCG."]
            }

        api_key = cls.get_api_key()
        if not api_key:
            # Deterministic algorithmic fallback if API key is not set
            return cls._deterministic_portfolio_analysis(portfolio_summary)

        try:
            holdings_summary = [
                f"{h['display_symbol']} ({h['name']}): Qty {h['quantity']}, Invested ₹{h['invested_value']:,}, Current ₹{h['current_value']:,}, P&L {h['unrealized_pnl_pct']:+.2f}%, Weight {h['allocation_pct']}%"
                for h in portfolio_summary.get("holdings", [])
            ]
            sectors_summary = [
                f"{s['sector']}: {s['percentage']}%"
                for s in portfolio_summary.get("sector_allocation", [])
            ]

            prompt = (
                f"Analyze this verified user investment portfolio:\n"
                f"Total Invested: ₹{portfolio_summary['total_invested']:,}\n"
                f"Total Current Value: ₹{portfolio_summary['total_value']:,}\n"
                f"Total Unrealized P&L: ₹{portfolio_summary['unrealized_pnl']:,} ({portfolio_summary['unrealized_pnl_pct']:+.2f}%)\n"
                f"Realized P&L: ₹{portfolio_summary['realized_pnl']:,}\n"
                f"Health Score: {portfolio_summary['health_score']}/100 ({portfolio_summary['health_label']})\n"
                f"Holdings:\n" + "\n".join(holdings_summary) + "\n"
                f"Sector Allocation:\n" + "\n".join(sectors_summary) + "\n\n"
                "Return a structured JSON with:\n"
                "1. 'summary': 2-3 sentence overview\n"
                "2. 'strengths': array of 2-3 key strengths\n"
                "3. 'risks': array of 2-3 key risks / concentration warnings\n"
                "4. 'recommendations': array of 2-3 practical rebalancing suggestions\n"
                "Do NOT make guaranteed return claims. Output valid JSON only."
            )

            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "X-Title": "InvestIQ Portfolio Advisor",
                },
                json={
                    "model": "openai/gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": "You are InvestIQ Portfolio Advisor. Respond strictly in valid JSON format."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"},
                    "max_tokens": 450,
                },
                timeout=18,
            )

            if response.status_code == 200:
                data = json.loads(response.json()["choices"][0]["message"]["content"])
                return {
                    "success": True,
                    "summary": data.get("summary", ""),
                    "strengths": data.get("strengths", []),
                    "risks": data.get("risks", []),
                    "recommendations": data.get("recommendations", [])
                }
        except Exception as e:
            print("Portfolio AI error:", e)

        return cls._deterministic_portfolio_analysis(portfolio_summary)

    @classmethod
    def _deterministic_portfolio_analysis(cls, summary):
        holdings = summary.get("holdings", [])
        sectors = summary.get("sector_allocation", [])
        total_pnl_pct = summary.get("total_return_pct", 0)

        strengths = []
        risks = []
        recs = []

        if len(holdings) >= 5:
            strengths.append(f"Diversified across {len(holdings)} holdings with active sector presence")
        else:
            risks.append("Concentration in fewer than 5 stocks increases portfolio volatility")
            recs.append("Consider adding 2-3 quality large-cap holdings to improve risk spread")

        if sectors and sectors[0]["percentage"] > 40:
            risks.append(f"Heavy sector tilt in {sectors[0]['sector']} ({sectors[0]['percentage']}%)")
            recs.append(f"Reduce new allocations to {sectors[0]['sector']} and diversify into under-represented sectors")
        elif len(sectors) >= 3:
            strengths.append(f"Balanced industry exposure across {len(sectors)} distinct sectors")

        if total_pnl_pct > 0:
            strengths.append(f"Overall portfolio returns are positive ({total_pnl_pct:+.2f}%)")
        else:
            risks.append(f"Portfolio is experiencing temporary drawdown ({total_pnl_pct:+.2f}%)")
            recs.append("Review underperforming positions against fundamental metrics before adding capital")

        overview = (
            f"Your portfolio has {len(holdings)} holdings with a current valuation of ₹{summary['total_value']:,}. "
            f"Overall return stands at {total_pnl_pct:+.2f}%. Health score is rated {summary['health_score']}/100 ({summary['health_label']})."
        )

        return {
            "success": True,
            "summary": overview,
            "strengths": strengths or ["Portfolio tracking is actively established"],
            "risks": risks or ["Subject to ongoing equity market swings"],
            "recommendations": recs or ["Maintain periodic rebalancing every quarter"]
        }

    @classmethod
    def _resolve_tools_context(cls, question, user_id, current_stock_context):
        from services.stock_service import StockService
        from services.portfolio_service import PortfolioService
        from database.models import Watchlist

        q_lower = question.lower()
        context_parts = []

        # 1. Check if user is asking about their Portfolio
        if any(w in q_lower for w in ["my portfolio", "portfolio", "holdings", "investment", "meri portfolio", "pnl"]):
            if user_id:
                try:
                    port = PortfolioService.get_or_create_portfolio(user_id)
                    summary = PortfolioService.get_portfolio_summary(port.id)
                    if summary["has_holdings"]:
                        h_strs = [f"{h['display_symbol']}: Qty {h['quantity']}, Value ₹{h['current_value']:,}, P&L {h['unrealized_pnl_pct']:+.2f}%" for h in summary["holdings"][:5]]
                        context_parts.append(
                            f"[Authenticated User Portfolio]\n"
                            f"Total Value: ₹{summary['total_value']:,} | Invested: ₹{summary['total_invested']:,} | P&L: ₹{summary['unrealized_pnl']:,} ({summary['unrealized_pnl_pct']:+.2f}%)\n"
                            f"Top Holdings: {', '.join(h_strs)}"
                        )
                    else:
                        context_parts.append("[Authenticated User Portfolio]: Currently empty (0 holdings).")
                except Exception as e:
                    context_parts.append(f"[Portfolio Data]: Error loading: {str(e)}")

        # 2. Check if user is asking about their Watchlist
        if "watchlist" in q_lower:
            if user_id:
                try:
                    items = Watchlist.query.filter_by(user_id=user_id).all()
                    syms = [i.symbol for i in items]
                    context_parts.append(f"[User Watchlist Stocks]: {', '.join(syms) if syms else 'Watchlist is currently empty.'}")
                except Exception:
                    pass

        # 3. Detect stock symbol from question
        detected_symbol = None
        for word in question.replace("?", "").replace(",", "").split():
            clean = word.strip().upper()
            if clean in ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "ITC", "LT", "AXISBANK", "MARUTI", "WIPRO", "TATAMOTORS", "BHARTIARTL"]:
                detected_symbol = f"{clean}.NS"
                break
            elif clean.endswith(".NS") or clean.endswith(".BO"):
                detected_symbol = clean
                break

        if detected_symbol:
            try:
                stock = StockService.get_stock_details(detected_symbol)
                ai_eval = StockService.get_ai_analysis(detected_symbol)
                if stock:
                    context_parts.append(
                        f"[Stock Data for {detected_symbol}]\n"
                        f"Company: {stock.get('name')} | Price: ₹{stock.get('price')} ({stock.get('price_change')})\n"
                        f"P/E: {stock.get('pe')} | Market Cap: {stock.get('market_cap')} | ROE: {stock.get('roe')}\n"
                        f"AI Signal: {ai_eval.get('signal')} (Score {ai_eval.get('overall')}/100) | Target: ₹{ai_eval.get('target')} | Stop Loss: ₹{ai_eval.get('stop_loss')}"
                    )
            except Exception as e:
                context_parts.append(f"[Stock Data]: Unable to fetch live details for {detected_symbol}: {e}")

        # 4. Add Market Indices summary
        try:
            m = StockService.get_market_data()
            context_parts.append(f"[Broad Market]: NIFTY 50: {m.get('nifty')}, SENSEX: {m.get('sensex')} (Status: {m.get('status')})")
        except Exception:
            pass

        if current_stock_context:
            context_parts.append(f"[Active Page Context]: {current_stock_context}")

        return "\n\n".join(context_parts) if context_parts else "No specific symbols detected. General market context loaded."
