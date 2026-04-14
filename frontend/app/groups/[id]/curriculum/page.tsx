"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { useAuth } from "@/components/auth-provider";
import { PageShell } from "@/components/page-shell";
import { ProtectedPage } from "@/components/protected-page";
import { apiFetch } from "@/lib/api";
import { controlFormTitle, formatHours, knownHoursLabel } from "@/lib/dictionaries";
import { CurriculumBlock, CurriculumItem, CurriculumOverview, SemesterCurriculum } from "@/lib/types";

type ViewMode = "semesters" | "blocks";

function ItemBadges({ item }: { item: CurriculumItem }) {
  return (
    <div className="summary-badges">
      <span className="status-pill">{item.control_form_title}</span>
      {item.is_practice ? <span className="status-pill status-success">{item.practice_type ?? "Практика"}</span> : null}
      {item.complex_group_code ? <span className="status-pill">Комплексный ДЗ: {item.complex_group_code}</span> : null}
      {item.requires_manual_confirmation ? <span className="status-pill status-danger">Нужна ручная проверка</span> : null}
    </div>
  );
}

interface SemesterTableProps {
  semester: SemesterCurriculum;
  items: CurriculumItem[];
}

function SemesterTable({ semester, items }: SemesterTableProps) {
  const hasManualItems = items.some((item) => item.requires_manual_confirmation);
  const openByDefault = semester.number <= 2;

  return (
    <details className="accordion" open={openByDefault}>
      <summary>
        {semester.title} · дисциплин: {items.length}
      </summary>
      <div className="summary-badges">
        <span className="status-pill">Всего часов: {knownHoursLabel(semester.summary.total_hours, semester.summary.known_hours_items)}</span>
        <span className="status-pill">Контактные: {formatHours(semester.summary.contact_hours || null)}</span>
        <span className="status-pill">Практика: {formatHours(semester.summary.practice_hours || null)}</span>
        <span className="status-pill">Экзамены: {semester.summary.exam_count}</span>
        <span className="status-pill">ДЗ: {semester.summary.dz_count}</span>
        <span className="status-pill">кДЗ: {semester.summary.kdz_count}</span>
      </div>
      <p className="muted">
        Заполнено часов по дисциплинам: {semester.summary.known_hours_items}; без часов: {semester.summary.missing_hours_items}
      </p>
      {semester.notes ? <p className="muted">{semester.notes}</p> : null}
      {hasManualItems ? <div className="note-box">Некоторые данные этого семестра требуют уточнения по учебному плану.</div> : null}

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
          {items.map((item) => (
            <tr key={item.id}>
              <td>{item.code}</td>
              <td>
                <div>{item.title}</div>
                <ItemBadges item={item} />
                <div className="button-row">
                  <Link href={`/attestation-sheets/new?curriculum_item_id=${item.id}`} className="button button-link compact-button">
                    Сформировать ведомость
                  </Link>
                </div>
              </td>
              <td>{item.cycle_title}</td>
              <td>
                <div>Всего: {formatHours(item.total_hours)}</div>
                <div className="muted">Контактные: {formatHours(item.contact_hours)}</div>
                <div className="muted">Практика: {formatHours(item.practice_hours)}</div>
              </td>
              <td>{item.control_form_title}</td>
              <td>{item.notes ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </details>
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
                    <div className="button-row">
                      <Link href={`/attestation-sheets/new?curriculum_item_id=${item.id}`} className="button button-link compact-button">
                        Сформировать ведомость
                      </Link>
                    </div>
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
  const [search, setSearch] = useState("");
  const [cycleFilter, setCycleFilter] = useState("");
  const [controlFilter, setControlFilter] = useState("");
  const [showOnlyManual, setShowOnlyManual] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      return;
    }
    apiFetch<CurriculumOverview>(`/groups/${params.id}/curriculum`, {}, token).then(setData).catch((err) => setError(err.message));
  }, [params.id, token]);

  const complexGroups = useMemo(() => Object.entries(data?.complex_groups ?? {}), [data?.complex_groups]);

  const cycleOptions = useMemo(() => {
    const set = new Set<string>();
    data?.semesters.forEach((semester) => semester.items.forEach((item) => set.add(item.cycle_key)));
    return Array.from(set).sort((a, b) => a.localeCompare(b));
  }, [data?.semesters]);

  const controlOptions = useMemo(() => {
    const set = new Set<string>();
    data?.semesters.forEach((semester) => semester.items.forEach((item) => set.add(item.control_form_code)));
    return Array.from(set).sort((a, b) => a.localeCompare(b));
  }, [data?.semesters]);

  const itemMatchesFilters = useCallback((item: CurriculumItem) => {
    const normalizedSearch = search.trim().toLowerCase();
    const bySearch =
      !normalizedSearch ||
      item.code.toLowerCase().includes(normalizedSearch) ||
      item.title.toLowerCase().includes(normalizedSearch);
    const byCycle = !cycleFilter || item.cycle_key === cycleFilter;
    const byControl = !controlFilter || item.control_form_code === controlFilter;
    const byManual = !showOnlyManual || item.requires_manual_confirmation;
    return bySearch && byCycle && byControl && byManual;
  }, [controlFilter, cycleFilter, search, showOnlyManual]);

  const filteredSemesters = useMemo(() => {
    if (!data) {
      return [];
    }
    return data.semesters
      .map((semester) => ({
        semester,
        items: semester.items.filter(itemMatchesFilters),
      }))
      .filter((entry) => entry.items.length > 0);
  }, [data, itemMatchesFilters]);

  const filteredBlocks = useMemo(() => {
    if (!data) {
      return [];
    }
    return data.blocks
      .map((block) => ({ ...block, items: block.items.filter(itemMatchesFilters) }))
      .filter((block) => block.items.length > 0);
  }, [data, itemMatchesFilters]);

  return (
    <ProtectedPage>
      <PageShell
        title={`Учебный план: ${data?.group.name ?? ""}`}
        description="Просмотр учебного плана по семестрам и по блокам. Для каждой дисциплины доступны часы, форма контроля и быстрый запуск ведомости."
        breadcrumbs={[
          { label: "Главная", href: "/dashboard" },
          { label: "Группы", href: "/groups" },
          { label: data?.group.name ?? "Группа", href: `/groups/${params.id}` },
          { label: "Учебный план" },
        ]}
      >
        {error ? <div className="error-box">{error}</div> : null}
        {data ? (
          <>
            <div className="card">
              <h3 className="section-title">Быстрое формирование ведомости</h3>
              <p className="muted">Выберите семестр и дисциплину ниже либо откройте отдельный мастер ведомостей.</p>
              <div className="button-row">
                <Link href={`/attestation-sheets?group_id=${params.id}`} className="button">
                  Открыть мастер ведомостей
                </Link>
              </div>
            </div>

            <div className="card">
              <h3 className="section-title">Фильтры учебного плана</h3>
              <div className="meta-grid">
                <label className="field">
                  <span>Поиск по коду или названию</span>
                  <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Например: ОП.03 или маркетинг" />
                </label>
                <label className="field">
                  <span>Цикл</span>
                  <select value={cycleFilter} onChange={(event) => setCycleFilter(event.target.value)}>
                    <option value="">Все циклы</option>
                    {cycleOptions.map((key) => (
                      <option key={key} value={key}>
                        {key}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="field">
                  <span>Форма контроля</span>
                  <select value={controlFilter} onChange={(event) => setControlFilter(event.target.value)}>
                    <option value="">Все формы</option>
                    {controlOptions.map((key) => (
                      <option key={key} value={key}>
                        {controlFormTitle(key, key)}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="field">
                  <span>Только элементы с ручной проверкой</span>
                  <select value={showOnlyManual ? "yes" : "no"} onChange={(event) => setShowOnlyManual(event.target.value === "yes")}>
                    <option value="no">Нет</option>
                    <option value="yes">Да</option>
                  </select>
                </label>
              </div>
            </div>

            <div className="tabs-row">
              <button type="button" className={`tab-button ${viewMode === "semesters" ? "tab-button-active" : ""}`} onClick={() => setViewMode("semesters")}>
                По семестрам
              </button>
              <button type="button" className={`tab-button ${viewMode === "blocks" ? "tab-button-active" : ""}`} onClick={() => setViewMode("blocks")}>
                По блокам
              </button>
            </div>

            {viewMode === "semesters" ? (
              <div className="page-content">
                {filteredSemesters.length ? (
                  filteredSemesters.map(({ semester, items }) => <SemesterTable key={semester.id} semester={semester} items={items} />)
                ) : (
                  <div className="card">
                    <p className="muted">По выбранным фильтрам пока нет дисциплин.</p>
                  </div>
                )}
              </div>
            ) : (
              <BlocksView blocks={filteredBlocks} />
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
                    <details key={code} className="accordion">
                      <summary>{code}</summary>
                      <ul className="list">
                        {items.map((item) => (
                          <li key={`${code}-${item.id}`} className="list-item">
                            <strong>
                              {item.code} {item.title}
                            </strong>
                            <div className="summary-badges">
                              {item.is_practice ? <span className="status-pill status-success">Практика</span> : null}
                              {item.requires_manual_confirmation ? <span className="status-pill status-danger">Нужна ручная проверка</span> : null}
                            </div>
                          </li>
                        ))}
                      </ul>
                    </details>
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
