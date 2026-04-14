"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/components/auth-provider";
import { ProtectedPage } from "@/components/protected-page";
import { apiFetch } from "@/lib/api";
import { AttestationSheet } from "@/lib/types";

export default function CreateAttestationSheetPage() {
  const { token } = useAuth();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      return;
    }
    const curriculumItemId = new URLSearchParams(window.location.search).get("curriculum_item_id");
    if (!curriculumItemId) {
      setError("Не удалось определить дисциплину для формирования ведомости.");
      return;
    }
    apiFetch<AttestationSheet>(
      "/attestation-sheets",
      {
        method: "POST",
        body: JSON.stringify({
          curriculum_item_id: Number(curriculumItemId),
        }),
      },
      token
    )
      .then((sheet) => {
        router.replace(`/attestation-sheets/${sheet.id}`);
      })
      .catch((err) => {
        setError(err.message);
      });
  }, [router, token]);

  return (
    <ProtectedPage roles={["admin", "curator", "teacher"]}>
      <div className="center-panel">
        {error ? <div className="error-box">{error}</div> : <p>Формируем ведомость и подготавливаем мастер заполнения…</p>}
      </div>
    </ProtectedPage>
  );
}
