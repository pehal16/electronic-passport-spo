from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.deps import get_current_user, get_db
from app.models import ControlForm, CurriculumItem, Group, Program, Subject, User
from app.schemas import AdminProgramsRead, ControlFormRead, ProgramRead, ProgramStructureRead

router = APIRouter(prefix="/programs", tags=["Программы"])


@router.get("", response_model=AdminProgramsRead)
def list_programs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AdminProgramsRead:
    programs = db.execute(
        select(Program)
        .options(
            selectinload(Program.subjects),
            selectinload(Program.groups).selectinload(Group.practices),
            selectinload(Program.groups).selectinload(Group.curriculum_items).joinedload(CurriculumItem.control_form),
        )
        .order_by(Program.code)
    ).unique().scalars().all()

    control_forms = db.execute(select(ControlForm).order_by(ControlForm.id)).scalars().all()

    structures: list[ProgramStructureRead] = []
    for program in programs:
        practice_titles: set[str] = set()
        control_form_titles: set[str] = set()
        for group in program.groups:
            for practice in group.practices:
                suffix = []
                if practice.hours is not None:
                    suffix.append(f"{practice.hours} ч.")
                if practice.weeks is not None:
                    suffix.append(f"{practice.weeks} нед.")
                label = practice.title
                if suffix:
                    label = f"{label} ({', '.join(suffix)})"
                practice_titles.add(label)
            for item in group.curriculum_items:
                control_form_titles.add(item.control_form.title)

        key_modules = sorted(
            {
                f"{subject.code} {subject.title}"
                for subject in program.subjects
                if subject.block_type in {"professional_module", "mdk"}
            }
        )

        structures.append(
            ProgramStructureRead(
                program_id=program.id,
                code=program.code,
                title=program.title,
                qualification=program.qualification,
                education_form=program.education_form,
                duration_text=program.duration_text,
                gia_type=program.gia_type,
                total_hours=program.total_hours,
                practices=sorted(practice_titles),
                control_forms=sorted(control_form_titles),
                key_modules=key_modules,
                notes=program.notes,
            )
        )

    return AdminProgramsRead(
        programs=[ProgramRead.model_validate(program) for program in programs],
        control_forms=[ControlFormRead.model_validate(form) for form in control_forms],
        structures=structures,
    )

