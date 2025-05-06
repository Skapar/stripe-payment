import os
import json
import asyncio

from dotenv import load_dotenv

import stripe
from celery import Celery

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.app.db import AsyncSessionLocal
from src.app.models import Task

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

celery_app = Celery(
    "tasks",
    broker="amqp://guest:guest@localhost:5672//",
    backend="rpc://"
)

def sync_create_stripe_session(price, currency, success_url, cancel_url):
    return asyncio.run(create_stripe_session_async(price, currency, success_url, cancel_url))

async def create_stripe_session_async(price, currency, success_url, cancel_url):
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": currency,
                    "product_data": {"name": "Ticket"},
                    "unit_amount": price,
                },
                "quantity": 1,
            },
        ],
        mode="payment",
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return session

async def update_task_status(db: AsyncSession, task_id: str, status: str, result: dict):
    query = await db.execute(select(Task).filter(Task.task_id == task_id))
    task = query.scalar_one_or_none()

    if task:
        task.status = status
        task.result = json.dumps(result)
        await db.commit()
    else:
        print(f"Task with ID {task_id} not found")

@celery_app.task(bind=True)
def create_stripe_session(self, price, currency, success_url, cancel_url):
    try:
        session = sync_create_stripe_session(price, currency, success_url, cancel_url)

        asyncio.run(update_task_status_wrapper(self.request.id, "SUCCESS", {"sessionId": session.id}))

        return {"sessionId": session.id}

    except Exception as e:
        asyncio.run(update_task_status_wrapper(self.request.id, "FAILED", {"error": str(e)}))
        return {"error": str(e)}

async def update_task_status_wrapper(task_id, status, result):
    async with AsyncSessionLocal() as db:
        await update_task_status(db, task_id, status, result)
