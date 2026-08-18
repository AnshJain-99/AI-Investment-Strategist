import os
from datetime import datetime
import yfinance as yf
import plotly.graph_objects as go
from plotly.offline import plot
import pandas as pd

from services.cache_service import CacheService
from services.technical_service import TechnicalService
from services.fundamental_service import FundamentalService
from services.target_service import TargetService
from services.scoring_service import ScoringEngine
from services.news_service import NewsService


YFINANCE_CACHE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "instance",
    "yfinance_cache",
)
os.makedirs(YFINANCE_CACHE_DIR, exist_ok=True)

try:
    yf.set_tz_cache_location(YFINANCE_CACHE_DIR)
except AttributeError:
    pass


class StockService:

    # ==================================================
    # MARKET DATA
    # ==================================================

    @staticmethod
    def get_market_data():
        cached = CacheService.get("market_data_indices")
        if cached:
            return cached

        try:
            nifty = yf.Ticker("^NSEI")
            sensex = yf.Ticker("^BSESN")

            nifty_price = nifty.fast_info.get("lastPrice") or 0
            sensex_price = sensex.fast_info.get("lastPrice") or 0

            res = {
                "nifty": f"{nifty_price:,.2f}" if nifty_price else "--",
                "sensex": f"{sensex_price:,.2f}" if sensex_price else "--",
                "status": "Live",
            }
            if nifty_price and sensex_price:
                CacheService.set("market_data_indices", res, ttl_seconds=30)
            return res

        except Exception as e:
            print("Market Data Error:", e)
            return {"nifty": "--", "sensex": "--", "status": "Offline"}

    # ==================================================
    # STOCK DETAILS
    # ==================================================

    @staticmethod
    def get_stock_details(symbol):
        if not symbol:
            return None

        clean_symbol = symbol.strip().upper()
        if "." not in clean_symbol and not clean_symbol.startswith("^"):
            clean_symbol = f"{clean_symbol}.NS"

        cached = CacheService.get(f"stock_details_{clean_symbol}")
        if cached:
            return cached

        try:
            ticker = yf.Ticker(clean_symbol)

            try:
                info = ticker.info or {}
            except Exception:
                info = {}

            try:
                fast_info = ticker.fast_info or {}
            except Exception:
                fast_info = {}

            history = ticker.history(period="5d")

            # Day High & Low
            day_high = format_number(info.get("dayHigh") or fast_info.get("dayHigh"))
            day_low = format_number(info.get("dayLow") or fast_info.get("dayLow"))

            # Volume formatting
            volume = format_volume(info.get("volume") or fast_info.get("lastVolume"))

            # Current price resolution
            price_value = (
                info.get("currentPrice")
                or info.get("regularMarketPrice")
                or fast_info.get("lastPrice")
            )

            if not price_value and not history.empty:
                close_prices = history["Close"].dropna()
                if not close_prices.empty:
                    price_value = float(close_prices.iloc[-1])

            price = f"{float(price_value):,.2f}" if price_value is not None else "N/A"

            price_change = "0.00%"
            price_change_value = 0.0
            price_change_color = "gray"

            try:
                if len(history) >= 2:
                    latest = float(history["Close"].iloc[-1])
                    previous = float(history["Close"].iloc[-2])
                    change = latest - previous
                    percent = (change / previous) * 100
                    price_change = f"{percent:+.2f}%"
                    price_change_value = round(percent, 2)
                    price_change_color = "green" if percent > 0 else "red" if percent < 0 else "gray"
            except Exception:
                pass

            roe = info.get("returnOnEquity")
            roe_str = f"{roe * 100:.2f}%" if roe is not None else "N/A"

            dividend = info.get("dividendYield")
            dividend_str = f"{dividend * 100:.2f}%" if dividend is not None else "N/A"

            res = {
                "symbol": clean_symbol,
                "display_symbol": clean_symbol.replace(".NS", "").replace(".BO", ""),
                "name": info.get("longName") or info.get("shortName") or clean_symbol,
                "price": price,
                "raw_price": float(price_value) if price_value is not None else None,
                "price_change": price_change,
                "price_change_value": price_change_value,
                "price_change_color": price_change_color,
                "day_high": day_high,
                "day_low": day_low,
                "volume": volume,
                "market_cap": format_market_cap(info.get("marketCap") or fast_info.get("marketCap")),
                "pe": format_number(info.get("trailingPE")),
                "eps": format_number(info.get("trailingEps")),
                "sector": info.get("sector", "Others"),
                "industry": info.get("industry", "N / A"),
                "revenue": format_market_cap(info.get("totalRevenue")),
                "roe": roe_str,
                "dividend": dividend_str,
                "employees": format_integer(info.get("fullTimeEmployees")),
                "high52": format_number(info.get("fiftyTwoWeekHigh") or fast_info.get("yearHigh")),
                "low52": format_number(info.get("fiftyTwoWeekLow") or fast_info.get("yearLow")),
                "website": info.get("website", "N / A"),
                "raw_info": info
            }

            if price_value is not None:
                CacheService.set(f"stock_details_{clean_symbol}", res, ttl_seconds=60)

            return res

        except Exception as e:
            print("Stock Details Error:", e)
            return None

    # ==================================================
    # STOCK PRICE CHART
    # ==================================================

    @staticmethod
    def get_stock_chart(symbol):
        if not symbol:
            return None

        clean_symbol = symbol.strip().upper()
        if "." not in clean_symbol and not clean_symbol.startswith("^"):
            clean_symbol = f"{clean_symbol}.NS"

        try:
            stock_data = yf.download(
                clean_symbol, period="6mo", interval="1d", progress=False, auto_adjust=False
            )

            if stock_data.empty:
                return None

            close_price = stock_data["Close"].dropna()
            if hasattr(close_price, "columns"):
                close_price = close_price.iloc[:, 0]

            figure = go.Figure()
            figure.add_trace(
                go.Scatter(
                    x=close_price.index,
                    y=close_price.values,
                    mode="lines",
                    name=clean_symbol.replace(".NS", ""),
                    line=dict(color="#7C3AED", width=3),
                    fill="none",
                    hovertemplate="<b>%{x|%d %b %Y}</b><br>Price: ₹%{y:,.2f}<extra></extra>",
                )
            )

            figure.update_layout(
                height=390,
                margin=dict(l=20, r=20, t=20, b=20),
                paper_bgcolor="white",
                plot_bgcolor="white",
                showlegend=False,
                hovermode="x unified",
                template="plotly_white",
                xaxis=dict(
                    title="",
                    showgrid=False,
                    tickformat="%d %b",
                    tickfont=dict(color="#64748B", size=11),
                ),
                yaxis=dict(
                    title="",
                    showgrid=True,
                    gridcolor="rgba(226, 232, 240, 0.80)",
                    rangemode="normal",
                    tickprefix="₹",
                    separatethousands=True,
                    tickfont=dict(color="#64748B", size=11),
                ),
            )

            return plot(
                figure,
                output_type="div",
                include_plotlyjs="cdn",
                config={
                    "responsive": True,
                    "displaylogo": False,
                    "displayModeBar": False,
                },
            )

        except Exception as error:
            print("Stock Chart Error:", error)
            return None

    # ==================================================
    # DASHBOARD MARKET CHART
    # ==================================================

    @staticmethod
    def get_market_chart(period="6mo"):
        try:
            allowed_periods = {"1mo": "1mo", "3mo": "3mo", "6mo": "6mo"}
            chart_period = allowed_periods.get(period, "6mo")

            market_data = yf.download(
                ["^NSEI", "^BSESN"],
                period=chart_period,
                interval="1d",
                progress=False,
                auto_adjust=False,
                group_by="ticker",
                threads=False,
            )

            if market_data.empty:
                return None

            def close_prices(sym):
                try:
                    data = market_data[sym]
                    close = data["Close"]
                    if hasattr(close, "columns"):
                        close = close.iloc[:, 0]
                    return close.dropna()
                except Exception:
                    return None

            nifty_close = close_prices("^NSEI")
            sensex_close = close_prices("^BSESN")

            if nifty_close is None or nifty_close.empty or sensex_close is None or sensex_close.empty:
                return None

            figure = go.Figure()
            figure.add_trace(
                go.Scatter(
                    x=nifty_close.index,
                    y=nifty_close.values,
                    mode="lines",
                    name="NIFTY 50",
                    visible=True,
                    line=dict(color="#7C3AED", width=3),
                    hovertemplate="<b>NIFTY 50</b><br>%{x|%d %b %Y}<br>%{y:,.2f}<extra></extra>",
                )
            )

            figure.add_trace(
                go.Scatter(
                    x=sensex_close.index,
                    y=sensex_close.values,
                    mode="lines",
                    name="SENSEX",
                    visible=False,
                    line=dict(color="#7C3AED", width=3),
                    hovertemplate="<b>SENSEX</b><br>%{x|%d %b %Y}<br>%{y:,.2f}<extra></extra>",
                )
            )

            figure.update_layout(
                height=360,
                margin=dict(l=20, r=20, t=20, b=15),
                paper_bgcolor="white",
                plot_bgcolor="white",
                showlegend=False,
                hovermode="x unified",
                template="plotly_white",
                xaxis=dict(showgrid=False, tickformat="%d %b", tickfont=dict(color="#8B8F9C", size=11)),
                yaxis=dict(showgrid=True, gridcolor="rgba(226, 232, 240, 0.75)", separatethousands=True, tickformat=",.0f", tickfont=dict(color="#8B8F9C", size=11)),
                updatemenus=[
                    dict(
                        type="buttons",
                        direction="right",
                        x=1,
                        xanchor="right",
                        y=1.16,
                        yanchor="top",
                        showactive=True,
                        bgcolor="#F5F3FF",
                        bordercolor="#DDD6FE",
                        font=dict(color="#6D28D9", size=11),
                        buttons=[
                            dict(label="NIFTY 50", method="update", args=[{"visible": [True, False]}]),
                            dict(label="SENSEX", method="update", args=[{"visible": [False, True]}]),
                        ],
                    )
                ],
            )

            return plot(
                figure,
                output_type="div",
                include_plotlyjs=False,
                config={"responsive": True, "displaylogo": False, "displayModeBar": False},
            )

        except Exception as error:
            print("Market Chart Error:", error)
            return None

    # ==================================================
    # LATEST COMPANY NEWS
    # ==================================================

    @staticmethod
    def get_stock_news(symbol):
        return NewsService.get_stock_news(symbol)

    # ==================================================
    # MULTI-FACTOR AI ANALYSIS ENGINE
    # ==================================================

    @staticmethod
    def get_ai_analysis(symbol):
        if not symbol:
            return fallback_analysis()

        clean_symbol = symbol.strip().upper()
        if "." not in clean_symbol and not clean_symbol.startswith("^"):
            clean_symbol = f"{clean_symbol}.NS"

        cached = CacheService.get(f"ai_analysis_{clean_symbol}")
        if cached:
            return cached

        try:
            ticker = yf.Ticker(clean_symbol)
            try:
                info = ticker.info or {}
            except Exception:
                info = {}

            history = ticker.history(period="6mo")

            # 1. Fundamentals Analysis
            fundamentals_data = FundamentalService.extract_fundamentals(info)

            # 2. Technicals Analysis
            technicals_data = TechnicalService.calculate_indicators(history)

            # 3. News & Sentiment
            news_items = NewsService.get_stock_news(clean_symbol)
            sentiment_score = NewsService.get_sentiment_score(news_items)

            # 4. Multi-Factor Composite Evaluation
            evaluation = ScoringEngine.evaluate_stock(
                fundamentals_data=fundamentals_data,
                technicals_data=technicals_data,
                news_sentiment_score=sentiment_score
            )

            # 5. ATR / Support-Resistance Targets
            current_price = technicals_data.get("latest_price", 0) if technicals_data.get("available") else None
            if not current_price:
                current_price = info.get("currentPrice") or info.get("regularMarketPrice")

            target_data = TargetService.calculate_targets(current_price, technicals_data)

            target_val = target_data.get("target_price") if target_data.get("available") else "N/A"
            stop_val = target_data.get("stop_loss") if target_data.get("available") else "N/A"
            time_horizon = target_data.get("time_horizon", "6-12 Months")

            res = {
                "overall": evaluation["overall_score"],
                "fundamental": evaluation["factor_scores"]["fundamentals"],
                "technical": evaluation["factor_scores"]["technicals"],
                "valuation": evaluation["factor_scores"]["valuation"],
                "momentum": evaluation["factor_scores"]["momentum"],
                "sentiment": evaluation["factor_scores"]["sentiment"],
                "risk_score": evaluation["factor_scores"]["risk"],
                "signal": evaluation["signal"].upper() if evaluation["signal"] in ["Buy", "Hold", "Sell", "Strong Buy"] else evaluation["signal"],
                "raw_signal": evaluation["signal"],
                "confidence": evaluation["confidence"],
                "risk": evaluation["risk_label"],
                "summary": evaluation["summary"],
                "strengths": evaluation["strengths"],
                "risks": evaluation["risks"],
                "target": target_val,
                "stop_loss": stop_val,
                "risk_reward": target_data.get("risk_reward_ratio", "N/A"),
                "time_horizon": time_horizon,
                "technicals_detail": technicals_data,
                "fundamentals_detail": fundamentals_data,
            }

            CacheService.set(f"ai_analysis_{clean_symbol}", res, ttl_seconds=300) # 5 min cache
            return res

        except Exception as e:
            print(f"AI Analysis Error for {symbol}:", e)
            return fallback_analysis()

    # ==================================================
    # WATCHLIST SUMMARY
    # ==================================================

    @staticmethod
    def get_watchlist_summary(symbols):
        if not symbols:
            return {
                "holdings": 0,
                "gainers": 0,
                "losers": 0,
                "avg_return": 0.0,
                "allocation": [],
                "stocks": [],
            }

        stocks = []
        gainers = 0
        losers = 0
        total_change = 0.0
        sector_count = {}

        for symbol in symbols:
            stock = StockService.get_stock_details(symbol)
            if not stock:
                continue

            stocks.append(stock)
            change = stock.get("price_change_value", 0.0)
            total_change += change

            if change > 0:
                gainers += 1
            elif change < 0:
                losers += 1

            sector = stock.get("sector") or "Others"
            if sector in ["N / A", "Not available", "N/A"]:
                sector = "Others"
            sector_count[sector] = sector_count.get(sector, 0) + 1

        avg_return = round(total_change / len(stocks), 2) if stocks else 0.0

        allocation = []
        for sector, count in sector_count.items():
            allocation.append({
                "sector": sector,
                "count": count,
                "percentage": round((count / len(stocks)) * 100, 1) if stocks else 0.0,
            })
        allocation.sort(key=lambda x: x["count"], reverse=True)

        return {
            "holdings": len(stocks),
            "gainers": gainers,
            "losers": losers,
            "avg_return": avg_return,
            "allocation": allocation,
            "stocks": stocks,
        }


