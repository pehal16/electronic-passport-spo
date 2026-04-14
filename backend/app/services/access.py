from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models import (
    CuratorGroupLink,
    Group,
    ParentStudentLink,
    Student,
    StudentAccountLink,
    TeacherAssignment,
    User,
)


def get_access_scope(db: Session, user: User) -> dict[str, set[int]]:
    role_code = user.role.code
    group_ids: set[int] = set()
    student_ids: set[int] = set()
    subject_ids: set[int] = set()

    if role_code == "admin":
        group_ids = {
            value
            for value in db.execute(select(Group.id)).scalars().all()
        }
        student_ids = {
            value
            for value in db.execute(select(Student.id)).scalars().all()
        }
        return {"groups": group_ids, "students": student_ids, "subjects": subject_ids}

    if role_code == "curator":
        group_ids = {
            link.group_id
            for link in db.execute(
                select(CuratorGroupLink).where(CuratorGroupLink.user_id == user.id)
            )
            .scalars()
            .all()
        }
        student_ids = {
            value
            for value in db.execute(select(Student.id).where(Student.group_id.in_(group_ids))).scalars().all()
        } if group_ids else set()
        return {"groups": group_ids, "students": student_ids, "subjects": subject_ids}

    if role_code == "teacher":
        assignments = db.execute(
            select(TeacherAssignment).where(TeacherAssignment.user_id == user.id)
        ).scalars().all()
        group_ids = {item.group_id for item in assignments}
        subject_ids = {item.subject_id for item in assignments}
        student_ids = {
            value
            for value in db.execute(select(Student.id).where(Student.group_id.in_(group_ids))).scalars().all()
        } if group_ids else set()
        return {"groups": group_ids, "students": student_ids, "subjects": subject_ids}

    if role_code == "student":
        student_ids = {
            link.student_id
            for link in db.execute(
                select(StudentAccountLink).where(StudentAccountLink.user_id == user.id)
            )
            .scalars()
            .all()
        }
        group_ids = {
            value
            for value in db.execute(select(Student.group_id).where(Student.id.in_(student_ids))).scalars().all()
        } if student_ids else set()
        return {"groups": group_ids, "students": student_ids, "subjects": subject_ids}

    if role_code == "parent":
        student_ids = {
            link.student_id
            for link in db.execute(
                select(ParentStudentLink).where(ParentStudentLink.user_id == user.id)
            )
            .scalars()
            .all()
        }
        group_ids = {
            value
            for value in db.execute(select(Student.group_id).where(Student.id.in_(student_ids))).scalars().all()
        } if student_ids else set()
        return {"groups": group_ids, "students": student_ids, "subjects": subject_ids}

    return {"groups": group_ids, "students": student_ids, "subjects": subject_ids}


def apply_group_scope(statement: Select, model, group_ids: set[int]) -> Select:
    if not group_ids:
        return statement.where(model.id == -1)
    return statement.where(model.id.in_(group_ids))


def can_access_group(group_id: int, scope: dict[str, set[int]]) -> bool:
    return group_id in scope["groups"]


def can_access_student(student_id: int, scope: dict[str, set[int]]) -> bool:
    return student_id in scope["students"]
