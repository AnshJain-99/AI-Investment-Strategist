from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import yfinance as yf

# from datetime import datetime
from datetime import datetime, timedelta
import feedparser
import random
import smtplib
import ssl
from email.message import EmailMessage
from database.models import db, User, Watchlist


from flask_bcrypt import Bcrypt

from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)

from config import Config

from services.stock_service import StockService

import requests

app = Flask(__name__)

app.config.from_object(Config)


POPULAR_STOCKS = [
    {"symbol": "RELIANCE.NS", "display_symbol": "RELIANCE", "name": "Reliance Industries", "exchange": "NSE", "type": "EQUITY"},
    {"symbol": "TCS.NS", "display_symbol": "TCS", "name": "Tata Consultancy Services", "exchange": "NSE", "type": "EQUITY"},
    {"symbol": "INFY.NS", "display_symbol": "INFY", "name": "Infosys Limited", "exchange": "NSE", "type": "EQUITY"},
    {"symbol": "HDFCBANK.NS", "display_symbol": "HDFCBANK", "name": "HDFC Bank", "exchange": "NSE", "type": "EQUITY"},
    {"symbol": "ICICIBANK.NS", "display_symbol": "ICICIBANK", "name": "ICICI Bank", "exchange": "NSE", "type": "EQUITY"},
    {"symbol": "SBIN.NS", "display_symbol": "SBIN", "name": "State Bank of India", "exchange": "NSE", "type": "EQUITY"},
    {"symbol": "BHARTIARTL.NS", "display_symbol": "BHARTIARTL", "name": "Bharti Airtel", "exchange": "NSE", "type": "EQUITY"},
    {"symbol": "ITC.NS", "display_symbol": "ITC", "name": "ITC Limited", "exchange": "NSE", "type": "EQUITY"},
    {"symbol": "LT.NS", "display_symbol": "LT", "name": "Larsen & Toubro", "exchange": "NSE", "type": "EQUITY"},
    {"symbol": "AXISBANK.NS", "display_symbol": "AXISBANK", "name": "Axis Bank", "exchange": "NSE", "type": "EQUITY"},
    {"symbol": "MARUTI.NS", "display_symbol": "MARUTI", "name": "Maruti Suzuki", "exchange": "NSE", "type": "EQUITY"},
    {"symbol": "TATAMOTORS.NS", "display_symbol": "TATAMOTORS", "name": "Tata Motors", "exchange": "NSE", "type": "EQUITY"},
]


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


@login_manager.unauthorized_handler
def unauthorized():

    return redirect(url_for("login"))


# ==================================================
# CREATE DATABASE TABLES
# ==================================================

with app.app_context():
    db.create_all()

    def ensure_column(table_name, column_name, column_definition):
        columns = db.session.execute(
            db.text(f"PRAGMA table_info({table_name})")
        ).fetchall()

        if column_name not in [column[1] for column in columns]:
            db.session.execute(
                db.text(
                    f"ALTER TABLE {table_name} "
                    f"ADD COLUMN {column_name} {column_definition}"
                )
            )
            db.session.commit()

    ensure_column("users", "phone", "VARCHAR(25)")
    ensure_column("users", "risk_profile", "VARCHAR(30) DEFAULT 'Moderate' NOT NULL")
    ensure_column("users", "investment_goal", "VARCHAR(120)")
    ensure_column("users", "preferred_market", "VARCHAR(30) DEFAULT 'NSE' NOT NULL")


def send_otp_email(recipient, otp):

    mail_server = app.config.get("MAIL_SERVER")
    mail_username = app.config.get("MAIL_USERNAME")
    mail_password = app.config.get("MAIL_PASSWORD")
    mail_sender = app.config.get("MAIL_DEFAULT_SENDER") or mail_username
    mail_port = int(app.config.get("MAIL_PORT") or 587)

    if not mail_server or not mail_username or not mail_password or not mail_sender:
        print(f"Password reset OTP for {recipient}: {otp}")
        return False

    message = EmailMessage()
    message["Subject"] = "Your InvestIQ OTP"
    message["From"] = mail_sender
    message["To"] = recipient
    message.set_content(
        "Use this OTP to reset your password:\n\n"
        f"{otp}\n\n"
        "This OTP will expire in 10 minutes."
    )

    context = ssl.create_default_context()

    with smtplib.SMTP(mail_server, mail_port) as server:
        server.starttls(context=context)
        server.login(mail_username, mail_password)
        server.send_message(message)

    return True


# ==================================================
# LOGIN
# ==================================================


