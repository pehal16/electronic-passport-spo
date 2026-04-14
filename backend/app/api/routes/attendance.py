from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.deps import get_current_user, get_db, require_roles
from app.models import AttendanceRecord, CurriculumItem, Student, User
from app.schemas import AttendanceBulkUpsert, AttendanceRead, AttendanceUpsert, MessageRead
from app.services.access import can_access_group, can_access_student, get_access_scope
from app.services.presenters import serialize_attendance

router = APIRouter(prefix="/attendance", tags=["Посещаемость"])

ATTENDANCE_STATUS_ALIAS = {
    "present": "present",
    "присутствовал": "present",
    "absent": "absent",
    "отсутствовал": "absent",
    "late": "late",
    "опоздал": "late",
    "excused": "excused",
    "уважительная причина": "excused",
}


def normalize_attendance_status(raw_value: str) -> str:
    normalized = ATTENDANCE_STATUS_ALIAS.get(raw_value.strip().lower())
    if not normalized:
        raise HTTPException(status_code=422, detail="Некорректный статус посещаемости.")
    return normalized


def _check_item_access(item: CurriculumItem, scope: dict[str, set[int]], current_user: User) -> None:
    if current_user.role.code != "admin" and item.group_id not in scope["groups"]:
        raise HTTPException(status_code=403, detail="Нет доступа к дисциплине.")
    if current_user.role.code == "teacher":
        if not scope["subjects"] or item.subject_id not in scope["subjects"]:
            raise HTTPException(status_code=403, detail="Нет доступа к дисциплине.")


@router.get("", response_model=list[AttendanceRead])
def list_attendance(
    group_id: int | None = Query(default=None),
    student_id: int | None = Query(default=None),
    semester_id: int | None = Query(default=None),
    curriculum_item_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AttendanceRead]:
    scope = get_access_scope(db, current_user)
    statement = (
        select(AttendanceRecord)
        .options(
            joinedload(AttendanceRecord.student).joinedload(Student.group),
            joinedload(AttendanceRecord.curriculum_item).joinedload(CurriculumItem.subject),
        )
        .order_by(AttendanceRecord.date.desc(), AttendanceRecord.id.desc())
    )

    if student_id is not None:
        if current_user.role.code != "admin" and not can_access_student(student_id, scope):
            raise HTTPException(status_code=403, detail="Нет доступа к посещаемости студента.")
        statement = statement.where(AttendanceRecord.student_id == student_id)
    elif group_id is not None:
        if current_user.role.code != "admin" and not can_access_group(group_id, scope):
            raise HTTPException(status_code=403, detail="Нет доступа к посещаемости группы.")
        statement = statement.join(AttendanceRecord.student).where(Student.group_id == group_id)
    elif current_user.role.code != "admin":
        if not scope["students"]:
            return []
        statement = statement.where(AttendanceRecord.student_id.in_(scope["students"]))

    if semester_id is not None:
        statement = statement.join(AttendanceRecord.curriculum_item).where(CurriculumItem.semester_id == semester_id)
    if curriculum_item_id is not None:
        statement = statement.where(AttendanceRecord.curriculum_item_id == curriculum_item_id)

    return [serialize_attendance(record) for record in db.execute(statement).unique().scalars().all()]


@router.post("", response_model=MessageRead)
def upsert_attendance(
    payload: AttendanceUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "curator", "teacher")),
) -> MessageRead:
    scope = get_access_scope(db, current_user)
    if current_user.role.code != "admin" and not can_access_student(payload.student_id, scope):
        raise HTTPException(status_code=403, detail="Нет доступа к студенту.")

    item = db.execute(select(CurriculumItem).where(CurriculumItem.id == payload.curriculum_item_id)).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Элемент учебного плана не найден.")
    _check_item_access(item, scope, current_user)

    status = normalize_attendance_status(payload.status)
    existing = db.execute(
        select(AttendanceRecord).where(
            AttendanceRecord.student_id == payload.student_id,
            AttendanceRecord.curriculum_item_id == payload.curriculum_item_id,
            AttendanceRecord.date == payload.date,
        )
    ).scalar_one_or_none()
    if existing:
        existing.status = status
        existing.reason = payload.reason
    else:
        db.add(
            AttendanceRecord(
                student_id=payload.student_id,
                curriculum_item_id=payload.curriculum_item_id,
                date=payload.date,
                status=status,
                reason=payload.reason,
            )
        )
    db.commit()
    return MessageRead(message="Посещаемость сохранена.")


@router.post("/bulk", response_model=MessageRead)
def bulk_upsert_attendance(
    payload: AttendanceBulkUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "curator", "teacher")),
) -> MessageRead:
    if not payload.entries:
        raise HTTPException(status_code=422, detail="Передайте хотя бы одну запись посещаемости.")

    scope = get_access_scope(db, current_user)
    item = db.execute(select(CurriculumItem).where(CurriculumItem.id == payload.curriculum_item_id)).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Элемент учебного плана не найден.")
    _check_item_access(item, scope, current_user)

    student_ids = [entry.student_id for entry in payload.entries]
    students = db.execute(select(Student).where(Student.id.in_(student_ids))).scalars().all()
    students_map = {student.id: student for student in students}

    for entry in payload.entries:
        student = students_map.get(entry.student_id)
        if not student:
            raise HTTPException(status_code=404, detail=f"Студент с id={entry.student_id} не найден.")
        if student.group_id != item.group_id:
            raise HTTPException(status_code=422, detail=f"Студент {student.full_name} не относится к выбранной группе.")
        if current_user.role.code != "admin" and not can_access_student(entry.student_id, scope):
            raise HTTPException(status_code=403, detail=f"Нет доступа к студенту {student.full_name}.")

        status = normalize_attendance_status(entry.status)
        existing = db.execute(
            select(AttendanceRecord).where(
                AttendanceRecord.student_id == entry.student_id,
                AttendanceRecord.curriculum_item_id == payload.curriculum_item_id,
                AttendanceRecord.date == payload.date,
            )
        ).scalar_one_or_none()
        if existing:
            existing.status = status
            existing.reason = entry.reason
        else:
            db.add(
                AttendanceRecord(
                    student_id=entry.student_id,
                    curriculum_item_id=payload.curriculum_item_id,
                    date=payload.date,
                    status=status,
                    reason=entry.reason,
                )
            )

    db.commit()
    return MessageRead(message="Посещаемость группы сохранена.")
