from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from html import escape

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.config import settings
from app.models import (
    AttestationSheet,
    AttestationSheetDiscipline,
    AttestationSheetRow,
    CurriculumItem,
    GradeRecord,
    Group,
    PrintSnapshot,
    Semester,
    SheetTemplate,
    Student,
    User,
)
from app.schemas.attestation import (
    AttestationSheetCreateRequest,
    AttestationSheetRead,
    AttestationSheetRowRead,
    AttestationSheetRowUpdate,
    AttestationTotalsRead,
    SheetTemplateRead,
)

GRADE_FULL = {
    "5": "5 (отлично)",
    "4": "4 (хорошо)",
    "3": "3 (удовлетворительно)",
    "2": "2 (неудовлетворительно)",
}

GRADE_SHORT = {
    "5": "5 (отл.)",
    "4": "4 (хор.)",
    "3": "3 (удовлет.)",
    "2": "2 (неуд.)",
}

ATTENDANCE_RESULT_TITLE = {
    "regular": "Обычная сдача",
    "not_submitted": "Не сдавал",
    "not_appeared": "Не явился",
}

TEMPLATE_BY_CONTROL_FORM = {
    "dz": "diff_credit",
    "kdz": "complex_diff_credit",
    "complex_exam": "complex_exam",
    "credit_sheet": "credit_sheet",
    "exam": "complex_exam",
}

ONES = [
    "ноль",
    "один",
    "два",
    "три",
    "четыре",
    "пять",
    "шесть",
    "семь",
    "восемь",
    "девять",
]
TEENS = [
    "десять",
    "одиннадцать",
    "двенадцать",
    "тринадцать",
    "четырнадцать",
    "пятнадцать",
    "шестнадцать",
    "семнадцать",
    "восемнадцать",
    "девятнадцать",
]
TENS = [
    "",
    "",
    "двадцать",
    "тридцать",
    "сорок",
    "пятьдесят",
    "шестьдесят",
    "семьдесят",
    "восемьдесят",
    "девяносто",
]
HUNDREDS = [
    "",
    "сто",
    "двести",
    "триста",
    "четыреста",
    "пятьсот",
    "шестьсот",
    "семьсот",
    "восемьсот",
    "девятьсот",
]


