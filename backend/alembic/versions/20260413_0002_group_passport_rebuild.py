"""group passport rebuild

Revision ID: 20260413_0002
Revises: 20260411_0001
Create Date: 2026-04-13 12:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260413_0002"
down_revision: Union[str, None] = "20260411_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("student_assessments")
    op.drop_table("lessons")
    op.drop_table("students")
    op.drop_table("lesson_templates")
    op.drop_table("groups")
    op.drop_table("users")
    op.drop_table("assessment_criteria")
    op.drop_table("disciplines")
    op.drop_table("specialities")
    op.drop_table("roles")

    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "programs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("qualification", sa.String(length=255), nullable=False),
        sa.Column("education_form", sa.String(length=100), nullable=False),
        sa.Column("duration_text", sa.String(length=100), nullable=False),
        sa.Column("total_hours", sa.Integer(), nullable=True),
        sa.Column("gia_type", sa.String(length=255), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "control_forms",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("login", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("login"),
    )
    op.create_table(
        "groups",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("program_id", sa.Integer(), sa.ForeignKey("programs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("start_year", sa.Integer(), nullable=False),
        sa.Column("course_now", sa.Integer(), nullable=False),
        sa.Column("curator_name", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "students",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id", ondelete="CASCADE"), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_table(
        "semesters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id", ondelete="CASCADE"), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("course_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.UniqueConstraint("group_id", "number", name="uq_group_semester_number"),
    )
    op.create_table(
        "subjects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("program_id", sa.Integer(), sa.ForeignKey("programs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("block_type", sa.String(length=50), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.UniqueConstraint("program_id", "code", name="uq_program_subject_code"),
    )
    op.create_table(
        "curriculum_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id", ondelete="CASCADE"), nullable=False),
        sa.Column("semester_id", sa.Integer(), sa.ForeignKey("semesters.id", ondelete="CASCADE"), nullable=False),
        sa.Column("subject_id", sa.Integer(), sa.ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("control_form_id", sa.Integer(), sa.ForeignKey("control_forms.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("hours", sa.Integer(), nullable=True),
        sa.Column("is_practice", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("practice_type", sa.String(length=100), nullable=True),
        sa.Column("complex_group_code", sa.String(length=100), nullable=True),
        sa.Column("requires_manual_confirmation", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.UniqueConstraint("group_id", "semester_id", "subject_id", name="uq_group_semester_subject"),
    )
    op.create_table(
        "practice_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id", ondelete="CASCADE"), nullable=False),
        sa.Column("semester_id", sa.Integer(), sa.ForeignKey("semesters.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("practice_type", sa.String(length=100), nullable=False),
        sa.Column("weeks", sa.Integer(), nullable=True),
        sa.Column("hours", sa.Integer(), nullable=True),
        sa.Column("final_control_form_id", sa.Integer(), sa.ForeignKey("control_forms.id", ondelete="SET NULL"), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_table(
        "gia_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id", ondelete="CASCADE"), nullable=False),
        sa.Column("has_demo_exam", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("has_diploma_defense", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("total_weeks", sa.Integer(), nullable=True),
        sa.Column("preparation_weeks", sa.Integer(), nullable=True),
        sa.Column("defense_weeks", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.UniqueConstraint("group_id"),
    )
    op.create_table(
        "attendance_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("curriculum_item_id", sa.Integer(), sa.ForeignKey("curriculum_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.UniqueConstraint("student_id", "curriculum_item_id", "date", name="uq_attendance_per_day"),
    )
    op.create_table(
        "grade_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("curriculum_item_id", sa.Integer(), sa.ForeignKey("curriculum_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("grade_value", sa.String(length=50), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.UniqueConstraint("student_id", "curriculum_item_id", "date", name="uq_grade_per_day"),
    )
    op.create_table(
        "curator_group_links",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id", ondelete="CASCADE"), nullable=False),
        sa.UniqueConstraint("user_id", "group_id", name="uq_curator_group"),
    )
    op.create_table(
        "teacher_assignments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id", ondelete="CASCADE"), nullable=False),
        sa.Column("subject_id", sa.Integer(), sa.ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False),
        sa.UniqueConstraint("user_id", "group_id", "subject_id", name="uq_teacher_assignment"),
    )
    op.create_table(
        "student_account_links",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.UniqueConstraint("user_id", "student_id", name="uq_student_account"),
    )
    op.create_table(
        "parent_student_links",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.UniqueConstraint("user_id", "student_id", name="uq_parent_student"),
    )


def downgrade() -> None:
    op.drop_table("parent_student_links")
    op.drop_table("student_account_links")
    op.drop_table("teacher_assignments")
    op.drop_table("curator_group_links")
    op.drop_table("grade_records")
    op.drop_table("attendance_records")
    op.drop_table("gia_records")
    op.drop_table("practice_records")
    op.drop_table("curriculum_items")
    op.drop_table("subjects")
    op.drop_table("semesters")
    op.drop_table("students")
    op.drop_table("groups")
    op.drop_table("users")
    op.drop_table("control_forms")
    op.drop_table("programs")
    op.drop_table("roles")
