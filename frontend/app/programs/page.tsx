"use client";

import { useEffect, useState } from "react";

import { useAuth } from "@/components/auth-provider";
import { PageShell } from "@/components/page-shell";
import { ProtectedPage } from "@/components/protected-page";
import { apiFetch } from "@/lib/api";
import { formatHours } from "@/lib/dictionaries";
import { AdminProgramsResponse } from "@/lib/types";

export default function ProgramsPage() {
  const { token } = useAuth();
  const [data, setData] = useState<AdminProgramsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      return;
    }
    apiFetch<AdminProgramsResponse>("/programs", {}, token).then(setData).catch((err) => setError(err.message));
  }, [token]);

  return (
    <ProtectedPage>
      <PageShell
        title="Программы СПО"
        description="Структура программ: квалификация, срок обучения, ГИА, практика, формы контроля и ключевые модули."
        breadcrumbs={[{ label: "Главная", href: "/dashboard" }, { label: "Программы" }]}
      >
        {error ? <div className="error-box">{error}</div> : null}

        <div className="grid">
          {data?.structures.map((program) => (
            <article className="card" key={program.program_id}>
              <p className="eyebrow">{program.code}</p>
              <h3>{program.title}</h3>

              <div className="meta-grid">
                <div className="meta">
                  <strong>Квалификация</strong>
                  {program.qualification}
                </div>
                <div className="meta">
                  <strong>Срок обучения</strong>
                  {program.duration_text}
                </div>
                <div className="meta">
                  <strong>Форма обучения</strong>
                  {program.education_form}
                </div>
                <div className="meta">
                  <strong>ГИА</strong>
                  {program.gia_type}
                </div>
                <div className="meta">
                  <strong>Общий объём</strong>
                  {formatHours(program.total_hours)}
                </div>
              </div>

              <details className="accordion" open>
                <summary>Практика</summary>
                {program.practices.length ? (
                  <ul className="list">
                    {program.practices.map((practice) => (
                      <li key={practice} className="list-item">
                        {practice}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="muted">Пока нет записей.</p>
                )}
              </details>

              <details className="accordion">
                <summary>Формы контроля</summary>
                <div className="summary-badges">
                  {program.control_forms.map((form) => (
                    <span key={form} className="status-pill">
                      {form}
                    </span>
                  ))}
                </div>
              </details>

              <details className="accordion">
                <summary>Ключевые модули и МДК</summary>
                {program.key_modules.length ? (
                  <ul className="list">
                    {program.key_modules.map((module) => (
                      <li key={module} className="list-item">
                        {module}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="muted">Пока нет записей.</p>
                )}
              </details>
            </article>
          ))}
        </div>
      </PageShell>
    </ProtectedPage>
  );
}

