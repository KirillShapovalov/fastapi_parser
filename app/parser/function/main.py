import asyncio

from function.db import init_db_pool, close_db_pool
from function.parsers import parse_top100_data, parse_activity_data
from function.utils import logger, init_http_client, close_http_client


async def start_parsing():
    db_pool = None
    http_client = None
    try:
        db_pool = await init_db_pool()
        http_client = await init_http_client()

        await asyncio.gather(
            parse_top100_data(db_pool, http_client),
            parse_activity_data(db_pool, http_client)
        )
    except Exception as e:
        logger.error(f"Error at start processing: {e}")
        raise
    finally:
        await close_http_client(http_client)
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
