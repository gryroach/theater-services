FROM python:3.12

WORKDIR /opt/app

RUN apt-get update \
  && apt-get install -y gettext \
  && pip install --upgrade pip \
  && apt-get install --no-install-recommends -y build-essential \
  pkg-config \
  && pip install poetry

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN  mkdir -p /var/www/static/ \
  && mkdir -p /var/www/media/ \
  && mkdir -p /opt/app/static/ \
  && mkdir -p /opt/app/media/

COPY django-entrypoint.sh django-entrypoint.sh

COPY poetry.lock pyproject.toml ./
RUN POETRY_VIRTUALENVS_CREATE=false poetry install --no-interaction --no-ansi --no-root

COPY . .

EXPOSE 8000

ENTRYPOINT ["bash", "django-entrypoint.sh"]
