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
  { href: "/attestation-sheets", label: "Ведомости", roles: ["admin", "curator", "teacher"] },
  { href: "/attendance", label: "Посещаемость", roles: ["admin", "curator", "teacher", "student", "parent"] },
  { href: "/grades", label: "Оценки", roles: ["admin", "curator", "teacher", "student", "parent"] },
  { href: "/programs", label: "Программы", roles: ["admin", "curator", "teacher", "student", "parent"] },
  { href: "/admin/users", label: "Пользователи", roles: ["admin"] },
];

interface Crumb {
  label: string;
  href?: string;
}

function getInitials(name?: string | null) {
  if (!name) {
    return "КК";
  }
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("")
    .slice(0, 2);
}

export function PageShell({
  title,
  description,
  breadcrumbs = [],
  children,
}: {
  title: string;
  description: string;
  breadcrumbs?: Crumb[];
  children: ReactNode;
}) {
  const pathname = usePathname();
  const { user, signOut } = useAuth();
  const allowedNav = navItems.filter((item) => user && item.roles.includes(user.role.code));
  const isActive = (href: string) => pathname === href || pathname.startsWith(`${href}/`);

  return (
    <div className="app-shell">
      <div className="page-backdrop page-backdrop-one" />
      <div className="page-backdrop page-backdrop-two" />

      <header className="topbar">
        <div className="brand-block">
          <div className="eyebrow-row">
            <p className="eyebrow">Электронный паспорт группы СПО</p>
            <span className="status-pill status-success">Рабочий кабинет</span>
          </div>
          <div className="brand-row">
            <div>
              <h1 className="brand-title">Кабинет колледжа</h1>
              <p className="brand-subtitle">Единое пространство для групп, учебных планов, журнала и ведомостей.</p>
            </div>
          </div>
        </div>

        <div className="user-box">
          <div className="user-avatar" aria-hidden="true">
            {getInitials(user?.full_name)}
          </div>
          <div className="user-meta">
            <strong>{user?.full_name}</strong>
            <p className="muted">{user?.login}</p>
            <span className="status-pill">{user?.role.title}</span>
          </div>
          <button className="button button-secondary" type="button" onClick={signOut}>
            Выйти
          </button>
        </div>
      </header>

      <nav className="nav-row" aria-label="Основные разделы">
        {allowedNav.map((item) => (
          <Link key={item.href} href={item.href} className={`nav-button ${isActive(item.href) ? "nav-button-active" : ""}`}>
            {item.label}
          </Link>
        ))}
      </nav>

      {breadcrumbs.length ? <Breadcrumbs items={breadcrumbs} /> : null}

      <section className="hero-panel">
        <div>
          <p className="hero-kicker">Рабочий экран</p>
          <h2>{title}</h2>
          <p className="hero-description">{description}</p>
        </div>
        <div className="hero-side">
          <div className="hero-side-card">
            <span className="eyebrow">Пользователь</span>
            <strong>{user?.role.title}</strong>
            <p className="muted">Интерфейс подстраивается под роль и показывает только нужные разделы.</p>
          </div>
        </div>
      </section>

      <main className="page-content">{children}</main>

      <footer className="developer-plaque">
        <div>
          <span className="eyebrow">Разработка и сопровождение</span>
          <strong>Разработчик: Постовит Д.А.</strong>
        </div>
        <span className="status-pill">Современный кабинет колледжа</span>
      </footer>
    </div>
  );
}
