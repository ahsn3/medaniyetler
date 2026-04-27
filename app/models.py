from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


def utcnow():
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    transactions = db.relationship(
        "Transaction", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    kind = db.Column(db.String(16), nullable=False)  # "income" | "expense"
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False, index=True)

    @staticmethod
    def totals_for_user(user_id: int):
        from sqlalchemy import case, func

        row = (
            db.session.query(
                func.coalesce(
                    func.sum(case((Transaction.kind == "income", Transaction.amount), else_=0)),
                    0,
                ).label("income"),
                func.coalesce(
                    func.sum(case((Transaction.kind == "expense", Transaction.amount), else_=0)),
                    0,
                ).label("expense"),
            )
            .filter(Transaction.user_id == user_id)
            .one()
        )
        income = float(row.income or 0)
        expense = float(row.expense or 0)
        return income, expense, income - expense
