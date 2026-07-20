from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import yfinance as yf
# from datetime import datetime
import feedparser


from flask_bcrypt import Bcrypt

from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)

from config import Config

from database.models import db, User

from services.stock_service import StockService

import requests

app = Flask(__name__)

app.config.from_object(Config)


# ==================================================
# DATABASE
# ==================================================

db.init_app(app)


# ==================================================
# PASSWORD ENCRYPTION
# ==================================================

bcrypt = Bcrypt(app)


# ==================================================
# LOGIN MANAGER
# ==================================================

login_manager = LoginManager(app)

login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):

    return db.session.get(User, int(user_id))


# ==================================================
# CREATE DATABASE TABLES
# ==================================================

with app.app_context():
    db.create_all()


# ==================================================
# LOGIN
# ==================================================


@app.route("/", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form["email"]

        password = request.form["password"]

        user = db.session.execute( db.select(User).filter_by(email=email)).scalar_one_or_none()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)

            return redirect(url_for("dashboard"))

        flash("Invalid Email or Password", "danger")

    return render_template("login.html")


# ==================================================
# REGISTER
# ==================================================


@app.route("/register", methods=["GET", "POST"])
def register():

    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        fullname = request.form["fullname"]

        email = request.form["email"]

        password = request.form["password"]

        confirm = request.form["confirm"]

        # ------------------------------
        # CHECK PASSWORDS
        # ------------------------------

        if password != confirm:
            flash("Passwords do not match", "danger")

            return redirect(url_for("register"))

        # ------------------------------
        # CHECK EXISTING EMAIL
        # ------------------------------

        existing = db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()

        if existing:
            flash("Email already exists", "danger")

            return redirect(url_for("register"))

        # ------------------------------
        # HASH PASSWORD
        # ------------------------------

        hashed = bcrypt.generate_password_hash(password).decode("utf-8")

        # ------------------------------
        # CREATE USER
        # ------------------------------

        new_user = User(full_name=fullname, email=email, password=hashed)

        db.session.add(new_user)

        db.session.commit()

        flash("Registration Successful", "success")

        return redirect(url_for("login"))

    return render_template("register.html")


# ==================================================
# DASHBOARD
# ==================================================


# ==================================================
# DASHBOARD
# ==================================================


@app.route("/dashboard")
@login_required
def dashboard():

    # Get current NIFTY and SENSEX values
    market = StockService.get_market_data()

    # Get interactive market chart
    market_chart = StockService.get_market_chart()


    # ==========================================
    # DYNAMIC AI MARKET RECOMMENDATION
    # ==========================================

    ai_signal = "HOLD"
    confidence = 50

    try:

        # Download recent NIFTY 50 market data
        nifty_history = yf.download(
            "^NSEI",
            period="3mo",
            progress=False,
            auto_adjust=False,
        )

        # Get valid closing prices
        nifty_close = nifty_history[
            "Close"
        ].dropna()


        # Minimum 20 trading days required
        if len(nifty_close) >= 20:

            current_price = float(
                nifty_close.iloc[-1].item()
            )

            price_20_days_ago = float(
                nifty_close.iloc[-20].item()
            )


            # Calculate NIFTY 20-day return
            market_return = (
                (
                    current_price
                    - price_20_days_ago
                )
                / price_20_days_ago
            ) * 100


            # ==================================
            # BUY SIGNAL
            # ==================================

            if market_return >= 3:

                ai_signal = "BUY"

                confidence = min(
                    90,
                    round(
                        65
                        + market_return * 3
                    ),
                )


            # ==================================
            # SELL SIGNAL
            # ==================================

            elif market_return <= -3:

                ai_signal = "SELL"

                confidence = min(
                    90,
                    round(
                        65
                        + abs(
                            market_return
                        ) * 3
                    ),
                )


            # ==================================
            # HOLD SIGNAL
            # ==================================

            else:

                ai_signal = "HOLD"

                confidence = round(
                    55
                    + (
                        3
                        - abs(
                            market_return
                        )
                    ) * 5
                )


            # Show result in terminal
            print(
                "NIFTY 20-day return:",
                round(
                    market_return,
                    2,
                ),
                "%",
            )

            print(
                "AI recommendation:",
                ai_signal,
                confidence,
            )


    except Exception as error:

        print(
            "AI recommendation error:",
            error,
        )


    # ==========================================
    # DASHBOARD CARD INFORMATION
    # ==========================================

    dashboard_data = {

        "portfolio_value": "₹0",

        "today_change": "+0.00%",

        "nifty": market[
            "nifty"
        ],

        "nifty_change": market[
            "status"
        ],

        "sensex": market[
            "sensex"
        ],

        "sensex_change": market[
            "status"
        ],

        "ai_signal": ai_signal,

        "confidence": (
            f"{confidence}%"
        ),

    }


    # ==========================================
    # LIVE INDIAN STOCK MARKET NEWS
    # ==========================================

    market_news = []


    try:

        news_feed = feedparser.parse(

            "https://news.google.com/"
            "rss/search?"

            "q=Indian+stock+market+"
            "NIFTY+SENSEX"

            "&hl=en-IN"

            "&gl=IN"

            "&ceid=IN:en"

        )


        # Get latest five news articles
        for article in (
            news_feed.entries[:5]
        ):

            market_news.append(

                {

                    "title": article.get(

                        "title",

                        "Market news "
                        "unavailable",

                    ),


                    "link": article.get(

                        "link",

                        "#",

                    ),


                    "published": article.get(

                        "published",

                        "Recently",

                    ),


                    "source": article.get(

                        "source",

                        {},

                    ).get(

                        "title",

                        "Market News",

                    ),

                }

            )


    except Exception as error:

        print(
            "Market news error:",
            error,
        )


    # ==========================================
    # SEND DATA TO DASHBOARD
    # ==========================================

    return render_template(

        "dashboard.html",

        data=dashboard_data,

        market_chart=market_chart,

        market_news=market_news,

    )
