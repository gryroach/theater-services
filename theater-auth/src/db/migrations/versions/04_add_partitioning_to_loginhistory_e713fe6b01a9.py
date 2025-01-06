"""04_add partitioning to loginhistory

Revision ID: e713fe6b01a9
Revises: f7751ffad0be
Create Date: 2025-01-05 18:27:35.851914

"""

import datetime
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from dateutil.relativedelta import relativedelta

# revision identifiers, used by Alembic.
revision: str = "e713fe6b01a9"
down_revision: Union[str, None] = "f7751ffad0be"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Шаг 1: Переименовываем существующую таблицу
    op.execute("ALTER TABLE loginhistory RENAME TO loginhistory_old;")

    # Шаг 2: Создаем новую таблицу с партиционированием
    op.execute(
        """
        CREATE TABLE loginhistory (
            id UUID NOT NULL,
            user_id UUID NOT NULL,
            ip_address VARCHAR(50),
            user_agent VARCHAR(255),
            login_time TIMESTAMP NOT NULL,
            PRIMARY KEY (login_time, id),
            FOREIGN KEY (user_id) REFERENCES "user"(id)
        ) PARTITION BY RANGE (login_time);
    """
    )

    # Шаг 3: Создаем партиции по месяцам
    start_date = datetime.datetime(2020, 1, 1)  # Начало периода
    end_date = datetime.datetime(2030, 1, 1)  # Конец периода

    current_date = start_date
    while current_date < end_date:
        next_month = current_date + relativedelta(months=1)
        partition_name = (
            f"loginhistory_p{current_date.year}_{current_date.month:02}"
        )

        op.execute(
            f"""
            CREATE TABLE {partition_name} PARTITION OF loginhistory
            FOR VALUES FROM ('{current_date.strftime('%Y-%m-%d')}') TO ('{next_month.strftime('%Y-%m-%d')}');
        """
        )
        current_date = next_month

    # Шаг 4: Перенос данных из старой таблицы в новую
    op.execute(
        """
        INSERT INTO loginhistory (id, user_id, ip_address, user_agent, login_time)
        SELECT id, user_id, ip_address, user_agent, login_time
        FROM loginhistory_old;
    """
    )

    # Шаг 5: Удаляем старую таблицу
    op.drop_table("loginhistory_old")


def downgrade() -> None:
    # Шаг 1: Создаем старую таблицу без партиционирования
    op.create_table(
        "loginhistory_old",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("ip_address", sa.String(length=50), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("login_time", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Шаг 2: Переносим данные обратно
    op.execute(
        """
        INSERT INTO loginhistory_old (id, user_id, ip_address, user_agent, login_time)
        SELECT id, user_id, ip_address, user_agent, login_time
        FROM loginhistory;
    """
    )

    # Шаг 3: Удаляем партиционированную таблицу
    op.execute("DROP TABLE loginhistory CASCADE;")

    # Шаг 4: Переименовываем старую таблицу обратно
    op.execute("ALTER TABLE loginhistory_old RENAME TO loginhistory;")
