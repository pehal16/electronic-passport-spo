from __future__ import annotations

from collections import defaultdict

from app.models import AttendanceRecord, CurriculumItem, GiaRecord, GradeRecord, Group, PracticeRecord, Program, Semester, Student
from app.schemas.domain import (
    AttendanceRead,
    ControlFormRead,
    CurriculumBlockRead,
    CurriculumItemRead,
    CurriculumOverviewRead,
    GiaRead,
    GradeRead,
    GroupDetailRead,
    GroupRead,
    GroupSummaryStatsRead,
    PracticeRead,
    ProgramRead,
    SemesterCurriculumRead,
    SemesterRead,
    SemesterSummaryRead,
)

CYCLE_TITLE_MAP = {
    "school": "Общеобразовательный цикл",
    "social_humanitarian": "Социально-гуманитарный цикл",
    "natural_science": "Естественнонаучный цикл",
    "professional_general": "Общепрофессиональный цикл",
    "professional_module": "Профессиональные модули",
    "mdk": "МДК",
    "practice": "Практики",
    "gia": "ГИА",
}

ATTENDANCE_STATUS_MAP = {
    "present": "Присутствовал",
    "absent": "Отсутствовал",
    "late": "Опоздал",
    "excused": "Уважительная причина",
}

PRACTICE_LABELS = {
    "учебная": "Учебная практика",
    "производственная": "Производственная практика",
    "преддипломная": "Преддипломная практика",
}


def cycle_title(block_key: str) -> str:
    return CYCLE_TITLE_MAP.get(block_key, "Прочий раздел")


def attendance_status_title(status_code: str) -> str:
    return ATTENDANCE_STATUS_MAP.get(status_code, status_code)


def practice_type_title(value: str | None) -> str:
    if not value:
        return "Практика"
    return PRACTICE_LABELS.get(value, value.capitalize())


def serialize_program(program: Program) -> ProgramRead:
    return ProgramRead.model_validate(program)


def serialize_group(group: Group) -> GroupRead:
    exams_count = sum(1 for item in group.curriculum_items if item.control_form.code == "exam")
    dz_count = sum(1 for item in group.curriculum_items if item.control_form.code == "dz")
    kdz_count = sum(1 for item in group.curriculum_items if item.control_form.code == "kdz")
    practices_count = len(group.practices)

    return GroupRead(
        id=group.id,
        name=group.name,
        start_year=group.start_year,
        course_now=group.course_now,
        curator_name=group.curator_name,
        notes=group.notes,
        program=serialize_program(group.program),
        student_count=len(group.students),
        semester_count=len(group.semesters),
        exams_count=exams_count,
        dz_count=dz_count,
        kdz_count=kdz_count,
        has_kdz=kdz_count > 0,
        practices_count=practices_count,
        has_practices=practices_count > 0,
    )


def serialize_semester(semester: Semester) -> SemesterRead:
    return SemesterRead.model_validate(semester)


def serialize_curriculum_item(item: CurriculumItem) -> CurriculumItemRead:
    contact_hours = item.contact_hours
    practice_hours = item.practice_hours
    if contact_hours is None and practice_hours is None and item.hours is not None:
        if item.is_practice:
            practice_hours = item.hours
        else:
            contact_hours = item.hours

    total_hours = item.hours
    if total_hours is None and (contact_hours is not None or practice_hours is not None):
        total_hours = (contact_hours or 0) + (practice_hours or 0)

    return CurriculumItemRead(
        id=item.id,
        code=item.subject.code,
        title=item.subject.title,
        semester_id=item.semester_id,
        semester_number=item.semester.number,
        semester_title=item.semester.title,
        cycle_key=item.subject.block_type,
        cycle_title=cycle_title(item.subject.block_type),
        total_hours=total_hours,
        contact_hours=contact_hours,
        practice_hours=practice_hours,
        control_form_code=item.control_form.code,
        control_form_title=item.control_form.title,
        is_practice=item.is_practice,
        practice_type=item.practice_type,
        complex_group_code=item.complex_group_code,
        requires_manual_confirmation=item.requires_manual_confirmation,
        notes=item.notes,
        subject=item.subject,
        control_form=item.control_form,
    )