# ==================================================
# DYNAMIC STOCK SEARCH API
# ==================================================

@app.route("/api/search-stocks")
@login_required
def stock_search():

    query = request.args.get("q", "").strip()

    # Do not call Yahoo for empty input

    if len(query) < 1:
        return jsonify([])

    try:
        yahoo_url = "https://query2.finance.yahoo.com/v1/finance/search"

        parameters = {
            "q": query,
            "quotesCount": 15,
            "newsCount": 0,
            "enableFuzzyQuery": "true",
            "quotesQueryId": "tss_match_phrase_query",
        }

        headers = {"User-Agent": "Mozilla/5.0"}

        response = requests.get(
            yahoo_url, params=parameters, headers=headers, timeout=6
        )

        response.raise_for_status()

        yahoo_data = response.json()

        yahoo_quotes = yahoo_data.get("quotes", [])

        suggestions = []

        # ------------------------------------------
        # CREATE CLEAN STOCK SUGGESTIONS
        # ------------------------------------------

        for stock in yahoo_quotes:
            quote_type = stock.get("quoteType", "").upper()

            # Only show stocks and ETFs

            if quote_type not in ["EQUITY", "ETF"]:
                continue

            symbol = stock.get("symbol", "").strip()

            if not symbol:
                continue

            company_name = stock.get("longname") or stock.get("shortname") or symbol

            exchange = stock.get("exchDisp") or stock.get("exchange", "")

            # Symbol shown in UI:
            # TCS.NS -> TCS
            # IDEA.NS -> IDEA

            display_symbol = symbol.replace(".NS", "").replace(".BO", "")

            suggestions.append(
                {
                    # Exact Yahoo symbol sent
                    # to analysis page
                    "symbol": symbol,
                    # Clean symbol shown
                    # inside dropdown
                    "display_symbol": display_symbol,
                    "name": company_name,
                    "exchange": exchange,
                    "type": quote_type,
                }
            )

        # ------------------------------------------
        # SHOW INDIAN NSE RESULTS FIRST
        # ------------------------------------------

        suggestions.sort(key=lambda item: 0 if item["symbol"].endswith(".NS") else 1)

        return jsonify(suggestions[:8])

    except Exception as error:
        print("Stock Search Error:", error)

        return jsonify([])


# ==================================================
# STOCK ANALYSIS
# ==================================================


@app.route("/analysis")
@login_required
def analysis():

    symbol = request.args.get("symbol", "").strip()

    if not symbol:
        return render_template("analysis.html", stock=None, chart=None, news=[])

    # Get company information

    stock = StockService.get_stock_details(symbol)

    # Get six-month stock chart

    chart = StockService.get_stock_chart(symbol)

    # Get latest company news

    news = StockService.get_stock_news(symbol)

    return render_template("analysis.html", stock=stock, chart=chart, news=news)


# ==================================================
# LOGOUT
# ==================================================


@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(url_for("login"))


# ==================================================
# FORGOT PASSWORD
# ==================================================


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":
        email = request.form["email"]

        password = request.form["password"]

        confirm = request.form["confirm"]

        # ------------------------------
        # CHECK PASSWORDS
        # ------------------------------

        if password != confirm:
            flash("Passwords do not match!", "danger")

            return redirect(url_for("forgot_password"))

        # ------------------------------
        # CHECK USER
        # ------------------------------

        user = db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()

        if not user:
            flash("Email not found!", "danger")

            return redirect(url_for("forgot_password"))

        # ------------------------------
        # CREATE NEW PASSWORD HASH
        # ------------------------------

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        # ------------------------------
        # UPDATE PASSWORD
        # ------------------------------

        user.password = hashed_password

        db.session.commit()

        flash("Password updated successfully! Please login.", "success")

        return redirect(url_for("login"))

    return render_template("forgot_password.html")


