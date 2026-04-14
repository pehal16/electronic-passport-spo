import type { Metadata } from "next";
import { Manrope } from "next/font/google";
import type { ReactNode } from "react";

import { AuthProvider } from "@/components/auth-provider";

import "./globals.css";

const manrope = Manrope({
  subsets: ["latin", "cyrillic"],
  variable: "--font-sans",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Электронный паспорт группы СПО",
  description: "Современный кабинет колледжа: группы, учебные планы, журнал, ведомости, посещаемость и оценки.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="ru">
      <body className={manrope.variable}>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
