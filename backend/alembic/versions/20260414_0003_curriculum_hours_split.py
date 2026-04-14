"""add curriculum contact/practice hours

Revision ID: 20260414_0003
Revises: 20260413_0002
Create Date: 2026-04-14 11:30:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260414_0003"
down_revision: Union[str, None] = "20260413_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("curriculum_items", sa.Column("contact_hours", sa.Integer(), nullable=True))
    op.add_column("curriculum_items", sa.Column("practice_hours", sa.Integer(), nullable=True))

    op.execute(
        sa.text(
            """
            UPDATE curriculum_items
            SET
                contact_hours = CASE WHEN is_practice = false THEN hours ELSE contact_hours END,
                practice_hours = CASE WHEN is_practice = true THEN hours ELSE practice_hours END
            """
        )
    )


def downgrade() -> None:
    op.drop_column("curriculum_items", "practice_hours")
    op.drop_column("curriculum_items", "contact_hours")

