"use client";

import { useParams } from "next/navigation";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import { useAuth } from "@/components/auth-provider";
import { PageShell } from "@/components/page-shell";
import { ProtectedPage } from "@/components/protected-page";
import { apiFetch, downloadBase64File } from "@/lib/api";
import { AttestationExport, AttestationPreview, AttestationSheet } from "@/lib/types";

type SheetTab = "fill" | "preview" | "print";

type AttendanceResult = "regular" | "not_submitted" | "not_appeared";

interface RowDraft {
  id: number;
  ticket_number: string;
  grade_numeric: string;
  attendance_result: AttendanceResult;
  comment: string;
}

const GRADE_OPTIONS = ["", "5", "4", "3", "2", "н/а", "зачет", "незачет"];

const ATTENDANCE_OPTIONS: Array<{ value: AttendanceResult; label: string }> = [
  { value: "regular", label: "Обычная сдача" },
  { value: "not_submitted", label: "Не сдавал" },
  { value: "not_appeared", label: "Не явился" },
];

const GRADE_TEXT_FULL: Record<string, string> = {
  "5": "5 (отлично)",
  "4": "4 (хорошо)",
  "3": "3 (удовлетворительно)",
  "2": "2 (неудовлетворительно)",
  "н/а": "н/а",
  зачет: "зачет",
  незачет: "незачет",
};

