"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { useAuth } from "@/components/auth-provider";
import { PageShell } from "@/components/page-shell";
import { ProtectedPage } from "@/components/protected-page";
import { apiFetch, buildQuery } from "@/lib/api";
import { controlFormTitle } from "@/lib/dictionaries";
import { GradeRecord, GroupSummary, JournalRow, Semester, StudentListItem } from "@/lib/types";

type EntryMode = "sheet" | "quick";

function todayIsoDate() {
  return new Date().toISOString().slice(0, 10);
}

interface GradeDraft {
  value: string;
  comment: string;
}

const gradeOptions = ["5", "4", "3", "2", "н/а", "зачет", "незачет"];

export default function GradesPage() {
  const { token, user } = useAuth();

  const [groups, setGroups] = useState<GroupSummary[]>([]);
  const [semesters, setSemesters] = useState<Semester[]>([]);
  const [students, setStudents] = useState<StudentListItem[]>([]);
  const [journalRows, setJournalRows] = useState<JournalRow[]>([]);
  const [records, setRecords] = useState<GradeRecord[]>([]);

  const [mode, setMode] = useState<EntryMode>("sheet");
  const [selectedGroupId, setSelectedGroupId] = useState("");
  const [selectedSemesterId, setSelectedSemesterId] = useState("");
  const [selectedItemId, setSelectedItemId] = useState("");
  const [selectedStudentId, setSelectedStudentId] = useState("");
  const [dateValue, setDateValue] = useState(todayIsoDate());
  const [quickValue, setQuickValue] = useState("5");
  const [quickComment, setQuickComment] = useState("");
  const [sheetDraft, setSheetDraft] = useState<Record<number, GradeDraft>>({});

  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const canEdit = useMemo(() => ["admin", "teacher"].includes(user?.role.code ?? ""), [user?.role.code]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const groupId = params.get("group_id");
    const semesterId = params.get("semester_id");
    const curriculumItemId = params.get("curriculum_item_id");
    if (groupId) {
      setSelectedGroupId(groupId);
    }
    if (semesterId) {
      setSelectedSemesterId(semesterId);
    }
    if (curriculumItemId) {
      setSelectedItemId(curriculumItemId);
    }
  }, []);

  useEffect(() => {
    if (!token) {
      return;
    }
    apiFetch<GroupSummary[]>("/groups", {}, token)
      .then((items) => {
        setGroups(items);
        setSelectedGroupId((prev) => (prev || (items.length ? String(items[0].id) : "")));
      })
      .catch((err) => setError(err.message));
  }, [token]);

  useEffect(() => {
    if (!token || !selectedGroupId) {
      return;
    }
    apiFetch<StudentListItem[]>(`/groups/${selectedGroupId}/students`, {}, token)
      .then((items) => {
        setStudents(items);
        setSelectedStudentId((prev) => (prev ? prev : items[0] ? String(items[0].id) : ""));
      })
      .catch((err) => setError(err.message));

    apiFetch<Semester[]>(`/groups/${selectedGroupId}/semesters`, {}, token)
      .then((items) => {
        setSemesters(items);
        if (!selectedSemesterId && items.length) {
          setSelectedSemesterId(String(items[0].id));
        }
      })
      .catch((err) => setError(err.message));

    apiFetch<JournalRow[]>(`/journal${buildQuery({ group_id: selectedGroupId })}`, {}, token)
      .then((items) => {
        setJournalRows(items);
        if (!selectedItemId && items.length) {
          setSelectedItemId(String(items[0].curriculum_item_id));
        }
      })
      .catch((err) => setError(err.message));
  }, [selectedGroupId, selectedItemId, selectedSemesterId, token]);

  const disciplineOptions = useMemo(() => {
    if (!selectedSemesterId) {
      return journalRows;
    }
    return journalRows.filter((row) => String(row.semester_id) === selectedSemesterId);
  }, [journalRows, selectedSemesterId]);

  const selectedDiscipline = useMemo(
    () => disciplineOptions.find((row) => String(row.curriculum_item_id) === selectedItemId) ?? null,
    [disciplineOptions, selectedItemId]
  );

  useEffect(() => {
    setSheetDraft((prev) => {
      const nextDraft: Record<number, GradeDraft> = {};
      students.forEach((student) => {
        nextDraft[student.id] = prev[student.id] ?? { value: "5", comment: "" };
      });
      return nextDraft;
    });
  }, [students]);

  useEffect(() => {
    if (!token) {
      return;
    }
    const query = buildQuery({
      group_id: selectedGroupId || undefined,
      semester_id: selectedSemesterId || undefined,
      curriculum_item_id: selectedItemId || undefined
    });
    apiFetch<GradeRecord[]>(`/grades${query}`, {}, token).then(setRecords).catch((err) => setError(err.message));
  }, [selectedGroupId, selectedItemId, selectedSemesterId, token]);

  async function saveQuickGrade(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !selectedStudentId || !selectedItemId) {
      setError("Выберите группу, семестр, дисциплину и студента.");
      return;
    }
    setSaving(true);
    setError(null);
    setNotice(null);
    try {
      const result = await apiFetch<{ message: string }>(
        "/grades",
        {
          method: "POST",
          body: JSON.stringify({
            student_id: Number(selectedStudentId),
            curriculum_item_id: Number(selectedItemId),
            date: dateValue,
            grade_value: quickValue,
            comment: quickComment || null
          })
        },
        token
      );
      setNotice(result.message);
      const query = buildQuery({
        group_id: selectedGroupId || undefined,
        semester_id: selectedSemesterId || undefined,
        curriculum_item_id: selectedItemId || undefined
      });
      const items = await apiFetch<GradeRecord[]>(`/grades${query}`, {}, token);
      setRecords(items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось сохранить оценку.");
    } finally {
      setSaving(false);
    }
  }

  async function saveSheetGrades(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !selectedItemId) {
      setError("Выберите дисциплину.");
      return;
    }
    setSaving(true);
    setError(null);
    setNotice(null);
    try {
      const entries = students.map((student) => ({
        student_id: student.id,
        grade_value: sheetDraft[student.id]?.value ?? "5",
        comment: sheetDraft[student.id]?.comment || null
      }));
      const result = await apiFetch<{ message: string }>(
        "/grades/bulk",
        {
          method: "POST",
          body: JSON.stringify({
            curriculum_item_id: Number(selectedItemId),
            date: dateValue,
            entries
          })
        },
        token
      );
      setNotice(result.message);
      const query = buildQuery({
        group_id: selectedGroupId || undefined,
        semester_id: selectedSemesterId || undefined,
        curriculum_item_id: selectedItemId || undefined
      });
      const items = await apiFetch<GradeRecord[]>(`/grades${query}`, {}, token);
      setRecords(items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось сохранить оценки группы.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <ProtectedPage>
      <PageShell
        title="Оценки"
        description="Рабочая логика: группа → семестр → дисциплина → дата → ведомость группы."
        breadcrumbs={[{ label: "Главная", href: "/dashboard" }, { label: "Оценки" }]}
      >
        {error ? <div className="error-box">{error}</div> : null}
        {notice ? <div className="note-box">{notice}</div> : null}

        <div className="card">
          <h3 className="section-title">Параметры ведомости</h3>
          <div className="meta-grid">
            <label className="field">
              <span>Группа</span>
              <select value={selectedGroupId} onChange={(event) => setSelectedGroupId(event.target.value)}>
                {groups.map((group) => (
                  <option key={group.id} value={group.id}>
                    {group.name}
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              <span>Семестр</span>
              <select value={selectedSemesterId} onChange={(event) => setSelectedSemesterId(event.target.value)}>
                {semesters.map((semester) => (
                  <option key={semester.id} value={semester.id}>
                    {semester.title}
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              <span>Дисциплина</span>
              <select value={selectedItemId} onChange={(event) => setSelectedItemId(event.target.value)}>
                {disciplineOptions.map((row) => (
                  <option key={row.curriculum_item_id} value={row.curriculum_item_id}>
                    {row.subject_code} {row.subject_title}
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              <span>Дата</span>
              <input type="date" value={dateValue} onChange={(event) => setDateValue(event.target.value)} />
            </label>
          </div>
          {selectedDiscipline ? (
            <>
              <p className="muted">
                Форма контроля: {controlFormTitle(selectedDiscipline.control_form_code, selectedDiscipline.control_form_title)}
              </p>
              <div className="button-row">
                <Link
                  href={`/attestation-sheets/new?curriculum_item_id=${selectedDiscipline.curriculum_item_id}`}
                  className="button button-link compact-button"
                >
                  Сформировать ведомость
                </Link>
                <Link href={`/attestation-sheets${selectedGroupId ? `?group_id=${selectedGroupId}` : ""}`} className="button button-link compact-button">
                  Открыть мастер ведомостей
                </Link>
              </div>
            </>
          ) : (
            <div className="button-row">
              <Link href={`/attestation-sheets${selectedGroupId ? `?group_id=${selectedGroupId}` : ""}`} className="button button-link compact-button">
                Открыть мастер ведомостей
              </Link>
            </div>
          )}
        </div>

        {canEdit ? (
          <>
            <div className="tabs-row">
              <button type="button" className={`tab-button ${mode === "sheet" ? "tab-button-active" : ""}`} onClick={() => setMode("sheet")}>
                Ведомость группы
              </button>
              <button type="button" className={`tab-button ${mode === "quick" ? "tab-button-active" : ""}`} onClick={() => setMode("quick")}>
                Быстрое внесение
              </button>
            </div>

            {mode === "quick" ? (
              <form className="card" onSubmit={saveQuickGrade}>
                <h3 className="section-title">Быстрое выставление одной оценки</h3>
                <div className="meta-grid">
                  <label className="field">
                    <span>Студент</span>
                    <select value={selectedStudentId} onChange={(event) => setSelectedStudentId(event.target.value)}>
                      {students.map((student) => (
                        <option key={student.id} value={student.id}>
                          {student.full_name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="field">
                    <span>Оценка</span>
                    <select value={quickValue} onChange={(event) => setQuickValue(event.target.value)}>
                      {gradeOptions.map((value) => (
                        <option key={value} value={value}>
                          {value}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="field">
                    <span>Комментарий</span>
                    <input value={quickComment} onChange={(event) => setQuickComment(event.target.value)} />
                  </label>
                </div>
                <button className="button" type="submit" disabled={saving}>
                  {saving ? "Сохраняем..." : "Сохранить оценку"}
                </button>
              </form>
            ) : (
              <form className="card" onSubmit={saveSheetGrades}>
                <h3 className="section-title">Ведомость группы</h3>
                <table className="compact-table">
                  <thead>
                    <tr>
                      <th>ФИО</th>
                      <th>Оценка</th>
                      <th>Комментарий</th>
                    </tr>
                  </thead>
                  <tbody>
                    {students.map((student) => (
                      <tr key={student.id}>
                        <td>{student.full_name}</td>
                        <td>
                          <select
                            value={sheetDraft[student.id]?.value ?? "5"}
                            onChange={(event) =>
                              setSheetDraft((prev) => ({
                                ...prev,
                                [student.id]: {
                                  value: event.target.value,
                                  comment: prev[student.id]?.comment ?? ""
                                }
                              }))
                            }
                          >
                            {gradeOptions.map((value) => (
                              <option key={value} value={value}>
                                {value}
                              </option>
                            ))}
                          </select>
                        </td>
                        <td>
                          <input
                            value={sheetDraft[student.id]?.comment ?? ""}
                            onChange={(event) =>
                              setSheetDraft((prev) => ({
                                ...prev,
                                [student.id]: {
                                  value: prev[student.id]?.value ?? "5",
                                  comment: event.target.value
                                }
                              }))
                            }
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <button className="button" type="submit" disabled={saving}>
                  {saving ? "Сохраняем..." : "Сохранить оценки группы"}
                </button>
              </form>
            )}
          </>
        ) : null}

        <div className="table-card">
          <h3 className="section-title">История оценок</h3>
          {records.length ? (
            <table>
              <thead>
                <tr>
                  <th>Дата</th>
                  <th>Студент</th>
                  <th>Дисциплина</th>
                  <th>Оценка</th>
                  <th>Комментарий</th>
                </tr>
              </thead>
              <tbody>
                {records.map((record) => (
                  <tr key={record.id}>
                    <td>{record.date}</td>
                    <td>{record.student_name}</td>
                    <td>{record.curriculum_item_title}</td>
                    <td>{record.grade_value}</td>
                    <td>{record.comment ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="muted">Оценки по этой дисциплине еще не внесены.</p>
          )}
        </div>
      </PageShell>
    </ProtectedPage>
  );
}
