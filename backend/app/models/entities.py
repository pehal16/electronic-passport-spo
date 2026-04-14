from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

BLOCK_TYPES = (
    "school",
    "social_humanitarian",
    "natural_science",
    "professional_general",
    "professional_module",
    "mdk",
    "practice",
    "gia",
)


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="role")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    login: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    role: Mapped["Role"] = relationship(back_populates="users")
    curator_groups: Mapped[list["CuratorGroupLink"]] = relationship(back_populates="user")
    teacher_assignments: Mapped[list["TeacherAssignment"]] = relationship(back_populates="user")
    student_links: Mapped[list["StudentAccountLink"]] = relationship(back_populates="user")
    parent_links: Mapped[list["ParentStudentLink"]] = relationship(back_populates="user")


class Program(Base):
    __tablename__ = "programs"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    qualification: Mapped[str] = mapped_column(String(255), nullable=False)
    education_form: Mapped[str] = mapped_column(String(100), nullable=False)
    duration_text: Mapped[str] = mapped_column(String(100), nullable=False)
    total_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gia_type: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    groups: Mapped[list["Group"]] = relationship(back_populates="program")
    subjects: Mapped[list["Subject"]] = relationship(back_populates="program")


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    program_id: Mapped[int] = mapped_column(
        ForeignKey("programs.id", ondelete="CASCADE"),
        nullable=False,
    )
    start_year: Mapped[int] = mapped_column(Integer, nullable=False)
    course_now: Mapped[int] = mapped_column(Integer, nullable=False)
    curator_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    program: Mapped["Program"] = relationship(back_populates="groups")
    students: Mapped[list["Student"]] = relationship(back_populates="group")
    semesters: Mapped[list["Semester"]] = relationship(
        back_populates="group",
        order_by="Semester.number",
    )
    curriculum_items: Mapped[list["CurriculumItem"]] = relationship(back_populates="group")
    practices: Mapped[list["PracticeRecord"]] = relationship(back_populates="group")
    gia_record: Mapped["GiaRecord | None"] = relationship(back_populates="group", uselist=False)
    curator_links: Mapped[list["CuratorGroupLink"]] = relationship(back_populates="group")
    teacher_assignments: Mapped[list["TeacherAssignment"]] = relationship(back_populates="group")
    attestation_sheets: Mapped[list["AttestationSheet"]] = relationship(back_populates="group")


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="active",
        server_default="active",
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    group: Mapped["Group"] = relationship(back_populates="students")
    attendance_records: Mapped[list["AttendanceRecord"]] = relationship(back_populates="student")
    grade_records: Mapped[list["GradeRecord"]] = relationship(back_populates="student")
    account_links: Mapped[list["StudentAccountLink"]] = relationship(back_populates="student")
    parent_links: Mapped[list["ParentStudentLink"]] = relationship(back_populates="student")


