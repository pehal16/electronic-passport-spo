# Структура БД (MVP)

Цель: единая база данных с ролевым доступом и изоляцией данных по контексту пользователя.

## 1. Ядро идентификации и доступа

1. `users`
- id, full_name, email, phone, password_hash, is_active, created_at

2. `roles`
- id, code (`admin/curator/teacher/student/parent/management`), name

3. `user_roles`
- id, user_id, role_id, scope_type, scope_id

## 2. Справочники и структура колледжа

1. `specialities`
- id, code, name

2. `groups`
- id, code, title, course_number, speciality_id, start_year, end_year, status

3. `group_curators`
- id, group_id, curator_user_id, from_date, to_date

4. `disciplines`
- id, code, name, grading_type (`5_point/pass_fail/score`)

5. `teacher_assignments`
- id, teacher_user_id, group_id, discipline_id, hours_plan

## 3. Студенты и родители

1. `students`
- id, user_id (nullable), full_name, birth_date, group_id, student_no, status

2. `parents`
- id, user_id (nullable), full_name, phone, email, relation_type

3. `student_parents`
- id, student_id, parent_id, is_primary

## 4. Паспорт группы и карточка студента

1. `group_passports`
- id, group_id, summary, headman_student_id, notes, updated_at

2. `student_profiles`
- id, student_id, address, medical_notes, social_category, curator_notes_private

3. `student_achievements`
- id, student_id, title, event_date, level, comment

4. `student_practice`
- id, student_id, company, supervisor, period_from, period_to, result

## 5. Учебный процесс

1. `schedule_items`
- id, group_id, discipline_id, teacher_user_id, weekday, lesson_no, room

2. `lessons`
- id, group_id, discipline_id, teacher_user_id, lesson_date, topic, lesson_type

3. `attendance_records`
- id, lesson_id, student_id, status (`present/absent/late`), reason_type, comment

4. `grades`
- id, lesson_id, student_id, grade_value, grade_type, is_debt, comment

5. `teacher_comments`
- id, lesson_id, student_id, teacher_user_id, category (`remark/praise/info`), text

## 6. Коммуникации и документы

1. `notifications`
- id, sender_user_id, target_type (`group/student/parent`), target_id, title, body, created_at

2. `notification_receipts`
- id, notification_id, user_id, is_read, read_at, acknowledged

3. `documents`
- id, owner_type (`group/student/system`), owner_id, file_name, file_path, category, visibility

## 7. Аналитика и риски

1. `risk_signals`
- id, student_id, signal_type (`attendance_drop/grade_drop/debts/discipline`), score, details, status, created_at

2. `risk_actions`
- id, signal_id, curator_user_id, action_type, action_note, action_date

## 8. Аудит

1. `audit_log`
- id, actor_user_id, action, entity_type, entity_id, payload_json, created_at, ip

## 9. Ключевые связи

1. `groups -> specialities` (many-to-one)
2. `students -> groups` (many-to-one)
3. `teacher_assignments` связывает `teacher + group + discipline`
4. `lessons` строятся из assignment/schedule
5. `attendance_records` и `grades` привязаны к уроку и студенту
6. `student_parents` реализует связь many-to-many
7. `risk_signals` формируются по данным посещаемости и оценок

## 10. Минимум для старта разработки

Если нужно сократить первую итерацию:
1. `users, roles, user_roles`
2. `specialities, groups, disciplines`
3. `students, parents, student_parents`
4. `lessons, attendance_records, grades`
5. `notifications, notification_receipts`
6. `risk_signals`
