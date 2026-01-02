"""Main entry point for the Alain Telegram bot."""

import os
import logging

from dotenv import load_dotenv
from telegram.ext import Application

from db import Database
from bot.handlers import start_handler, message_handler, reset_handler, northstar_handler

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def post_init(application: Application) -> None:
    """Initialize database connection after app starts."""
    logger.info("Connecting to database...")
    await Database.connect()
    logger.info("Database connected!")


async def post_shutdown(application: Application) -> None:
    """Cleanup on shutdown."""
    logger.info("Disconnecting from database...")
    await Database.disconnect()
    logger.info("Database disconnected!")


def main() -> None:
    """Start the bot."""
    # Load environment variables
    load_dotenv()

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")

    webhook_url = os.environ.get("WEBHOOK_URL")
    # Webhook configuration
    webhook_port = int(os.environ.get("WEBHOOK_PORT", "8443"))
    webhook_path = f"/webhook/{token}"  # Use token as secret path

    # Build application
    application = (
        Application.builder()
        .token(token)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    # Register handlers
    application.add_handler(start_handler)
    application.add_handler(reset_handler)
    application.add_handler(northstar_handler)
    application.add_handler(message_handler)

    # Start the bot with webhook
    logger.info(f"Starting Alain bot with webhook on port {webhook_port}...")
    logger.info(f"Webhook URL: {webhook_url}{webhook_path}")
    application.run_webhook(
        listen="0.0.0.0",
        port=webhook_port,
        url_path=webhook_path,
        webhook_url=f"{webhook_url}{webhook_path}",
        allowed_updates=["message"],
    )


if __name__ == "__main__":
    main()

