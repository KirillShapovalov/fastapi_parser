from collections import defaultdict
from datetime import datetime
import asyncio

from function.api.github_api import fetch_from_github, GITHUB_API_URL
from function.utils import logger

SEMAPHORE_LIMIT = 10  # лимит одновременно выполняемых задач
SEMAPHORE = asyncio.Semaphore(SEMAPHORE_LIMIT)


# запрос для получения активности по репозиториям
async def parse_activity_data(db_pool, client):
    if db_pool is None:
        logger.error("Database connection pool is not initialized.")
        return
    try:
        async with db_pool.acquire() as conn:
            # получаем список топ-100 репозиториев с ID
            top_repos = await fetch_top100_repos_with_ids(conn)

            # если данные в top100 отсутствуют - выходим
            if not top_repos:
                logger.info("No repositories found in the database to parse activity.")
                return

            # создание задач для обработки каждого репозитория
            tasks = [
                limited_fetch(db_pool, repo_info["repo_id"], repo_info["owner"], repo_info["repo"].split("/")[-1], SEMAPHORE, client)
                for repo_info in top_repos
            ]
            await asyncio.gather(*tasks)
            logger.info("Completed parsing activity for all repositories.")
    except Exception as e:
        logger.error(f"Unexpected error while parsing activity data: {e}")
        raise


# запрос имеющихся в top100 репозиториев с целью получить данные для запроса активности по коммитам
async def fetch_top100_repos_with_ids(conn):
    rows = await conn.fetch("SELECT id AS repo_id, repo, owner FROM top100")
    return [{"repo_id": row["repo_id"], "repo": row["repo"], "owner": row["owner"]} for row in rows] if rows else None


# создание запроса к api с учетом лимита и последующее сохранение
async def limited_fetch(db_pool, repo_id, owner, repo, semaphore, client):
    async with semaphore:
        activity_data = await fetch_repo_activity(owner, repo, client)
        if activity_data:
            await save_activity_to_db(db_pool, repo_id, activity_data)


# запрос к github api для получения активности по коммитам с заданными owner и repo из существующих данных в top100
async def fetch_repo_activity(owner, repo, client):
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/activity"
    response = await fetch_from_github(url, client)
    return await process_activity_response(response) if response else None


# обработка ответа
async def process_activity_response(response):
    try:
        # группируем данные по датам
        activity_by_date = defaultdict(lambda: {"authors": set(), "commits": 0})

        for commit in response:
            date = commit["timestamp"][:10]  # извлекаем дату в формате YYYY-MM-DD
            author = commit["actor"]["login"]

            activity_by_date[date]["authors"].add(author)
            activity_by_date[date]["commits"] += 1

        # преобразуем результат в список словарей
        return [
            {"date": date, "authors": list(data["authors"]), "commits": data["commits"]}
            for date, data in sorted(activity_by_date.items())
        ]
    except Exception as e:
        logger.error(f"Error while processing activity data: {e}")
        return


# сохранение данных в таблицу activity
async def save_activity_to_db(db_pool, repo_id, activity_data):
    try:
        async with db_pool.acquire() as conn:
            async with conn.transaction():
                # в случае конфликта по уникальности (repo_id, date) старые данные будут перезаписываться новыми
                query = """
                INSERT INTO activity (repo_id, date, commits, authors)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (repo_id, date) DO UPDATE 
                SET commits = EXCLUDED.commits, authors = EXCLUDED.authors;
                """
                for record in activity_data:
                    await conn.execute(
                        query,
                        repo_id,
                        datetime.strptime(record["date"], '%Y-%m-%d').date(),
                        record["commits"],
                        record["authors"]
                    )
        logger.info(f"Saved activity data for repo ID {repo_id}.")
    except Exception as e:
        logger.error(f"Error while saving activity data for repo ID {repo_id}: {e}")
