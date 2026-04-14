"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/auth-provider";
import { PageShell } from "@/components/page-shell";
import { ProtectedPage } from "@/components/protected-page";
import { apiFetch } from "@/lib/api";
import { DashboardData } from "@/lib/types";

export default function DashboardPage() {
  const { token } = useAuth();
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const canCreateSheets = data ? ["admin", "curator", "teacher"].includes(data.role_code) : false;

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
        description="Рабочий стартовый экран: быстрый доступ к группам, журналу, ведомостям, оценкам и посещаемости."
        breadcrumbs={[{ label: "Главная" }]}
      >
        {error ? <div className="error-box">{error}</div> : null}

        <section className="grid">
          {data?.stats.map((stat) => (
            <article className="card" key={stat.label}>
              <p className="eyebrow">{stat.label}</p>
              <h3 style={{ fontSize: "2rem", margin: "6px 0 8px" }}>{stat.value}</h3>
              <p className="muted">{stat.hint}</p>
            </article>
          ))}
        </section>

        {canCreateSheets ? (
          <section className="card">
            <div className="two-col">
              <div>
                <h3 className="section-title">Формирование ведомостей</h3>
                <p className="muted">
                  Быстрый сценарий: открыть мастер, выбрать группу, семестр и дисциплину, затем нажать «Сформировать ведомость».
                </p>
                <div className="button-row" style={{ marginTop: "14px" }}>
                  <Link className="button" href="/attestation-sheets">
                    Сформировать ведомость
                  </Link>
                  <Link className="button button-link" href="/journal">
                    Открыть журнал
                  </Link>
                </div>
              </div>
              <div className="hero-side-card">
                <span className="eyebrow">Быстрый путь</span>
                <strong>Группа → Семестр → Дисциплина → Ведомость</strong>
                <p className="muted">Предпросмотр, печать и экспорт доступны прямо из мастера.</p>
              </div>
            </div>
          </section>
        ) : null}

        <section className="three-col">
          <article className="card">
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
          </article>

          <article className="card">
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
              <div className="note-box" style={{ marginTop: "12px" }}>
                {data.alerts.map((alert) => (
                  <div key={alert}>{alert}</div>
                ))}
              </div>
            ) : null}
          </article>

          <article className="card">
            <h3 className="section-title">Быстрые действия</h3>
            <div className="button-col">
              {data?.quick_links.map((item) => (
                <Link key={`${item.href}-${item.label}`} className="button button-link" href={item.href}>
                  {item.label}
                </Link>
              ))}
              {!data?.quick_links.length ? <p className="muted">Переходы будут доступны после входа в кабинет.</p> : null}
            </div>
          </article>
        </section>

        <section className="card">
          <h3 className="section-title">Почему это удобно</h3>
          <div className="meta-grid">
            <div className="meta">
              <strong>Русский интерфейс</strong>
              <span className="muted">Крупные кнопки, понятные названия, минимум вложенных меню.</span>
            </div>
            <div className="meta">
              <strong>Рабочая логика</strong>
              <span className="muted">Журнал, посещаемость и ведомости связаны через одну базу данных.</span>
            </div>
            <div className="meta">
              <strong>Подходит для преподавателей</strong>
              <span className="muted">Главные действия доступны сразу с главной панели за несколько кликов.</span>
            </div>
          </div>
        </section>
      </PageShell>
    </ProtectedPage>
  );
}
