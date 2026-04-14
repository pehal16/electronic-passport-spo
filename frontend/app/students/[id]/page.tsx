"use client";

import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { useAuth } from "@/components/auth-provider";
import { PageShell } from "@/components/page-shell";
import { ProtectedPage } from "@/components/protected-page";
import { apiFetch } from "@/lib/api";
import { attendanceStatusTitle, studentStatusTitle } from "@/lib/dictionaries";
import { StudentDetail } from "@/lib/types";

export default function StudentPage() {
  const params = useParams<{ id: string }>();
  const { token } = useAuth();
  const [student, setStudent] = useState<StudentDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      return;
    }
    apiFetch<StudentDetail>(`/students/${params.id}`, {}, token).then(setStudent).catch((err) => setError(err.message));
  }, [params.id, token]);

  const recentAbsences = useMemo(
    () => student?.attendance.filter((item) => item.status !== "present").slice(0, 10) ?? [],
    [student?.attendance]
  );

  return (
    <ProtectedPage>
      <PageShell
        title={student?.full_name ?? "Карточка студента"}
        description="Карточка студента: группа, специальность, текущие дисциплины, последние оценки, посещаемость, практики и форма ГИА."
        breadcrumbs={[
          { label: "Главная", href: "/dashboard" },
          { label: "Группы", href: "/groups" },
          { label: student?.group.name ? student.group.name : "Группа", href: student?.group ? `/groups/${student.group.id}` : "/groups" },
          { label: "Карточка студента" }
        ]}
      >
        {error ? <div className="error-box">{error}</div> : null}
        {student ? (
          <>
            <div className="meta-grid">
              <div className="meta">
                <strong>ФИО</strong>
                {student.full_name}
              </div>
              <div className="meta">
                <strong>Группа</strong>
                {student.group.name}
              </div>
              <div className="meta">
                <strong>Специальность</strong>
                {student.group.program.title}
              </div>
              <div className="meta">
                <strong>Статус</strong>
                {studentStatusTitle(student.status, student.status)}
              </div>
              <div className="meta">
                <strong>Форма ГИА группы</strong>
                {student.gia_text ?? student.group.program.gia_type}
              </div>
            </div>

            <div className="three-col">
              <div className="card">
                <h3 className="section-title">Текущие дисциплины</h3>
                {student.current_subjects.length ? (
                  <ul className="list">
                    {student.current_subjects.map((subject) => (
                      <li key={subject} className="list-item">
                        {subject}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="muted">Пока нет записей.</p>
                )}
              </div>

              <div className="card">
                <h3 className="section-title">Последние оценки</h3>
                {student.grades.length ? (
                  <ul className="list">
                    {student.grades.slice(0, 10).map((grade) => (
                      <li className="list-item" key={grade.id}>
                        <strong>{grade.date}</strong>
                        <div>{grade.curriculum_item_title}</div>
                        <div>Оценка: {grade.grade_value}</div>
                        <div className="muted">{grade.comment ?? "Без комментария"}</div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="muted">Оценки по этой дисциплине еще не внесены.</p>
                )}
              </div>

              <div className="card">
                <h3 className="section-title">Последние пропуски</h3>
                {recentAbsences.length ? (
                  <ul className="list">
                    {recentAbsences.map((item) => (
                      <li className="list-item" key={item.id}>
                        <strong>{item.date}</strong>
                        <div>{item.curriculum_item_title}</div>
                        <div>{attendanceStatusTitle(item.status, item.status_title)}</div>
                        <div className="muted">{item.reason ?? "Причина не указана"}</div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="muted">Посещаемость по этой дисциплине еще не заполнена.</p>
                )}
              </div>
            </div>

            <div className="card">
              <h3 className="section-title">Практики</h3>
              {student.practices.length ? (
                <div className="grid">
                  {student.practices.map((practice) => (
                    <div className="list-item" key={practice.id}>
                      <strong>{practice.title}</strong>
                      <div className="muted">
                        {practice.hours ? `${practice.hours} ч.` : practice.weeks ? `${practice.weeks} нед.` : "Объем не указан"}
                      </div>
                      <div>{practice.outcome_text ?? practice.final_control_form?.title ?? "Итог уточняется"}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="muted">Пока нет записей.</p>
              )}
            </div>
          </>
        ) : null}
      </PageShell>
    </ProtectedPage>
  );
}