# ==================================================
# HELPER FUNCTIONS
# ==================================================

def fallback_analysis():
    return {
        "overall": 50,
        "fundamental": 50,
        "technical": 50,
        "valuation": 50,
        "momentum": 50,
        "sentiment": 50,
        "risk_score": 50,
        "signal": "HOLD",
        "raw_signal": "Hold",
        "confidence": 50,
        "risk": "Moderate Risk",
        "summary": "Live AI analysis is limited because complete market data is unavailable right now. Keep this stock on watch and refresh after live data updates.",
        "strengths": ["Stock remains trackable with active listing"],
        "risks": ["Incomplete live feeds - awaiting confirmation"],
        "target": "N/A",
        "stop_loss": "N/A",
        "risk_reward": "N/A",
        "time_horizon": "Data pending",
    }


def format_market_cap(value):
    if value is None:
        return "N/A"
    try:
        val = float(value)
        if val >= 1_000_000_000_000:
            return f"₹{val / 1_000_000_000_000:.2f} T"
        if val >= 1_000_000_000:
            return f"₹{val / 1_000_000_000:.2f} B"
        if val >= 10_000_000:
            return f"₹{val / 10_000_000:.2f} Cr"
        if val >= 100_000:
            return f"₹{val / 100_000:.2f} L"
        return f"₹{val:,.0f}"
    except (ValueError, TypeError):
        return "N/A"


def format_number(value):
    if value is None:
        return "N/A"
    try:
        return f"{float(value):,.2f}"
    except Exception:
        return value


def format_integer(value):
    if value is None:
        return "N/A"
    try:
        return f"{int(value):,}"
    except Exception:
        return value


def format_volume(value):
    if value is None:
        return "N/A"
    try:
        val = int(value)
        if val >= 10_000_000:
            return f"{val / 10_000_000:.2f} Cr"
        elif val >= 100_000:
            return f"{val / 100_000:.2f} L"
        elif val >= 1_000:
            return f"{val / 1_000:.1f} K"
        return f"{val:,}"
    except (TypeError, ValueError):
        return "N/A"