export default function AttestationSheetPage() {
  const params = useParams<{ id: string }>();
  const { token } = useAuth();

  const [tab, setTab] = useState<SheetTab>("fill");
  const [sheet, setSheet] = useState<AttestationSheet | null>(null);
  const [rowDrafts, setRowDrafts] = useState<RowDraft[]>([]);
  const [dateValue, setDateValue] = useState("");
  const [teacherName, setTeacherName] = useState("");
  const [secondTeacherName, setSecondTeacherName] = useState("");
  const [disciplineDisplayText, setDisciplineDisplayText] = useState("");
  const [disciplineDrafts, setDisciplineDrafts] = useState<Array<{ id: number; discipline_name: string; discipline_code: string; order_index: number }>>([]);

  const [previewHtml, setPreviewHtml] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const hasTicketNumber = sheet?.sheet_template.has_ticket_number ?? false;
  const isSaved = sheet?.status === "saved";

  const loadSheet = useCallback(async () => {
    if (!token) {
      return;
    }
    const response = await apiFetch<AttestationSheet>(`/attestation-sheets/${params.id}`, {}, token);
    setSheet(response);
    setDateValue(response.date);
    setTeacherName(response.teacher_name);
    setSecondTeacherName(response.second_teacher_name ?? "");
    setDisciplineDisplayText(response.discipline_display_text);
    setDisciplineDrafts(
      response.disciplines.map((item) => ({
        id: item.id,
        discipline_name: item.discipline_name,
        discipline_code: item.discipline_code ?? "",
        order_index: item.order_index,
      }))
    );
    setRowDrafts(
      response.rows.map((row) => ({
        id: row.id,
        ticket_number: row.ticket_number ?? "",
        grade_numeric: row.grade_numeric ?? "",
        attendance_result: row.attendance_result,
        comment: row.comment ?? "",
      }))
    );
  }, [params.id, token]);

  useEffect(() => {
    if (!token) {
      return;
    }
    loadSheet().catch((err) => setError(err.message));
  }, [loadSheet, token]);

  async function saveSheet(status: "draft" | "saved") {
    if (!token || !sheet) {
      return;
    }
    setLoading(true);
    setError(null);
    setNotice(null);
    try {
      await apiFetch<AttestationSheet>(
        `/attestation-sheets/${sheet.id}`,
        {
          method: "PUT",
          body: JSON.stringify({
            date: dateValue,
            teacher_name: teacherName,
            second_teacher_name: secondTeacherName || null,
            discipline_display_text: disciplineDisplayText,
            status,
            rows: rowDrafts.map((row) => ({
              id: row.id,
              ticket_number: row.ticket_number || null,
              grade_numeric: row.grade_numeric || null,
              attendance_result: row.attendance_result,
              comment: row.comment || null,
            })),
            disciplines: disciplineDrafts.map((item) => ({
              id: item.id,
              discipline_name: item.discipline_name,
              discipline_code: item.discipline_code || null,
              order_index: item.order_index,
            })),
          }),
        },
        token
      );
      await loadSheet();
      setNotice(status === "saved" ? "Ведомость сохранена." : "Черновик сохранен.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось сохранить ведомость.");
    } finally {
      setLoading(false);
    }
  }

  async function refreshStudents() {
    if (!token || !sheet) {
      return;
    }
    setLoading(true);
    setError(null);
    setNotice(null);
    try {
      await apiFetch<AttestationSheet>(`/attestation-sheets/${sheet.id}/refresh-students`, { method: "POST" }, token);
      await loadSheet();
      setNotice("Состав ведомости обновлен из группы.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось обновить состав.");
    } finally {
      setLoading(false);
    }
  }

  async function fillFromJournal() {
    if (!token || !sheet) {
      return;
    }
    setLoading(true);
    setError(null);
    setNotice(null);
    try {
      await apiFetch<AttestationSheet>(`/attestation-sheets/${sheet.id}/fill-from-journal`, { method: "POST" }, token);
      await loadSheet();
      setNotice("Оценки из журнала перенесены в ведомость.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось заполнить из журнала.");
    } finally {
      setLoading(false);
    }
  }

  async function loadPreview() {
    if (!token || !sheet) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await apiFetch<AttestationPreview>(`/attestation-sheets/${sheet.id}/preview`, {}, token);
      setPreviewHtml(response.html);
      setTab("preview");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось построить предпросмотр.");
    } finally {
      setLoading(false);
    }
  }

  function printPreview() {
    if (!previewHtml) {
      return;
    }
    const popup = window.open("", "_blank", "noopener,noreferrer");
    if (!popup) {
      setError("Браузер заблокировал окно печати. Разрешите всплывающие окна.");
      return;
    }
    popup.document.open();
    popup.document.write(previewHtml);
    popup.document.close();
    popup.focus();
    popup.print();
  }

  async function downloadExport(type: "pdf" | "docx") {
    if (!token || !sheet) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await apiFetch<AttestationExport>(`/attestation-sheets/${sheet.id}/export/${type}`, {}, token);
      downloadBase64File(result.content_base64, result.filename, result.content_type);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось скачать файл.");
    } finally {
      setLoading(false);
    }
  }

  const disciplineTitle = useMemo(() => {
    if (!sheet) {
      return "Ведомость";
    }
    return `${sheet.title} — ${sheet.group_name}`;
  }, [sheet]);

  return (
    <ProtectedPage roles={["admin", "curator", "teacher"]}>
      <PageShell
        title={disciplineTitle}
        description="Мастер ведомости: заполнение, предпросмотр и печать. Все реквизиты и состав группы подставляются автоматически."
        breadcrumbs={[
          { label: "Главная", href: "/dashboard" },
          { label: "Ведомости", href: "/attestation-sheets" },
          { label: sheet ? `№${sheet.id}` : "Ведомость" },
        ]}
      >
        {error ? <div className="error-box">{error}</div> : null}
        {notice ? <div className="note-box">{notice}</div> : null}

        <div className="tabs-row">
          <button type="button" className={`tab-button ${tab === "fill" ? "tab-button-active" : ""}`} onClick={() => setTab("fill")}>
            Заполнение
          </button>
          <button type="button" className={`tab-button ${tab === "preview" ? "tab-button-active" : ""}`} onClick={loadPreview}>
            Предпросмотр
          </button>
          <button type="button" className={`tab-button ${tab === "print" ? "tab-button-active" : ""}`} onClick={() => setTab("print")}>
            Печать
          </button>
        </div>

        {tab === "fill" ? (
          <>
            <form
              className="card"
              onSubmit={(event: FormEvent) => {
                event.preventDefault();
                saveSheet("draft");
              }}
            >
              <h3 className="section-title">Шапка ведомости</h3>
              <div className="meta-grid">
                <div className="meta">
                  <strong>Тип ведомости</strong>
                  {sheet?.sheet_template.title ?? "—"}
                </div>
                <div className="meta">
                  <strong>Группа</strong>
                  {sheet?.group_name ?? "—"}
                </div>
                <div className="meta">
                  <strong>{sheet?.header_label ?? "Специальность"}</strong>
                  {sheet?.header_value ?? "—"}
                </div>
                <label className="field">
                  <span>Дата</span>
                  <input type="date" value={dateValue} onChange={(event) => setDateValue(event.target.value)} disabled={isSaved} />
                </label>
                <label className="field">
                  <span>Преподаватель</span>
                  <input value={teacherName} onChange={(event) => setTeacherName(event.target.value)} disabled={isSaved} />
                </label>
                <label className="field">
                  <span>Второй преподаватель (при необходимости)</span>
                  <input value={secondTeacherName} onChange={(event) => setSecondTeacherName(event.target.value)} disabled={isSaved} />
                </label>
              </div>

              <label className="field">
                <span>Текст дисциплины для печати</span>
                <textarea value={disciplineDisplayText} onChange={(event) => setDisciplineDisplayText(event.target.value)} disabled={isSaved} />
              </label>
              {isSaved ? <div className="note-box">Ведомость сохранена: состав группы зафиксирован и недоступен для обновления.</div> : null}

              <h4>Состав дисциплин в ведомости</h4>
              <table className="compact-table">
                <thead>
                  <tr>
                    <th>№</th>
                    <th>Код</th>
                    <th>Дисциплина</th>
                  </tr>
                </thead>
                <tbody>
                  {disciplineDrafts.map((item, index) => (
                    <tr key={item.id}>
                      <td>{item.order_index}</td>
                      <td>
                        <input
                          value={item.discipline_code}
                          disabled={isSaved}
                          onChange={(event) =>
                            setDisciplineDrafts((prev) =>
                              prev.map((current, currentIndex) =>
                                currentIndex === index ? { ...current, discipline_code: event.target.value } : current
                              )
                            )
                          }
                        />
                      </td>
                      <td>
                        <input
                          value={item.discipline_name}
                          disabled={isSaved}
                          onChange={(event) =>
                            setDisciplineDrafts((prev) =>
                              prev.map((current, currentIndex) =>
                                currentIndex === index ? { ...current, discipline_name: event.target.value } : current
                              )
                            )
                          }
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <h3 className="section-title">Список студентов</h3>
              <table className="compact-table">
                <thead>
                  <tr>
                    <th>№</th>
                    <th>ФИО студента</th>
                    {hasTicketNumber ? <th>Билет/вариант</th> : null}
                    <th>Оценка</th>
                    <th>Оценка прописью</th>
                    <th>Статус</th>
                    <th>Подпись</th>
                  </tr>
                </thead>
                <tbody>
                  {sheet?.rows.map((row, index) => (
                    <tr key={row.id}>
                      <td>{row.row_number}</td>
                      <td>{row.student_name_snapshot}</td>
                      {hasTicketNumber ? (
                        <td>
                          <input
                            value={rowDrafts[index]?.ticket_number ?? ""}
                            disabled={isSaved}
                            onChange={(event) =>
                              setRowDrafts((prev) =>
                                prev.map((current, currentIndex) =>
                                  currentIndex === index ? { ...current, ticket_number: event.target.value } : current
                                )
                              )
                            }
                          />
                        </td>
                      ) : null}
                      <td>
                        <select
                          value={rowDrafts[index]?.grade_numeric ?? ""}
                          disabled={isSaved}
                          onChange={(event) =>
                            setRowDrafts((prev) =>
                              prev.map((current, currentIndex) =>
                                currentIndex === index ? { ...current, grade_numeric: event.target.value } : current
                              )
                            )
                          }
                        >
                          {GRADE_OPTIONS.map((grade) => (
                            <option key={grade || "empty"} value={grade}>
                              {grade || "—"}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td>{GRADE_TEXT_FULL[rowDrafts[index]?.grade_numeric ?? ""] ?? row.grade_text ?? "—"}</td>
                      <td>
                        <select
                          value={rowDrafts[index]?.attendance_result ?? "regular"}
                          disabled={isSaved}
                          onChange={(event) =>
                            setRowDrafts((prev) =>
                              prev.map((current, currentIndex) =>
                                currentIndex === index
                                  ? { ...current, attendance_result: event.target.value as AttendanceResult }
                                  : current
                              )
                            )
                          }
                        >
                          {ATTENDANCE_OPTIONS.map((option) => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td>_____________</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <div className="button-row">
                <button type="submit" className="button" disabled={loading || isSaved}>
                  {loading ? "Сохраняем..." : "Сохранить черновик"}
                </button>
                <button type="button" className="button button-link" onClick={() => saveSheet("saved")} disabled={loading || isSaved}>
                  Сохранить ведомость
                </button>
                <button type="button" className="button button-link" onClick={refreshStudents} disabled={loading || isSaved}>
                  Обновить состав из группы
                </button>
                <button type="button" className="button button-link" onClick={fillFromJournal} disabled={loading || isSaved}>
                  Заполнить из журнала
                </button>
              </div>
            </form>

            <div className="card">
              <h3 className="section-title">Итоги по ведомости</h3>
              <div className="meta-grid">
                <div className="meta">
                  <strong>Отлично</strong>
                  {sheet?.totals.excellent ?? 0}
                </div>
                <div className="meta">
                  <strong>Хорошо</strong>
                  {sheet?.totals.good ?? 0}
                </div>
                <div className="meta">
                  <strong>Удовлетворительно</strong>
                  {sheet?.totals.satisfactory ?? 0}
                </div>
                <div className="meta">
                  <strong>Неудовлетворительно</strong>
                  {sheet?.totals.unsatisfactory ?? 0}
                </div>
                <div className="meta">
                  <strong>Не сдавали</strong>
                  {sheet?.totals.not_submitted ?? 0}
                </div>
                <div className="meta">
                  <strong>Не явились</strong>
                  {sheet?.totals.not_appeared ?? 0}
                </div>
              </div>
            </div>
          </>
        ) : null}

        {tab === "preview" ? (
          <div className="card">
            <div className="button-row">
              <button type="button" className="button button-link" onClick={loadPreview} disabled={loading}>
                Обновить предпросмотр
              </button>
              <button type="button" className="button" onClick={printPreview} disabled={!previewHtml}>
                Печать
              </button>
            </div>
            {previewHtml ? (
              <iframe title="Предпросмотр ведомости" srcDoc={previewHtml} className="preview-frame" />
            ) : (
              <p className="muted">Нажмите «Обновить предпросмотр», чтобы увидеть печатную форму.</p>
            )}
          </div>
        ) : null}

        {tab === "print" ? (
          <div className="card">
            <h3 className="section-title">Печать и выгрузка</h3>
            <div className="button-row">
              <button type="button" className="button button-link" onClick={() => saveSheet("draft")} disabled={loading || isSaved}>
                Сохранить черновик
              </button>
              <button type="button" className="button button-link" onClick={() => saveSheet("saved")} disabled={loading || isSaved}>
                Сохранить ведомость
              </button>
              <button type="button" className="button" onClick={printPreview} disabled={!previewHtml}>
                Печать
              </button>
              <button type="button" className="button button-link" onClick={() => downloadExport("pdf")} disabled={loading}>
                Скачать PDF
              </button>
              <button type="button" className="button button-link" onClick={() => downloadExport("docx")} disabled={loading}>
                Скачать DOCX
              </button>
            </div>
          </div>
        ) : null}
      </PageShell>
    </ProtectedPage>
  );
}