def number_to_words_ru(value: int) -> str:
    if value < 0:
        return f"минус {number_to_words_ru(abs(value))}"
    if value < 10:
        return ONES[value]
    if value < 20:
        return TEENS[value - 10]
    if value < 100:
        tens = TENS[value // 10]
        tail = value % 10
        return tens if tail == 0 else f"{tens} {ONES[tail]}"
    if value < 1000:
        hundreds = HUNDREDS[value // 100]
        tail = value % 100
        return hundreds if tail == 0 else f"{hundreds} {number_to_words_ru(tail)}"
    if value < 10000:
        thousands = value // 1000
        tail = value % 1000
        thousand_word = "тысяча" if thousands == 1 else "тысячи" if 2 <= thousands <= 4 else "тысяч"
        head = f"{ONES[thousands]} {thousand_word}" if thousands < 10 else f"{number_to_words_ru(thousands)} {thousand_word}"
        return head if tail == 0 else f"{head} {number_to_words_ru(tail)}"
    return str(value)


def grade_to_text(grade_numeric: str | None, mode: str = "full") -> str | None:
    if not grade_numeric:
        return None
    if grade_numeric in {"н/а", "зачет", "незачет"}:
        return grade_numeric
    if mode == "short":
        return GRADE_SHORT.get(grade_numeric, grade_numeric)
    return GRADE_FULL.get(grade_numeric, grade_numeric)


def resolve_template_code(item: CurriculumItem, requested_template_code: str | None) -> str:
    if requested_template_code:
        return requested_template_code
    if item.statement_template_code:
        return item.statement_template_code
    if item.control_form.code == "exam":
        if item.requires_ticket_number or item.is_complex_exam:
            return "complex_exam"
        return "complex_exam"
    return TEMPLATE_BY_CONTROL_FORM.get(item.control_form.code, "diff_credit")


def resolve_header_label_and_value(group: Group, template: SheetTemplate) -> tuple[str, str]:
    program = group.program
    if template.header_label_type == "profession":
        return "Профессия", program.qualification
    if template.header_label_type == "specialty":
        return "Специальность", f"{program.code} {program.title}"
    if "професси" in program.title.lower():
        return "Профессия", f"{program.code} {program.title}"
    return "Специальность", f"{program.code} {program.title}"


def load_sheet_with_details(db: Session, sheet_id: int) -> AttestationSheet | None:
    return db.execute(
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
        .where(AttestationSheet.id == sheet_id)
    ).unique().scalar_one_or_none()


def create_sheet_from_curriculum(
    db: Session,
    payload: AttestationSheetCreateRequest,
    current_user: User,
) -> AttestationSheet:
    item = db.execute(
        select(CurriculumItem)
        .options(
            joinedload(CurriculumItem.group).joinedload(Group.program),
            joinedload(CurriculumItem.semester),
            joinedload(CurriculumItem.subject),
            joinedload(CurriculumItem.control_form),
        )
        .where(CurriculumItem.id == payload.curriculum_item_id)
    ).scalar_one()

    template_code = resolve_template_code(item, payload.template_code)
    template = db.execute(
        select(SheetTemplate)
        .where(SheetTemplate.code == template_code, SheetTemplate.is_active.is_(True))
    ).scalar_one()

    group_students = db.execute(select(Student).where(Student.group_id == item.group_id).order_by(Student.full_name)).scalars().all()
    header_label, header_value = resolve_header_label_and_value(item.group, template)
    discipline_label = payload.discipline_display_text or f"{item.subject.code} {item.subject.title}"

    sheet = AttestationSheet(
        group_id=item.group_id,
        semester_id=item.semester_id,
        curriculum_item_id=item.id,
        sheet_template_id=template.id,
        control_form_code=item.control_form.code,
        title=template.title,
        date=payload.date or date.today(),
        teacher_name=payload.teacher_name or current_user.full_name,
        second_teacher_name=payload.second_teacher_name,
        header_label=header_label,
        header_value=header_value,
        discipline_display_text=discipline_label,
        status="draft",
    )
    db.add(sheet)
    db.flush()

    db.add(
        AttestationSheetDiscipline(
            attestation_sheet_id=sheet.id,
            discipline_name=item.subject.title,
            discipline_code=item.subject.code,
            order_index=1,
        )
    )

    for index, student in enumerate(group_students, start=1):
        db.add(
            AttestationSheetRow(
                attestation_sheet_id=sheet.id,
                student_id=student.id,
                student_name_snapshot=student.full_name,
                row_number=index,
                ticket_number=None,
                grade_numeric=None,
                grade_text=None,
                attendance_result="regular",
                comment=None,
            )
        )

    db.flush()
    return sheet


def refresh_sheet_students_from_group(db: Session, sheet: AttestationSheet) -> None:
    students = db.execute(select(Student).where(Student.group_id == sheet.group_id).order_by(Student.full_name)).scalars().all()
    existing_by_student_id = {row.student_id: row for row in sheet.rows if row.student_id}
    updated_rows: list[AttestationSheetRow] = []

    for index, student in enumerate(students, start=1):
        existing = existing_by_student_id.get(student.id)
        if existing:
            existing.row_number = index
            existing.student_name_snapshot = student.full_name
            updated_rows.append(existing)
            continue
        updated_rows.append(
            AttestationSheetRow(
                attestation_sheet_id=sheet.id,
                student_id=student.id,
                student_name_snapshot=student.full_name,
                row_number=index,
                ticket_number=None,
                grade_numeric=None,
                grade_text=None,
                attendance_result="regular",
                comment=None,
            )
        )

    sheet.rows = updated_rows
    db.flush()


def fill_sheet_rows_from_journal(db: Session, sheet: AttestationSheet) -> None:
    if not sheet.curriculum_item_id:
        return

    rows_by_student = {row.student_id: row for row in sheet.rows if row.student_id}
    student_ids = [student_id for student_id in rows_by_student.keys() if student_id]
    if not student_ids:
        return

    latest_grades = db.execute(
        select(GradeRecord)
        .where(GradeRecord.curriculum_item_id == sheet.curriculum_item_id)
        .where(GradeRecord.student_id.in_(student_ids))
        .order_by(GradeRecord.student_id, GradeRecord.date.desc(), GradeRecord.id.desc())
    ).scalars().all()

    seen_students: set[int] = set()
    grade_map: dict[int, GradeRecord] = {}
    for grade in latest_grades:
        if grade.student_id in seen_students:
            continue
        seen_students.add(grade.student_id)
        grade_map[grade.student_id] = grade

    mode = sheet.sheet_template.grade_text_mode
    for student_id, row in rows_by_student.items():
        latest = grade_map.get(student_id)
        if not latest:
            continue
        row.grade_numeric = latest.grade_value
        row.grade_text = grade_to_text(latest.grade_value, mode)
        if row.attendance_result not in {"not_submitted", "not_appeared"}:
            row.attendance_result = "regular"
    db.flush()


def update_sheet_rows(sheet: AttestationSheet, rows: list[AttestationSheetRowUpdate]) -> None:
    row_map = {row.id: row for row in sheet.rows}
    for update in rows:
        row = row_map.get(update.id)
        if not row:
            continue
        row.ticket_number = update.ticket_number
        row.grade_numeric = update.grade_numeric
        row.attendance_result = update.attendance_result
        row.comment = update.comment
        row.grade_text = grade_to_text(update.grade_numeric, sheet.sheet_template.grade_text_mode)


def compute_totals(rows: list[AttestationSheetRow], template_code: str) -> AttestationTotalsRead:
    excellent = 0
    good = 0
    satisfactory = 0
    unsatisfactory = 0
    not_submitted = 0
    not_appeared = 0
    admitted = 0

    for row in rows:
        if row.attendance_result == "not_submitted":
            not_submitted += 1
            continue
        if row.attendance_result == "not_appeared":
            not_appeared += 1
            continue

        admitted += 1
        if row.grade_numeric == "5":
            excellent += 1
        elif row.grade_numeric == "4":
            good += 1
        elif row.grade_numeric == "3":
            satisfactory += 1
        elif row.grade_numeric == "2":
            unsatisfactory += 1

    total_rows = len(rows)
    return AttestationTotalsRead(
        excellent=excellent,
        good=good,
        satisfactory=satisfactory,
        unsatisfactory=unsatisfactory,
        not_submitted=not_submitted,
        not_appeared=not_appeared,
        admitted=admitted if template_code == "complex_exam" else 0,
        total_rows=total_rows,
        total_rows_words=number_to_words_ru(total_rows),
    )


def serialize_sheet(sheet: AttestationSheet) -> AttestationSheetRead:
    totals = compute_totals(sheet.rows, sheet.sheet_template.code)
    return AttestationSheetRead(
        id=sheet.id,
        group_id=sheet.group_id,
        group_name=sheet.group.name,
        semester_id=sheet.semester_id,
        semester_title=sheet.semester.title if sheet.semester else None,
        curriculum_item_id=sheet.curriculum_item_id,
        sheet_template=SheetTemplateRead.model_validate(sheet.sheet_template),
        control_form_code=sheet.control_form_code,
        title=sheet.title,
        date=sheet.date,
        teacher_name=sheet.teacher_name,
        second_teacher_name=sheet.second_teacher_name,
        header_label=sheet.header_label,
        header_value=sheet.header_value,
        discipline_display_text=sheet.discipline_display_text,
        status=sheet.status,
        created_at=sheet.created_at,
        updated_at=sheet.updated_at,
        program_title=sheet.group.program.title,
        college_name=settings.college_full_name,
        disciplines=[
            {
                "id": discipline.id,
                "discipline_name": discipline.discipline_name,
                "discipline_code": discipline.discipline_code,
                "order_index": discipline.order_index,
            }
            for discipline in sheet.disciplines
        ],
        rows=[
            AttestationSheetRowRead(
                id=row.id,
                student_id=row.student_id,
                student_name_snapshot=row.student_name_snapshot,
                row_number=row.row_number,
                ticket_number=row.ticket_number,
                grade_numeric=row.grade_numeric,
                grade_text=row.grade_text,
                attendance_result=row.attendance_result,
                comment=row.comment,
            )
            for row in sheet.rows
        ],
        totals=totals,
    )


@dataclass
class RenderedAttestation:
    html: str
    title: str


def render_sheet_html(sheet_data: AttestationSheetRead) -> RenderedAttestation:
    has_ticket = sheet_data.sheet_template.has_ticket_number
    is_complex_exam = sheet_data.sheet_template.code == "complex_exam"

    heading_by_template = {
        "diff_credit": "ВЕДОМОСТЬ ДИФФЕРЕНЦИРОВАННОГО ЗАЧЕТА",
        "credit_sheet": "ЗАЧЕТНАЯ ВЕДОМОСТЬ",
        "complex_diff_credit": "ВЕДОМОСТЬ КОМПЛЕКСНОГО ДИФФЕРЕНЦИРОВАННОГО ЗАЧЕТА",
        "complex_exam": "ВЕДОМОСТЬ КОМПЛЕКСНОГО ЭКЗАМЕНА",
    }
    heading = heading_by_template.get(sheet_data.sheet_template.code, sheet_data.title.upper())

    def count_with_words(value: int) -> str:
        return f"{value} ({number_to_words_ru(value)})"

    rows_html = []
    for row in sheet_data.rows:
        ticket_cell = f"<td>{escape(row.ticket_number or '')}</td>" if has_ticket else ""
        rows_html.append(
            "<tr>"
            f"<td>{row.row_number}</td>"
            f"<td>{escape(row.student_name_snapshot)}</td>"
            f"{ticket_cell}"
            f"<td>{escape(row.grade_text or row.grade_numeric or '')}</td>"
            + (f"<td>{escape(ATTENDANCE_RESULT_TITLE.get(row.attendance_result, row.attendance_result))}</td>" if not is_complex_exam else "")
            + "<td>&nbsp;</td>"
            "</tr>"
        )

    disciplines_text = ", ".join(
        f"{item.discipline_code} {item.discipline_name}".strip()
        for item in sorted(sheet_data.disciplines, key=lambda value: value.order_index)
    )
    totals = sheet_data.totals
    total_line = f"Итого: {count_with_words(totals.total_rows)}"
    if is_complex_exam:
        total_line = f"Допущено: {count_with_words(totals.admitted)}"
    totals_html = (
        f"Отлично: {count_with_words(totals.excellent)}; "
        f"Хорошо: {count_with_words(totals.good)}; "
        f"Удовлетворительно: {count_with_words(totals.satisfactory)}; "
        f"Неудовлетворительно: {count_with_words(totals.unsatisfactory)};"
    )
    if sheet_data.sheet_template.has_not_submitted_field:
        totals_html += f" Не сдавали: {count_with_words(totals.not_submitted)};"
    if sheet_data.sheet_template.has_not_appeared_field:
        totals_html += f" Не явились: {count_with_words(totals.not_appeared)};"

    signatures = []
    for index in range(max(sheet_data.sheet_template.signature_lines_count, 1)):
        label = "Преподаватель" if index == 0 else f"Преподаватель {index + 1}"
        signatures.append(f"<div>{label}: <span class='line'></span></div>")

    html = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <title>{escape(sheet_data.title)} — {escape(sheet_data.group_name)}</title>
  <style>
    @page {{ size: A4; margin: 15mm; }}
    body {{ font-family: "Times New Roman", serif; font-size: 13px; color: #111; }}
    .sheet {{ width: 100%; }}
    .center {{ text-align: center; }}
    .header-title {{ font-size: 15px; letter-spacing: 0.3px; margin: 8px 0 14px; }}
    .muted {{ color: #444; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
    th, td {{ border: 1px solid #333; padding: 6px; vertical-align: top; }}
    th {{ background: #f4f4f4; }}
    .meta-table th {{ width: 24%; text-align: left; background: #f9f9f9; }}
    .meta-table td {{ width: 26%; }}
    .score-table th {{ text-align: center; }}
    .signatures {{ margin-top: 24px; display: grid; gap: 10px; }}
    .line {{ border-bottom: 1px solid #111; height: 26px; }}
    .small {{ font-size: 12px; }}
    .totals {{ margin-top: 14px; line-height: 1.4; }}
  </style>
</head>
<body>
  <div class="sheet">
    <p class="center"><strong>{escape(sheet_data.college_name)}</strong></p>
    <div class="center header-title"><strong>{escape(heading)}</strong></div>
    <table class="meta-table">
      <tr>
        <th>Группа</th>
        <td>{escape(sheet_data.group_name)}</td>
        <th>{escape(sheet_data.header_label)}</th>
        <td>{escape(sheet_data.header_value)}</td>
      </tr>
      <tr>
        <th>Дисциплина</th>
        <td colspan="3">{escape(sheet_data.discipline_display_text)}</td>
      </tr>
      <tr>
        <th>Состав дисциплин</th>
        <td colspan="3">{escape(disciplines_text)}</td>
      </tr>
      <tr>
        <th>Преподаватель</th>
        <td>{escape(sheet_data.teacher_name)}</td>
        <th>Дата</th>
        <td>{sheet_data.date}</td>
      </tr>
    </table>
    <table class="score-table">
      <thead>
        <tr>
          <th>№</th>
          <th>ФИО студента</th>
          {"<th>Билет/вариант</th>" if has_ticket else ""}
          <th>{"Оценка (цифрой и прописью)" if is_complex_exam else "Оценка"}</th>
          {"" if is_complex_exam else "<th>Статус</th>"}
          <th>{"Подпись экзаменатора" if is_complex_exam else "Подпись"}</th>
        </tr>
      </thead>
      <tbody>
        {''.join(rows_html)}
      </tbody>
    </table>
    <div class="totals small">
      <p><strong>{escape(total_line)}</strong></p>
      <p>{escape(totals_html)}</p>
    </div>
    <div class="signatures">
      {''.join(signatures)}
      <div>Заведующий отделением: <span class="line"></span></div>
    </div>
  </div>
</body>
</html>
"""
    return RenderedAttestation(html=html, title=f"{sheet_data.group_name}_{sheet_data.id}")


def save_print_snapshot(db: Session, sheet: AttestationSheet, html: str, pdf_path: str | None = None, docx_path: str | None = None) -> PrintSnapshot:
    snapshot = PrintSnapshot(
        attestation_sheet_id=sheet.id,
        html_snapshot=html,
        pdf_path=pdf_path,
        docx_path=docx_path,
    )
    db.add(snapshot)
    db.flush()
    return snapshot
