"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ReactNode } from "react";

import { useAuth } from "@/components/auth-provider";
import { Breadcrumbs } from "@/components/breadcrumbs";

const navItems = [
  { href: "/dashboard", label: "Главная", roles: ["admin", "curator", "teacher", "student", "parent"] },
  { href: "/groups", label: "Группы", roles: ["admin", "curator", "teacher", "student", "parent"] },
  { href: "/curriculum", label: "Учебные планы", roles: ["admin", "curator", "teacher", "student", "parent"] },
  { href: "/journal", label: "Журнал", roles: ["admin", "curator", "teacher"] },
  { href: "/attendance", label: "Посещаемость", roles: ["admin", "curator", "teacher", "student", "parent"] },
  { href: "/grades", label: "Оценки", roles: ["admin", "curator", "teacher", "student", "parent"] },
  { href: "/admin/programs", label: "Программы", roles: ["admin"] },
  { href: "/admin/users", label: "Пользователи", roles: ["admin"] }
];

interface Crumb {
  label: string;
  href?: string;
}

export function PageShell({
  title,
  description,
  breadcrumbs = [],
  children
}: {
  title: string;
  description: string;
  breadcrumbs?: Crumb[];
  children: ReactNode;
}) {
  const pathname = usePathname();
  const { user, signOut } = useAuth();
  const allowedNav = navItems.filter((item) => user && item.roles.includes(user.role.code));

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Электронный паспорт группы СПО</p>
          <h1 className="brand-title">Кабинет колледжа</h1>
          <p className="muted">{user?.role.title}</p>
        </div>
        <div className="user-box">
          <div>
            <strong>{user?.full_name}</strong>
            <p className="muted">{user?.login}</p>
          </div>
          <button className="button button-secondary" type="button" onClick={signOut}>
            Выйти
          </button>
        </div>
      </header>

      <nav className="nav-row" aria-label="Основные разделы">
        {allowedNav.map((item) => (
          <Link key={item.href} href={item.href} className={`nav-button ${pathname === item.href ? "nav-button-active" : ""}`}>
            {item.label}
          </Link>
        ))}
      </nav>

      {breadcrumbs.length ? <Breadcrumbs items={breadcrumbs} /> : null}

      <section className="hero-panel">
        <div>
          <h2>{title}</h2>
          <p className="hero-description">{description}</p>
        </div>
      </section>

      <main className="page-content">{children}</main>
    </div>
  );
}
