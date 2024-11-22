# Сервисы онлайн-кинотеатра

### Основные сервисы
- админка
- etl-сервис переноса данных из postgres в elasticsearch
- api-сервис

Все взаимодействие с сервисами происходит через NGINX через 80-й порт.

## Запуск проекта

### Подготовка

1. Создайте файл `.env` на основе `.env.example`:
```shell
cp .env.example .env
```
2. Измените в этом файле переменные окружения, если это необходимо:
```shell
nano ./src/.env
```

### Запуск docker-compose через make

#### Запуск всех контейнеров
```shell
make run-all
```

#### Запуск асинхронного API
```shell
make run-api
```
Адрес документации API - `http://127.0.0.1/api/openapi`

#### Запуск админки
```shell
make run-admin
```
Адрес админки - `http://127.0.0.1/admin`

API базы - `http://127.0.0.1/admin_api/v1/`

#### Запуск сервиса переноса данных из БД в Elasticsearch
```shell
make run-etl
```

#### Остановка и удаление всех контейнеров
```shell
make down
```

## Тестирование

### Тестирование API

1. Создайте файл `.env.tests` на основе `.env.tests.example`:
```shell
cp .env.tests.example ./theater-async-api/tests/functional/.env.tests
```
2. Измените в этом файле переменные окружения, если это необходимо (например, при локальном тестировании):
```shell
nano ./theater-async-api/tests/functional/.env.tests
```

3. Запуск функциональных тестов

- через docker-compose с запуском и остановкой вспомогательных сервисов: 
```shell
make run-functional-tests
```

- через виртуальное окружение (предварительно запустите вспомогательные сервисы):
```shell
virtualenv --python=python3.12 theater-async-api/tests/functional/.venv
```

```shell
source theater-async-api/tests/functional/.venv/bin/activate
```

```shell
pip install -r theater-async-api/tests/functional/requirements.txt
```

```shell
pytest theater-async-api/tests/functional/src
```

