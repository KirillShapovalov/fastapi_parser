#!/bin/bash

# путь к корню
PROJECT_DIR="$(cd "$(dirname "$0")/../../.." || exit; pwd)"
if [ -z "$PROJECT_DIR" ]; then
  echo "Could not locate project directory!"
  exit 1
fi

ENV_FILE="$PROJECT_DIR/.env"  # путь к общему .env файлу
if [ -f "$ENV_FILE" ]; then
    while IFS= read -r line || [ -n "$line" ]; do
        # пропускаем комментарии и пустые строки
        if [[ ! "$line" =~ ^#.* && -n "$line" ]]; then
            # разделяем строку на имя переменной и её значение
            if [[ "$line" =~ ^([^=]+)=(.*)$ ]]; then
                VAR_NAME="${BASH_REMATCH[1]}"
                VAR_VALUE="${BASH_REMATCH[2]}"
                # экспортируем переменную
                export "$VAR_NAME=$VAR_VALUE"
            fi
        fi
    done < "$ENV_FILE"
else
    echo ".env file not found"
    exit 1
fi

FUNCTION_DIRECTORY="$PROJECT_DIR/app/parser/function"
if [ ! -d "$FUNCTION_DIRECTORY" ]; then
  echo "function directory not found!"
  exit 1
fi

REQUIREMENTS_FILE="$PROJECT_DIR/app/parser/requirements.txt"
if [ ! -f "$REQUIREMENTS_FILE" ]; then
  echo "requirements file not found!"
  exit 1
fi

# функция для проверки наличия переменной
check_env_var() {
    VAR_NAME=$1
    if [[ -z "${!VAR_NAME}" ]]; then
        echo "Ошибка: Переменная окружения $VAR_NAME не задана. Проверьте файл .env."
        exit 1
    fi
}

REQUIRED_VARS=("PG_HOST" "PG_PORT" "PG_USER" "PG_PASSWORD" "PG_DB" "YC_FOLDER_ID" "YC_FUNCTION_NAME" "YC_TRIGGER_NAME" "YC_SERVICE_ACCOUNT_ID")

for VAR in "${REQUIRED_VARS[@]}"; do
    check_env_var "$VAR"
done

FOLDER_ID=$YC_FOLDER_ID
FUNCTION_NAME=$YC_FUNCTION_NAME
TRIGGER_NAME=$YC_TRIGGER_NAME
SERVICE_ACCOUNT_ID=$YC_SERVICE_ACCOUNT_ID
PG_HOST=$PG_HOST
PG_PORT=$PG_PORT
PG_USER=$PG_USER
PG_PASSWORD=$PG_PASSWORD
PG_DB=$PG_DB
GITHUB_TOKEN=$GITHUB_TOKEN

# проверяем наличие GITHUB_TOKEN
if [[ -z "$GITHUB_TOKEN" ]]; then
  # если токен отсутствует, задаём менее частую периодичность
  CRON_SCHEDULE="0,30 * * * ? *" # каждые 30 минут
  echo "GITHUB_TOKEN not found. Setting CRON_SCHEDULE to '$CRON_SCHEDULE'."
else
  # если токен есть, задаём более частую периодичность
  CRON_SCHEDULE="*/5 * * * ? *" # каждые 5 минут
  echo "GITHUB_TOKEN found. Setting CRON_SCHEDULE to '$CRON_SCHEDULE'."
fi

# создание версии
yc serverless function create --name "$FUNCTION_NAME" --folder-id "$FOLDER_ID" --impersonate-service-account-id "$SERVICE_ACCOUNT_ID"
mkdir -p package
cp -r "$FUNCTION_DIRECTORY" "$REQUIREMENTS_FILE" package/
cd package || exit
zip -r function.zip .
cd ..

# создание версии функции
yc serverless function version create \
  --function-name "$FUNCTION_NAME" \
  --runtime python312 \
  --entrypoint function.main.handler \
  --memory 128m \
  --execution-timeout 60s \
  --service-account-id "$SERVICE_ACCOUNT_ID" \
  --source-path package/function.zip \
  --environment PG_HOST="$PG_HOST",PG_PORT="$PG_PORT",PG_USER="$PG_USER",PG_PASSWORD="$PG_PASSWORD",PG_DB="$PG_DB",GITHUB_TOKEN="$GITHUB_TOKEN"

# отключение требования роли serverless.functions.invoker
yc serverless function allow-unauthenticated-invoke --name "$FUNCTION_NAME"

# создание триггера
yc serverless trigger create timer \
  --name "$TRIGGER_NAME" \
  --cron-expression "$CRON_SCHEDULE" \
  --invoke-function-name "$FUNCTION_NAME"

echo "Function and trigger created successfully."
