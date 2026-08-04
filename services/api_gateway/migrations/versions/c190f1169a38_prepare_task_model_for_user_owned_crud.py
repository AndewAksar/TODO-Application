"""prepare task model for user owned CRUD

Revision ID: c190f1169a38
Revises: 9a3b9f28e495
Create Date: 2026-07-30 22:02:28.617613

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c190f1169a38"
down_revision: str | Sequence[str] | None = "9a3b9f28e495"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade database schema and data."""
    # The old composite index is not required by the current CRUD queries.
    # Drop it before renaming the indexed column.
    op.drop_index(
        "ix_tasks_user_id_done",
        table_name="tasks",
    )

    # Preserve all existing status values by renaming the column instead of
    # dropping `done` and creating a new `is_done` column.
    op.alter_column(
        "tasks",
        "done",
        existing_type=sa.Boolean(),
        existing_nullable=False,
        existing_server_default=sa.text("false"),
        new_column_name="is_done",
    )

    op.add_column(
        "tasks",
        sa.Column(
            "done_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "tasks",
        sa.Column(
            "due_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    # server_default is required so existing rows receive a non-NULL value.
    op.add_column(
        "tasks",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.alter_column(
        "tasks",
        "description",
        existing_type=sa.Text(),
        existing_nullable=False,
        nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    # The old schema does not allow NULL descriptions. Normalize values before
    # restoring the NOT NULL constraint.
    op.execute(
        sa.text(
            """
            UPDATE tasks
            SET description = ''
            WHERE description IS NULL
            """
        )
    )

    op.alter_column(
        "tasks",
        "description",
        existing_type=sa.Text(),
        existing_nullable=True,
        nullable=False,
    )

    op.drop_column("tasks", "updated_at")
    op.drop_column("tasks", "due_at")
    op.drop_column("tasks", "done_at")

    # Rename the status column back, preserving its values.
    op.alter_column(
        "tasks",
        "is_done",
        existing_type=sa.Boolean(),
        existing_nullable=False,
        existing_server_default=sa.text("false"),
        new_column_name="done",
    )

    op.create_index(
        "ix_tasks_user_id_done",
        "tasks",
        ["user_id", "done"],
        unique=False,
    )
