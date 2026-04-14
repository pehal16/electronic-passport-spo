"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/auth-provider";
import { PageShell } from "@/components/page-shell";
import { ProtectedPage } from "@/components/protected-page";
import { apiFetch } from "@/lib/api";
import { GroupSummary, Semester } from "@/lib/types";

export default function SemestersPage() {
  const params = useParams<{ id: string }>();
  const { token } = useAuth();
  const [semesters, setSemesters] = useState<Semester[]>([]);
  const [groups, setGroups] = useState<GroupSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    apiFetch<Semester[]>(`/groups/${params.id}/semesters`, {}, token).then(setSemesters).catch((err) => setError(err.message));
    apiFetch<GroupSummary[]>("/groups", {}, token).then(setGroups).catch((err) => setError(err.message));
  }, [params.id, token]);

  const group = groups.find((item) => String(item.id) === params.id);

  return (
    <ProtectedPage>
      <PageShell
        title="Семестры группы"
        description="Отдельный просмотр семестров помогает быстро ориентироваться в последовательности обучения."
        breadcrumbs={[
          { label: "Главная", href: "/dashboard" },
          { label: "Группы", href: "/groups" },
          { label: group?.name ?? "Группа", href: `/groups/${params.id}` },
          { label: "Семестры" }
        ]}
      >
        {error ? <div className="error-box">{error}</div> : null}
        <div className="card">
          <ul className="list">
            {semesters.map((semester) => (
              <li key={semester.id} className="list-item">
                <strong>{semester.title}</strong>
                <div className="muted">Курс {semester.course_number}</div>
                {semester.notes ? <div>{semester.notes}</div> : null}
              </li>
            ))}
          </ul>
        </div>
      </PageShell>
    </ProtectedPage>
  );
}
