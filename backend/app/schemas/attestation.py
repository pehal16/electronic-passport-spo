from __future__ import annotations

from datetime import date as DateType
from datetime import datetime as DateTimeType

from pydantic import BaseModel, ConfigDict


class SheetTemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    title: str
    type: str
    header_label_type: str
    has_ticket_number: bool
    has_multiple_disciplines: bool
    has_not_appeared_field: bool
    has_not_submitted_field: bool
    signature_lines_count: int
    grade_text_mode: str
    is_active: bool


class AttestationSheetDisciplineRead(BaseModel):
    id: int
    discipline_name: str
    discipline_code: str | None
    order_index: int


class AttestationSheetRowRead(BaseModel):
    id: int
    student_id: int | None
    student_name_snapshot: str
    row_number: int
    ticket_number: str | None
    grade_numeric: str | None
    grade_text: str | None
    attendance_result: str
    comment: str | None


class AttestationTotalsRead(BaseModel):
    excellent: int
    good: int
    satisfactory: int
    unsatisfactory: int
    not_submitted: int
    not_appeared: int
    admitted: int
    total_rows: int
    total_rows_words: str


class AttestationSheetRead(BaseModel):
    id: int
    group_id: int
    group_name: str
    semester_id: int | None
    semester_title: str | None
    curriculum_item_id: int | None
    sheet_template: SheetTemplateRead
    control_form_code: str
    title: str
    date: DateType
    teacher_name: str
    second_teacher_name: str | None
    header_label: str
    header_value: str
    discipline_display_text: str
    status: str
    created_at: DateTimeType
    updated_at: DateTimeType
    program_title: str
    college_name: str
    disciplines: list[AttestationSheetDisciplineRead]
    rows: list[AttestationSheetRowRead]
    totals: AttestationTotalsRead


class AttestationSheetCreateRequest(BaseModel):
    curriculum_item_id: int
    date: DateType | None = None
    teacher_name: str | None = None
    second_teacher_name: str | None = None
    discipline_display_text: str | None = None
    template_code: str | None = None


class AttestationSheetRowUpdate(BaseModel):
    id: int
    ticket_number: str | None = None
    grade_numeric: str | None = None
    attendance_result: str
    comment: str | None = None


class AttestationSheetDisciplineUpdate(BaseModel):
    id: int | None = None
    discipline_name: str
    discipline_code: str | None = None
    order_index: int


class AttestationSheetUpdateRequest(BaseModel):
    date: DateType
    teacher_name: str
    second_teacher_name: str | None = None
    discipline_display_text: str
    status: str = "draft"
    rows: list[AttestationSheetRowUpdate]
    disciplines: list[AttestationSheetDisciplineUpdate]


class AttestationPreviewRead(BaseModel):
    sheet_id: int
    html: str


class AttestationExportRead(BaseModel):
    sheet_id: int
    filename: str
    content_type: str
    content_base64: str
