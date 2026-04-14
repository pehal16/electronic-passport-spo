from datetime import date

from pydantic import BaseModel, ConfigDict

from app.schemas.auth import UserRead


class ProgramRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    title: str
    qualification: str
    education_form: str
    duration_text: str
    total_hours: int | None
    gia_type: str
    notes: str | None


class GroupRead(BaseModel):
    id: int
    name: str
    start_year: int
    course_now: int
    curator_name: str | None
    notes: str | None
    program: ProgramRead
    student_count: int
    semester_count: int
    exams_count: int
    dz_count: int
    kdz_count: int
    has_kdz: bool
    practices_count: int
    has_practices: bool


class SemesterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    number: int
    course_number: int
    title: str
    notes: str | None


class ControlFormRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    title: str


class SubjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    title: str
    block_type: str
    notes: str | None


class CurriculumItemRead(BaseModel):
    id: int
    code: str
    title: str
    semester_id: int
    semester_number: int
    semester_title: str
    cycle_key: str
    cycle_title: str
    total_hours: int | None
    contact_hours: int | None
    practice_hours: int | None
    control_form_code: str
    control_form_title: str
    is_practice: bool
    practice_type: str | None
    complex_group_code: str | None
    requires_manual_confirmation: bool
    notes: str | None
    subject: SubjectRead
    control_form: ControlFormRead


class SemesterSummaryRead(BaseModel):
    discipline_count: int
    total_hours: int
    practice_hours: int
    exam_count: int
    dz_count: int
    kdz_count: int
    practice_count: int
    control_forms_count: int


class SemesterCurriculumRead(SemesterRead):
    summary: SemesterSummaryRead
    items: list[CurriculumItemRead]


class CurriculumBlockRead(BaseModel):
    key: str
    title: str
    items: list[CurriculumItemRead]


class PracticeRead(BaseModel):
    id: int
    title: str
    practice_type: str
    weeks: int | None
    hours: int | None
    notes: str | None
    semester: SemesterRead | None
    final_control_form: ControlFormRead | None
    related_module: str | None
    complex_group_code: str | None
    outcome_text: str | None


class GiaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    has_demo_exam: bool
    has_diploma_defense: bool
    total_weeks: int | None
    preparation_weeks: int | None
    defense_weeks: int | None
    notes: str | None


class GroupSummaryStatsRead(BaseModel):
    students_total: int
    disciplines_total: int
    exams_total: int
    dz_total: int
    kdz_total: int
    practices_total: int
    gia_form: str


class GroupDetailRead(BaseModel):
    group: GroupRead
    semesters: list[SemesterRead]
    practices: list[PracticeRead]
    gia: GiaRead | None
    control_counts: dict[str, int]
    block_counts: dict[str, int]
    summary: GroupSummaryStatsRead


class CurriculumOverviewRead(BaseModel):
    group: GroupRead
    semesters: list[SemesterCurriculumRead]
    grouped_items: dict[str, list[CurriculumItemRead]]
    complex_groups: dict[str, list[CurriculumItemRead]]
    blocks: list[CurriculumBlockRead]


class StudentListItem(BaseModel):
    id: int
    full_name: str
    status: str
    notes: str | None
    group_name: str
    course_now: int
    grade_count: int
    absence_count: int


class AttendanceRead(BaseModel):
    id: int
    date: date
    student_id: int
    student_name: str
    status: str
    status_title: str
    reason: str | None
    curriculum_item_id: int
    curriculum_item_title: str
    group_name: str


class GradeRead(BaseModel):
    id: int
    date: date
    student_id: int
    student_name: str
    grade_value: str
    comment: str | None
    curriculum_item_id: int
    curriculum_item_title: str
    group_name: str


class StudentDetailRead(BaseModel):
    id: int
    full_name: str
    status: str
    notes: str | None
    group: GroupRead
    attendance: list[AttendanceRead]
    grades: list[GradeRead]
    current_subjects: list[str]
    practices: list[PracticeRead]
    gia_text: str | None


class DashboardStat(BaseModel):
    label: str
    value: str
    hint: str


class DashboardQuickLink(BaseModel):
    label: str
    href: str


class DashboardRead(BaseModel):
    role_code: str
    role_title: str
    user: UserRead
    stats: list[DashboardStat]
    alerts: list[str]
    quick_links: list[DashboardQuickLink]
    groups_in_work: list[str]
    attention_items: list[str]


class JournalRow(BaseModel):
    curriculum_item_id: int
    group_id: int
    group_name: str
    semester_id: int
    semester_number: int
    semester_title: str
    subject_id: int
    subject_code: str
    subject_title: str
    cycle_title: str
    total_hours: int | None
    control_form_code: str
    control_form_title: str
    student_count: int
    grades_count: int
    attendance_count: int
    has_grades: bool
    has_attendance: bool


class JournalSubjectStudentRead(BaseModel):
    student_id: int
    full_name: str
    last_grade: str | None
    grades_count: int
    attended_count: int
    absent_count: int
    excused_count: int
    late_count: int
    last_comment: str | None


class JournalSubjectRead(BaseModel):
    curriculum_item_id: int
    group_name: str
    semester_title: str
    subject_code: str
    subject_title: str
    control_form_title: str
    students: list[JournalSubjectStudentRead]


class AttendanceUpsert(BaseModel):
    student_id: int
    curriculum_item_id: int
    date: date
    status: str
    reason: str | None = None


class AttendanceBulkEntry(BaseModel):
    student_id: int
    status: str
    reason: str | None = None


class AttendanceBulkUpsert(BaseModel):
    curriculum_item_id: int
    date: date
    entries: list[AttendanceBulkEntry]


class GradeUpsert(BaseModel):
    student_id: int
    curriculum_item_id: int
    date: date
    grade_value: str
    comment: str | None = None


class GradeBulkEntry(BaseModel):
    student_id: int
    grade_value: str
    comment: str | None = None


class GradeBulkUpsert(BaseModel):
    curriculum_item_id: int
    date: date
    entries: list[GradeBulkEntry]


class MessageRead(BaseModel):
    message: str


class AdminUsersRead(BaseModel):
    users: list[UserRead]


class ProgramStructureRead(BaseModel):
    program_id: int
    code: str
    title: str
    qualification: str
    education_form: str
    duration_text: str
    gia_type: str
    total_hours: int | None
    practices: list[str]
    control_forms: list[str]
    key_modules: list[str]
    notes: str | None


class AdminProgramsRead(BaseModel):
    programs: list[ProgramRead]
    control_forms: list[ControlFormRead]
    structures: list[ProgramStructureRead]
