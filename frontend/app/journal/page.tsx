"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { useAuth } from "@/components/auth-provider";
import { PageShell } from "@/components/page-shell";
import { ProtectedPage } from "@/components/protected-page";
import { apiFetch, buildQuery } from "@/lib/api";
import { controlFormTitle, formatHours } from "@/lib/dictionaries";
import { GroupSummary, JournalRow, JournalSubject } from "@/lib/types";

type JournalMode = "list" | "subject";

export default function JournalPage() {
  const { token } = useAuth();

  const [groups, setGroups] = useState<GroupSummary[]>([]);
  const [rows, setRows] = useState<JournalRow[]>([]);
  const [subjectJournal, setSubjectJournal] = useState<JournalSubject | null>(null);

  const [mode, setMode] = useState<JournalMode>("list");
  const [selectedGroupId, setSelectedGroupId] = useState("");
  const [selectedSemesterId, setSelectedSemesterId] = useState("");
  const [selectedSubjectId, setSelectedSubjectId] = useState("");
  const [selectedControlFormCode, setSelectedControlFormCode] = useState("");
  const [gradesFilter, setGradesFilter] = useState("all");
  const [attendanceFilter, setAttendanceFilter] = useState("all");
  const [selectedCurriculumItemId, setSelectedCurriculumItemId] = useState("");

  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const groupId = params.get("group_id");
    if (groupId) {
      setSelectedGroupId(groupId);
    }
  }, []);

  useEffect(() => {
    if (!token) {
      return;
    }
    apiFetch<GroupSummary[]>("/groups", {}, token).then(setGroups).catch((err) => setError(err.message));
  }, [token]);

  useEffect(() => {
    if (!token) {
      return;
    }
    const query = buildQuery({
      group_id: selectedGroupId || undefined,
      semester_id: selectedSemesterId || undefined,
      subject_id: selectedSubjectId || undefined,
      control_form_code: selectedControlFormCode || undefined,
      grades_filter: gradesFilter,
      attendance_filter: attendanceFilter
    });
    apiFetch<JournalRow[]>(`/journal${query}`, {}, token).then(setRows).catch((err) => setError(err.message));
  }, [attendanceFilter, gradesFilter, selectedControlFormCode, selectedGroupId, selectedSemesterId, selectedSubjectId, token]);

  useEffect(() => {
    if (!token || !selectedCurriculumItemId || mode !== "subject") {
      return;
    }
    apiFetch<JournalSubject>(`/journal/${selectedCurriculumItemId}`, {}, token).then(setSubjectJournal).catch((err) => setError(err.message));
  }, [mode, selectedCurriculumItemId, token]);

  const semesterOptions = useMemo(() => {
    const map = new Map<number, string>();
    rows.forEach((row) => map.set(row.semester_id, row.semester_title));
    return Array.from(map.entries()).sort((a, b) => a[0] - b[0]);
  }, [rows]);

  const subjectOptions = useMemo(() => {
    const map = new Map<number, string>();
    rows.forEach((row) => map.set(row.subject_id, `${row.subject_code} ${row.subject_title}`));
    return Array.from(map.entries()).sort((a, b) => a[1].localeCompare(b[1], "ru"));
  }, [rows]);

  return (
    <ProtectedPage roles={["admin", "curator", "teacher"]}>
      <PageShell
        title="Электронный журнал"
        description="Фильтруйте дисциплины по группе, семестру и форме контроля. Открывайте журнал предмета и переходите к внесению оценок и посещаемости."
        breadcrumbs={[{ label: "Главная", href: "/dashboard" }, { label: "Журнал" }]}
      >
        {error ? <div className="error-box">{error}</div> : null}

        <div className="card">
          <h3 className="section-title">Фильтры журнала</h3>
          <div className="meta-grid">
            <label className="field">
              <span>Группа</span>
              <select value={selectedGroupId} onChange={(event) => setSelectedGroupId(event.target.value)}>
                <option value="">Все группы</option>
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
                <option value="">Все семестры</option>
                {semesterOptions.map(([id, title]) => (
                  <option key={id} value={id}>
                    {title}
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              <span>Дисциплина</span>
              <select value={selectedSubjectId} onChange={(event) => setSelectedSubjectId(event.target.value)}>
                <option value="">Все дисциплины</option>
                {subjectOptions.map(([id, title]) => (
                  <option key={id} value={id}>
                    {title}
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              <span>Форма контроля</span>
              <select value={selectedControlFormCode} onChange={(event) => setSelectedControlFormCode(event.target.value)}>
                <option value="">Все</option>
                <option value="exam">Экзамен</option>
                <option value="dz">Дифференцированный зачет</option>
                <option value="kdz">Комплексный дифференцированный зачет</option>
                <option value="module_exam">Экзамен по модулю</option>
              </select>
            </label>

            <label className="field">
              <span>Оценки</span>
              <select value={gradesFilter} onChange={(event) => setGradesFilter(event.target.value)}>
                <option value="all">Все дисциплины</option>
                <option value="with">Только с оценками</option>
                <option value="without">Только без оценок</option>
              </select>
            </label>

            <label className="field">
              <span>Посещаемость</span>
              <select value={attendanceFilter} onChange={(event) => setAttendanceFilter(event.target.value)}>
                <option value="all">Все дисциплины</option>
                <option value="with">Только с посещаемостью</option>
                <option value="without">Только без посещаемости</option>
              </select>
            </label>
          </div>
          <div className="button-row">
            <Link href={`/attestation-sheets${selectedGroupId ? `?group_id=${selectedGroupId}` : ""}`} className="button">
              Сформировать ведомость
            </Link>
          </div>
        </div>

        <div className="tabs-row">
          <button type="button" className={`tab-button ${mode === "list" ? "tab-button-active" : ""}`} onClick={() => setMode("list")}>
            Список дисциплин
          </button>
          <button
            type="button"
            className={`tab-button ${mode === "subject" ? "tab-button-active" : ""}`}
            onClick={() => setMode("subject")}
            disabled={!selectedCurriculumItemId}
          >
            Журнал предмета
          </button>
        </div>

        {mode === "list" ? (
          <div className="table-card">
            <table>
              <thead>
                <tr>
                  <th>Группа</th>
                  <th>Семестр</th>
                  <th>Код</th>
                  <th>Дисциплина</th>
                  <th>Часы</th>
                  <th>Форма контроля</th>
                  <th>Студентов</th>
                  <th>Оценок</th>
                  <th>Посещаемость</th>
                  <th>Действия</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.curriculum_item_id}>
                    <td>{row.group_name}</td>
                    <td>{row.semester_title}</td>
                    <td>{row.subject_code}</td>
                    <td>
                      <div>{row.subject_title}</div>
                      <div className="muted">{row.cycle_title}</div>
                    </td>
                    <td>{formatHours(row.total_hours)}</td>
                    <td>{controlFormTitle(row.control_form_code, row.control_form_title)}</td>
                    <td>{row.student_count}</td>
                    <td>{row.grades_count}</td>
                    <td>{row.attendance_count}</td>
                    <td>
                      <div className="button-col">
                        <button
                          type="button"
                          className="button button-link compact-button"
                          onClick={() => {
                            setSelectedCurriculumItemId(String(row.curriculum_item_id));
                            setMode("subject");
                          }}
                        >
                          Открыть журнал предмета
                        </button>
                        <Link href={`/grades?group_id=${row.group_id}&semester_id=${row.semester_id}&curriculum_item_id=${row.curriculum_item_id}`} className="button button-link compact-button">
                          Внести оценки
                        </Link>
                        <Link href={`/attendance?group_id=${row.group_id}&semester_id=${row.semester_id}&curriculum_item_id=${row.curriculum_item_id}`} className="button button-link compact-button">
                          Внести посещаемость
                        </Link>
                        <Link href={`/attestation-sheets/new?curriculum_item_id=${row.curriculum_item_id}`} className="button button-link compact-button">
                          Сформировать ведомость
                        </Link>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!rows.length ? <p className="muted">Пока нет записей.</p> : null}
          </div>
        ) : (
          <div className="card">
            {subjectJournal ? (
              <>
                <h3 className="section-title">
                  {subjectJournal.subject_code} {subjectJournal.subject_title}
                </h3>
                <p className="muted">
                  {subjectJournal.group_name} • {subjectJournal.semester_title} • {subjectJournal.control_form_title}
                </p>
                <div className="button-row">
                  <Link href={`/attestation-sheets/new?curriculum_item_id=${subjectJournal.curriculum_item_id}`} className="button button-link compact-button">
                    Сформировать ведомость
                  </Link>
                  <Link
                    href={`/grades?curriculum_item_id=${subjectJournal.curriculum_item_id}`}
                    className="button button-link compact-button"
                  >
                    Внести оценки
                  </Link>
                </div>
                <div className="table-card">
                  <table>
                    <thead>
                      <tr>
                        <th>ФИО студента</th>
                        <th>Последняя оценка</th>
                        <th>Количество оценок</th>
                        <th>Посещено</th>
                        <th>Пропущено</th>
                        <th>Уважительных</th>
                        <th>Опозданий</th>
                        <th>Комментарий</th>
                      </tr>
                    </thead>
                    <tbody>
                      {subjectJournal.students.map((student) => (
                        <tr key={student.student_id}>
                          <td>{student.full_name}</td>
                          <td>{student.last_grade ?? "—"}</td>
                          <td>{student.grades_count}</td>
                          <td>{student.attended_count}</td>
                          <td>{student.absent_count}</td>
                          <td>{student.excused_count}</td>
                          <td>{student.late_count}</td>
                          <td>{student.last_comment ?? "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            ) : (
              <p className="muted">Выберите дисциплину из списка, чтобы открыть журнал предмета.</p>
            )}
          </div>
        )}
      </PageShell>
    </ProtectedPage>
  );
}