@app.route("/")
def landing():

    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form["email"]

        password = request.form["password"]

        user = db.session.execute(
            db.select(User).filter_by(email=email)
        ).scalar_one_or_none()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)

            return redirect(url_for("dashboard"))

        flash("Invalid Email or Password", "danger")

    return render_template("login_form.html")


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

        existing = db.session.execute(
            db.select(User).filter_by(email=email)
        ).scalar_one_or_none()

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
    market_chart = StockService.get_market_chart("6mo")

    # ==========================================
    # DASHBOARD CARD INFORMATION
    # ==========================================


    dashboard_data = {
        "portfolio_value": "₹0",
        "today_change": "+0.00%",
        "nifty": market["nifty"],
        "nifty_change": market["status"],
        "sensex": market["sensex"],
        "sensex_change": market["status"],
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
        for article in news_feed.entries[:5]:

            market_news.append(
                {
                    "title": article.get(
                        "title",
                        "Market news " "unavailable",
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

    def fallback_suggestions():
        lowered_query = query.lower()

        return [
            stock
            for stock in POPULAR_STOCKS
            if lowered_query in stock["symbol"].lower()
            or lowered_query in stock["display_symbol"].lower()
            or lowered_query in stock["name"].lower()
        ][:8]

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

        return jsonify(suggestions[:8] or fallback_suggestions())

    except Exception as error:
        print("Stock Search Error:", error)

        return jsonify(fallback_suggestions())


# ==================================================
# STOCK ANALYSIS
# ==================================================


@app.route("/analysis")
@login_required
def analysis():

    symbol = request.args.get("symbol", "").strip()

    if not symbol:
        return render_template(
            "analysis.html", stock=None, chart=None, news=[], ai=None
        )

    # Get company information

    stock = StockService.get_stock_details(symbol)

    # Get six-month stock chart

    chart = StockService.get_stock_chart(symbol)

    # Get latest company news

    news = StockService.get_stock_news(symbol)

    ai = StockService.get_ai_analysis(symbol)

    print("AI Analysis:", ai)

    return render_template("analysis.html", stock=stock, chart=chart, news=news, ai=ai)


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

    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    step = session.get("reset_step", "request")

    if request.method == "POST":
        action = request.form.get("action", "send_otp")

        if action == "send_otp":
            email = request.form.get("email", "").strip().lower()

            user = db.session.execute(
                db.select(User).filter_by(email=email)
            ).scalar_one_or_none()

            if not user:
                flash("Email not found!", "danger")

                return redirect(url_for("forgot_password"))

            otp = f"{random.randint(100000, 999999)}"
            session["reset_email"] = email
            session["reset_otp"] = otp
            session["reset_otp_expires"] = (
                datetime.utcnow() + timedelta(minutes=10)
            ).isoformat()
            session["reset_step"] = "verify"

            try:
                email_sent = send_otp_email(email, otp)

                if email_sent:
                    flash("OTP sent to your registered email.", "success")
                else:
                    flash(f"Dev OTP: {otp}", "info")

            except Exception as error:
                print("OTP email error:", error)
                flash(f"Email failed. Dev OTP: {otp}", "warning")

            return redirect(url_for("forgot_password"))

        if action == "verify_otp":
            entered_otp = request.form.get("otp", "").strip()
            expires_raw = session.get("reset_otp_expires")

            if not expires_raw or datetime.utcnow() > datetime.fromisoformat(expires_raw):
                session["reset_step"] = "request"
                flash("OTP expired. Please request a new OTP.", "danger")

                return redirect(url_for("forgot_password"))

            if entered_otp != session.get("reset_otp"):
                flash("Invalid OTP. Please try again.", "danger")

                return redirect(url_for("forgot_password"))

            session["reset_step"] = "reset"
            flash("OTP verified. Set your new password.", "success")

            return redirect(url_for("forgot_password"))

        if action == "reset_password":
            password = request.form.get("password", "")
            confirm = request.form.get("confirm", "")
            email = session.get("reset_email")

            if session.get("reset_step") != "reset" or not email:
                flash("Please verify OTP first.", "danger")

                return redirect(url_for("forgot_password"))

            if password != confirm:
                flash("Passwords do not match!", "danger")

                return redirect(url_for("forgot_password"))

            user = db.session.execute(
                db.select(User).filter_by(email=email)
            ).scalar_one_or_none()

            if not user:
                flash("Email not found!", "danger")

                return redirect(url_for("forgot_password"))

            user.password = bcrypt.generate_password_hash(password).decode("utf-8")

            db.session.commit()

            session.pop("reset_email", None)
            session.pop("reset_otp", None)
            session.pop("reset_otp_expires", None)
            session.pop("reset_step", None)

            flash("Password updated successfully! Please login.", "success")

            return redirect(url_for("login"))

    return render_template("forgot_password.html", step=step)


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():

    if request.method == "POST":

        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        risk_profile = request.form.get("risk_profile", "Moderate").strip()
        investment_goal = request.form.get("investment_goal", "").strip()
        preferred_market = request.form.get("preferred_market", "NSE").strip()

        if not full_name or not email:
            flash("Name and email are required.", "danger")

            return redirect(url_for("profile"))

        existing_user = User.query.filter(
            User.email == email,
            User.id != current_user.id,
        ).first()

        if existing_user:
            flash("This email is already used by another account.", "danger")

            return redirect(url_for("profile"))

        current_user.full_name = full_name
        current_user.email = email
        current_user.phone = phone
        current_user.risk_profile = risk_profile
        current_user.investment_goal = investment_goal
        current_user.preferred_market = preferred_market

        db.session.commit()

        flash("Profile updated successfully.", "success")

        return redirect(url_for("profile"))

    return render_template("profile.html", active_panel="profile")


@app.route("/settings")
@login_required
def settings():

    return render_template("profile.html", active_panel="settings")


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


@app.route("/watchlist")
@login_required
def watchlist():

    stocks = Watchlist.query.filter_by(user_id=current_user.id).all()

    return render_template("watchlist.html", stocks=stocks)


@app.route("/watchlist/add", methods=["POST"])
@login_required
def add_to_watchlist():

    data = request.get_json(silent=True) or {}

    symbol = data.get("symbol", "").strip().upper()

    if not symbol:
        return jsonify({"success": False, "message": "Invalid symbol"}), 400

    exists = Watchlist.query.filter_by(user_id=current_user.id, symbol=symbol).first()

    if exists:
        return jsonify({"success": False, "message": "Already added"})

    stock = Watchlist(user_id=current_user.id, symbol=symbol)

    db.session.add(stock)
    db.session.commit()

    return jsonify({"success": True})


@app.route("/watchlist/remove", methods=["POST"])
@login_required
def remove_from_watchlist():

    data = request.get_json(silent=True) or {}

    symbol = data.get("symbol", "").strip().upper()

    stock = Watchlist.query.filter_by(user_id=current_user.id, symbol=symbol).first()

    if stock:

        db.session.delete(stock)
        db.session.commit()

    return jsonify({"success": True})


# ==================================================
# WATCHLIST SUMMARY API
# ==================================================


@app.route("/api/watchlist-summary")
@login_required
def watchlist_summary():

    try:

        watchlist = Watchlist.query.filter_by(user_id=current_user.id).all()

        symbols = [stock.symbol for stock in watchlist]

        summary = StockService.get_watchlist_summary(symbols)

        return jsonify(summary)

    except Exception as e:

        print("Watchlist Summary Error:", e)

        return jsonify(
            {
                "holdings": 0,
                "gainers": 0,
                "losers": 0,
                "avg_return": 0,
                "allocation": [],
                "stocks": [],
            }
        )


@app.route("/api/stock-live/<symbol>")
@login_required
def stock_live(symbol):

    try:

        if "." not in symbol:
            symbol = f"{symbol.upper()}.NS"
        else:
            symbol = symbol.upper()

        stock = yf.Ticker(symbol)

        try:
            info = stock.info or {}
        except Exception:
            info = {}

        try:
            fast_info = stock.fast_info or {}
        except Exception:
            fast_info = {}

        history = stock.history(period="5d")

        history = history.dropna(subset=["Close"])

        current = fast_info.get("lastPrice")

        if history.empty and not current:
            raise Exception("No price data")

        current = float(current or history["Close"].iloc[-1])

        previous = float(history["Close"].iloc[-2]) if len(history) >= 2 else current

        change = round(((current - previous) / previous) * 100, 2)

        return jsonify(
            {
                "company": info.get("longName", symbol),
                "price": f"{current:,.2f}",
                "change": change,
                "market_cap": info.get("marketCap"),
                "pe": info.get("trailingPE"),
                "high52": info.get("fiftyTwoWeekHigh"),
                "low52": info.get("fiftyTwoWeekLow"),
            }
        )

    except Exception as error:
        print("Live Stock Error:", error)

        return jsonify(
            {
                "company": symbol,
                "price": "--",
                "change": 0,
                "market_cap": "--",
                "pe": "--",
                "high52": "--",
                "low52": "--",
            }
        )


@app.route("/dashboard-market")
@login_required
def dashboard_market():

    market = StockService.get_market_data()

    return jsonify(
        {
            "nifty": market["nifty"],
            "sensex": market["sensex"],
            "nifty_change": market["status"],
            "sensex_change": market["status"],
        }
    )


@app.route("/api/dashboard-market-chart")
@login_required
def dashboard_market_chart():

    period = request.args.get("period", "6mo")

    chart = StockService.get_market_chart(period)

    if not chart:
        return jsonify(
            {
                "success": False,
                "message": "Unable to load market chart.",
            }
        ), 503

    return jsonify(
        {
            "success": True,
            "chart_html": chart,
        }
    )


# ==================================================
# RUN APPLICATION
# ==================================================


if __name__ == "__main__":
    app.run(debug=True)
