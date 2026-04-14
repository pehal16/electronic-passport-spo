"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import { useAuth } from "@/components/auth-provider";
import { PageShell } from "@/components/page-shell";
import { ProtectedPage } from "@/components/protected-page";
import { apiFetch, buildQuery } from "@/lib/api";
import { attendanceStatusTitle } from "@/lib/dictionaries";
import { AttendanceRecord, GroupSummary, JournalRow, Semester, StudentListItem } from "@/lib/types";

type AttendanceStatus = "present" | "absent" | "excused" | "late";
type EntryMode = "sheet" | "quick";

function todayIsoDate() {
  return new Date().toISOString().slice(0, 10);
}

interface AttendanceDraft {
  status: AttendanceStatus;
  reason: string;
}

export default function AttendancePage() {
  const { token, user } = useAuth();

  const [groups, setGroups] = useState<GroupSummary[]>([]);
  const [semesters, setSemesters] = useState<Semester[]>([]);
  const [students, setStudents] = useState<StudentListItem[]>([]);
  const [journalRows, setJournalRows] = useState<JournalRow[]>([]);
  const [records, setRecords] = useState<AttendanceRecord[]>([]);

  const [mode, setMode] = useState<EntryMode>("sheet");
  const [selectedGroupId, setSelectedGroupId] = useState("");
  const [selectedSemesterId, setSelectedSemesterId] = useState("");
  const [selectedItemId, setSelectedItemId] = useState("");
  const [selectedStudentId, setSelectedStudentId] = useState("");
  const [dateValue, setDateValue] = useState(todayIsoDate());
  const [quickStatus, setQuickStatus] = useState<AttendanceStatus>("present");
  const [quickReason, setQuickReason] = useState("");
  const [sheetDraft, setSheetDraft] = useState<Record<number, AttendanceDraft>>({});

  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const canEdit = useMemo(() => ["admin", "curator", "teacher"].includes(user?.role.code ?? ""), [user?.role.code]);

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

  useEffect(() => {
    setSheetDraft((prev) => {
      const nextDraft: Record<number, AttendanceDraft> = {};
      students.forEach((student) => {
        nextDraft[student.id] = prev[student.id] ?? { status: "present", reason: "" };
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
    apiFetch<AttendanceRecord[]>(`/attendance${query}`, {}, token)
      .then((items) => setRecords(items))
      .catch((err) => setError(err.message));
  }, [selectedGroupId, selectedItemId, selectedSemesterId, token]);

  async function saveQuickAttendance(event: FormEvent<HTMLFormElement>) {
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
        "/attendance",
        {
          method: "POST",
          body: JSON.stringify({
            student_id: Number(selectedStudentId),
            curriculum_item_id: Number(selectedItemId),
            date: dateValue,
            status: quickStatus,
            reason: quickReason || null
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
      const items = await apiFetch<AttendanceRecord[]>(`/attendance${query}`, {}, token);
      setRecords(items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось сохранить посещаемость.");
    } finally {
      setSaving(false);
    }
  }

  async function saveSheetAttendance(event: FormEvent<HTMLFormElement>) {
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
        status: sheetDraft[student.id]?.status ?? "present",
        reason: sheetDraft[student.id]?.reason || null
      }));
      const result = await apiFetch<{ message: string }>(
        "/attendance/bulk",
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
      const items = await apiFetch<AttendanceRecord[]>(`/attendance${query}`, {}, token);
      setRecords(items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось сохранить посещаемость группы.");
    } finally {
      setSaving(false);
    }
  }

  const studentSummary = useMemo(() => {
    const summary: Record<number, { present: number; absent: number; excused: number; late: number }> = {};
    records.forEach((record) => {
      const target = summary[record.student_id] ?? { present: 0, absent: 0, excused: 0, late: 0 };
      if (record.status === "present") {
        target.present += 1;
      } else if (record.status === "absent") {
        target.absent += 1;
      } else if (record.status === "excused") {
        target.excused += 1;
      } else if (record.status === "late") {
        target.late += 1;
      }
      summary[record.student_id] = target;
    });
    return summary;
  }, [records]);

  return (
    <ProtectedPage>
      <PageShell
        title="Посещаемость"
        description="Рабочая логика: группа → семестр → дисциплина → дата → список студентов."
        breadcrumbs={[{ label: "Главная", href: "/dashboard" }, { label: "Посещаемость" }]}
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
        </div>

        {canEdit ? (
          <>
            <div className="tabs-row">
              <button type="button" className={`tab-button ${mode === "sheet" ? "tab-button-active" : ""}`} onClick={() => setMode("sheet")}>
                Ведомость на всю группу
              </button>
              <button type="button" className={`tab-button ${mode === "quick" ? "tab-button-active" : ""}`} onClick={() => setMode("quick")}>
                Быстрое внесение по студенту
              </button>
            </div>

            {mode === "quick" ? (
              <form className="card" onSubmit={saveQuickAttendance}>
                <h3 className="section-title">Быстрое внесение</h3>
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
                    <span>Статус</span>
                    <select value={quickStatus} onChange={(event) => setQuickStatus(event.target.value as AttendanceStatus)}>
                      <option value="present">Присутствовал</option>
                      <option value="absent">Отсутствовал</option>
                      <option value="excused">Уважительная причина</option>
                      <option value="late">Опоздал</option>
                    </select>
                  </label>
                  <label className="field">
                    <span>Причина / комментарий</span>
                    <input value={quickReason} onChange={(event) => setQuickReason(event.target.value)} />
                  </label>
                </div>
                <button className="button" type="submit" disabled={saving}>
                  {saving ? "Сохраняем..." : "Сохранить посещаемость"}
                </button>
              </form>
            ) : (
              <form className="card" onSubmit={saveSheetAttendance}>
                <h3 className="section-title">Ведомость группы</h3>
                <table className="compact-table">
                  <thead>
                    <tr>
                      <th>ФИО</th>
                      <th>Статус</th>
                      <th>Причина / комментарий</th>
                    </tr>
                  </thead>
                  <tbody>
                    {students.map((student) => (
                      <tr key={student.id}>
                        <td>{student.full_name}</td>
                        <td>
                          <select
                            value={sheetDraft[student.id]?.status ?? "present"}
                            onChange={(event) =>
                              setSheetDraft((prev) => ({
                                ...prev,
                                [student.id]: {
                                  status: event.target.value as AttendanceStatus,
                                  reason: prev[student.id]?.reason ?? ""
                                }
                              }))
                            }
                          >
                            <option value="present">Присутствовал</option>
                            <option value="absent">Отсутствовал</option>
                            <option value="excused">Уважительная причина</option>
                            <option value="late">Опоздал</option>
                          </select>
                        </td>
                        <td>
                          <input
                            value={sheetDraft[student.id]?.reason ?? ""}
                            onChange={(event) =>
                              setSheetDraft((prev) => ({
                                ...prev,
                                [student.id]: {
                                  status: prev[student.id]?.status ?? "present",
                                  reason: event.target.value
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
                  {saving ? "Сохраняем..." : "Сохранить посещаемость группы"}
                </button>
              </form>
            )}
          </>
        ) : null}

        <div className="table-card">
          <h3 className="section-title">История посещаемости</h3>
          {records.length ? (
            <table>
              <thead>
                <tr>
                  <th>Дата</th>
                  <th>Студент</th>
                  <th>Дисциплина</th>
                  <th>Статус</th>
                  <th>Причина</th>
                </tr>
              </thead>
              <tbody>
                {records.map((record) => (
                  <tr key={record.id}>
                    <td>{record.date}</td>
                    <td>{record.student_name}</td>
                    <td>{record.curriculum_item_title}</td>
                    <td>{attendanceStatusTitle(record.status, record.status_title)}</td>
                    <td>{record.reason ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="muted">Посещаемость по этой дисциплине еще не заполнена.</p>
          )}
        </div>

        <div className="card">
          <h3 className="section-title">Сводка по студентам</h3>
          <table className="compact-table">
            <thead>
              <tr>
                <th>ФИО</th>
                <th>Всего посещений</th>
                <th>Всего пропусков</th>
                <th>Уважительных</th>
                <th>Опозданий</th>
              </tr>
            </thead>
            <tbody>
              {students.map((student) => {
                const summary = studentSummary[student.id] ?? { present: 0, absent: 0, excused: 0, late: 0 };
                return (
                  <tr key={`summary-${student.id}`}>
                    <td>{student.full_name}</td>
                    <td>{summary.present}</td>
                    <td>{summary.absent}</td>
                    <td>{summary.excused}</td>
                    <td>{summary.late}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </PageShell>
    </ProtectedPage>
  );
}
