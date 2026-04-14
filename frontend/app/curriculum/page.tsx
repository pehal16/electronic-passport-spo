"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/auth-provider";
import { PageShell } from "@/components/page-shell";
import { ProtectedPage } from "@/components/protected-page";
import { apiFetch } from "@/lib/api";
import { GroupSummary } from "@/lib/types";

export default function CurriculumHubPage() {
  const { token } = useAuth();
  const [groups, setGroups] = useState<GroupSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      return;
    }
    apiFetch<GroupSummary[]>("/groups", {}, token).then(setGroups).catch((err) => setError(err.message));
  }, [token]);

  return (
    <ProtectedPage>
      <PageShell
        title="Учебные планы групп"
        description="Откройте нужную группу, чтобы посмотреть учебный план по семестрам и по блокам."
        breadcrumbs={[{ label: "Главная", href: "/dashboard" }, { label: "Учебные планы" }]}
      >
        {error ? <div className="error-box">{error}</div> : null}
        <div className="grid">
          {groups.map((group) => (
            <div className="card" key={group.id}>
              <p className="eyebrow">{group.program.code}</p>
              <h3>{group.name}</h3>
              <p>{group.program.title}</p>
              <div className="button-row">
                <Link href={`/groups/${group.id}/curriculum`} className="button">
                  Открыть учебный план
                </Link>
                <Link href={`/groups/${group.id}`} className="button button-link">
                  Паспорт группы
                </Link>
              </div>
            </div>
          ))}
        </div>
      </PageShell>
    </ProtectedPage>
  );
}
