from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.forms import TransactionForm
from app.models import Transaction

bp = Blueprint("finance", __name__, url_prefix="")


@bp.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    form = TransactionForm()
    if form.validate_on_submit():
        tx = Transaction(
            user_id=current_user.id,
            kind=form.kind.data,
            amount=form.amount.data,
            description=(form.description.data or "").strip() or "—",
        )
        db.session.add(tx)
        db.session.commit()
        return redirect(url_for("finance.dashboard"))

    income, expense, balance = Transaction.totals_for_user(current_user.id)
    recent = (
        Transaction.query.filter_by(user_id=current_user.id)
        .order_by(Transaction.created_at.desc())
        .limit(15)
        .all()
    )
    return render_template(
        "dashboard.html",
        form=form,
        income=income,
        expense=expense,
        balance=balance,
        recent=recent,
    )


@bp.route("/transactions")
@login_required
def transactions_list():
    rows = (
        Transaction.query.filter_by(user_id=current_user.id)
        .order_by(Transaction.created_at.desc())
        .all()
    )
    income, expense, balance = Transaction.totals_for_user(current_user.id)
    return render_template(
        "transactions.html",
        rows=rows,
        income=income,
        expense=expense,
        balance=balance,
    )
