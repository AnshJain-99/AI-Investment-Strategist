import yfinance as yf
import plotly.graph_objects as go
from plotly.offline import plot
from datetime import datetime
import os


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

        try:

            nifty = yf.Ticker("^NSEI")
            sensex = yf.Ticker("^BSESN")

            nifty_price = nifty.fast_info.get("lastPrice") or 0

            sensex_price = sensex.fast_info.get("lastPrice") or 0

            return {
                "nifty": f"{nifty_price:,.2f}",
                "sensex": f"{sensex_price:,.2f}",
                "status": "Live",
            }

        except Exception as e:

            print("Market Data Error:", e)

            return {"nifty": "--", "sensex": "--", "status": "Offline"}

    # ==================================================
    # STOCK DETAILS
    # ==================================================

    @staticmethod
    def get_stock_details(symbol):

        try:

            # Convert Indian stock automatically
            # Example:
            # TCS -> TCS.NS

            if "." not in symbol:

                symbol = symbol.upper() + ".NS"

            ticker = yf.Ticker(symbol)

            try:
                info = ticker.info or {}
            except Exception:
                info = {}

            try:
                fast_info = ticker.fast_info or {}
            except Exception:
                fast_info = {}

            history = ticker.history(period="5d")

            # Day High
            day_high = format_number(info.get("dayHigh"))

            # Day Low
            day_low = format_number(info.get("dayLow"))

            # Volume
            def format_volume(value):
                try:
                    value = int(value)

                    if value >= 10000000:
                        return f"{value / 10000000:.2f} Cr"

                    elif value >= 100000:
                        return f"{value / 100000:.2f} L"

                    elif value >= 1000:
                        return f"{value / 1000:.1f} K"

                    return f"{value:,}"

                except (TypeError, ValueError):
                    return "N/A"

            volume = format_volume(info.get("volume") or fast_info.get("lastVolume"))

            # # Market State
            # market_state = (
            #     info.get("marketState")
            #     or "REGULAR"
            # )

            # -------------------------------
            # CURRENT STOCK PRICE
            # -------------------------------

            price_value = (
                info.get("currentPrice")
                or info.get("regularMarketPrice")
                or fast_info.get("lastPrice")
            )

            if not price_value and not history.empty:
                close_prices = history["Close"].dropna()

                if not close_prices.empty:
                    price_value = float(close_prices.iloc[-1])

            if price_value is not None:

                price = f"{float(price_value):,.2f}"

            else:

                price = "N/A"

            price_change = "0.00%"
            price_change_value = 0
            price_change_color = "gray"

            try:
                if len(history) >= 2:
                    latest = float(history["Close"].iloc[-1])
                    previous = float(history["Close"].iloc[-2])

                    change = latest - previous
                    percent = (change / previous) * 100

                    price_change = f"{percent:+.2f}%"
                    price_change_value = round(percent, 2)

                    if percent > 0:
                        price_change_color = "green"
                    elif percent < 0:
                        price_change_color = "red"

            except Exception:
                pass

            # -------------------------------
            # RETURN ON EQUITY
            # -------------------------------

            roe = info.get("returnOnEquity")

            if roe is not None:

                roe = f"{roe * 100:.2f}%"

            else:

                roe = "N/A"

            # -------------------------------
            # DIVIDEND YIELD
            # -------------------------------

            dividend = info.get("dividendYield")

            if dividend is not None:

                dividend = f"{dividend * 100:.2f}%"

            else:

                dividend = "N/A"

            # -------------------------------
            # RETURN STOCK INFORMATION
            # -------------------------------

            return {
                "symbol": symbol,
                "name": info.get("longName") or info.get("shortName") or symbol,
                "price": price,
                "price_change": price_change,
                "price_change_value": price_change_value,
                "price_change_color": price_change_color,
                "day_high": day_high if day_high != "N/A" else format_number(fast_info.get("dayHigh")),
                "day_low": day_low if day_low != "N/A" else format_number(fast_info.get("dayLow")),
                "volume": volume,
                # "market_state": market_state,
                "market_cap": format_market_cap(info.get("marketCap") or fast_info.get("marketCap")),
                "pe": format_number(info.get("trailingPE")),
                "eps": format_number(info.get("trailingEps")),
                "sector": info.get("sector", "N / A"),
                "industry": info.get("industry", "N / A"),
                "revenue": format_market_cap(info.get("totalRevenue")),
                "roe": roe,
                "dividend": dividend,
                "employees": format_integer(info.get("fullTimeEmployees")),
                "high52": format_number(info.get("fiftyTwoWeekHigh") or fast_info.get("yearHigh")),
                "low52": format_number(info.get("fiftyTwoWeekLow") or fast_info.get("yearLow")),
                "website": info.get("website", "N / A"),
            }

        except Exception as e:
            print("Stock Details Error:", e)
            return None

    # ==================================================
    # STOCK PRICE CHART
    # ==================================================
    @staticmethod
    def get_stock_chart(symbol):

        try:

            # Convert Indian stock symbol automatically
            # Example: TCS -> TCS.NS

            if "." not in symbol:

                symbol = symbol.upper() + ".NS"

            else:

                symbol = symbol.upper()

            # Download last 6 months stock data

            stock_data = yf.download(
                symbol, period="6mo", interval="1d", progress=False, auto_adjust=False
            )

            # Return None if data is unavailable

            if stock_data.empty:

                return None

            # Get closing prices

            close_price = stock_data["Close"].dropna()

            # Fix yfinance DataFrame format

            if hasattr(close_price, "columns"):

                close_price = close_price.iloc[:, 0]

            # Create Plotly chart

            figure = go.Figure()

            figure.add_trace(
                go.Scatter(
                    x=close_price.index,
                    y=close_price.values,
                    mode="lines",
                    name=symbol.replace(".NS", ""),
                    line=dict(color="#7C3AED", width=3),
                    fill="tozeroy",
                    fillcolor="rgba(124, 58, 237, 0.10)",
                    hovertemplate=(
                        "<b>%{x|%d %b %Y}</b>"
                        "<br>"
                        "Price: ₹%{y:,.2f}"
                        "<extra></extra>"
                    ),
                )
            )

            # Chart design

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
                    tickprefix="₹",
                    separatethousands=True,
                    tickfont=dict(color="#64748B", size=11),
                ),
            )

            # Return chart HTML

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

            allowed_periods = {
                "1mo": "1mo",
                "3mo": "3mo",
                "6mo": "6mo",
            }

            chart_period = allowed_periods.get(period, "6mo")

            # Download historical data for selected period
            # for NIFTY 50 and SENSEX

            market_data = yf.download(
                ["^NSEI", "^BSESN"],
                period=chart_period,
                interval="1d",
                progress=False,
                auto_adjust=False,
                group_by="ticker",
            )

            # Check downloaded data

            if market_data.empty:

                return None

            # Get closing prices

            nifty_close = market_data["^NSEI"]["Close"].dropna()

            sensex_close = market_data["^BSESN"]["Close"].dropna()

            # Create Plotly figure

            figure = go.Figure()

            # ------------------------------------------
            # NIFTY 50 LINE
            # ------------------------------------------

            figure.add_trace(
                go.Scatter(
                    x=nifty_close.index,
                    y=nifty_close.values,
                    mode="lines",
                    name="NIFTY 50",
                    visible=True,
                    line=dict(color="#7C3AED", width=3),
                    fill="tozeroy",
                    fillcolor=("rgba(" "124," "58," "237," "0.08" ")"),
                    hovertemplate=(
                        "<b>NIFTY 50</b>"
                        "<br>"
                        "%{x|%d %b %Y}"
                        "<br>"
                        "%{y:,.2f}"
                        "<extra></extra>"
                    ),
                )
            )

            # ------------------------------------------
            # SENSEX LINE
            # ------------------------------------------

            figure.add_trace(
                go.Scatter(
                    x=sensex_close.index,
                    y=sensex_close.values,
                    mode="lines",
                    name="SENSEX",
                    visible=False,
                    line=dict(color="#7C3AED", width=3),
                    fill="tozeroy",
                    fillcolor=("rgba(" "124," "58," "237," "0.08" ")"),
                    hovertemplate=(
                        "<b>SENSEX</b>"
                        "<br>"
                        "%{x|%d %b %Y}"
                        "<br>"
                        "%{y:,.2f}"
                        "<extra></extra>"
                    ),
                )
            )

            # ------------------------------------------
            # CHART DESIGN
            # ------------------------------------------

            figure.update_layout(
                height=360,
                margin=dict(l=20, r=20, t=20, b=15),
                paper_bgcolor="white",
                plot_bgcolor="white",
                showlegend=False,
                hovermode="x unified",
                template="plotly_white",
                xaxis=dict(
                    title="",
                    showgrid=False,
                    tickformat="%d %b",
                    tickfont=dict(color="#8B8F9C", size=11),
                ),
                yaxis=dict(
                    title="",
                    showgrid=True,
                    gridcolor=("rgba(" "226," "232," "240," "0.75" ")"),
                    separatethousands=True,
                    tickfont=dict(color="#8B8F9C", size=11),
                ),
                # NIFTY / SENSEX buttons
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
                            dict(
                                label="NIFTY 50",
                                method="update",
                                args=[{"visible": [True, False]}, {"yaxis.title": ""}],
                            ),
                            dict(
                                label="SENSEX",
                                method="update",
                                args=[{"visible": [False, True]}, {"yaxis.title": ""}],
                            ),
                        ],
                    )
                ],
            )

            # Return chart HTML

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

            print("Market Chart Error:", error)

            return None

    # ==================================================
    # LATEST COMPANY NEWS
    # ==================================================

    @staticmethod
    def get_stock_news(symbol):

        try:

            # Convert Indian stock automatically

            if "." not in symbol:

                symbol = symbol.upper() + ".NS"

            ticker = yf.Ticker(symbol)

            raw_news = ticker.news or []

            latest_news = []

            # Only show latest 5 news

            for item in raw_news[:5]:

                # New yfinance versions
                # keep news inside content

                content = item.get("content", item)

                title = content.get("title", "Market News")

                summary = content.get("summary", "")

                # ---------------------------
                # NEWS LINK
                # ---------------------------

                news_url = "#"

                canonical_url = content.get("canonicalUrl") or {}

                click_url = content.get("clickThroughUrl") or {}

                if isinstance(canonical_url, dict):

                    news_url = canonical_url.get("url") or news_url

                if news_url == "#" and isinstance(click_url, dict):

                    news_url = click_url.get("url") or news_url

                # Older yfinance structure

                if news_url == "#":

                    news_url = item.get("link") or "#"

                # ---------------------------
                # NEWS PUBLISHER
                # ---------------------------

                publisher = content.get("provider", {}) or {}

                if isinstance(publisher, dict):

                    publisher = publisher.get("displayName") or "Yahoo Finance"

                else:

                    publisher = item.get("publisher") or "Yahoo Finance"

                # ---------------------------
                # NEWS DATE
                # ---------------------------

                published_date = "Latest"

                publish_time = item.get("providerPublishTime")

                if publish_time:

                    published_date = datetime.fromtimestamp(publish_time).strftime(
                        "%d %b %Y"
                    )

                latest_news.append(
                    {
                        "title": title,
                        "summary": summary,
                        "publisher": publisher,
                        "date": published_date,
                        "url": news_url,
                    }
                )

            return latest_news

        except Exception as e:

            print("News Error:", e)

            return []

    @staticmethod
    def get_ai_analysis(symbol):

        def fallback_analysis():
            return {
                "overall": 50,
                "fundamental": 50,
                "technical": 50,
                "signal": "HOLD",
                "confidence": 50,
                "summary": "Live AI analysis is limited because complete market data is unavailable right now. Keep this stock on watch and refresh after live data updates.",
                "strengths": ["Stock remains trackable", "Live price feed can be refreshed"],
                "risks": ["Incomplete live data", "Wait for stronger confirmation"],
                "target": "N/A",
                "stop_loss": "N/A",
                "time_horizon": "Data pending",
            }

        try:

            if "." not in symbol:
                symbol = symbol.upper() + ".NS"

            ticker = yf.Ticker(symbol)

            try:
                info = ticker.info or {}
            except Exception:
                info = {}

            history = ticker.history(period="6mo")

            if history.empty:
                return fallback_analysis()

            close = history["Close"].dropna()

            if close.empty:
                return fallback_analysis()

            latest = float(close.iloc[-1])

            sma20 = float(close.tail(20).mean())

            sma50 = float(close.tail(50).mean())

            # -----------------------------
            # Technical Score
            # -----------------------------

            technical = 50

            if latest > sma20:
                technical += 15

            if latest > sma50:
                technical += 15

            change = ((latest - float(close.iloc[0])) / float(close.iloc[0])) * 100

            if change > 15:
                technical += 20

            elif change > 5:
                technical += 10

            technical = min(100, technical)

            # -----------------------------
            # Fundamental Score
            # -----------------------------

            fundamental = 50

            pe = info.get("trailingPE")

            roe = info.get("returnOnEquity")

            market_cap = info.get("marketCap")

            if pe and pe < 30:
                fundamental += 15

            if roe and roe > 0.15:
                fundamental += 20

            if market_cap and market_cap > 100000000000:
                fundamental += 15

            fundamental = min(100, fundamental)

            # -----------------------------
            # Overall
            # -----------------------------

            overall = round((fundamental * 0.6) + (technical * 0.4))

            # -----------------------------
            # Recommendation
            # -----------------------------

            if overall >= 80:

                signal = "BUY"

            elif overall >= 60:

                signal = "HOLD"

            else:

                signal = "SELL"

            confidence = min(95, overall + 5)
            if signal == "BUY":

                summary = "AI sees supportive fundamentals and positive price momentum. This stock may suit a monitored medium-term entry."

                strengths = [
                    "Healthy revenue growth",
                    "Positive technical trend",
                    "Strong market position",
                ]

                risks = ["Short-term market volatility", "Sector correction risk"]

            elif signal == "HOLD":

                summary = "AI sees a balanced setup. Momentum is not strong enough for an aggressive call, so monitor confirmation levels."

                strengths = [
                    "Stable business",
                    "Balanced financials",
                    "Long-term potential",
                ]

                risks = ["Limited short-term upside", "Market uncertainty"]

            else:

                summary = "AI sees weak momentum or below-average financial strength. Risk control is important before taking a position."

                strengths = ["Large market presence"]

                risks = [
                    "Weak price trend",
                    "Poor technical indicators",
                    "High downside risk",
                ]

            return {
                "overall": overall,
                "fundamental": fundamental,
                "technical": technical,
                "signal": signal,
                "confidence": confidence,
                "summary": summary,
                "strengths": strengths,
                "risks": risks,
                "target": round(latest * 1.10, 2),
                "stop_loss": round(latest * 0.92, 2),
                "time_horizon": "6-12 Months",
            }

        except Exception as e:

            print("AI Error:", e)

            return fallback_analysis()

    @staticmethod
    def get_watchlist_summary(symbols):

        holdings = len(symbols)
        gainers = 0
        losers = 0
        total_change = 0

        sector_count = {}
        stocks = []

        for symbol in symbols:

            stock = StockService.get_stock_details(symbol)

            if not stock:
                continue

            stocks.append(stock)

            change = stock.get("price_change_value", 0)
            total_change += change

            if change > 0:
                gainers += 1
            elif change < 0:
                losers += 1

            sector = stock.get("sector") or "Others"

            if sector == "N / A":
                sector = "Others"

            sector_count[sector] = sector_count.get(sector, 0) + 1

        avg_return = round(total_change / len(stocks), 2) if stocks else 0

        allocation = []

        for sector, count in sector_count.items():

            allocation.append(
                {
                    "sector": sector,
                    "count": count,
                    "percentage": (
                        round((count / len(stocks)) * 100, 1) if stocks else 0
                    ),
                }
            )

        allocation.sort(key=lambda x: x["count"], reverse=True)

        return {
            "holdings": holdings,
            "gainers": gainers,
            "losers": losers,
            "avg_return": avg_return,
            "allocation": allocation,
            "stocks": stocks,
        }


