"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/auth-provider";
import { PageShell } from "@/components/page-shell";
import { ProtectedPage } from "@/components/protected-page";
import { apiFetch } from "@/lib/api";
import { formatHours, formatWeeks } from "@/lib/dictionaries";
import { GroupDetailResponse, Practice } from "@/lib/types";

export default function PracticesPage() {
  const params = useParams<{ id: string }>();
  const { token } = useAuth();
  const [practices, setPractices] = useState<Practice[]>([]);
  const [group, setGroup] = useState<GroupDetailResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      return;
    }
    apiFetch<Practice[]>(`/groups/${params.id}/practices`, {}, token).then(setPractices).catch((err) => setError(err.message));
    apiFetch<GroupDetailResponse>(`/groups/${params.id}`, {}, token).then(setGroup).catch((err) => setError(err.message));
  }, [params.id, token]);

  return (
    <ProtectedPage>
      <PageShell
        title="Практика группы"
        description="Отдельный модуль по практике: вид, семестр, часы или недели, итоговая форма контроля и связь с комплексным зачетом."
        breadcrumbs={[
          { label: "Главная", href: "/dashboard" },
          { label: "Группы", href: "/groups" },
          { label: group?.group.name ?? "Группа", href: `/groups/${params.id}` },
          { label: "Практика" }
        ]}
      >
        {error ? <div className="error-box">{error}</div> : null}
        <div className="table-card">
          <table>
            <thead>
              <tr>
                <th>Вид практики</th>
                <th>Семестр</th>
                <th>Часы</th>
                <th>Недели</th>
                <th>Итог</th>
                <th>Модуль</th>
                <th>кДЗ</th>
              </tr>
            </thead>
            <tbody>
              {practices.map((practice) => (
                <tr key={practice.id}>
                  <td>
                    <strong>{practice.title}</strong>
                    {practice.notes ? <div className="muted">{practice.notes}</div> : null}
                  </td>
                  <td>{practice.semester?.title ?? "По группе"}</td>
                  <td>{formatHours(practice.hours)}</td>
                  <td>{formatWeeks(practice.weeks)}</td>
                  <td>{practice.outcome_text ?? practice.final_control_form?.title ?? "—"}</td>
                  <td>{practice.related_module ?? "—"}</td>
                  <td>{practice.complex_group_code ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </PageShell>
    </ProtectedPage>
  );
}
