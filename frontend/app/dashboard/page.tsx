"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { PageShell } from "@/components/page-shell";
import { ProtectedPage } from "@/components/protected-page";
import { useAuth } from "@/components/auth-provider";
import { apiFetch } from "@/lib/api";
import { DashboardData } from "@/lib/types";

export default function DashboardPage() {
  const { token } = useAuth();
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      return;
    }
    apiFetch<DashboardData>("/dashboard", {}, token).then(setData).catch((err) => setError(err.message));
  }, [token]);

  return (
    <ProtectedPage>
      <PageShell
        title="Главная панель"
        description="Рабочий стартовый экран: показатели по группам, студентам, учебному плану, оценкам и посещаемости."
        breadcrumbs={[{ label: "Главная" }]}
      >
        {error ? <div className="error-box">{error}</div> : null}

        <div className="grid">
          {data?.stats.map((stat) => (
            <div className="card" key={stat.label}>
              <p className="eyebrow">{stat.label}</p>
              <h3>{stat.value}</h3>
              <p className="muted">{stat.hint}</p>
            </div>
          ))}
        </div>

        <div className="three-col">
          <div className="card">
            <h3 className="section-title">Группы в работе</h3>
            {data?.groups_in_work.length ? (
              <ul className="list">
                {data.groups_in_work.map((name) => (
                  <li key={name} className="list-item">
                    {name}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="muted">Пока нет групп в зоне доступа.</p>
            )}
          </div>

          <div className="card">
            <h3 className="section-title">Что требует внимания</h3>
            {data?.attention_items.length ? (
              <ul className="list">
                {data.attention_items.map((item) => (
                  <li className="list-item" key={item}>
                    {item}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="muted">Критичных замечаний сейчас нет.</p>
            )}
            {data?.alerts.length ? (
              <div className="note-box">
                {data.alerts.map((alert) => (
                  <div key={alert}>{alert}</div>
                ))}
              </div>
            ) : null}
          </div>

          <div className="card">
            <h3 className="section-title">Быстрые действия</h3>
            <div className="button-col">
              {data?.quick_links.map((item) => (
                <Link key={`${item.href}-${item.label}`} className="button button-link" href={item.href}>
                  {item.label}
                </Link>
              ))}
              {!data?.quick_links.length ? <p className="muted">Переходы будут доступны после входа в кабинет.</p> : null}
            </div>
          </div>
        </div>
      </PageShell>
    </ProtectedPage>
  );
}
