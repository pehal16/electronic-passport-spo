"use client";

import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { useAuth } from "@/components/auth-provider";
import { PageShell } from "@/components/page-shell";
import { ProtectedPage } from "@/components/protected-page";
import { apiFetch } from "@/lib/api";
import { GroupDetailResponse } from "@/lib/types";

export default function GiaPage() {
  const params = useParams<{ id: string }>();
  const { token } = useAuth();
  const [data, setData] = useState<GroupDetailResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      return;
    }
    apiFetch<GroupDetailResponse>(`/groups/${params.id}/gia`, {}, token).then(setData).catch((err) => setError(err.message));
  }, [params.id, token]);

  const gia = data?.gia;
  const giaFormText = useMemo(() => {
    if (!gia) {
      return data?.group.program.gia_type ?? "—";
    }
    if (gia.has_demo_exam && gia.has_diploma_defense) {
      return "Демонстрационный экзамен профильного уровня + защита дипломной работы";
    }
    if (gia.has_diploma_defense) {
      return "Защита дипломной работы";
    }
    if (gia.has_demo_exam) {
      return "Демонстрационный экзамен";
    }
    return data?.group.program.gia_type ?? "—";
  }, [data?.group.program.gia_type, gia]);

  return (
    <ProtectedPage>
      <PageShell
        title="Государственная итоговая аттестация"
        description="Понятная карточка ГИА: форма, продолжительность и этапы допуска/защиты."
        breadcrumbs={[
          { label: "Главная", href: "/dashboard" },
          { label: "Группы", href: "/groups" },
          { label: data?.group.name ?? "Группа", href: `/groups/${params.id}` },
          { label: "ГИА" }
        ]}
      >
        {error ? <div className="error-box">{error}</div> : null}
        {gia ? (
          <div className="meta-grid">
            <div className="meta">
              <strong>Форма ГИА</strong>
              {giaFormText}
            </div>
            <div className="meta">
              <strong>Всего недель</strong>
              {gia.total_weeks ?? "—"}
            </div>
            <div className="meta">
              <strong>Выполнение ВКР / дипломной работы</strong>
              {gia.preparation_weeks ?? "—"} недели
            </div>
            <div className="meta">
              <strong>Защита</strong>
              {gia.defense_weeks ?? "—"} недели
            </div>
            <div className="meta">
              <strong>Комментарий</strong>
              {gia.notes ?? "—"}
            </div>
          </div>
        ) : (
          <p className="muted">Пока нет записей по ГИА.</p>
        )}
      </PageShell>
    </ProtectedPage>
  );
}
