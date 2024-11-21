from psycopg2.extras import RealDictCursor

from app.core.decorators import crud_error_handler


@crud_error_handler
async def get_top100_repos(db, logger, sort_by=None, order="asc"):
    # базовый запрос
    query = "SELECT * FROM top100"

    # добавляем сортировку, если указано поле
    if sort_by:
        sort_order = "ASC" if order.lower() == "asc" else "DESC"
        query += f" ORDER BY {sort_by.value} {sort_order}"
    else:
        query += " ORDER BY stars DESC"  # сортировка по умолчанию

    # ограничиваем выборку 100 записями, если записей в таблице больше
    query += " LIMIT 100"
    with db.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query)
        return cursor.fetchall()


@crud_error_handler
async def get_repo_activity(db, repo_owner, repo_name, since, until, logger):
    with db.cursor(cursor_factory=RealDictCursor) as cursor:
        # получаем repo_id для указанного repo_owner и repo_name
        cursor.execute("""
                    SELECT id FROM top100
                    WHERE owner = %s AND repo = %s;
                """, (repo_owner, f"{repo_owner}/{repo_name}"))
        repo = cursor.fetchone()

        if not repo or "id" not in repo:
            logger.warning("Repository %s/%s not found in the database.", repo_owner, repo_name)
            raise ValueError(f"Repository {repo_owner}/{repo_name} not found in the database.")

        repo_id = repo["id"]
        # теперь используем repo_id для выборки из таблицы activity
        cursor.execute("""
                    SELECT date, commits, authors FROM activity
                    WHERE repo_id = %s AND date BETWEEN %s AND %s;
                """, (repo_id, since, until))

        return cursor.fetchall()