@app.route("/compare")
@login_required
def compare():
    return render_template("compare.html")


@app.route("/compare-results")
@login_required
def compare_results():

    symbols_string = request.args.get("symbols", "")

    symbols = [
        symbol.strip().upper() for symbol in symbols_string.split(",") if symbol.strip()
    ]

    # Minimum 2 stocks required
    if len(symbols) < 2:
        return redirect(url_for("compare"))

    # Maximum 3 stocks allowed
    symbols = symbols[:3]

    comparison_data = []

    # Historical chart data
    chart_data = {
        "1M": [],
        "6M": [],
        "1Y": [],
        "3Y": [],
        "5Y": [],
    }

    # Yahoo Finance periods
    chart_periods = {
        "1M": "1mo",
        "6M": "6mo",
        "1Y": "1y",
        "3Y": "3y",
        "5Y": "5y",
    }

    for symbol in symbols:
        try:
            # Convert symbol into NSE ticker
            clean_symbol = symbol.replace(".NS", "").strip().upper()

            ticker_symbol = f"{clean_symbol}.NS"

            print(
                "Fetching comparison ticker:",
                ticker_symbol,
            )

            ticker = yf.Ticker(ticker_symbol)

            info = ticker.info or {}

            # Get latest stock price
            latest_history = ticker.history(period="5d")

            latest_price = "N/A"

            if not latest_history.empty and "Close" in latest_history.columns:
                close_prices = latest_history["Close"].dropna()

                if not close_prices.empty:
                    latest_price = round(
                        float(close_prices.iloc[-1]),
                        2,
                    )

            # =================================
            # COMPANY INFORMATION
            # =================================

            stock_data = {
                "symbol": clean_symbol,
                "name": (info.get("longName") or info.get("shortName") or clean_symbol),
                "price": latest_price,
                "market_cap": (info.get("marketCap") or "N/A"),
                "pe_ratio": (info.get("trailingPE") or "N/A"),
                "eps": (info.get("trailingEps") or "N/A"),
                "revenue": (info.get("totalRevenue") or "N/A"),
                "roe": (info.get("returnOnEquity") or "N/A"),
                "dividend_yield": (
                    round(float(info.get("dividendYield")), 2)
                    if info.get("dividendYield") is not None
                    else "N/A"
                ),
                "sector": (info.get("sector") or "N/A"),
                "industry": (info.get("industry") or "N/A"),
                "website": (info.get("website") or "N/A"),
                "description": (
                    info.get("longBusinessSummary")
                    or ("Company information is currently unavailable.")
                ),
            }

            comparison_data.append(stock_data)

            # =================================
            # HISTORICAL PRICE DATA
            # =================================

            for range_name, yahoo_period in chart_periods.items():
                try:
                    historical_data = ticker.history(
                        period=yahoo_period,
                        auto_adjust=False,
                    )

                    dates = []
                    prices = []

                    if not historical_data.empty and "Close" in historical_data.columns:
                        historical_data = historical_data.dropna(
                            subset=["Close"]
                        ).sort_index()

                        for date, row in historical_data.iterrows():
                            dates.append(date.strftime("%Y-%m-%d"))
                            prices.append(round(float(row["Close"]), 2))

                    chart_data[range_name].append(
                        {
                            "symbol": clean_symbol,
                            "name": stock_data["name"],
                            "dates": dates,
                            "prices": prices,
                        }
                    )

                except Exception as chart_error:
                    print(
                        (f"Historical chart error for {clean_symbol} {range_name}:"),
                        chart_error,
                    )

                    chart_data[range_name].append(
                        {
                            "symbol": clean_symbol,
                            "name": stock_data["name"],
                            "dates": [],
                            "prices": [],
                        }
                    )

        except Exception as error:
            print(
                (f"Comparison data error for {symbol}:"),
                error,
            )

            comparison_data.append(
                {
                    "symbol": symbol,
                    "name": symbol,
                    "price": "N/A",
                    "market_cap": "N/A",
                    "pe_ratio": "N/A",
                    "eps": "N/A",
                    "revenue": "N/A",
                    "roe": "N/A",
                    "dividend_yield": "N/A",
                    "sector": "N/A",
                    "industry": "N/A",
                    "website": "N/A",
                    "description": ("Company information is currently unavailable."),
                }
            )

    return render_template(
        "compare_results.html",
        stocks=comparison_data,
        # Send historical data to HTML
        chart_data=chart_data,
    )


# ==================================================
# RUN APPLICATION
# ==================================================

if __name__ == "__main__":
    app.run(debug=True)