def _detect_practice_links(practice: PracticeRecord) -> tuple[str | None, str | None]:
    if not practice.group:
        return None, None
    related_items = [item for item in practice.group.curriculum_items if item.is_practice]
    if practice.semester_id is not None:
        related_items = [item for item in related_items if item.semester_id == practice.semester_id]

    key = practice.practice_type.lower()
    filtered = [item for item in related_items if (item.practice_type or "").lower() == key]
    target_items = filtered or related_items
    if not target_items:
        return None, None

    first_with_complex = next((item for item in target_items if item.complex_group_code), None)
    complex_group_code = first_with_complex.complex_group_code if first_with_complex else None
    module_item = next((item for item in target_items if item.subject.block_type == "professional_module"), None)
    related_module = module_item.subject.title if module_item else None
    return related_module, complex_group_code


def serialize_practice(practice: PracticeRecord) -> PracticeRead:
    if practice.practice_type == "преддипломная":
        outcome_text = "Допуск к ГИА"
    elif practice.final_control_form:
        outcome_text = practice.final_control_form.title
    else:
        outcome_text = None

    related_module, complex_group_code = _detect_practice_links(practice)
    title = practice.title
    if title.lower() in {"учебная практика", "производственная практика", "преддипломная практика"}:
        title = practice_type_title(practice.practice_type)

    return PracticeRead(
        id=practice.id,
        title=title,
        practice_type=practice.practice_type,
        weeks=practice.weeks,
        hours=practice.hours,
        notes=practice.notes,
        semester=serialize_semester(practice.semester) if practice.semester else None,
        final_control_form=ControlFormRead.model_validate(practice.final_control_form) if practice.final_control_form else None,
        related_module=related_module,
        complex_group_code=complex_group_code,
        outcome_text=outcome_text,
    )


def serialize_gia(gia: GiaRecord | None) -> GiaRead | None:
    return GiaRead.model_validate(gia) if gia else None


def build_group_detail(group: Group) -> GroupDetailRead:
    control_counts: dict[str, int] = defaultdict(int)
    block_counts: dict[str, int] = defaultdict(int)
    for item in group.curriculum_items:
        control_counts[item.control_form.code] += 1
        block_counts[item.subject.block_type] += 1

    summary = GroupSummaryStatsRead(
        students_total=len(group.students),
        disciplines_total=len(group.curriculum_items),
        exams_total=control_counts.get("exam", 0),
        dz_total=control_counts.get("dz", 0),
        kdz_total=control_counts.get("kdz", 0),
        practices_total=len(group.practices),
        gia_form=group.program.gia_type,
    )

    return GroupDetailRead(
        group=serialize_group(group),
        semesters=[serialize_semester(semester) for semester in group.semesters],
        practices=[serialize_practice(practice) for practice in group.practices],
        gia=serialize_gia(group.gia_record),
        control_counts=dict(control_counts),
        block_counts=dict(block_counts),
        summary=summary,
    )


def semester_summary(semester: Semester) -> SemesterSummaryRead:
    items = semester.curriculum_items
    total_hours = 0
    contact_hours = 0
    practice_hours = 0
    known_hours_items = 0
    missing_hours_items = 0

    for item in items:
        item_contact = item.contact_hours
        item_practice = item.practice_hours

        if item_contact is None and item_practice is None and item.hours is not None:
            if item.is_practice:
                item_practice = item.hours
            else:
                item_contact = item.hours

        has_item_hours = item.hours is not None or item_contact is not None or item_practice is not None
        if has_item_hours:
            known_hours_items += 1
        else:
            missing_hours_items += 1

        resolved_total = item.hours
        if resolved_total is None:
            resolved_total = (item_contact or 0) + (item_practice or 0)

        total_hours += resolved_total or 0
        contact_hours += item_contact or 0
        practice_hours += item_practice or 0

    exam_count = sum(1 for item in items if item.control_form.code == "exam")
    dz_count = sum(1 for item in items if item.control_form.code == "dz")
    kdz_count = sum(1 for item in items if item.control_form.code == "kdz")
    practice_count = sum(1 for item in items if item.is_practice)
    forms_count = len({item.control_form.code for item in items})

    return SemesterSummaryRead(
        discipline_count=len(items),
        total_hours=total_hours,
        contact_hours=contact_hours,
        practice_hours=practice_hours,
        known_hours_items=known_hours_items,
        missing_hours_items=missing_hours_items,
        exam_count=exam_count,
        dz_count=dz_count,
        kdz_count=kdz_count,
        practice_count=practice_count,
        control_forms_count=forms_count,
    )


