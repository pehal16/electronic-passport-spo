"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { useAuth } from "@/components/auth-provider";
import { PageShell } from "@/components/page-shell";
import { ProtectedPage } from "@/components/protected-page";
import { apiFetch } from "@/lib/api";
import { yesNoLabel } from "@/lib/dictionaries";
import { GroupDetailResponse, StudentListItem } from "@/lib/types";

const tabs = [
  { key: "general", label: "Общая информация" },
  { key: "students", label: "Студенты" },
  { key: "curriculum", label: "Учебный план" },
  { key: "practice", label: "Практика" },
  { key: "gia", label: "ГИА" },
  { key: "journal", label: "Журнал" },
  { key: "attendance", label: "Посещаемость" },
  { key: "grades", label: "Успеваемость" }
] as const;

type TabKey = (typeof tabs)[number]["key"];

export default function GroupDetailPage() {
  const params = useParams<{ id: string }>();
  const [activeTab, setActiveTab] = useState<TabKey>("general");
  const { token, user } = useAuth();
  const [data, setData] = useState<GroupDetailResponse | null>(null);
  const [students, setStudents] = useState<StudentListItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const paramsFromUrl = new URLSearchParams(window.location.search);
    const tabFromUrl = paramsFromUrl.get("tab") as TabKey | null;
    if (tabFromUrl && tabs.some((tab) => tab.key === tabFromUrl)) {
      setActiveTab(tabFromUrl);
    }
  }, []);

  useEffect(() => {
    if (!token) {
      return;
    }
    apiFetch<GroupDetailResponse>(`/groups/${params.id}`, {}, token).then(setData).catch((err) => setError(err.message));
    apiFetch<StudentListItem[]>(`/groups/${params.id}/students`, {}, token).then(setStudents).catch((err) => setError(err.message));
  }, [params.id, token]);

  const hasStudyPractice = useMemo(() => data?.practices.some((item) => item.practice_type === "учебная") ?? false, [data?.practices]);
  const hasProductionPractice = useMemo(() => data?.practices.some((item) => item.practice_type === "производственная") ?? false, [data?.practices]);
  const hasPreDiplomaPractice = useMemo(() => data?.practices.some((item) => item.practice_type === "преддипломная") ?? false, [data?.practices]);

  return (
    <ProtectedPage>
      <PageShell
        title={data?.group.name ?? "Паспорт группы"}
        description="Паспорт группы объединяет общие сведения, состав, учебный план, практики, ГИА, журнал и текущую успеваемость."
        breadcrumbs={[
          { label: "Главная", href: "/dashboard" },
          { label: "Группы", href: "/groups" },
          { label: data?.group.name ?? "Паспорт группы" }
        ]}
      >
        {error ? <div className="error-box">{error}</div> : null}
        {data ? (
          <>
            <div className="meta-grid">
              <div className="meta">
                <strong>Всего студентов</strong>
                {data.summary.students_total}
              </div>
              <div className="meta">
                <strong>Всего дисциплин</strong>
                {data.summary.disciplines_total}
              </div>
              <div className="meta">
                <strong>Экзамены</strong>
                {data.summary.exams_total}
              </div>
              <div className="meta">
                <strong>ДЗ</strong>
                {data.summary.dz_total}
              </div>
              <div className="meta">
                <strong>кДЗ</strong>
                {data.summary.kdz_total}
              </div>
              <div className="meta">
                <strong>Практики</strong>
                {data.summary.practices_total}
              </div>
            </div>

            {user && ["admin", "curator", "teacher"].includes(user.role.code) ? (
              <div className="card">
                <h3 className="section-title">Формирование ведомостей</h3>
                <p className="muted">Если не видите кнопки в журнале или учебном плане, используйте отдельный мастер формирования ведомостей.</p>
                <Link href={`/attestation-sheets?group_id=${params.id}`} className="button">
                  Сформировать ведомость
                </Link>
              </div>
            ) : null}

            <div className="tabs-row">
              {tabs.map((tab) => (
                <button
                  key={tab.key}
                  type="button"
                  className={`tab-button ${activeTab === tab.key ? "tab-button-active" : ""}`}
                  onClick={() => setActiveTab(tab.key)}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {activeTab === "general" ? (
              <div className="card">
                <h3 className="section-title">Общая информация</h3>
                <div className="meta-grid">
                  <div className="meta">
                    <strong>Группа</strong>
                    {data.group.name}
                  </div>
                  <div className="meta">
                    <strong>Специальность</strong>
                    {data.group.program.title}
                  </div>
                  <div className="meta">
                    <strong>Квалификация</strong>
                    {data.group.program.qualification}
                  </div>
                  <div className="meta">
                    <strong>Срок обучения</strong>
                    {data.group.program.duration_text}
                  </div>
                  <div className="meta">
                    <strong>Год набора</strong>
                    {data.group.start_year}
                  </div>
                  <div className="meta">
                    <strong>Курс</strong>
                    {data.group.course_now}
                  </div>
                  <div className="meta">
                    <strong>Количество студентов</strong>
                    {data.group.student_count}
                  </div>
                  <div className="meta">
                    <strong>Количество семестров</strong>
                    {data.group.semester_count}
                  </div>
                  <div className="meta">
                    <strong>Форма обучения</strong>
                    {data.group.program.education_form}
                  </div>
                  <div className="meta">
                    <strong>Форма ГИА</strong>
                    {data.summary.gia_form}
                  </div>
                  <div className="meta">
                    <strong>Учебная практика</strong>
                    {yesNoLabel(hasStudyPractice)}
                  </div>
                  <div className="meta">
                    <strong>Производственная практика</strong>
                    {yesNoLabel(hasProductionPractice)}
                  </div>
                  <div className="meta">
                    <strong>Преддипломная практика</strong>
                    {yesNoLabel(hasPreDiplomaPractice)}
                  </div>
                </div>
              </div>
            ) : null}

            {activeTab === "students" ? (
              <div className="card">
                <h3 className="section-title">Состав группы</h3>
                {students.length ? (
                  <table className="compact-table">
                    <thead>
                      <tr>
                        <th>ФИО</th>
                        <th>Оценок</th>
                        <th>Пропусков</th>
                        <th>Действие</th>
                      </tr>
                    </thead>
                    <tbody>
                      {students.map((student) => (
                        <tr key={student.id}>
                          <td>{student.full_name}</td>
                          <td>{student.grade_count}</td>
                          <td>{student.absence_count}</td>
                          <td>
                            <Link href={`/students/${student.id}`} className="button button-link compact-button">
                              Карточка студента
                            </Link>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <p className="muted">Пока нет записей.</p>
                )}
              </div>
            ) : null}

            {activeTab === "curriculum" ? (
              <div className="card">
                <h3 className="section-title">Учебный план</h3>
                <p className="muted">Откройте подробный учебный план по семестрам и по блокам.</p>
                <Link href={`/groups/${params.id}/curriculum`} className="button">
                  Открыть учебный план
                </Link>
              </div>
            ) : null}

            {activeTab === "practice" ? (
              <div className="card">
                <h3 className="section-title">Практика</h3>
                {data.practices.length ? (
                  <ul className="list">
                    {data.practices.map((practice) => (
                      <li key={practice.id} className="list-item">
                        <strong>{practice.title}</strong>
                        <div className="muted">
                          {practice.hours ? `${practice.hours} ч.` : practice.weeks ? `${practice.weeks} нед.` : "Объем не указан"}
                        </div>
                        <div>{practice.outcome_text ?? "Итог уточняется"}</div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="muted">Пока нет записей.</p>
                )}
                <Link href={`/groups/${params.id}/practices`} className="button button-link">
                  Подробно по практике
                </Link>
              </div>
            ) : null}

            {activeTab === "gia" ? (
              <div className="card">
                <h3 className="section-title">ГИА</h3>
                {data.gia ? (
                  <div className="meta-grid">
                    <div className="meta">
                      <strong>Форма</strong>
                      {data.gia.notes ?? data.summary.gia_form}
                    </div>
                    <div className="meta">
                      <strong>Всего</strong>
                      {data.gia.total_weeks ?? "—"} нед.
                    </div>
                    <div className="meta">
                      <strong>Подготовка</strong>
                      {data.gia.preparation_weeks ?? "—"} нед.
                    </div>
                    <div className="meta">
                      <strong>Защита</strong>
                      {data.gia.defense_weeks ?? "—"} нед.
                    </div>
                  </div>
                ) : (
                  <p className="muted">Пока нет записей.</p>
                )}
                <Link href={`/groups/${params.id}/gia`} className="button button-link">
                  Подробно по ГИА
                </Link>
              </div>
            ) : null}

            {activeTab === "journal" ? (
              <div className="card">
                <h3 className="section-title">Журнал</h3>
                <p className="muted">Открыть журнал группы с фильтрами по семестру и дисциплине.</p>
                <Link href={`/journal?group_id=${params.id}`} className="button">
                  Открыть журнал группы
                </Link>
              </div>
            ) : null}

            {activeTab === "attendance" ? (
              <div className="card">
                <h3 className="section-title">Посещаемость</h3>
                <p className="muted">Внесение посещаемости в логике: группа → семестр → дисциплина → студент.</p>
                <Link href={`/attendance?group_id=${params.id}`} className="button">
                  Открыть посещаемость
                </Link>
              </div>
            ) : null}

            {activeTab === "grades" ? (
              <div className="card">
                <h3 className="section-title">Успеваемость</h3>
                <p className="muted">Внесение оценок и история оценивания по группе.</p>
                <Link href={`/grades?group_id=${params.id}`} className="button">
                  Открыть оценки
                </Link>
              </div>
            ) : null}
          </>
        ) : null}
      </PageShell>
    </ProtectedPage>
  );
}
