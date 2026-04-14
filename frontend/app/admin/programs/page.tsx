"use client";

import { useEffect, useState } from "react";

import { useAuth } from "@/components/auth-provider";
import { PageShell } from "@/components/page-shell";
import { ProtectedPage } from "@/components/protected-page";
import { apiFetch } from "@/lib/api";
import { AdminProgramsResponse } from "@/lib/types";

export default function AdminProgramsPage() {
  const { token } = useAuth();
  const [data, setData] = useState<AdminProgramsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      return;
    }
    apiFetch<AdminProgramsResponse>("/admin/programs", {}, token).then(setData).catch((err) => setError(err.message));
  }, [token]);

  return (
    <ProtectedPage roles={["admin"]}>
      <PageShell
        title="Программы и структура"
        description="Раздел показывает срок обучения, квалификацию, ГИА, практики, формы контроля и ключевые профессиональные модули."
        breadcrumbs={[{ label: "Главная", href: "/dashboard" }, { label: "Программы" }]}
      >
        {error ? <div className="error-box">{error}</div> : null}

        <div className="grid">
          {data?.structures.map((program) => (
            <div className="card" key={program.program_id}>
              <p className="eyebrow">{program.code}</p>
              <h3>{program.title}</h3>
              <div className="meta-grid">
                <div className="meta">
                  <strong>Квалификация</strong>
                  {program.qualification}
                </div>
                <div className="meta">
                  <strong>Форма обучения</strong>
                  {program.education_form}
                </div>
                <div className="meta">
                  <strong>Срок</strong>
                  {program.duration_text}
                </div>
                <div className="meta">
                  <strong>ГИА</strong>
                  {program.gia_type}
                </div>
              </div>

              <h4>Практики</h4>
              <ul className="list">
                {program.practices.length ? (
                  program.practices.map((practice) => (
                    <li key={practice} className="list-item">
                      {practice}
                    </li>
                  ))
                ) : (
                  <li className="list-item">Пока нет записей.</li>
                )}
              </ul>

              <h4>Формы контроля</h4>
              <div className="summary-badges">
                {program.control_forms.map((form) => (
                  <span key={form} className="status-pill">
                    {form}
                  </span>
                ))}
              </div>

              <h4>Ключевые модули</h4>
              <ul className="list">
                {program.key_modules.slice(0, 8).map((module) => (
                  <li key={module} className="list-item">
                    {module}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </PageShell>
    </ProtectedPage>
  );
}
