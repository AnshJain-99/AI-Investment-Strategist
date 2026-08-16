from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(25), nullable=True)
    risk_profile = db.Column(db.String(30), nullable=False, default="Moderate")
    investment_goal = db.Column(db.String(120), nullable=True)
    preferred_market = db.Column(db.String(30), nullable=False, default="NSE")
    google_id = db.Column(db.String(255), unique=True, nullable=True)
    auth_provider = db.Column(db.String(30), nullable=False, default="email")

    watchlist = db.relationship(
        "Watchlist",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )


class Watchlist(db.Model):
    __tablename__ = "watchlist"
    __table_args__ = (
    db.UniqueConstraint(
        "user_id",
        "symbol",
        name="unique_watchlist_stock"
    ),
)

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    symbol = db.Column(
        db.String(20),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )
