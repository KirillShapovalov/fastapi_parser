import asyncio

from function.db import init_db_pool, close_db_pool
from function.parsers import parse_top100_data, parse_activity_data
from function.utils import logger


async def start_parsing():
    db_pool = None
    try:
        db_pool = await init_db_pool()

        await asyncio.gather(
            parse_top100_data(db_pool),
            parse_activity_data(db_pool)
        )
    except Exception as e:
        logger.error(f"Error at start processing: {e}")
        raise
    finally:
        await close_db_pool(db_pool)


async def handler(event, context):
    try:
        await start_parsing()
        logger.info("Parsing completed successfully.")
        return {
            "statusCode": 200,
            "body": "parsing successful"
        }
    except Exception as e:
        logger.error(f"Fatal error in handler: {e}")
        return {
            "statusCode": 500,
            "body": str(e)
        }