def build_curriculum_overview(group: Group) -> CurriculumOverviewRead:
    semesters: list[SemesterCurriculumRead] = []
    grouped_items: dict[str, list[CurriculumItemRead]] = {
        "Экзамены": [],
        "Дифференцированные зачеты": [],
        "Комплексные дифференцированные зачеты": [],
        "Практики": [],
        "ГИА": [],
    }
    complex_groups: dict[str, list[CurriculumItemRead]] = defaultdict(list)
    block_map: dict[str, list[CurriculumItemRead]] = defaultdict(list)

    for semester in group.semesters:
        items = [serialize_curriculum_item(item) for item in semester.curriculum_items]
        semesters.append(
            SemesterCurriculumRead(
                **serialize_semester(semester).model_dump(),
                summary=semester_summary(semester),
                items=items,
            )
        )
        for serialized in items:
            block_map[serialized.cycle_key].append(serialized)
            if serialized.control_form_code == "exam":
                grouped_items["Экзамены"].append(serialized)
            elif serialized.control_form_code == "dz":
                grouped_items["Дифференцированные зачеты"].append(serialized)
            elif serialized.control_form_code == "kdz":
                grouped_items["Комплексные дифференцированные зачеты"].append(serialized)
            if serialized.is_practice:
                grouped_items["Практики"].append(serialized)
            if serialized.cycle_key == "gia":
                grouped_items["ГИА"].append(serialized)
            if serialized.complex_group_code:
                complex_groups[serialized.complex_group_code].append(serialized)

    blocks = [
        CurriculumBlockRead(key=key, title=cycle_title(key), items=value)
        for key, value in sorted(block_map.items(), key=lambda entry: entry[0])
    ]

    return CurriculumOverviewRead(
        group=serialize_group(group),
        semesters=semesters,
        grouped_items=grouped_items,
        complex_groups=dict(complex_groups),
        blocks=blocks,
    )


def serialize_attendance(record: AttendanceRecord) -> AttendanceRead:
    status_title = attendance_status_title(record.status)
    return AttendanceRead(
        id=record.id,
        date=record.date,
        student_id=record.student_id,
        student_name=record.student.full_name,
        status=record.status,
        status_title=status_title,
        reason=record.reason,
        curriculum_item_id=record.curriculum_item_id,
        curriculum_item_title=f"{record.curriculum_item.subject.code} {record.curriculum_item.subject.title}",
        group_name=record.student.group.name,
    )


def serialize_grade(record: GradeRecord) -> GradeRead:
    return GradeRead(
        id=record.id,
        date=record.date,
        student_id=record.student_id,
        student_name=record.student.full_name,
        grade_value=record.grade_value,
        comment=record.comment,
        curriculum_item_id=record.curriculum_item_id,
        curriculum_item_title=f"{record.curriculum_item.subject.code} {record.curriculum_item.subject.title}",
        group_name=record.student.group.name,
    )


def build_student_grades(student: Student) -> list[GradeRead]:
    sorted_records = sorted(student.grade_records, key=lambda item: (item.date, item.id), reverse=True)
    return [serialize_grade(record) for record in sorted_records]


def build_student_attendance(student: Student) -> list[AttendanceRead]:
    sorted_records = sorted(student.attendance_records, key=lambda item: (item.date, item.id), reverse=True)
    return [serialize_attendance(record) for record in sorted_records]
