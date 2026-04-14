import base64
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.deps import get_current_user, get_db, require_roles
from app.models import AttestationSheet, AttestationSheetDiscipline, CurriculumItem, Group, SheetTemplate, User
from app.schemas import (
    AttestationExportRead,
    AttestationPreviewRead,
    AttestationSheetCreateRequest,
    AttestationSheetRead,
    AttestationSheetUpdateRequest,
    MessageRead,
    SheetTemplateRead,
)
from app.services.access import can_access_group, get_access_scope
from app.services.attestation import (
    create_sheet_from_curriculum,
    fill_sheet_rows_from_journal,
    load_sheet_with_details,
    refresh_sheet_students_from_group,
    render_sheet_html,
    save_print_snapshot,
    serialize_sheet,
    update_sheet_rows,
)
from app.services.attestation_export import build_docx_bytes, build_pdf_bytes

router = APIRouter(prefix="/attestation-sheets", tags=["Ведомости"])


def _sheet_base_query():
    return (
        select(AttestationSheet)
        .options(
            joinedload(AttestationSheet.group).joinedload(Group.program),
            joinedload(AttestationSheet.semester),
            joinedload(AttestationSheet.curriculum_item).joinedload(CurriculumItem.subject),
            joinedload(AttestationSheet.sheet_template),
            selectinload(AttestationSheet.disciplines),
            selectinload(AttestationSheet.rows),
            selectinload(AttestationSheet.print_snapshots),
        )
    )


def _require_sheet_access(sheet: AttestationSheet, scope: dict[str, set[int]], current_user: User) -> None:
    if current_user.role.code == "admin":
        return
    if not can_access_group(sheet.group_id, scope):
        raise HTTPException(status_code=403, detail="Нет доступа к ведомости этой группы.")


@router.get("/templates", response_model=list[SheetTemplateRead])
def list_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SheetTemplateRead]:
    templates = db.execute(select(SheetTemplate).where(SheetTemplate.is_active.is_(True)).order_by(SheetTemplate.id)).scalars().all()
    return [SheetTemplateRead.model_validate(template) for template in templates]


@router.post("", response_model=AttestationSheetRead)
def create_attestation_sheet(
    payload: AttestationSheetCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "curator", "teacher")),
) -> AttestationSheetRead:
    scope = get_access_scope(db, current_user)
    item = db.execute(select(CurriculumItem).where(CurriculumItem.id == payload.curriculum_item_id)).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Дисциплина учебного плана не найдена.")
    if current_user.role.code != "admin" and not can_access_group(item.group_id, scope):
        raise HTTPException(status_code=403, detail="Нет доступа к выбранной группе.")

    sheet = create_sheet_from_curriculum(db, payload, current_user)
    db.commit()
    db.refresh(sheet)
    loaded = load_sheet_with_details(db, sheet.id)
    if not loaded:
        raise HTTPException(status_code=404, detail="Не удалось сформировать ведомость.")
    return serialize_sheet(loaded)


@router.get("", response_model=list[AttestationSheetRead])
def list_attestation_sheets(
    group_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AttestationSheetRead]:
    scope = get_access_scope(db, current_user)
    statement = _sheet_base_query().order_by(AttestationSheet.date.desc(), AttestationSheet.id.desc())
    if current_user.role.code != "admin":
        if not scope["groups"]:
            return []
        statement = statement.where(AttestationSheet.group_id.in_(scope["groups"]))
    if group_id is not None:
        statement = statement.where(AttestationSheet.group_id == group_id)

    sheets = db.execute(statement).unique().scalars().all()
    return [serialize_sheet(sheet) for sheet in sheets]


@router.get("/{sheet_id}", response_model=AttestationSheetRead)
def get_attestation_sheet(
    sheet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AttestationSheetRead:
    scope = get_access_scope(db, current_user)
    sheet = load_sheet_with_details(db, sheet_id)
    if not sheet:
        raise HTTPException(status_code=404, detail="Ведомость не найдена.")
    _require_sheet_access(sheet, scope, current_user)
    return serialize_sheet(sheet)


@router.put("/{sheet_id}", response_model=AttestationSheetRead)
def update_attestation_sheet(
    sheet_id: int,
    payload: AttestationSheetUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "curator", "teacher")),
) -> AttestationSheetRead:
    scope = get_access_scope(db, current_user)
    sheet = load_sheet_with_details(db, sheet_id)
    if not sheet:
        raise HTTPException(status_code=404, detail="Ведомость не найдена.")
    _require_sheet_access(sheet, scope, current_user)

    sheet.date = payload.date
    sheet.teacher_name = payload.teacher_name
    sheet.second_teacher_name = payload.second_teacher_name
    sheet.discipline_display_text = payload.discipline_display_text
    sheet.status = payload.status

    update_sheet_rows(sheet, payload.rows)
    sheet.disciplines = [
        AttestationSheetDiscipline(
            attestation_sheet_id=sheet.id,
            discipline_name=item.discipline_name,
            discipline_code=item.discipline_code,
            order_index=item.order_index,
        )
        for item in sorted(payload.disciplines, key=lambda value: value.order_index)
    ]

    db.commit()
    loaded = load_sheet_with_details(db, sheet_id)
    if not loaded:
        raise HTTPException(status_code=404, detail="Ведомость не найдена.")
    return serialize_sheet(loaded)


