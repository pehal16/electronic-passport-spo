"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/auth-provider";
import { PageShell } from "@/components/page-shell";
import { ProtectedPage } from "@/components/protected-page";
import { apiFetch } from "@/lib/api";
import { studentStatusTitle } from "@/lib/dictionaries";
import { GroupDetailResponse, StudentListItem } from "@/lib/types";

export default function GroupStudentsPage() {
  const params = useParams<{ id: string }>();
  const { token } = useAuth();
  const [students, setStudents] = useState<StudentListItem[]>([]);
  const [group, setGroup] = useState<GroupDetailResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      return;
    }
    apiFetch<StudentListItem[]>(`/groups/${params.id}/students`, {}, token).then(setStudents).catch((err) => setError(err.message));
    apiFetch<GroupDetailResponse>(`/groups/${params.id}`, {}, token).then(setGroup).catch((err) => setError(err.message));
  }, [params.id, token]);

  return (
    <ProtectedPage>
      <PageShell
        title="Студенты группы"
        description="Таблица студентов группы с быстрым переходом в карточку студента."
        breadcrumbs={[
          { label: "Главная", href: "/dashboard" },
          { label: "Группы", href: "/groups" },
          { label: group?.group.name ?? "Группа", href: `/groups/${params.id}` },
          { label: "Студенты" }
        ]}
      >
        {error ? <div className="error-box">{error}</div> : null}
        <div className="table-card">
          <table>
            <thead>
              <tr>
                <th>ФИО</th>
                <th>Группа</th>
                <th>Курс</th>
                <th>Оценок</th>
                <th>Пропусков</th>
                <th>Статус</th>
                <th>Действия</th>
              </tr>
            </thead>
            <tbody>
              {students.map((student) => (
                <tr key={student.id}>
                  <td>{student.full_name}</td>
                  <td>{student.group_name}</td>
                  <td>{student.course_now}</td>
                  <td>{student.grade_count}</td>
                  <td>{student.absence_count}</td>
                  <td>{studentStatusTitle(student.status, student.status)}</td>
                  <td>
                    <Link href={`/students/${student.id}`} className="button button-link compact-button">
                      Карточка студента
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </PageShell>
    </ProtectedPage>
  );
}
