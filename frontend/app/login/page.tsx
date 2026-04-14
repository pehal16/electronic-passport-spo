"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/components/auth-provider";
import { apiFetch } from "@/lib/api";
import { LoginResponse } from "@/lib/types";

export default function LoginPage() {
  const router = useRouter();
  const { signIn } = useAuth();
  const [login, setLogin] = useState("admin");
  const [password, setPassword] = useState("admin123");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await apiFetch<LoginResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ login, password })
      });
      signIn(response);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось войти в систему.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-shell">
      <div className="login-layout">
        <section className="login-visual">
          <div>
            <p className="eyebrow">Кабинет колледжа</p>
            <h1>Электронный паспорт группы СПО</h1>
            <p className="muted">
              Современное рабочее пространство для куратора, преподавателя, студента и администратора.
            </p>
          </div>

          <div className="meta-grid">
            <div className="meta">
              <strong>Паспорт группы</strong>
              <span className="muted">Состав, учебный план, практика и ГИА в одном месте.</span>
            </div>
            <div className="meta">
              <strong>Журнал и ведомости</strong>
              <span className="muted">Понятные сценарии для оценки, посещаемости и печати.</span>
            </div>
            <div className="meta">
              <strong>Для преподавателей</strong>
              <span className="muted">Крупные кнопки, русский язык и минимум лишних экранов.</span>
            </div>
          </div>

          <ul className="login-points">
            <li>Быстрый вход в рабочий кабинет колледжа</li>
            <li>Ведомости, журнал, посещаемость и оценки на одном экране</li>
            <li>Современное оформление с аккуратной визуальной иерархией</li>
          </ul>
        </section>

        <section className="login-card">
          <p className="eyebrow">Вход в систему</p>
          <h1>Добро пожаловать</h1>
          <p className="muted">Используйте демо-логины или учётную запись преподавателя колледжа.</p>
          <form onSubmit={handleSubmit}>
            <label className="field">
              <span>Логин</span>
              <input value={login} onChange={(event) => setLogin(event.target.value)} placeholder="Введите логин" />
            </label>
            <label className="field">
              <span>Пароль</span>
              <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Введите пароль" />
            </label>
            {error ? <div className="error-box">{error}</div> : null}
            <button className="button" type="submit" disabled={loading}>
              {loading ? "Входим..." : "Войти в кабинет"}
            </button>
          </form>
          <div className="note-box" style={{ marginTop: "14px" }}>
            Демо-логины: admin/admin123, curator/curator123, teacher/teacher123, student/student123.
          </div>
        </section>
      </div>
    </div>
  );
}
