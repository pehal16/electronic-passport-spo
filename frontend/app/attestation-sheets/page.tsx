"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { useAuth } from "@/components/auth-provider";
import { PageShell } from "@/components/page-shell";
import { ProtectedPage } from "@/components/protected-page";
import { apiFetch, buildQuery } from "@/lib/api";
import { AttestationSheet, CurriculumItem, CurriculumOverview, GroupSummary } from "@/lib/types";

export default function AttestationSheetsPage() {
  const { token } = useAuth();
  const router = useRouter();
  const [groups, setGroups] = useState<GroupSummary[]>([]);
  const [curriculum, setCurriculum] = useState<CurriculumOverview | null>(null);
  const [sheets, setSheets] = useState<AttestationSheet[]>([]);
  const [selectedGroupId, setSelectedGroupId] = useState("");
  const [selectedSemesterId, setSelectedSemesterId] = useState("");
  const [selectedCurriculumItemId, setSelectedCurriculumItemId] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      return;
    }
    const query = buildQuery({ group_id: selectedGroupId || undefined });
    apiFetch<AttestationSheet[]>(`/attestation-sheets${query}`, {}, token)
      .then(setSheets)
      .catch((err) => setError(err.message));
  }, [selectedGroupId, token]);

  useEffect(() => {
    if (!token) {
      return;
    }
    apiFetch<GroupSummary[]>("/groups", {}, token)
      .then((items) => {
        setGroups(items);
        const groupFromUrl = new URLSearchParams(window.location.search).get("group_id");
        if (groupFromUrl && items.some((group) => String(group.id) === groupFromUrl)) {
          setSelectedGroupId(groupFromUrl);
          return;
        }
        if (items.length) {
          setSelectedGroupId(String(items[0].id));
        }
      })
      .catch((err) => setError(err.message));
  }, [token]);

  useEffect(() => {
    if (!token || !selectedGroupId) {
      setCurriculum(null);
      return;
    }
    apiFetch<CurriculumOverview>(`/groups/${selectedGroupId}/curriculum`, {}, token)
      .then((response) => {
        setCurriculum(response);
      })
      .catch((err) => setError(err.message));
  }, [selectedGroupId, token]);

  const semesterOptions = useMemo(
    () =>
      (curriculum?.semesters ?? [])
        .filter((semester) => semester.items.length > 0)
        .sort((left, right) => left.number - right.number),
    [curriculum?.semesters]
  );

  useEffect(() => {
    if (!semesterOptions.length) {
      setSelectedSemesterId("");
      return;
    }
    if (!selectedSemesterId || !semesterOptions.some((semester) => String(semester.id) === selectedSemesterId)) {
      setSelectedSemesterId(String(semesterOptions[0].id));
    }
  }, [selectedSemesterId, semesterOptions]);

  const disciplineOptions = useMemo<CurriculumItem[]>(() => {
    if (!curriculum || !selectedSemesterId) {
      return [];
    }
    const targetSemester = curriculum.semesters.find((semester) => String(semester.id) === selectedSemesterId);
    return targetSemester?.items ?? [];
  }, [curriculum, selectedSemesterId]);

  useEffect(() => {
    if (!disciplineOptions.length) {
      setSelectedCurriculumItemId("");
      return;
    }
    if (!selectedCurriculumItemId || !disciplineOptions.some((item) => String(item.id) === selectedCurriculumItemId)) {
      setSelectedCurriculumItemId(String(disciplineOptions[0].id));
    }
  }, [disciplineOptions, selectedCurriculumItemId]);

  async function createSheet(event: FormEvent) {
    event.preventDefault();
    if (!token) {
      return;
    }
    if (!selectedCurriculumItemId) {
      setError("Выберите дисциплину, чтобы сформировать ведомость.");
      return;
    }
    setCreating(true);
    setError(null);
    setNotice(null);
    try {
      const sheet = await apiFetch<AttestationSheet>(
        "/attestation-sheets",
        {
          method: "POST",
          body: JSON.stringify({ curriculum_item_id: Number(selectedCurriculumItemId) }),
        },
        token
      );
      setNotice(`Ведомость №${sheet.id} сформирована.`);
      router.push(`/attestation-sheets/${sheet.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось сформировать ведомость.");
    } finally {
      setCreating(false);
    }
  }

  return (
    <ProtectedPage roles={["admin", "curator", "teacher"]}>
      <PageShell
        title="Ведомости"
        description="Сначала выберите группу и дисциплину, затем нажмите «Сформировать ведомость». Ниже отображается список уже созданных ведомостей."
        breadcrumbs={[{ label: "Главная", href: "/dashboard" }, { label: "Ведомости" }]}
      >
        {error ? <div className="error-box">{error}</div> : null}
        {notice ? <div className="note-box">{notice}</div> : null}

        <form className="card" onSubmit={createSheet}>
          <h3 className="section-title">Сформировать новую ведомость</h3>
          <div className="meta-grid">
            <label className="field">
              <span>Группа</span>
              <select value={selectedGroupId} onChange={(event) => setSelectedGroupId(event.target.value)}>
                {!groups.length ? <option value="">Нет доступных групп</option> : null}
                {groups.map((group) => (
                  <option key={group.id} value={group.id}>
                    {group.name} — {group.program.code}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>Семестр</span>
              <select value={selectedSemesterId} onChange={(event) => setSelectedSemesterId(event.target.value)}>
                {!semesterOptions.length ? <option value="">Семестр недоступен</option> : null}
                {semesterOptions.map((semester) => (
                  <option key={semester.id} value={semester.id}>
                    {semester.title}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>Дисциплина</span>
              <select value={selectedCurriculumItemId} onChange={(event) => setSelectedCurriculumItemId(event.target.value)}>
                {!disciplineOptions.length ? <option value="">Дисциплина недоступна</option> : null}
                {disciplineOptions.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.code} {item.title} ({item.control_form_title})
                  </option>
                ))}
              </select>
            </label>
          </div>
          <div className="button-row">
            <button type="submit" className="button" disabled={!selectedCurriculumItemId || creating}>
              {creating ? "Формируем..." : "Сформировать ведомость"}
            </button>
            {selectedGroupId ? (
              <Link href={`/groups/${selectedGroupId}/curriculum`} className="button button-link">
                Открыть учебный план группы
              </Link>
            ) : null}
          </div>
        </form>

        <div className="table-card">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Дата</th>
                <th>Группа</th>
                <th>Тип</th>
                <th>Дисциплина</th>
                <th>Статус</th>
                <th>Действие</th>
              </tr>
            </thead>
            <tbody>
              {sheets.map((sheet) => (
                <tr key={sheet.id}>
                  <td>{sheet.id}</td>
                  <td>{sheet.date}</td>
                  <td>{sheet.group_name}</td>
                  <td>{sheet.sheet_template.title}</td>
                  <td>{sheet.discipline_display_text}</td>
                  <td>{sheet.status === "saved" ? "Сохранена" : "Черновик"}</td>
                  <td>
                    <Link href={`/attestation-sheets/${sheet.id}`} className="button button-link compact-button">
                      Открыть
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!sheets.length ? <p className="muted">Пока нет сформированных ведомостей.</p> : null}
        </div>
      </PageShell>
    </ProtectedPage>
  );
}
