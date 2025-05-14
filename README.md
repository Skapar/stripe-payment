# Stripe FastAPI + Celery

## Описание

Этот проект демонстрирует интеграцию Stripe Checkout с FastAPI и асинхронной обработкой задач через Celery.  
Используется PostgreSQL (через SQLAlchemy + asyncpg) и RabbitMQ для брокера задач.

---

## Быстрый старт

### 1. Клонируйте репозиторий и создайте виртуальное окружение

```bash
git clone <repo_url>
cd stripe
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

### 2. Настройте переменные окружения

Скопируйте `.env.template` в `.env` и заполните своими значениями:

```bash
cp .env.template .env
```

Пример содержимого `.env`:
```
DATABASE_URL=postgresql+asyncpg://user:password@host:port/dbname
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
RABBITMQ_URL=amqp://guest:guest@localhost:5672//
```

---

### 3. Запустите FastAPI приложение

```bash
python -m src.main
```
или
```bash
uvicorn src.main:app --reload
```

---

### 4. Запустите Celery worker

```bash
celery -A src.app.tasks worker --loglevel=info
```

---

### 5. Проверьте работу

- Создайте сессию оплаты:  
  `POST /create-checkout-session/`
- Проверьте статус задачи:  
  `GET /task-status/{task_id}`
- Stripe webhook:  
  `POST /webhook/`

---

## Примечания

- Для работы Stripe webhook используйте публичный адрес или сервис типа [ngrok](https://ngrok.com/).
- Все настройки можно менять через `.env`.
- Для работы с асинхронным PostgreSQL используйте драйвер `asyncpg` и строку подключения с префиксом `postgresql+asyncpg://`.

---

## Структура проекта

```
stripe/
├── src/
│   ├── app/
│   │   ├── models.py
│   │   ├── tasks.py
│   │   ├── db.py
│   │   ├── celery.py
│   │   └── ...
│   └── main.py
├── .env
├── .env.template
├── requirements.txt
└── README.md
```

---

## Лицензия