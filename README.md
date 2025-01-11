# Сервисы онлайн-кинотеатра

### Основные сервисы
- админка
- etl-сервис переноса данных из postgres в elasticsearch
- api-сервис
- сервис авторизации

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

#### Запуск API сервиса фильмов
```shell
make run-api
```
Адрес документации API - `http://127.0.0.1/api/openapi`

#### Запуск API сервиса авторизации
```shell
make run-auth
```
Адрес документации API - `http://127.0.0.1/api-auth/openapi`


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

### Тестирование API сервиса фильмов

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

### Тестирование API сервиса авторизации
Запуск через докер (предварительно запустите сервисы `db-auth` и `redis-auth`):
```shell
make run-auth-tests
```

Также можно протестировать привязку социальной сети к аккаунту. Для этого есть отдельный скрипт,
чтобы можно было проверить редирект в браузере и при этом быть авторизованным.

- Запустите сервис авторизации
```shell
make run-auth
```
- Пройдите аутентификацию через запрос по адресу `https://127.0.0.1/api-auth/v1/auth/login`
- Скопируйте access-токен
- Измените скрипт `theater-auth/src/tests/link_social_network_test.py` и запустите его.

