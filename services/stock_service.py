import yfinance as yf
import plotly.graph_objects as go
from plotly.offline import plot
from datetime import datetime


class StockService:

    # ==================================================
    # MARKET DATA
    # ==================================================

    @staticmethod
    def get_market_data():

        try:

            nifty = yf.Ticker("^NSEI")
            sensex = yf.Ticker("^BSESN")

            nifty_price = nifty.fast_info.get(
                "lastPrice",
                0
            )

            sensex_price = sensex.fast_info.get(
                "lastPrice",
                0
            )

            return {

                "nifty": f"{nifty_price:,.2f}",

                "sensex": f"{sensex_price:,.2f}",

                "status": "Live"
            }

        except Exception as e:

            print(
                "Market Data Error:",
                e
            )

            return {

                "nifty": "--",

                "sensex": "--",

                "status": "Offline"
            }

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

                symbol = (
                    symbol.upper()
                    +".NS"
                )

            ticker = yf.Ticker(symbol)

            info = ticker.info


            # Day High
            day_high = format_number(
                info.get("dayHigh")
            )
            
            # Day Low
            day_low = format_number(
                info.get("dayLow")
            )
            
            # Volume
            def format_volume(value):
                try:
                    value = int(value)
            
                    if value >= 10000000:
                        return f"{value/10000000:.2f} Cr"
            
                    elif value >= 100000:
                        return f"{value/100000:.2f} L"
            
                    elif value >= 1000:
                        return f"{value/1000:.1f} K"
            
                    return f"{value:,}"
                
                except (TypeError, ValueError):
                    return "N/A"
            
            volume = format_volume(info.get("volume"))
            
            # # Market State
            # market_state = (
            #     info.get("marketState")
            #     or "REGULAR"
            # )
            
            # -------------------------------
            # CURRENT STOCK PRICE
            # -------------------------------

            price = (

                info.get(
                    "currentPrice"
                )

                or

                info.get(
                    "regularMarketPrice"
                )
            )

            if price is not None:

                price = (
                    f"{price:,.2f}"
                )

            else:

                price = "N/A"

            history = ticker.history(period="5d")
            
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

            dividend = info.get(
                "dividendYield"
            )

            if dividend is not None:

                dividend = (
                    f"{dividend * 100:.2f}%"
                )

            else:

                dividend = "N/A"

            # -------------------------------
            # RETURN STOCK INFORMATION
            # -------------------------------

            return {

                "symbol": symbol,
                "name": info.get("longName", symbol),
                "price": price,
                "price_change": price_change,
                "price_change_value": price_change_value,
                "price_change_color": price_change_color,
                "day_high": day_high,
                "day_low": day_low,
                "volume": volume,
                # "market_state": market_state,

                "market_cap":
                    format_market_cap(

                        info.get(
                            "marketCap"
                        )
                    ),

                "pe":
                    format_number(

                        info.get(
                            "trailingPE"
                        )
                    ),

                "eps":
                    format_number(

                        info.get(
                            "trailingEps"
                        )
                    ),

                "sector":
                    info.get(
                        "sector",
                        "N / A"
                    ),

                "industry":
                    info.get(
                        "industry",
                        "N / A"
                    ),

                "revenue":
                    format_market_cap(

                        info.get(
                            "totalRevenue"
                        )
                    ),

                "roe":
                    roe,

                "dividend":
                    dividend,

                "employees":
                    format_integer(

                        info.get(
                            "fullTimeEmployees"
                        )
                    ),

                "high52":
                    format_number(

                        info.get(
                            "fiftyTwoWeekHigh"
                        )
                    ),

                "low52":
                    format_number(

                        info.get(
                            "fiftyTwoWeekLow"
                        )
                    ),

                "website":
                    info.get(
                        "website",
                        "N / A"
                    )
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

                symbol,

                period="6mo",

                interval="1d",

                progress=False,

                auto_adjust=False

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

                    line=dict(

                        color="  # 7C3AED",

                        width=3

                    ),

                    fill="tozeroy",

                    fillcolor="rgba(124, 58, 237, 0.10)",

                    hovertemplate=(

                        "<b>%{x|%d %b %Y}</b>"

                        "<br>"

                        "Price: ₹%{y:,.2f}"

                        "<extra></extra>"

                    )

                )

            )

            # Chart design

            figure.update_layout(

                height=390,

                margin=dict(

                    l=20,

                    r=20,

                    t=20,

                    b=20

                ),

                paper_bgcolor="white",

                plot_bgcolor="white",

                showlegend=False,

                hovermode="x unified",

                template="plotly_white",

                xaxis=dict(

                    title="",

                    showgrid=False,

                    tickformat="%d %b",

                    tickfont=dict(

                        color="#64748B",

                        size=11

                    )

                ),

                yaxis=dict(

                    title="",

                    showgrid=True,

                    gridcolor="rgba(226, 232, 240, 0.80)",

                    tickprefix="₹",

                    separatethousands=True,

                    tickfont=dict(

                        color="#64748B",

                        size=11

                    )

                )

            )

            # Return chart HTML

            return plot(

                figure,

                output_type="div",

                include_plotlyjs="cdn",

                config={

                    "responsive": True,

                    "displaylogo": False,

                    "displayModeBar": False

                }

            )

        except Exception as error:

            print(

                "Stock Chart Error:",

                error

            )

            return None
    # ==================================================
    # DASHBOARD MARKET CHART
    # ==================================================

    @staticmethod
    def get_market_chart():

        try:

            # Download 6-month historical data
            # for NIFTY 50 and SENSEX

            market_data = yf.download(

                [
                    "^NSEI",
                    "^BSESN"
                ],

                period="6mo",

                interval="1d",

                progress=False,

                auto_adjust=False,

                group_by="ticker"
            )

            # Check downloaded data

            if market_data.empty:

                return None

            # Get closing prices

            nifty_close = (

                market_data[
                    "^NSEI"
                ][
                    "Close"
                ]

                .dropna()
            )

            sensex_close = (

                market_data[
                    "^BSESN"
                ][
                    "Close"
                ]

                .dropna()
            )

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

                    line=dict(color="#7C3AED",width=3),


                    fill="tozeroy",

                    fillcolor=(

                        "rgba("
                        "124,"
                        "58,"
                        "237,"
                        "0.08"
                        ")"

                    ),

                    hovertemplate=(

                        "<b>NIFTY 50</b>"

                        "<br>"

                        "%{x|%d %b %Y}"

                        "<br>"

                        "%{y:,.2f}"

                        "<extra></extra>"

                    )

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

                    line=dict(

                        color="#7C3AED",

                        width=3

                    ),

                    fill="tozeroy",

                    fillcolor=(

                        "rgba("
                        "124,"
                        "58,"
                        "237,"
                        "0.08"
                        ")"

                    ),

                    hovertemplate=(

                        "<b>SENSEX</b>"

                        "<br>"

                        "%{x|%d %b %Y}"

                        "<br>"

                        "%{y:,.2f}"

                        "<extra></extra>"

                    )

                )

            )

            # ------------------------------------------
            # CHART DESIGN
            # ------------------------------------------

            figure.update_layout(

                height=360,

                margin=dict(

                    l=20,

                    r=20,

                    t=20,

                    b=15

                ),

                paper_bgcolor="white",

                plot_bgcolor="white",

                showlegend=False,

                hovermode="x unified",

                template="plotly_white",

                xaxis=dict(

                    title="",

                    showgrid=False,

                    tickformat="%d %b",

                    tickfont=dict(

                        color="#8B8F9C",

                        size=11

                    )

                ),

                yaxis=dict(

                    title="",

                    showgrid=True,

                    gridcolor=(

                        "rgba("
                        "226,"
                        "232,"
                        "240,"
                        "0.75"
                        ")"

                    ),

                    separatethousands=True,

                    tickfont=dict(

                        color="#8B8F9C",

                        size=11

                    )

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

                        font=dict(

                            color="#6D28D9",

                            size=11

                        ),

                        buttons=[

                            dict(

                                label="NIFTY 50",

                                method="update",

                                args=[

                                    {

                                        "visible":

                                        [
                                            True,
                                            False
                                        ]

                                    },

                                    {

                                        "yaxis.title":

                                        ""

                                    }

                                ]

                            ),

                            dict(

                                label="SENSEX",

                                method="update",

                                args=[

                                    {

                                        "visible":

                                        [
                                            False,
                                            True
                                        ]

                                    },

                                    {

                                        "yaxis.title":

                                        ""

                                    }

                                ]

                            )

                        ]

                    )

                ]

            )

            # Return chart HTML

            return plot(

                figure,

                output_type="div",

                include_plotlyjs="cdn",

                config={

                    "responsive": True,

                    "displaylogo": False,

                    "displayModeBar": False

                }

            )

        except Exception as error:

            print(

                "Market Chart Error:",

                error

            )

            return None

    # ==================================================
    # LATEST COMPANY NEWS
    # ==================================================

    @staticmethod
    def get_stock_news(symbol):

        try:

            # Convert Indian stock automatically

            if "." not in symbol:

                symbol = (
                    symbol.upper()
                    +".NS"
                )

            ticker = yf.Ticker(symbol)

            raw_news = (
                ticker.news
                or []
            )

            latest_news = []

            # Only show latest 5 news

            for item in raw_news[:5]:

                # New yfinance versions
                # keep news inside content

                content = item.get(

                    "content",

                    item
                )

                title = content.get(

                    "title",

                    "Market News"
                )

                summary = content.get(

                    "summary",

                    ""
                )

                # ---------------------------
                # NEWS LINK
                # ---------------------------

                news_url = "#"

                canonical_url = (

                    content.get(
                        "canonicalUrl"
                    )

                    or {}
                )

                click_url = (

                    content.get(
                        "clickThroughUrl"
                    )

                    or {}
                )

                if isinstance(

                    canonical_url,

                    dict
                ):

                    news_url = (

                        canonical_url.get(
                            "url"
                        )

                        or news_url
                    )

                if (

                    news_url == "#"

                    and

                    isinstance(
                        click_url,
                        dict
                    )
                ):

                    news_url = (

                        click_url.get(
                            "url"
                        )

                        or news_url
                    )

                # Older yfinance structure

                if news_url == "#":

                    news_url = (

                        item.get(
                            "link"
                        )

                        or "#"
                    )

                # ---------------------------
                # NEWS PUBLISHER
                # ---------------------------

                publisher = (

                    content.get(
                        "provider",
                        {}
                    )

                    or {}
                )

                if isinstance(

                    publisher,

                    dict
                ):

                    publisher = (

                        publisher.get(
                            "displayName"
                        )

                        or "Yahoo Finance"
                    )

                else:

                    publisher = (

                        item.get(
                            "publisher"
                        )

                        or "Yahoo Finance"
                    )

                # ---------------------------
                # NEWS DATE
                # ---------------------------

                published_date = (
                    "Latest"
                )

                publish_time = (

                    item.get(
                        "providerPublishTime"
                    )
                )

                if publish_time:

                    published_date = (

                        datetime
                        .fromtimestamp(
                            publish_time
                        )
                        .strftime(
                            "%d %b %Y"
                        )
                    )

                latest_news.append({

                    "title":
                        title,

                    "summary":
                        summary,

                    "publisher":
                        publisher,

                    "date":
                        published_date,

                    "url":
                        news_url
                })

            return latest_news

        except Exception as e:

            print(
                "News Error:",
                e
            )

            return []

# ==================================================
# HELPER FUNCTIONS
# ==================================================


def format_market_cap(value):

    if value is None:

        return "N/A"

    if value >= 1_000_000_000_000:

        return (

            f"₹"
            f"{value / 1_000_000_000_000:.2f}"
            f" T"
        )

    if value >= 1_000_000_000:

        return (

            f"₹"
            f"{value / 1_000_000_000:.2f}"
            f" B"
        )

    if value >= 10_000_000:

        return (

            f"₹"
            f"{value / 10_000_000:.2f}"
            f" Cr"
        )

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
    
