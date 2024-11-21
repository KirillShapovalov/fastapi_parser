from functools import wraps

import psycopg2


def crud_error_handler(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        logger = kwargs.get('logger')  # извлекаем logger из аргументов функции
        if not logger:
            raise ValueError("Logger is required for this function.")
        try:
            return await func(*args, **kwargs)
        except psycopg2.OperationalError as e:
            logger.error("Database connection error: %s", e)
            raise ConnectionError("Failed to connect to the database. Please try again later.")
        except psycopg2.ProgrammingError as e:
            logger.error("SQL query error: %s", e)
            raise ValueError("Invalid SQL query. Check your inputs or sorting parameters.")
        except Exception as e:
            logger.error("Unhandled exception in %s: %s", func.__name__, e)
            raise RuntimeError("An unexpected error occurred. Please contact support.")

    return wrapper


def router_error_handler(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        core_deps = kwargs.get('core_deps')  # извлекаем core_deps из аргументов функции
        if not core_deps:
            raise ValueError("Core dependencies are required for this function.")
        try:
            return await func(*args, **kwargs)
        except psycopg2.OperationalError as db_err:
            core_deps.error_handler(db_err, core_deps.logger)
        except Exception as e:
            core_deps.error_handler(e, core_deps.logger)

    return wrapper
