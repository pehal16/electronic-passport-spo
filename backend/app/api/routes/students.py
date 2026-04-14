from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.deps import get_current_user, get_db
from app.models import AttendanceRecord, CurriculumItem, GradeRecord, Group, PracticeRecord, Semester, Student, User
from app.schemas import StudentDetailRead
from app.services.access import can_access_student, get_access_scope
from app.services.presenters import build_student_attendance, build_student_grades, serialize_group, serialize_practice

router = APIRouter(prefix="/students", tags=["Студенты"])


@router.get("/{student_id}", response_model=StudentDetailRead)
def student_detail(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StudentDetailRead:
    scope = get_access_scope(db, current_user)
    if current_user.role.code != "admin" and not can_access_student(student_id, scope):
        raise HTTPException(status_code=403, detail="Нет доступа к карточке студента.")

    statement = (
        select(Student)
        .options(
            joinedload(Student.group).joinedload(Group.program),
            joinedload(Student.group).selectinload(Group.students),
            joinedload(Student.group).selectinload(Group.semesters),
            joinedload(Student.group).selectinload(Group.curriculum_items).joinedload(CurriculumItem.subject),
            joinedload(Student.group).selectinload(Group.curriculum_items).joinedload(CurriculumItem.control_form),
            joinedload(Student.group).selectinload(Group.practices).joinedload(PracticeRecord.semester),
            joinedload(Student.group).selectinload(Group.practices).joinedload(PracticeRecord.final_control_form),
            joinedload(Student.group).joinedload(Group.gia_record),
            selectinload(Student.attendance_records).joinedload(AttendanceRecord.curriculum_item).joinedload(CurriculumItem.subject),
            selectinload(Student.attendance_records).joinedload(AttendanceRecord.student).joinedload(Student.group),
            selectinload(Student.grade_records).joinedload(GradeRecord.curriculum_item).joinedload(CurriculumItem.subject),
            selectinload(Student.grade_records).joinedload(GradeRecord.student).joinedload(Student.group),
        )
        .where(Student.id == student_id)
    )
    student = db.execute(statement).unique().scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Студент не найден.")

    group = student.group
    current_semester_ids = {semester.id for semester in group.semesters if semester.course_number == group.course_now}
    if not current_semester_ids:
        current_semester_ids = {semester.id for semester in group.semesters}

    subjects_seen: set[str] = set()
    current_subjects: list[str] = []
    for item in sorted(group.curriculum_items, key=lambda curriculum_item: (curriculum_item.subject.code, curriculum_item.subject.title)):
        if item.semester_id not in current_semester_ids:
            continue
        if item.subject.block_type in {"practice", "gia"}:
            continue
        subject_label = f"{item.subject.code} {item.subject.title}"
        if subject_label not in subjects_seen:
            subjects_seen.add(subject_label)
            current_subjects.append(subject_label)

    practices = [serialize_practice(practice) for practice in group.practices]
    gia_text = group.gia_record.notes if group.gia_record and group.gia_record.notes else group.program.gia_type

    return StudentDetailRead(
        id=student.id,
        full_name=student.full_name,
        status=student.status,
        notes=student.notes,
        group=serialize_group(group),
        attendance=build_student_attendance(student),
        grades=build_student_grades(student),
        current_subjects=current_subjects,
        practices=practices,
        gia_text=gia_text,
    )
