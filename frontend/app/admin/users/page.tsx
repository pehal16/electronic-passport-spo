"use client";

import { useEffect, useState } from "react";

import { useAuth } from "@/components/auth-provider";
import { PageShell } from "@/components/page-shell";
import { ProtectedPage } from "@/components/protected-page";
import { apiFetch } from "@/lib/api";
import { AdminUsersResponse } from "@/lib/types";

export default function AdminUsersPage() {
  const { token } = useAuth();
  const [data, setData] = useState<AdminUsersResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    apiFetch<AdminUsersResponse>("/admin/users", {}, token).then(setData).catch((err) => setError(err.message));
  }, [token]);

  return (
    <ProtectedPage roles={["admin"]}>
      <PageShell
        title="Пользователи"
        description="Администратор управляет пользователями и ролями доступа."
        breadcrumbs={[{ label: "Главная", href: "/dashboard" }, { label: "Пользователи" }]}
      >
        {error ? <div className="error-box">{error}</div> : null}
        <div className="table-card">
          <table>
            <thead><tr><th>ФИО</th><th>Логин</th><th>Роль</th><th>Статус</th></tr></thead>
            <tbody>
              {data?.users.map((user) => (
                <tr key={user.id}>
                  <td>{user.full_name}</td>
                  <td>{user.login}</td>
                  <td>{user.role.title}</td>
                  <td>{user.is_active ? "Активен" : "Отключен"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </PageShell>
    </ProtectedPage>
  );
}
