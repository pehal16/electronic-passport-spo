export const ROLE_TITLE_MAP: Record<string, string> = {
  admin: "Администратор",
  curator: "Куратор",
  teacher: "Преподаватель",
  student: "Студент",
  parent: "Родитель"
};

export const CONTROL_FORM_TITLE_MAP: Record<string, string> = {
  exam: "Экзамен",
  dz: "Дифференцированный зачет",
  kdz: "Комплексный дифференцированный зачет",
  module_exam: "Экзамен по модулю",
  demo_exam: "Демонстрационный экзамен",
  diploma_defense: "Защита дипломной работы",
  none: "Без итоговой формы контроля"
};

export const ATTENDANCE_STATUS_TITLE_MAP: Record<string, string> = {
  present: "Присутствовал",
  absent: "Отсутствовал",
  late: "Опоздал",
  excused: "Уважительная причина"
};

export const CYCLE_TITLE_MAP: Record<string, string> = {
  school: "Общеобразовательный цикл",
  social_humanitarian: "Социально-гуманитарный цикл",
  natural_science: "Естественнонаучный цикл",
  professional_general: "Общепрофессиональный цикл",
  professional_module: "Профессиональные модули",
  mdk: "МДК",
  practice: "Практики",
  gia: "ГИА"
};

export const STUDENT_STATUS_TITLE_MAP: Record<string, string> = {
  active: "Обучается",
  graduated: "Выпущен",
  archived: "Архив"
};

export function controlFormTitle(code: string, fallback?: string) {
  return CONTROL_FORM_TITLE_MAP[code] ?? fallback ?? code;
}

export function attendanceStatusTitle(code: string, fallback?: string) {
  return ATTENDANCE_STATUS_TITLE_MAP[code] ?? fallback ?? code;
}

export function cycleTitle(code: string, fallback?: string) {
  return CYCLE_TITLE_MAP[code] ?? fallback ?? code;
}

export function roleTitle(code: string, fallback?: string) {
  return ROLE_TITLE_MAP[code] ?? fallback ?? code;
}

export function studentStatusTitle(code: string, fallback?: string) {
  return STUDENT_STATUS_TITLE_MAP[code] ?? fallback ?? code;
}

export function yesNoLabel(value: boolean) {
  return value ? "Да" : "Нет";
}

export function formatHours(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "—";
  }
  return `${value} ч.`;
}

export function formatWeeks(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "—";
  }
  return `${value} нед.`;
}

export function knownHoursLabel(totalHours: number, knownItems: number) {
  if (knownItems <= 0) {
    return "—";
  }
  return `${totalHours} ч.`;
}

export function countLabel(value: number, emptyText = "—") {
  if (!value) {
    return emptyText;
  }
  return String(value);
}
