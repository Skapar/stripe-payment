import os
import uuid

import stripe
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request

from celery.result import AsyncResult
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select

from src.app.models import CheckoutRequest, Ticket, Task
from src.app.tasks import create_stripe_session
from src.app.celery import process_payment
from src.app.db import AsyncSession as async_session, AsyncSessionLocal
from src.app import settings

import uvicorn

app = FastAPI()

load_dotenv()
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

@app.post("/create-checkout-session/")
async def create_checkout_session(data: CheckoutRequest):
    task_id = str(uuid.uuid4())
    async with AsyncSessionLocal() as db:
        new_task = Task(task_id=task_id, status="PENDING", result=None)
        db.add(new_task)
        await db.commit()
    task = create_stripe_session.apply_async(
        args=[data.price, data.currency, data.success_url, data.cancel_url],
        task_id=task_id
    )
    return {"task_id": task_id}

@app.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Task).filter(Task.task_id == task_id))
        task = result.scalar_one_or_none()
        if not task:
            return {"error": "Task not found"}

        return {
            "task_id": task_id,
            "celery_status": AsyncResult(task_id).state,
            "db_status": task.status,
            "db_result": task.result,
        }

@app.post("/webhook/")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        print(f"✅ Платёж успешен: {session['id']}")

        async with async_session() as db:
            try:
                new_ticket = Ticket(
                    session_id=session["id"],
                    paid=True
                )
                db.add(new_ticket)
                await db.commit()
            except SQLAlchemyError as e:
                await db.rollback()
                raise HTTPException(status_code=500, detail=str(e))

        process_payment.delay(session["id"])

    return {"message": "Webhook received"}

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=settings.run.host,
        port=settings.run.port,
        reload=True
    )