"""Seed data for the public demo: two accounts with balances and history."""

from datetime import timedelta

from flask import current_app

from .extensions import db
from .models import Transaction, User, Wallet
from .money import make_reference
from .security import hash_secret
from .timeutils import utcnow

DEMO_USERS = [
    {
        "mobile": "9000000001",
        "name": "Aarav Sharma",
        "email": "aarav@demowallet.app",
        "pin": "1234",
        "balance_paise": 500000,  # ₹5,000
    },
    {
        "mobile": "9000000002",
        "name": "Meera Iyer",
        "email": "meera@demowallet.app",
        "pin": "1234",
        "balance_paise": 250000,  # ₹2,500
    },
]


def seed_demo():
    """Idempotently create the demo accounts, wallets and a little history."""
    suffix = current_app.config["VPA_SUFFIX"]
    created = {}

    for spec in DEMO_USERS:
        user = User.query.filter_by(mobile=spec["mobile"]).first()
        if user is None:
            user = User(
                mobile=spec["mobile"],
                name=spec["name"],
                email=spec["email"],
                vpa=f"{spec['mobile']}@{suffix}",
                is_verified=True,
                pin_hash=hash_secret(spec["pin"]),
            )
            db.session.add(user)
            db.session.flush()
            created[spec["mobile"]] = (user, spec["balance_paise"] > 0)
        if user.wallet is None:
            user.wallet = Wallet(user_id=user.id, balance_paise=spec["balance_paise"])
        elif spec["mobile"] in created:
            user.wallet.balance_paise = spec["balance_paise"]

    db.session.commit()
    _seed_history()


def _seed_history():
    """Add a few backdated transactions so the history screen looks alive."""
    if Transaction.query.count() > 0:
        return

    sender = User.query.filter_by(mobile=DEMO_USERS[0]["mobile"]).first()
    receiver = User.query.filter_by(mobile=DEMO_USERS[1]["mobile"]).first()
    if sender is None or receiver is None:
        return

    now = utcnow()
    history = [
        # (days ago, type, sender, receiver, rupees)
        (12, "topup", None, sender.id, 3000),
        (10, "topup", None, receiver.id, 2500),
        (6, "transfer", sender.id, receiver.id, 250),
        (3, "topup", None, sender.id, 2500),
        (2, "transfer", receiver.id, sender.id, 100),
        (1, "transfer", sender.id, receiver.id, 400),
    ]
    for days_ago, kind, sender_id, receiver_id, rupees in history:
        db.session.add(
            Transaction(
                reference=make_reference(),
                type=kind,
                sender_id=sender_id,
                receiver_id=receiver_id,
                amount_paise=rupees * 100,
                note="Demo history" if kind == "transfer" else None,
                timestamp=now - timedelta(days=days_ago),
            )
        )
    db.session.commit()
