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
    <div className="login-card">
      <p className="eyebrow">Колледж</p>
      <h1>Электронный паспорт группы СПО</h1>
      <p className="muted">
        Простая система для куратора, преподавателя, студента и администратора.
      </p>
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
      <div className="note-box">
        Демо-логины: admin/admin123, curator/curator123, teacher/teacher123, student/student123.
      </div>
    </div>
  );
}
