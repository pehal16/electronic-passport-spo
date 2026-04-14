"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { useAuth } from "@/components/auth-provider";
import { PageShell } from "@/components/page-shell";
import { ProtectedPage } from "@/components/protected-page";
import { apiFetch } from "@/lib/api";
import { yesNoLabel } from "@/lib/dictionaries";
import { GroupSummary } from "@/lib/types";

export default function GroupsPage() {
  const { token } = useAuth();
  const [groups, setGroups] = useState<GroupSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      return;
    }
    apiFetch<GroupSummary[]>("/groups", {}, token)
      .then((items) => {
        setGroups(items);
      })
      .catch((err) => {
        setError(err.message);
      });
  }, [token]);

  const totalStudents = useMemo(() => groups.reduce((sum, group) => sum + group.student_count, 0), [groups]);

  return (
    <ProtectedPage>
      <PageShell
        title="Группы и паспорта"
        description="Выберите группу и переходите в паспорт, учебный план, журнал, посещаемость, оценки и список студентов."
        breadcrumbs={[{ label: "Главная", href: "/dashboard" }, { label: "Группы" }]}
      >
        {error ? <div className="error-box">{error}</div> : null}

        <div className="meta-grid">
          <div className="meta">
            <strong>Групп в работе</strong>
            {groups.length}
          </div>
          <div className="meta">
            <strong>Студентов всего</strong>
            {totalStudents}
          </div>
          <div className="meta">
            <strong>Принцип системы</strong>
            Одна база данных, разные кабинеты по ролям
          </div>
        </div>

        <div className="grid">
          {groups.map((group) => (
            <div key={group.id} className="card">
              <p className="eyebrow">{group.program.code}</p>
              <h3>{group.name}</h3>
              <p>{group.program.title}</p>

              <div className="meta-grid">
                <div className="meta">
                  <strong>Год набора</strong>
                  {group.start_year}
                </div>
                <div className="meta">
                  <strong>Текущий курс</strong>
                  {group.course_now}
                </div>
                <div className="meta">
                  <strong>Студентов</strong>
                  {group.student_count}
                </div>
                <div className="meta">
                  <strong>Семестров</strong>
                  {group.semester_count}
                </div>
                <div className="meta">
                  <strong>Форма ГИА</strong>
                  {group.program.gia_type}
                </div>
                <div className="meta">
                  <strong>Практики</strong>
                  {yesNoLabel(group.has_practices)}
                </div>
              </div>

              <div className="summary-badges">
                <span className="status-pill">Экзамены: {group.exams_count}</span>
                <span className="status-pill">ДЗ: {group.dz_count}</span>
                <span className="status-pill">кДЗ: {group.kdz_count}</span>
              </div>

              {group.notes ? <p className="muted">{group.notes}</p> : null}

              <div className="button-row">
                <Link href={`/groups/${group.id}`} className="button">
                  Паспорт группы
                </Link>
                <Link href={`/groups/${group.id}/curriculum`} className="button button-link">
                  Учебный план
                </Link>
                <Link href={`/groups/${group.id}/students`} className="button button-link">
                  Студенты
                </Link>
                <Link href={`/journal?group_id=${group.id}`} className="button button-link">
                  Журнал группы
                </Link>
                <Link href={`/attendance?group_id=${group.id}`} className="button button-link">
                  Посещаемость
                </Link>
                <Link href={`/grades?group_id=${group.id}`} className="button button-link">
                  Оценки
                </Link>
              </div>
            </div>
          ))}
        </div>
      </PageShell>
    </ProtectedPage>
  );
}
