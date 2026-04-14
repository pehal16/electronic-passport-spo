"""attestation sheets module

Revision ID: 20260414_0004
Revises: 20260414_0003
Create Date: 2026-04-14 13:10:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260414_0004"
down_revision: Union[str, None] = "20260414_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("curriculum_items", sa.Column("statement_template_code", sa.String(length=50), nullable=True))
    op.add_column("curriculum_items", sa.Column("is_complex_exam", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("curriculum_items", sa.Column("requires_ticket_number", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("curriculum_items", sa.Column("examiner_count", sa.Integer(), nullable=False, server_default="1"))

    op.create_table(
        "sheet_templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("header_label_type", sa.String(length=50), nullable=False),
        sa.Column("has_ticket_number", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("has_multiple_disciplines", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("has_not_appeared_field", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("has_not_submitted_field", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("signature_lines_count", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("grade_text_mode", sa.String(length=30), nullable=False, server_default="full"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "attestation_sheets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id", ondelete="CASCADE"), nullable=False),
        sa.Column("semester_id", sa.Integer(), sa.ForeignKey("semesters.id", ondelete="SET NULL"), nullable=True),
        sa.Column("curriculum_item_id", sa.Integer(), sa.ForeignKey("curriculum_items.id", ondelete="SET NULL"), nullable=True),
        sa.Column("sheet_template_id", sa.Integer(), sa.ForeignKey("sheet_templates.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("control_form_code", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("teacher_name", sa.String(length=255), nullable=False),
        sa.Column("second_teacher_name", sa.String(length=255), nullable=True),
        sa.Column("header_label", sa.String(length=100), nullable=False),
        sa.Column("header_value", sa.String(length=255), nullable=False),
        sa.Column("discipline_display_text", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "attestation_sheet_disciplines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("attestation_sheet_id", sa.Integer(), sa.ForeignKey("attestation_sheets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("discipline_name", sa.String(length=255), nullable=False),
        sa.Column("discipline_code", sa.String(length=100), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="1"),
    )

    op.create_table(
        "attestation_sheet_rows",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("attestation_sheet_id", sa.Integer(), sa.ForeignKey("attestation_sheets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="SET NULL"), nullable=True),
        sa.Column("student_name_snapshot", sa.String(length=255), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("ticket_number", sa.String(length=50), nullable=True),
        sa.Column("grade_numeric", sa.String(length=20), nullable=True),
        sa.Column("grade_text", sa.String(length=100), nullable=True),
        sa.Column("attendance_result", sa.String(length=50), nullable=False, server_default="regular"),
        sa.Column("comment", sa.Text(), nullable=True),
    )

    op.create_table(
        "print_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("attestation_sheet_id", sa.Integer(), sa.ForeignKey("attestation_sheets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("html_snapshot", sa.Text(), nullable=False),
        sa.Column("pdf_path", sa.String(length=500), nullable=True),
        sa.Column("docx_path", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("print_snapshots")
    op.drop_table("attestation_sheet_rows")
    op.drop_table("attestation_sheet_disciplines")
    op.drop_table("attestation_sheets")
    op.drop_table("sheet_templates")

    op.drop_column("curriculum_items", "examiner_count")
    op.drop_column("curriculum_items", "requires_ticket_number")
    op.drop_column("curriculum_items", "is_complex_exam")
    op.drop_column("curriculum_items", "statement_template_code")

