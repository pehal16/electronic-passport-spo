export type RoleCode = "admin" | "curator" | "teacher" | "student" | "parent";

export interface Role {
  id: number;
  code: RoleCode;
  title: string;
}

export interface User {
  id: number;
  full_name: string;
  login: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  role: Role;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Program {
  id: number;
  code: string;
  title: string;
  qualification: string;
  education_form: string;
  duration_text: string;
  total_hours: number | null;
  gia_type: string;
  notes: string | null;
}

export interface GroupSummary {
  id: number;
  name: string;
  start_year: number;
  course_now: number;
  curator_name: string | null;
  notes: string | null;
  program: Program;
  student_count: number;
  semester_count: number;
  exams_count: number;
  dz_count: number;
  kdz_count: number;
  has_kdz: boolean;
  practices_count: number;
  has_practices: boolean;
}

export interface Semester {
  id: number;
  number: number;
  course_number: number;
  title: string;
  notes: string | null;
}

export interface ControlForm {
  id: number;
  code: string;
  title: string;
}

export interface Subject {
  id: number;
  code: string;
  title: string;
  block_type: string;
  notes: string | null;
}

export interface CurriculumItem {
  id: number;
  code: string;
  title: string;
  semester_id: number;
  semester_number: number;
  semester_title: string;
  cycle_key: string;
  cycle_title: string;
  total_hours: number | null;
  contact_hours: number | null;
  practice_hours: number | null;
  control_form_code: string;
  control_form_title: string;
  is_practice: boolean;
  practice_type: string | null;
  complex_group_code: string | null;
  requires_manual_confirmation: boolean;
  notes: string | null;
  subject: Subject;
  control_form: ControlForm;
}

export interface SemesterSummary {
  discipline_count: number;
  total_hours: number;
  contact_hours: number;
  practice_hours: number;
  known_hours_items: number;
  missing_hours_items: number;
  exam_count: number;
  dz_count: number;
  kdz_count: number;
  practice_count: number;
  control_forms_count: number;
}

export interface SemesterCurriculum extends Semester {
  summary: SemesterSummary;
  items: CurriculumItem[];
}

export interface CurriculumBlock {
  key: string;
  title: string;
  items: CurriculumItem[];
}

export interface Practice {
  id: number;
  title: string;
  practice_type: string;
  weeks: number | null;
  hours: number | null;
  notes: string | null;
  semester: Semester | null;
  final_control_form: ControlForm | null;
  related_module: string | null;
  complex_group_code: string | null;
  outcome_text: string | null;
}

export interface GiaRecord {
  id: number;
  has_demo_exam: boolean;
  has_diploma_defense: boolean;
  total_weeks: number | null;
  preparation_weeks: number | null;
  defense_weeks: number | null;
  notes: string | null;
}

export interface GroupSummaryStats {
  students_total: number;
  disciplines_total: number;
  exams_total: number;
  dz_total: number;
  kdz_total: number;
  practices_total: number;
  gia_form: string;
}

export interface GroupDetailResponse {
  group: GroupSummary;
  semesters: Semester[];
  practices: Practice[];
  gia: GiaRecord | null;
  control_counts: Record<string, number>;
  block_counts: Record<string, number>;
  summary: GroupSummaryStats;
}

export interface CurriculumOverview {
  group: GroupSummary;
  semesters: SemesterCurriculum[];
  grouped_items: Record<string, CurriculumItem[]>;
  complex_groups: Record<string, CurriculumItem[]>;
  blocks: CurriculumBlock[];
}

export interface StudentListItem {
  id: number;
  full_name: string;
  status: string;
  notes: string | null;
  group_name: string;
  course_now: number;
  grade_count: number;
  absence_count: number;
}

export interface AttendanceRecord {
  id: number;
  date: string;
  student_id: number;
  student_name: string;
  status: string;
  status_title: string;
  reason: string | null;
  curriculum_item_id: number;
  curriculum_item_title: string;
  group_name: string;
}

export interface GradeRecord {
  id: number;
  date: string;
  student_id: number;
  student_name: string;
  grade_value: string;
  comment: string | null;
  curriculum_item_id: number;
  curriculum_item_title: string;
  group_name: string;
}

export interface StudentDetail {
  id: number;
  full_name: string;
  status: string;
  notes: string | null;
  group: GroupSummary;
  attendance: AttendanceRecord[];
  grades: GradeRecord[];
  current_subjects: string[];
  practices: Practice[];
  gia_text: string | null;
}

export interface DashboardStat {
  label: string;
  value: string;
  hint: string;
}

export interface DashboardQuickLink {
  label: string;
  href: string;
}

export interface DashboardData {
  role_code: RoleCode;
  role_title: string;
  user: User;
  stats: DashboardStat[];
  alerts: string[];
  quick_links: DashboardQuickLink[];
  groups_in_work: string[];
  attention_items: string[];
}

export interface JournalRow {
  curriculum_item_id: number;
  group_id: number;
  group_name: string;
  semester_id: number;
  semester_number: number;
  semester_title: string;
  subject_id: number;
  subject_code: string;
  subject_title: string;
  cycle_title: string;
  total_hours: number | null;
  control_form_code: string;
  control_form_title: string;
  student_count: number;
  grades_count: number;
  attendance_count: number;
  has_grades: boolean;
  has_attendance: boolean;
}

export interface JournalSubjectStudent {
  student_id: number;
  full_name: string;
  last_grade: string | null;
  grades_count: number;
  attended_count: number;
  absent_count: number;
  excused_count: number;
  late_count: number;
  last_comment: string | null;
}

export interface JournalSubject {
  curriculum_item_id: number;
  group_name: string;
  semester_title: string;
  subject_code: string;
  subject_title: string;
  control_form_title: string;
  students: JournalSubjectStudent[];
}

export interface AdminUsersResponse {
  users: User[];
}

export interface ProgramStructure {
  program_id: number;
  code: string;
  title: string;
  qualification: string;
  education_form: string;
  duration_text: string;
  gia_type: string;
  total_hours: number | null;
  practices: string[];
  control_forms: string[];
  key_modules: string[];
  notes: string | null;
}

export interface AdminProgramsResponse {
  programs: Program[];
  control_forms: ControlForm[];
  structures: ProgramStructure[];
}

export interface SheetTemplate {
  id: number;
  code: string;
  title: string;
  type: string;
  header_label_type: string;
  has_ticket_number: boolean;
  has_multiple_disciplines: boolean;
  has_not_appeared_field: boolean;
  has_not_submitted_field: boolean;
  signature_lines_count: number;
  grade_text_mode: string;
  is_active: boolean;
}

export interface AttestationSheetDiscipline {
  id: number;
  discipline_name: string;
  discipline_code: string | null;
  order_index: number;
}

export interface AttestationSheetRow {
  id: number;
  student_id: number | null;
  student_name_snapshot: string;
  row_number: number;
  ticket_number: string | null;
  grade_numeric: string | null;
  grade_text: string | null;
  attendance_result: "regular" | "not_submitted" | "not_appeared";
  comment: string | null;
}

export interface AttestationSheetTotals {
  excellent: number;
  good: number;
  satisfactory: number;
  unsatisfactory: number;
  not_submitted: number;
  not_appeared: number;
  admitted: number;
  total_rows: number;
  total_rows_words: string;
}

export interface AttestationSheet {
  id: number;
  group_id: number;
  group_name: string;
  semester_id: number | null;
  semester_title: string | null;
  curriculum_item_id: number | null;
  sheet_template: SheetTemplate;
  control_form_code: string;
  title: string;
  date: string;
  teacher_name: string;
  second_teacher_name: string | null;
  header_label: string;
  header_value: string;
  discipline_display_text: string;
  status: string;
  created_at: string;
  updated_at: string;
  program_title: string;
  college_name: string;
  disciplines: AttestationSheetDiscipline[];
  rows: AttestationSheetRow[];
  totals: AttestationSheetTotals;
}

export interface AttestationPreview {
  sheet_id: number;
  html: string;
}

export interface AttestationExport {
  sheet_id: number;
  filename: string;
  content_type: string;
  content_base64: string;
}
