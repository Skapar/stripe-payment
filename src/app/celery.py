import os

from celery import Celery
from dotenv import load_dotenv
import stripe
from sqlalchemy.orm import Session

from src.app.db import get_db
from src.app.models import Ticket

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")

celery = Celery(
    "tasks",
    broker=RABBITMQ_URL,
    backend="rpc://"
)

celery.conf.update(
    task_routes={
        "tasks.process_payment": {"queue": "payments"},
    }
)

@celery.task
def process_payment(session_id: str):
    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except stripe.error.StripeError as e:
        return {"error": str(e)}

    if session.get("payment_status") != "paid":
        return {"error": "Payment not successful."}

    user_email = session["customer_email"]
    amount_paid = session["amount_total"] / 100 
    currency = session["currency"]
    payment_intent_id = session["payment_intent"]

    db: Session = get_db()
    
    try:
        ticket = Ticket(
            email=user_email,
            amount=amount_paid,
            currency=currency,
            payment_intent_id=payment_intent_id,
            session_id=session_id,
            status="paid"
        )
        db.add(ticket)
        db.commit()
    except Exception as e:
        db.rollback() 
        return {"error": f"Database error: {str(e)}"}

    print(f"Payment processed for user: {user_email}")
    return {"status": "success", "session_id": session_id, "email": user_email, "amount": amount_paid}