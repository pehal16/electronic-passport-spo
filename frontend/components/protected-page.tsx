"use client";

import { ReactNode, useEffect } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/components/auth-provider";
import { RoleCode } from "@/lib/types";

export function ProtectedPage({ children, roles }: { children: ReactNode; roles?: RoleCode[] }) {
  const router = useRouter();
  const { isReady, token, user } = useAuth();

  useEffect(() => {
    if (!isReady) {
      return;
    }
    if (!token) {
      router.replace("/login");
      return;
    }
    if (roles && user && !roles.includes(user.role.code)) {
      router.replace("/dashboard");
    }
  }, [isReady, roles, router, token, user]);

  if (!isReady) {
    return <div className="center-panel">Проверяем доступ к кабинету...</div>;
  }
  if (!token || !user) {
    return <div className="center-panel">Переходим на страницу входа...</div>;
  }
  if (roles && !roles.includes(user.role.code)) {
    return <div className="center-panel">Для этого раздела у вашей роли нет доступа.</div>;
  }
  return <>{children}</>;
}