# ==================================================
# HELPER FUNCTIONS
# ==================================================


def format_market_cap(value):

    if value is None:

        return "N/A"

    if value >= 1_000_000_000_000:

        return f"₹" f"{value / 1_000_000_000_000:.2f}" f" T"

    if value >= 1_000_000_000:

        return f"₹" f"{value / 1_000_000_000:.2f}" f" B"

    if value >= 10_000_000:

        return f"₹" f"{value / 10_000_000:.2f}" f" Cr"

    return f"₹{value:,.0f}"


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


def generate_ai_summary(ai, stock):
    summary = []

    if ai["signal"] == "BUY":
        summary.append(
            f"{stock['name']} shows strong investment potential based on current market data."
        )

    elif ai["signal"] == "HOLD":
        summary.append(f"{stock['name']} is currently showing neutral signals.")

    else:
        summary.append(f"{stock['name']} is showing weak momentum.")

    if ai["fundamental"] >= 80:
        summary.append("Fundamental indicators are healthy.")

    elif ai["fundamental"] >= 60:
        summary.append("Fundamentals are average.")

    else:
        summary.append("Fundamentals need improvement.")

    if ai["technical"] >= 80:
        summary.append("Technical momentum is positive.")

    elif ai["technical"] >= 60:
        summary.append("Technical trend is neutral.")

    else:
        summary.append("Technical trend remains weak.")

    strengths = []

    if stock["pe"] != "N/A" and float(stock["pe"]) < 25:
        strengths.append("Attractive valuation")

    if ai["technical"] >= 75:
        strengths.append("Positive momentum")

    if ai["fundamental"] >= 80:
        strengths.append("Strong fundamentals")

    risks = []

    if stock["roe"] == "N/A":
        risks.append("ROE data unavailable")

    elif float(stock["roe"].replace("%", "")) < 10:
        risks.append("Low return on equity")

    if ai["technical"] < 60:
        risks.append("Weak momentum")

    if ai["overall"] >= 85:
        risk = "Low"

    elif ai["overall"] >= 70:
        risk = "Medium"

    else:
        risk = "High"

    return {
        "summary": " ".join(summary),
        "strengths": strengths,
        "risks": risks,
        "risk": risk,
    }
