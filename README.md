# Alain AI


An AI agent that helps you learn about life and crush your goals.

## Quick Start

### 1. Setup Environment

```bash
# Copy env template and add your tokens
cp .env.example .env
# Edit .env with your TELEGRAM_BOT_TOKEN
```

### 2. Start PostgreSQL

```bash
docker compose up -d
```

### 3. Install Dependencies

```bash
pip install -e .
```

### 4. Run the Bot

```bash
alain
# or
python -m bot.main
```

## Project Structure

```
alain/
├── bot/                    # Telegram bot
│   ├── main.py            # Entry point
│   └── handlers/          # Message handlers
│       ├── start.py       # /start onboarding
│       └── echo.py        # Echo messages
├── db/                    # Database layer
│   ├── connection.py      # asyncpg pool
│   ├── models.py          # Dataclasses
│   ├── repository.py      # CRUD operations
│   └── migrations/
│       └── init.sql       # Schema
├── ai_client/             # Anthropic client
├── docker-compose.yml     # PostgreSQL
└── pyproject.toml
```

## Database

The bot uses PostgreSQL with three tables:
- `user` - Telegram users and onboarding status
- `conversation` - Chat sessions
- `message` - All messages for RAG indexing

## Environment Variables

Create a `.env` file with:

```bash
TELEGRAM_BOT_TOKEN=your_token_here
DATABASE_URL=postgresql://alain:alain_secret@localhost:5432/alain_db
```

