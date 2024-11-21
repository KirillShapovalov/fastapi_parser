# fastapi_parser

---

## API Эндпоинты

#### -- **GET** `/api/repos/top100`

Получить топ-100 публичных репозиториев из базы данных, отсортированных по количеству звёзд.

**Пример ответа:**

```json
[
  {
    "repo": "owner/repo-name",
    "owner": "owner",
    "position_cur": 1,
    "position_prev": 2,
    "stars": 12345,
    "watchers": 54321,
    "forks": 123,
    "open_issues": 10,
    "language": "Python"
  },
  ...
]
```

#### -- **GET** `/api/repos/{owner}/{repo}/activity`

Эндпоинт для получения активности репозитория (коммиты) за указанный промежуток времени.

**Пример запроса:**
`GET /api/repos/octocat/hello-world/activity?since=2024-01-01&until=2024-01-07
`

**Пример ответа:**

```json
[
  {
    "date": "2024-01-01",
    "commits": 15,
    "authors": [
      "user1",
      "user2"
    ]
  },
  {
    "date": "2024-01-02",
    "commits": 10,
    "authors": [
      "user3"
    ]
  }
]
```

## Структура проекта:

```
fastapi_parser/
├── app/                                # Основной модуль приложения
│   ├── api/                            # Эндпоинты API
│   │   └── routers/                    # Подмодуль маршрутов
│   │       └── repos.py                # Включение маршрутов
│   ├── core/                           # Вспомогательные утилиты
│   │   ├── utils.py                    # Вспомогательные функции
│   │   └── decorators.py               # Декораторы
│   ├── crud/                           # Логика взаимодействия с базой данных
│   │   └── crud.py                     # CRUD-операции
│   ├── db/                             # Модуль базы данных
│   │   └── database.py                 # Логика подключения к PostgreSQL
│   ├── dependecies/                    # Зависимости для маршрутов
│   │   └── dependencies.py             # Логика зависимостей
│   ├── parser/                         # Модуль парсера данных
│   │   └── deploy/                     # Файлы для развёртывания
│   │       └── deploy_yc_function.sh   # Скрипт для развёртывания в Яндекс.Облаке
│   │   └── function/                   # Логика функции Яндекс.Облака
│   │       └── requirements.txt        # Зависимости для функции
│   ├── schemas/                        # Pydantic-схемы
│   │   └── schemas.py                  # Логика схем и валидации
│   ├── Dockerfile                      # Dockerfile приложения FastAPI
│   ├── main.py                         # Основной файл с маршрутизатором
├── .env                                # Переменные окружения
├── .gitignore                          # Игнорируемые файлы
├── docker-compose.yml                  # Конфигурация Docker Compose
└── README.md                           # Документация проекта
├── requirements.txt                    # Зависимости Python для проекта
```

## Запуск

### 1. Клонируйте репозиторий и перейдите в директорию проекта:

```bash
git clone https://https://github.com/KirillShapovalov/fastapi_parser
cd fastapi_parser
```

### 2. Создайте файл `.env` в корне проекта и укажите следующие переменные:

```
# PostgreSQL
PG_HOST=
PG_PORT=
PG_USER=
PG_PASSWORD=
PG_DB=

# Яндекс.Облако
YC_FOLDER_ID=
YC_FUNCTION_NAME=
YC_TRIGGER_NAME=
YC_SERVICE_ACCOUNT_ID=

# GitHub API (при наличии)
GITHUB_TOKEN=
```

### 3. Соберите и запустите Docker-контейнер:

```bash
docker-compose up --build
```

### 4. Выполните скрипт, создающий функцию парсера с триггером в Yandex.Cloud:

```bash
bash app/parser/deploy/deploy_yc_function.sh
```
Будет создана YC функция с определенным триггером (каждые 5 минут при наличии GITHUB_TOKEN, либо каждые 30 минут)

### 5. API будет доступно по адресу `http://localhost:8000`.

## Использование

1. Откройте документацию API по адресу `http://localhost:8000/docs`.
2. Выполните запросы:

- `GET /api/repos/top100`: Получение топ-100 репозиториев.
- `GET /api/repos/{owner}/{repo}/activity?since=date&until=date`: Получение активности конкретного репозитория за указанный временной промежуток.

На данный момент логика пасинга следующая - в таблицу top100 сохраняются данные о первых 100 публичных репозиториях из GitHub API, отсортированные по убыванию звезд.
При последующем парсинге в таблицу top100 происходит перезапись дублирующихся строк и заполнение поля position_prev.
При наличии данных в top100 берутся по каждой записи владелец и название репозитория и асинхронно запрашиваются данные по активности, сохраняясь в activity с указанием repo_id для связи с top100.