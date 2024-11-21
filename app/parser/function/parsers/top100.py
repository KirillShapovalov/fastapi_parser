from function.api.github_api import fetch_from_github, GITHUB_API_URL
from function.utils.logger import logger


# запрос для получения top100 данных
async def parse_top100_data(db_pool):
    if db_pool is None:
        logger.error("Database connection pool is not initialized.")
        return
    url = f"{GITHUB_API_URL}/search/repositories?q=stars:>0&sort=stars&per_page=100"
    data = await fetch_from_github(url)
    if data:
        await insert_top100_data_to_db(db_pool, data["items"])


async def insert_top100_data_to_db(db_pool, data):
    # запрос для получения предыдущих позиций
    fetch_positions_query = """
    SELECT repo, position_cur 
    FROM top100
    """
    # запрос для вставки данных с обновлением position_prev (предполагается уникальность по repo)
    upsert_query = """
    INSERT INTO top100 (repo, owner, position_cur, position_prev, stars, watchers, forks, open_issues, language)
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
    ON CONFLICT (repo) DO UPDATE 
    SET position_cur = EXCLUDED.position_cur,
        position_prev = EXCLUDED.position_prev,
        stars = EXCLUDED.stars,
        watchers = EXCLUDED.watchers,
        forks = EXCLUDED.forks,
        open_issues = EXCLUDED.open_issues,
        language = EXCLUDED.language;
    """
    async with db_pool.acquire() as conn:
        async with conn.transaction():
            previous_positions = await conn.fetch(fetch_positions_query)
            position_map = {row["repo"]: row["position_cur"] for row in
                            previous_positions} if previous_positions else {}
            for idx, repo in enumerate(data, start=1):
                position_prev = position_map.get(repo["full_name"], None)
                await conn.execute(upsert_query,
                    repo["full_name"],
                    repo["owner"]["login"],
                    idx,
                    position_prev,
                    repo["stargazers_count"],
                    repo["watchers_count"],
                    repo["forks_count"],
                    repo["open_issues_count"],
                    repo["language"]
                )
            logger.info(f"Inserted or updated {len(data)} records in top100 table.")
