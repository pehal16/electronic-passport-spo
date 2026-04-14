from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.deps import get_current_user, get_db
from app.models import AttendanceRecord, CurriculumItem, GradeRecord, Group, PracticeRecord, Semester, Student, User
from app.schemas import CurriculumOverviewRead, GroupDetailRead, GroupRead, PracticeRead, SemesterRead, StudentListItem
from app.services.access import can_access_group, get_access_scope
from app.services.presenters import build_curriculum_overview, build_group_detail, serialize_group, serialize_practice, serialize_semester

router = APIRouter(prefix="/groups", tags=["Группы"])


def load_group(db: Session, group_id: int) -> Group | None:
    statement = (
        select(Group)
        .options(
            joinedload(Group.program),
            selectinload(Group.students),
            selectinload(Group.semesters).selectinload(Semester.curriculum_items).joinedload(CurriculumItem.subject),
            selectinload(Group.semesters).selectinload(Semester.curriculum_items).joinedload(CurriculumItem.control_form),
            selectinload(Group.curriculum_items).joinedload(CurriculumItem.subject),
            selectinload(Group.curriculum_items).joinedload(CurriculumItem.control_form),
            selectinload(Group.practices).joinedload(PracticeRecord.semester),
            selectinload(Group.practices).joinedload(PracticeRecord.final_control_form),
            joinedload(Group.gia_record),
        )
        .where(Group.id == group_id)
    )
    return db.execute(statement).unique().scalar_one_or_none()


@router.get("", response_model=list[GroupRead])
def list_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[GroupRead]:
    scope = get_access_scope(db, current_user)
    statement = (
        select(Group)
        .options(
            joinedload(Group.program),
            selectinload(Group.students),
            selectinload(Group.semesters),
            selectinload(Group.curriculum_items).joinedload(CurriculumItem.control_form),
            selectinload(Group.practices),
        )
        .order_by(Group.name)
    )
    if current_user.role.code != "admin":
        if not scope["groups"]:
            return []
        statement = statement.where(Group.id.in_(scope["groups"]))
    groups = db.execute(statement).unique().scalars().all()
    return [serialize_group(group) for group in groups]


@router.get("/{group_id}", response_model=GroupDetailRead)
def group_detail(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GroupDetailRead:
    scope = get_access_scope(db, current_user)
    if current_user.role.code != "admin" and not can_access_group(group_id, scope):
        raise HTTPException(status_code=403, detail="Нет доступа к группе.")
    group = load_group(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена.")
    return build_group_detail(group)


@router.get("/{group_id}/students", response_model=list[StudentListItem])
def group_students(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[StudentListItem]:
    scope = get_access_scope(db, current_user)
    if current_user.role.code != "admin" and not can_access_group(group_id, scope):
        raise HTTPException(status_code=403, detail="Нет доступа к студентам группы.")
    group = db.execute(select(Group).options(selectinload(Group.students)).where(Group.id == group_id)).unique().scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена.")

    student_ids = [student.id for student in group.students]
    grade_counts = dict(
        db.execute(
            select(GradeRecord.student_id, func.count(GradeRecord.id))
            .where(GradeRecord.student_id.in_(student_ids))
            .group_by(GradeRecord.student_id)
        ).all()
    ) if student_ids else {}

    absence_counts = dict(
        db.execute(
            select(AttendanceRecord.student_id, func.count(AttendanceRecord.id))
            .where(AttendanceRecord.student_id.in_(student_ids))
            .where(AttendanceRecord.status.in_(["absent", "late", "excused"]))
            .group_by(AttendanceRecord.student_id)
        ).all()
    ) if student_ids else {}

    return [
        StudentListItem(
            id=student.id,
            full_name=student.full_name,
            status=student.status,
            notes=student.notes,
            group_name=group.name,
            course_now=group.course_now,
            grade_count=grade_counts.get(student.id, 0),
            absence_count=absence_counts.get(student.id, 0),
        )
        for student in group.students
    ]


@router.get("/{group_id}/semesters", response_model=list[SemesterRead])
def group_semesters(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SemesterRead]:
    scope = get_access_scope(db, current_user)
    if current_user.role.code != "admin" and not can_access_group(group_id, scope):
        raise HTTPException(status_code=403, detail="Нет доступа к семестрам группы.")
    semesters = db.execute(select(Semester).where(Semester.group_id == group_id).order_by(Semester.number)).scalars().all()
    return [serialize_semester(semester) for semester in semesters]


@router.get("/{group_id}/curriculum", response_model=CurriculumOverviewRead)
def group_curriculum(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CurriculumOverviewRead:
    scope = get_access_scope(db, current_user)
    if current_user.role.code != "admin" and not can_access_group(group_id, scope):
        raise HTTPException(status_code=403, detail="Нет доступа к учебному плану группы.")
    group = load_group(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена.")
    return build_curriculum_overview(group)


@router.get("/{group_id}/practices", response_model=list[PracticeRead])
def group_practices(
    group_id: int,
    semester_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[PracticeRead]:
    scope = get_access_scope(db, current_user)
    if current_user.role.code != "admin" and not can_access_group(group_id, scope):
        raise HTTPException(status_code=403, detail="Нет доступа к практикам группы.")
    group = load_group(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена.")
    practices = group.practices
    if semester_id is not None:
        practices = [practice for practice in practices if practice.semester_id == semester_id]
    practices_sorted = sorted(
        practices,
        key=lambda practice: (
            practice.semester.number if practice.semester else 999,
            practice.id,
        ),
    )
    return [serialize_practice(practice) for practice in practices_sorted]


@router.get("/{group_id}/gia", response_model=GroupDetailRead)
def group_gia(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GroupDetailRead:
    return group_detail(group_id=group_id, db=db, current_user=current_user)
