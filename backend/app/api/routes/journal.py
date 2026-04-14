from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.deps import get_current_user, get_db
from app.models import AttendanceRecord, CurriculumItem, GradeRecord, Student, User
from app.schemas import JournalRow, JournalSubjectRead, JournalSubjectStudentRead
from app.services.access import get_access_scope
from app.services.presenters import cycle_title

router = APIRouter(prefix="/journal", tags=["Журнал"])


@router.get("", response_model=list[JournalRow])
def get_journal(
    group_id: int | None = Query(default=None),
    semester_id: int | None = Query(default=None),
    subject_id: int | None = Query(default=None),
    control_form_code: str | None = Query(default=None),
    grades_filter: str = Query(default="all"),
    attendance_filter: str = Query(default="all"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[JournalRow]:
    scope = get_access_scope(db, current_user)
    accessible_groups = set(scope["groups"])

    if group_id is not None:
        if current_user.role.code != "admin" and group_id not in accessible_groups:
            return []
        accessible_groups = {group_id}

    if current_user.role.code != "admin" and not accessible_groups:
        return []

    statement = (
        select(CurriculumItem)
        .options(
            joinedload(CurriculumItem.group),
            joinedload(CurriculumItem.semester),
            joinedload(CurriculumItem.subject),
            joinedload(CurriculumItem.control_form),
        )
        .order_by(
            CurriculumItem.group_id,
            CurriculumItem.semester_id,
            CurriculumItem.id,
        )
    )

    if current_user.role.code != "admin" or group_id is not None:
        statement = statement.where(CurriculumItem.group_id.in_(accessible_groups))
    if semester_id is not None:
        statement = statement.where(CurriculumItem.semester_id == semester_id)
    if subject_id is not None:
        statement = statement.where(CurriculumItem.subject_id == subject_id)
    if control_form_code is not None and control_form_code != "":
        statement = statement.where(CurriculumItem.control_form.has(code=control_form_code))
    if current_user.role.code == "teacher":
        if not scope["subjects"]:
            return []
        statement = statement.where(CurriculumItem.subject_id.in_(scope["subjects"]))

    items = db.execute(statement).unique().scalars().all()
    item_ids = [item.id for item in items]
    group_ids = {item.group_id for item in items}

    grade_counts = dict(
        db.execute(
            select(GradeRecord.curriculum_item_id, func.count(GradeRecord.id))
            .where(GradeRecord.curriculum_item_id.in_(item_ids))
            .group_by(GradeRecord.curriculum_item_id)
        ).all()
    ) if item_ids else {}

    attendance_counts = dict(
        db.execute(
            select(AttendanceRecord.curriculum_item_id, func.count(AttendanceRecord.id))
            .where(AttendanceRecord.curriculum_item_id.in_(item_ids))
            .group_by(AttendanceRecord.curriculum_item_id)
        ).all()
    ) if item_ids else {}

    students_per_group = dict(
        db.execute(
            select(Student.group_id, func.count(Student.id))
            .where(Student.group_id.in_(group_ids))
            .group_by(Student.group_id)
        ).all()
    ) if group_ids else {}

    rows = [
        JournalRow(
            curriculum_item_id=item.id,
            group_id=item.group_id,
            group_name=item.group.name,
            semester_id=item.semester_id,
            semester_number=item.semester.number,
            semester_title=item.semester.title,
            subject_id=item.subject_id,
            subject_code=item.subject.code,
            subject_title=item.subject.title,
            cycle_title=cycle_title(item.subject.block_type),
            total_hours=item.hours,
            control_form_code=item.control_form.code,
            control_form_title=item.control_form.title,
            student_count=students_per_group.get(item.group_id, 0),
            grades_count=grade_counts.get(item.id, 0),
            attendance_count=attendance_counts.get(item.id, 0),
            has_grades=grade_counts.get(item.id, 0) > 0,
            has_attendance=attendance_counts.get(item.id, 0) > 0,
        )
        for item in items
    ]

    if grades_filter == "with":
        rows = [row for row in rows if row.has_grades]
    elif grades_filter == "without":
        rows = [row for row in rows if not row.has_grades]

    if attendance_filter == "with":
        rows = [row for row in rows if row.has_attendance]
    elif attendance_filter == "without":
        rows = [row for row in rows if not row.has_attendance]

    return rows


@router.get("/{curriculum_item_id}", response_model=JournalSubjectRead)
def get_subject_journal(
    curriculum_item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JournalSubjectRead:
    scope = get_access_scope(db, current_user)

    item = db.execute(
        select(CurriculumItem)
        .options(
            joinedload(CurriculumItem.group),
            joinedload(CurriculumItem.semester),
            joinedload(CurriculumItem.subject),
            joinedload(CurriculumItem.control_form),
        )
        .where(CurriculumItem.id == curriculum_item_id)
    ).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Элемент учебного плана не найден.")

    if current_user.role.code != "admin" and item.group_id not in scope["groups"]:
        raise HTTPException(status_code=403, detail="Нет доступа к журналу этой дисциплины.")
    if current_user.role.code == "teacher":
        if not scope["subjects"] or item.subject_id not in scope["subjects"]:
            raise HTTPException(status_code=403, detail="Нет доступа к дисциплине.")

    students = db.execute(
        select(Student)
        .where(Student.group_id == item.group_id)
        .order_by(Student.full_name)
    ).scalars().all()
    student_ids = [student.id for student in students]

    latest_grade_records = db.execute(
        select(GradeRecord)
        .where(
            GradeRecord.curriculum_item_id == curriculum_item_id,
            GradeRecord.student_id.in_(student_ids),
        )
        .order_by(GradeRecord.date.desc(), GradeRecord.id.desc())
    ).scalars().all()
    latest_grade_by_student: dict[int, GradeRecord] = {}
    for record in latest_grade_records:
        if record.student_id not in latest_grade_by_student:
            latest_grade_by_student[record.student_id] = record

    grades_count = dict(
        db.execute(
            select(GradeRecord.student_id, func.count(GradeRecord.id))
            .where(
                GradeRecord.curriculum_item_id == curriculum_item_id,
                GradeRecord.student_id.in_(student_ids),
            )
            .group_by(GradeRecord.student_id)
        ).all()
    ) if student_ids else {}

    attendance_stats_raw = db.execute(
        select(
            AttendanceRecord.student_id,
            AttendanceRecord.status,
            func.count(AttendanceRecord.id),
        )
        .where(
            AttendanceRecord.curriculum_item_id == curriculum_item_id,
            AttendanceRecord.student_id.in_(student_ids),
        )
        .group_by(AttendanceRecord.student_id, AttendanceRecord.status)
    ).all()

    attendance_stats: dict[int, dict[str, int]] = {}
    for student_id, status, count in attendance_stats_raw:
        stats = attendance_stats.setdefault(student_id, {"present": 0, "absent": 0, "excused": 0, "late": 0})
        stats[status] = count

    student_rows = [
        JournalSubjectStudentRead(
            student_id=student.id,
            full_name=student.full_name,
            last_grade=latest_grade_by_student.get(student.id).grade_value if latest_grade_by_student.get(student.id) else None,
            grades_count=grades_count.get(student.id, 0),
            attended_count=attendance_stats.get(student.id, {}).get("present", 0),
            absent_count=attendance_stats.get(student.id, {}).get("absent", 0),
            excused_count=attendance_stats.get(student.id, {}).get("excused", 0),
            late_count=attendance_stats.get(student.id, {}).get("late", 0),
            last_comment=latest_grade_by_student.get(student.id).comment if latest_grade_by_student.get(student.id) else None,
        )
        for student in students
    ]

    return JournalSubjectRead(
        curriculum_item_id=item.id,
        group_name=item.group.name,
        semester_title=item.semester.title,
        subject_code=item.subject.code,
        subject_title=item.subject.title,
        control_form_title=item.control_form.title,
        students=student_rows,
    )