class Semester(Base):
    __tablename__ = "semesters"
    __table_args__ = (UniqueConstraint("group_id", "number", name="uq_group_semester_number"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
    )
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    course_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    group: Mapped["Group"] = relationship(back_populates="semesters")
    curriculum_items: Mapped[list["CurriculumItem"]] = relationship(
        back_populates="semester",
        order_by="CurriculumItem.id",
    )
    practices: Mapped[list["PracticeRecord"]] = relationship(back_populates="semester")
    attestation_sheets: Mapped[list["AttestationSheet"]] = relationship(back_populates="semester")


class Subject(Base):
    __tablename__ = "subjects"
    __table_args__ = (UniqueConstraint("program_id", "code", name="uq_program_subject_code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    program_id: Mapped[int] = mapped_column(
        ForeignKey("programs.id", ondelete="CASCADE"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    block_type: Mapped[str] = mapped_column(String(50), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    program: Mapped["Program"] = relationship(back_populates="subjects")
    curriculum_items: Mapped[list["CurriculumItem"]] = relationship(back_populates="subject")
    teacher_assignments: Mapped[list["TeacherAssignment"]] = relationship(back_populates="subject")


class ControlForm(Base):
    __tablename__ = "control_forms"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)

    curriculum_items: Mapped[list["CurriculumItem"]] = relationship(back_populates="control_form")
    practice_records: Mapped[list["PracticeRecord"]] = relationship(back_populates="final_control_form")


class CurriculumItem(Base):
    __tablename__ = "curriculum_items"
    __table_args__ = (
        UniqueConstraint(
            "group_id",
            "semester_id",
            "subject_id",
            name="uq_group_semester_subject",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
    )
    semester_id: Mapped[int] = mapped_column(
        ForeignKey("semesters.id", ondelete="CASCADE"),
        nullable=False,
    )
    subject_id: Mapped[int] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
    )
    control_form_id: Mapped[int] = mapped_column(
        ForeignKey("control_forms.id", ondelete="RESTRICT"),
        nullable=False,
    )
    hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    contact_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    practice_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_practice: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    practice_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    complex_group_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    statement_template_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_complex_exam: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    requires_ticket_number: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    examiner_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )
    requires_manual_confirmation: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    group: Mapped["Group"] = relationship(back_populates="curriculum_items")
    semester: Mapped["Semester"] = relationship(back_populates="curriculum_items")
    subject: Mapped["Subject"] = relationship(back_populates="curriculum_items")
    control_form: Mapped["ControlForm"] = relationship(back_populates="curriculum_items")
    attendance_records: Mapped[list["AttendanceRecord"]] = relationship(back_populates="curriculum_item")
    grade_records: Mapped[list["GradeRecord"]] = relationship(back_populates="curriculum_item")
    attestation_sheets: Mapped[list["AttestationSheet"]] = relationship(back_populates="curriculum_item")


class PracticeRecord(Base):
    __tablename__ = "practice_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
    )
    semester_id: Mapped[int | None] = mapped_column(
        ForeignKey("semesters.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    practice_type: Mapped[str] = mapped_column(String(100), nullable=False)
    weeks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    final_control_form_id: Mapped[int | None] = mapped_column(
        ForeignKey("control_forms.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    group: Mapped["Group"] = relationship(back_populates="practices")
    semester: Mapped["Semester | None"] = relationship(back_populates="practices")
    final_control_form: Mapped["ControlForm | None"] = relationship(back_populates="practice_records")


class GiaRecord(Base):
    __tablename__ = "gia_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    has_demo_exam: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    has_diploma_defense: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    total_weeks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    preparation_weeks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    defense_weeks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    group: Mapped["Group"] = relationship(back_populates="gia_record")


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "curriculum_item_id",
            "date",
            name="uq_attendance_per_day",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
    )
    curriculum_item_id: Mapped[int] = mapped_column(
        ForeignKey("curriculum_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    student: Mapped["Student"] = relationship(back_populates="attendance_records")
    curriculum_item: Mapped["CurriculumItem"] = relationship(back_populates="attendance_records")


class GradeRecord(Base):
    __tablename__ = "grade_records"
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "curriculum_item_id",
            "date",
            name="uq_grade_per_day",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
    )
    curriculum_item_id: Mapped[int] = mapped_column(
        ForeignKey("curriculum_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    grade_value: Mapped[str] = mapped_column(String(50), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    student: Mapped["Student"] = relationship(back_populates="grade_records")
    curriculum_item: Mapped["CurriculumItem"] = relationship(back_populates="grade_records")


class SheetTemplate(Base):
    __tablename__ = "sheet_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    header_label_type: Mapped[str] = mapped_column(String(50), nullable=False)
    has_ticket_number: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    has_multiple_disciplines: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    has_not_appeared_field: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    has_not_submitted_field: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    signature_lines_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=2,
        server_default="2",
    )
    grade_text_mode: Mapped[str] = mapped_column(String(30), nullable=False, default="full", server_default="full")
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    attestation_sheets: Mapped[list["AttestationSheet"]] = relationship(back_populates="sheet_template")


class AttestationSheet(Base):
    __tablename__ = "attestation_sheets"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    semester_id: Mapped[int | None] = mapped_column(ForeignKey("semesters.id", ondelete="SET NULL"), nullable=True)
    curriculum_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("curriculum_items.id", ondelete="SET NULL"),
        nullable=True,
    )
    sheet_template_id: Mapped[int] = mapped_column(ForeignKey("sheet_templates.id", ondelete="RESTRICT"), nullable=False)
    control_form_code: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    teacher_name: Mapped[str] = mapped_column(String(255), nullable=False)
    second_teacher_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    header_label: Mapped[str] = mapped_column(String(100), nullable=False)
    header_value: Mapped[str] = mapped_column(String(255), nullable=False)
    discipline_display_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", server_default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    group: Mapped["Group"] = relationship(back_populates="attestation_sheets")
    semester: Mapped["Semester | None"] = relationship(back_populates="attestation_sheets")
    curriculum_item: Mapped["CurriculumItem | None"] = relationship(back_populates="attestation_sheets")
    sheet_template: Mapped["SheetTemplate"] = relationship(back_populates="attestation_sheets")
    disciplines: Mapped[list["AttestationSheetDiscipline"]] = relationship(
        back_populates="attestation_sheet",
        cascade="all, delete-orphan",
        order_by="AttestationSheetDiscipline.order_index",
    )
    rows: Mapped[list["AttestationSheetRow"]] = relationship(
        back_populates="attestation_sheet",
        cascade="all, delete-orphan",
        order_by="AttestationSheetRow.row_number",
    )
    print_snapshots: Mapped[list["PrintSnapshot"]] = relationship(
        back_populates="attestation_sheet",
        cascade="all, delete-orphan",
        order_by="PrintSnapshot.created_at",
    )


class AttestationSheetDiscipline(Base):
    __tablename__ = "attestation_sheet_disciplines"

    id: Mapped[int] = mapped_column(primary_key=True)
    attestation_sheet_id: Mapped[int] = mapped_column(
        ForeignKey("attestation_sheets.id", ondelete="CASCADE"),
        nullable=False,
    )
    discipline_name: Mapped[str] = mapped_column(String(255), nullable=False)
    discipline_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")

    attestation_sheet: Mapped["AttestationSheet"] = relationship(back_populates="disciplines")


class AttestationSheetRow(Base):
    __tablename__ = "attestation_sheet_rows"

    id: Mapped[int] = mapped_column(primary_key=True)
    attestation_sheet_id: Mapped[int] = mapped_column(
        ForeignKey("attestation_sheets.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_id: Mapped[int | None] = mapped_column(ForeignKey("students.id", ondelete="SET NULL"), nullable=True)
    student_name_snapshot: Mapped[str] = mapped_column(String(255), nullable=False)
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    ticket_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    grade_numeric: Mapped[str | None] = mapped_column(String(20), nullable=True)
    grade_text: Mapped[str | None] = mapped_column(String(100), nullable=True)
    attendance_result: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="regular",
        server_default="regular",
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    attestation_sheet: Mapped["AttestationSheet"] = relationship(back_populates="rows")


class PrintSnapshot(Base):
    __tablename__ = "print_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    attestation_sheet_id: Mapped[int] = mapped_column(
        ForeignKey("attestation_sheets.id", ondelete="CASCADE"),
        nullable=False,
    )
    html_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    pdf_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    docx_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    attestation_sheet: Mapped["AttestationSheet"] = relationship(back_populates="print_snapshots")


class CuratorGroupLink(Base):
    __tablename__ = "curator_group_links"
    __table_args__ = (UniqueConstraint("user_id", "group_id", name="uq_curator_group"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)

    user: Mapped["User"] = relationship(back_populates="curator_groups")
    group: Mapped["Group"] = relationship(back_populates="curator_links")


class TeacherAssignment(Base):
    __tablename__ = "teacher_assignments"
    __table_args__ = (
        UniqueConstraint("user_id", "group_id", "subject_id", name="uq_teacher_assignment"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)

    user: Mapped["User"] = relationship(back_populates="teacher_assignments")
    group: Mapped["Group"] = relationship(back_populates="teacher_assignments")
    subject: Mapped["Subject"] = relationship(back_populates="teacher_assignments")


class StudentAccountLink(Base):
    __tablename__ = "student_account_links"
    __table_args__ = (UniqueConstraint("user_id", "student_id", name="uq_student_account"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False)

    user: Mapped["User"] = relationship(back_populates="student_links")
    student: Mapped["Student"] = relationship(back_populates="account_links")


class ParentStudentLink(Base):
    __tablename__ = "parent_student_links"
    __table_args__ = (UniqueConstraint("user_id", "student_id", name="uq_parent_student"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False)

    user: Mapped["User"] = relationship(back_populates="parent_links")
    student: Mapped["Student"] = relationship(back_populates="parent_links")