@router.post("/{sheet_id}/refresh-students", response_model=AttestationSheetRead)
def refresh_students_snapshot(
    sheet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "curator", "teacher")),
) -> AttestationSheetRead:
    scope = get_access_scope(db, current_user)
    sheet = load_sheet_with_details(db, sheet_id)
    if not sheet:
        raise HTTPException(status_code=404, detail="Ведомость не найдена.")
    _require_sheet_access(sheet, scope, current_user)
    if sheet.status == "saved":
        raise HTTPException(status_code=409, detail="Состав уже зафиксирован. Создайте новую ведомость для обновления списка.")

    refresh_sheet_students_from_group(db, sheet)
    db.commit()
    loaded = load_sheet_with_details(db, sheet_id)
    if not loaded:
        raise HTTPException(status_code=404, detail="Ведомость не найдена.")
    return serialize_sheet(loaded)


@router.post("/{sheet_id}/fill-from-journal", response_model=AttestationSheetRead)
def fill_from_journal(
    sheet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "curator", "teacher")),
) -> AttestationSheetRead:
    scope = get_access_scope(db, current_user)
    sheet = load_sheet_with_details(db, sheet_id)
    if not sheet:
        raise HTTPException(status_code=404, detail="Ведомость не найдена.")
    _require_sheet_access(sheet, scope, current_user)
    if sheet.status == "saved":
        raise HTTPException(status_code=409, detail="Ведомость уже сохранена. Заполнение из журнала доступно только для черновика.")

    fill_sheet_rows_from_journal(db, sheet)
    db.commit()
    loaded = load_sheet_with_details(db, sheet_id)
    if not loaded:
        raise HTTPException(status_code=404, detail="Ведомость не найдена.")
    return serialize_sheet(loaded)


@router.get("/{sheet_id}/preview", response_model=AttestationPreviewRead)
def sheet_preview(
    sheet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AttestationPreviewRead:
    scope = get_access_scope(db, current_user)
    sheet = load_sheet_with_details(db, sheet_id)
    if not sheet:
        raise HTTPException(status_code=404, detail="Ведомость не найдена.")
    _require_sheet_access(sheet, scope, current_user)

    rendered = render_sheet_html(serialize_sheet(sheet))
    save_print_snapshot(db, sheet, rendered.html)
    db.commit()
    return AttestationPreviewRead(sheet_id=sheet.id, html=rendered.html)


@router.get("/{sheet_id}/export/pdf", response_model=AttestationExportRead)
def export_sheet_pdf(
    sheet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AttestationExportRead:
    scope = get_access_scope(db, current_user)
    sheet = load_sheet_with_details(db, sheet_id)
    if not sheet:
        raise HTTPException(status_code=404, detail="Ведомость не найдена.")
    _require_sheet_access(sheet, scope, current_user)

    sheet_data = serialize_sheet(sheet)
    rendered = render_sheet_html(sheet_data)
    content = build_pdf_bytes(sheet_data)
    save_print_snapshot(db, sheet, rendered.html, pdf_path=f"attestation_sheet_{sheet.id}.pdf")
    db.commit()

    return AttestationExportRead(
        sheet_id=sheet.id,
        filename=f"vedomost_{sheet.id}.pdf",
        content_type="application/pdf",
        content_base64=base64.b64encode(content).decode("utf-8"),
    )


@router.get("/{sheet_id}/export/docx", response_model=AttestationExportRead)
def export_sheet_docx(
    sheet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AttestationExportRead:
    scope = get_access_scope(db, current_user)
    sheet = load_sheet_with_details(db, sheet_id)
    if not sheet:
        raise HTTPException(status_code=404, detail="Ведомость не найдена.")
    _require_sheet_access(sheet, scope, current_user)

    sheet_data = serialize_sheet(sheet)
    rendered = render_sheet_html(sheet_data)
    content = build_docx_bytes(sheet_data)
    save_print_snapshot(db, sheet, rendered.html, docx_path=f"attestation_sheet_{sheet.id}.docx")
    db.commit()

    return AttestationExportRead(
        sheet_id=sheet.id,
        filename=f"vedomost_{sheet.id}.docx",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        content_base64=base64.b64encode(content).decode("utf-8"),
    )


@router.post("/{sheet_id}/save", response_model=MessageRead)
def save_sheet(
    sheet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "curator", "teacher")),
) -> MessageRead:
    scope = get_access_scope(db, current_user)
    sheet = load_sheet_with_details(db, sheet_id)
    if not sheet:
        raise HTTPException(status_code=404, detail="Ведомость не найдена.")
    _require_sheet_access(sheet, scope, current_user)
    sheet.status = "saved"
    db.commit()
    return MessageRead(message="Ведомость сохранена.")
