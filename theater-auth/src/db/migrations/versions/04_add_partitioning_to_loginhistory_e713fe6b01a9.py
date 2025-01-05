"""04_add partitioning to loginhistory

Revision ID: e713fe6b01a9
Revises: f7751ffad0be
Create Date: 2025-01-05 18:27:35.851914

"""

import datetime
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e713fe6b01a9"
down_revision: Union[str, None] = "f7751ffad0be"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE loginhistory_new (
            id UUID NOT NULL,
            user_id UUID NOT NULL,
            ip_address VARCHAR(50),
            user_agent VARCHAR(255),
            login_time TIMESTAMP DEFAULT now(),
            partition_date DATE NOT NULL,
            PRIMARY KEY (partition_date, id),
            FOREIGN KEY (user_id) REFERENCES "user"(id)
        ) PARTITION BY RANGE (partition_date);
    """
    )

    start_date = datetime.date(2024, 1, 1)
    end_date = datetime.date(2026, 1, 1)

    current_date = start_date
    while current_date < end_date:
        partition_name = (
            f"loginhistory_p{current_date.year}_{current_date.month:02d}"
        )

        next_month = current_date.replace(day=28) + datetime.timedelta(days=4)
        partition_end_date = next_month.replace(day=1)

        op.execute(
            f"""
            CREATE TABLE {partition_name} PARTITION OF loginhistory_new
            FOR VALUES FROM ('{current_date}') TO ('{partition_end_date}');
        """
        )

        current_date = partition_end_date

    op.execute(
        """
        INSERT INTO loginhistory_new (id, user_id, ip_address, user_agent, login_time, partition_date)
        SELECT id, user_id, ip_address, user_agent, login_time, login_time::DATE AS partition_date
        FROM loginhistory;
    """
    )

    op.drop_table("loginhistory")

    op.execute("ALTER TABLE loginhistory_new RENAME TO loginhistory;")


def downgrade() -> None:
    op.create_table(
        "loginhistory",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("ip_address", sa.String(length=50), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("login_time", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.execute(
        """
        INSERT INTO loginhistory (id, user_id, ip_address, user_agent, login_time)
        SELECT id, user_id, ip_address, user_agent, login_time
        FROM loginhistory_new;
    """
    )

    op.execute("DROP TABLE loginhistory_new;")
