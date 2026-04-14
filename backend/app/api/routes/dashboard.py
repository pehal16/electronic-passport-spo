from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models import AttendanceRecord, CurriculumItem, GradeRecord, Group, User
from app.schemas import DashboardQuickLink, DashboardRead, DashboardStat, UserRead
from app.services.access import get_access_scope

router = APIRouter(prefix="/dashboard", tags=["Панель"])


def _role_quick_links(role_code: str) -> list[DashboardQuickLink]:
    by_role: dict[str, list[tuple[str, str]]] = {
        "admin": [
            ("Открыть группы", "/groups"),
            ("Открыть учебные планы", "/groups"),
            ("Открыть журнал", "/journal"),
            ("Пользователи", "/admin/users"),
            ("Программы", "/admin/programs"),
        ],
        "curator": [
            ("Открыть группы", "/groups"),
            ("Открыть учебные планы", "/groups"),
            ("Открыть журнал", "/journal"),
            ("Внести посещаемость", "/attendance"),
            ("Внести оценку", "/grades"),
        ],
        "teacher": [
            ("Открыть группы", "/groups"),
            ("Открыть журнал", "/journal"),
            ("Внести посещаемость", "/attendance"),
            ("Внести оценку", "/grades"),
        ],
        "student": [
            ("Моя группа", "/groups"),
            ("Мои оценки", "/grades"),
            ("Моя посещаемость", "/attendance"),
        ],
        "parent": [
            ("Группа ребенка", "/groups"),
            ("Оценки ребенка", "/grades"),
            ("Посещаемость ребенка", "/attendance"),
        ],
    }
    return [DashboardQuickLink(label=label, href=href) for label, href in by_role.get(role_code, [("Открыть группы", "/groups")])]


@router.get("", response_model=DashboardRead)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardRead:
    scope = get_access_scope(db, current_user)
    group_ids = scope["groups"]
    student_ids = scope["students"]
    role_code = current_user.role.code

    groups_count = db.execute(select(func.count(Group.id)).where(Group.id.in_(group_ids))).scalar_one() if group_ids else 0
    students_count = len(student_ids)
    curriculum_count = db.execute(select(func.count(CurriculumItem.id)).where(CurriculumItem.group_id.in_(group_ids))).scalar_one() if group_ids else 0
    grade_count = db.execute(select(func.count(GradeRecord.id)).where(GradeRecord.student_id.in_(student_ids))).scalar_one() if student_ids else 0
    attendance_count = db.execute(select(func.count(AttendanceRecord.id)).where(AttendanceRecord.student_id.in_(student_ids))).scalar_one() if student_ids else 0

    groups_in_work = (
        db.execute(select(Group.name).where(Group.id.in_(group_ids)).order_by(Group.name)).scalars().all()
        if group_ids
        else []
    )

    missing_hours_count = db.execute(
        select(func.count(CurriculumItem.id))
        .where(CurriculumItem.group_id.in_(group_ids))
        .where(CurriculumItem.hours.is_(None))
    ).scalar_one() if group_ids else 0

    missing_control_form_count = db.execute(
        select(func.count(CurriculumItem.id))
        .where(CurriculumItem.group_id.in_(group_ids))
        .where(CurriculumItem.control_form.has(code="none"))
    ).scalar_one() if group_ids else 0

    manual_confirmation_count = db.execute(
        select(func.count(CurriculumItem.id))
        .where(CurriculumItem.group_id.in_(group_ids))
        .where(CurriculumItem.requires_manual_confirmation.is_(True))
    ).scalar_one() if group_ids else 0

    no_grades_count = db.execute(
        select(func.count(CurriculumItem.id))
        .where(CurriculumItem.group_id.in_(group_ids))
        .where(~CurriculumItem.grade_records.any())
    ).scalar_one() if group_ids else 0

    no_attendance_count = db.execute(
        select(func.count(CurriculumItem.id))
        .where(CurriculumItem.group_id.in_(group_ids))
        .where(~CurriculumItem.attendance_records.any())
    ).scalar_one() if group_ids else 0

    alerts: list[str] = []
    if role_code in {"admin", "curator", "teacher"}:
        alerts.append("Проверяйте заполнение журнала по каждому семестру: сначала посещаемость, затем оценки.")
    if role_code == "student":
        alerts.append("В кабинете показаны только ваши дисциплины, оценки, посещаемость, практики и ГИА.")
    if role_code == "parent":
        alerts.append("Родительский доступ ограничен только данными одного ребенка.")

    attention_items = [
        f"Предметы без часов: {missing_hours_count}",
        f"Элементы без формы контроля: {missing_control_form_count}",
        f"Элементы с ручной проверкой: {manual_confirmation_count}",
        f"Дисциплины без оценок: {no_grades_count}",
        f"Дисциплины без посещаемости: {no_attendance_count}",
    ]

    stats = [
        DashboardStat(label="Группы", value=str(groups_count), hint="Групп в работе"),
        DashboardStat(label="Студенты", value=str(students_count), hint="Студентов в зоне доступа"),
        DashboardStat(label="Учебный план", value=str(curriculum_count), hint="Элементов учебного плана"),
        DashboardStat(label="Оценки", value=str(grade_count), hint="Записей оценок"),
        DashboardStat(label="Посещаемость", value=str(attendance_count), hint="Записей посещаемости"),
    ]

    return DashboardRead(
        role_code=role_code,
        role_title=current_user.role.title,
        user=UserRead.model_validate(current_user),
        stats=stats,
        alerts=alerts,
        quick_links=_role_quick_links(role_code),
        groups_in_work=groups_in_work,
        attention_items=attention_items,
    )
