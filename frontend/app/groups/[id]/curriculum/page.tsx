"use client";

import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { useAuth } from "@/components/auth-provider";
import { PageShell } from "@/components/page-shell";
import { ProtectedPage } from "@/components/protected-page";
import { apiFetch } from "@/lib/api";
import { controlFormTitle, formatHours } from "@/lib/dictionaries";
import { CurriculumBlock, CurriculumItem, CurriculumOverview, SemesterCurriculum } from "@/lib/types";

type ViewMode = "semesters" | "blocks";

function ItemBadges({ item }: { item: CurriculumItem }) {
  return (
    <div className="summary-badges">
      <span className="status-pill">{item.control_form_title}</span>
      {item.is_practice ? <span className="status-pill status-success">{item.practice_type ?? "Практика"}</span> : null}
      {item.complex_group_code ? <span className="status-pill">Комплексный ДЗ: {item.complex_group_code}</span> : null}
    </div>
  );
}

function SemesterTable({ semester }: { semester: SemesterCurriculum }) {
  const hasManualItems = semester.items.some((item) => item.requires_manual_confirmation);
  return (
    <div className="card">
      <h3 className="section-title">{semester.title}</h3>
      <div className="summary-badges">
        <span className="status-pill">Дисциплин: {semester.summary.discipline_count}</span>
        <span className="status-pill">Часов: {semester.summary.total_hours}</span>
        <span className="status-pill">Экзаменов: {semester.summary.exam_count}</span>
        <span className="status-pill">ДЗ: {semester.summary.dz_count}</span>
        <span className="status-pill">кДЗ: {semester.summary.kdz_count}</span>
        <span className="status-pill">Практик: {semester.summary.practice_count}</span>
      </div>
      {semester.notes ? <p className="muted">{semester.notes}</p> : null}
      {hasManualItems ? (
        <div className="note-box">Некоторые данные этого семестра требуют уточнения по учебному плану.</div>
      ) : null}
      <table className="compact-table">
        <thead>
          <tr>
            <th>Код</th>
            <th>Дисциплина</th>
            <th>Цикл</th>
            <th>Часы</th>
            <th>Форма контроля</th>
            <th>Примечание</th>
          </tr>
        </thead>
        <tbody>
          {semester.items.map((item) => (
            <tr key={item.id}>
              <td>{item.code}</td>
              <td>
                <div>{item.title}</div>
                <ItemBadges item={item} />
              </td>
              <td>{item.cycle_title}</td>
              <td>{formatHours(item.total_hours)}</td>
              <td>{item.control_form_title}</td>
              <td>{item.notes ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function BlocksView({ blocks }: { blocks: CurriculumBlock[] }) {
  const order = ["school", "social_humanitarian", "natural_science", "professional_general", "professional_module", "mdk", "practice", "gia"];
  const sortedBlocks = [...blocks].sort((left, right) => order.indexOf(left.key) - order.indexOf(right.key));
  return (
    <div className="grid">
      {sortedBlocks.map((block) => (
        <div className="card" key={block.key}>
          <h3 className="section-title">{block.title}</h3>
          <table className="compact-table">
            <thead>
              <tr>
                <th>Код</th>
                <th>Дисциплина</th>
                <th>Семестр</th>
                <th>Часы</th>
                <th>Форма контроля</th>
              </tr>
            </thead>
            <tbody>
              {block.items.map((item) => (
                <tr key={`${block.key}-${item.id}`}>
                  <td>{item.code}</td>
                  <td>
                    <div>{item.title}</div>
                    {item.complex_group_code ? <span className="status-pill">кДЗ: {item.complex_group_code}</span> : null}
                  </td>
                  <td>{item.semester_title}</td>
                  <td>{formatHours(item.total_hours)}</td>
                  <td>{controlFormTitle(item.control_form_code, item.control_form_title)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  );
}

export default function CurriculumPage() {
  const params = useParams<{ id: string }>();
  const { token } = useAuth();
  const [data, setData] = useState<CurriculumOverview | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("semesters");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      return;
    }
    apiFetch<CurriculumOverview>(`/groups/${params.id}/curriculum`, {}, token).then(setData).catch((err) => setError(err.message));
  }, [params.id, token]);

  const complexGroups = useMemo(() => Object.entries(data?.complex_groups ?? {}), [data?.complex_groups]);

  return (
    <ProtectedPage>
      <PageShell
        title={`Учебный план: ${data?.group.name ?? ""}`}
        description="Два режима просмотра: по семестрам и по блокам. Внутри дисциплин отображаются часы, форма контроля, практики и комплексные зачеты."
        breadcrumbs={[
          { label: "Главная", href: "/dashboard" },
          { label: "Группы", href: "/groups" },
          { label: data?.group.name ?? "Группа", href: `/groups/${params.id}` },
          { label: "Учебный план" }
        ]}
      >
        {error ? <div className="error-box">{error}</div> : null}
        {data ? (
          <>
            <div className="tabs-row">
              <button
                type="button"
                className={`tab-button ${viewMode === "semesters" ? "tab-button-active" : ""}`}
                onClick={() => setViewMode("semesters")}
              >
                По семестрам
              </button>
              <button
                type="button"
                className={`tab-button ${viewMode === "blocks" ? "tab-button-active" : ""}`}
                onClick={() => setViewMode("blocks")}
              >
                По блокам
              </button>
            </div>

            {viewMode === "semesters" ? (
              <div className="page-content">
                {data.semesters.map((semester) => (
                  <SemesterTable key={semester.id} semester={semester} />
                ))}
              </div>
            ) : (
              <BlocksView blocks={data.blocks} />
            )}

            <div className="card">
              <h3 className="section-title">Сводные блоки учебного плана</h3>
              <div className="grid">
                {Object.entries(data.grouped_items).map(([title, items]) => (
                  <div className="list-item" key={title}>
                    <strong>{title}</strong>
                    <div className="muted">Всего: {items.length}</div>
                    {items.slice(0, 8).map((item) => (
                      <div key={`${title}-${item.id}`}>
                        {item.code} {item.title}
                      </div>
                    ))}
                    {items.length > 8 ? <div className="muted">… и еще {items.length - 8}</div> : null}
                  </div>
                ))}
              </div>
            </div>

            <div className="card">
              <h3 className="section-title">Комплексные дифференцированные зачеты</h3>
              {complexGroups.length ? (
                <div className="grid">
                  {complexGroups.map(([code, items]) => (
                    <div key={code} className="list-item">
                      <strong>{code}</strong>
                      <ul className="list">
                        {items.map((item) => (
                          <li key={`${code}-${item.id}`} className="list-item">
                            {item.code} {item.title}
                            {item.is_practice ? <span className="status-pill status-success">Практика</span> : null}
                            {item.requires_manual_confirmation ? (
                              <div className="muted">Структура требует ручной проверки по учебному плану.</div>
                            ) : null}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="muted">Пока нет записей.</p>
              )}
            </div>
          </>
        ) : null}
      </PageShell>
    </ProtectedPage>
  );
}
