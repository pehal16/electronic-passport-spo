from __future__ import annotations

from datetime import date

from sqlalchemy import select, text

from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models import (
    AttendanceRecord,
    ControlForm,
    CurriculumItem,
    CuratorGroupLink,
    GiaRecord,
    GradeRecord,
    Group,
    ParentStudentLink,
    PracticeRecord,
    Program,
    Role,
    Semester,
    Student,
    StudentAccountLink,
    Subject,
    TeacherAssignment,
    User,
    SheetTemplate,
)

TEK_STUDENTS = [
    "Алексашов Архип Александрович",
    "Ангарова Асусена Юрьевна",
    "Емец Яна Владимировна",
    "Колесникова Марина Геннадьевна",
    "Киприянова Кристина Сергеевна",
    "Лозовой Глеб Вячеславович",
    "Смелова Дарья Игоревна",
    "Урсаленко Богдана Олеговна",
    "Хижняк Виктория Юрьевна",
    "Юрова Виктория Викторовна",
]

TD_STUDENTS = [
    "Агаркова Екатерина Вячеславовна",
    "Белькова София Владимировна",
    "Бигунова Анастасия Григорьевна",
    "Гарах Екатерина Олеговна",
    "Гула Карина Михайловна",
    "Денисова Кристина Эдуардовна",
    "Дьяковой Софии Сергеевны",
    "Липская Татьяна Викторовна",
    "Медведевой Ксении Алексеевны",
    "Меньшикова Анастасия Алексеевна",
    "Миронова Полина Дмитриевна",
    "Миронова Ульяна Дмитриевна",
    "Попова Виолетта Сергеевна",
    "Саенко Алина Антоновна",
    "Шапкина Варвара Артемовна",
    "Щенникова Светлана Викторовна",
    "Юрченко Елизавета Исмаилова",
]


def clear_database(session) -> None:
    table_names = [
        "attendance_records",
        "grade_records",
        "teacher_assignments",
        "curator_group_links",
        "student_account_links",
        "parent_student_links",
        "practice_records",
        "gia_records",
        "curriculum_items",
        "students",
        "semesters",
        "subjects",
        "groups",
        "programs",
        "control_forms",
        "users",
        "roles",
        "sheet_templates",
    ]
    session.execute(text(f"TRUNCATE TABLE {', '.join(table_names)} RESTART IDENTITY CASCADE;"))
    session.commit()


def create_roles(session) -> dict[str, Role]:
    roles = {
        "admin": Role(code="admin", title="Администратор"),
        "curator": Role(code="curator", title="Куратор"),
        "teacher": Role(code="teacher", title="Преподаватель"),
        "student": Role(code="student", title="Студент"),
        "parent": Role(code="parent", title="Родитель"),
    }
    session.add_all(roles.values())
    session.flush()
    return roles


def create_users(session, roles: dict[str, Role]) -> dict[str, User]:
    users = {
        "admin": User(full_name="Администратор системы", login="admin", password_hash=get_password_hash("admin123"), role_id=roles["admin"].id),
        "curator": User(full_name="Куратор учебной группы", login="curator", password_hash=get_password_hash("curator123"), role_id=roles["curator"].id),
        "teacher": User(full_name="Преподаватель специальных дисциплин", login="teacher", password_hash=get_password_hash("teacher123"), role_id=roles["teacher"].id),
        "student": User(full_name="Демо студент", login="student", password_hash=get_password_hash("student123"), role_id=roles["student"].id),
    }
    session.add_all(users.values())
    session.flush()
    return users


def create_control_forms(session) -> dict[str, ControlForm]:
    data = {
        "exam": "Экзамен",
        "dz": "Дифференцированный зачет",
        "kdz": "Комплексный дифференцированный зачет",
        "module_exam": "Экзамен по модулю",
        "credit_sheet": "Зачетная ведомость",
        "complex_exam": "Комплексный экзамен",
        "demo_exam": "Демонстрационный экзамен",
        "diploma_defense": "Защита дипломной работы",
        "none": "Нет итоговой формы в семестре",
    }
    forms = {code: ControlForm(code=code, title=title) for code, title in data.items()}
    session.add_all(forms.values())
    session.flush()
    return forms


def create_sheet_templates(session) -> dict[str, SheetTemplate]:
    templates = {
        "diff_credit": SheetTemplate(
            code="diff_credit",
            title="Ведомость дифференцированного зачета",
            type="diff_credit",
            header_label_type="specialty_or_profession",
            has_ticket_number=False,
            has_multiple_disciplines=False,
            has_not_appeared_field=True,
            has_not_submitted_field=True,
            signature_lines_count=2,
            grade_text_mode="full",
            is_active=True,
        ),
        "credit_sheet": SheetTemplate(
            code="credit_sheet",
            title="Зачетная ведомость",
            type="credit_sheet",
            header_label_type="specialty_or_profession",
            has_ticket_number=False,
            has_multiple_disciplines=False,
            has_not_appeared_field=True,
            has_not_submitted_field=True,
            signature_lines_count=2,
            grade_text_mode="full",
            is_active=True,
        ),
        "complex_diff_credit": SheetTemplate(
            code="complex_diff_credit",
            title="Ведомость комплексного дифференцированного зачета",
            type="complex_diff_credit",
            header_label_type="specialty_or_profession",
            has_ticket_number=False,
            has_multiple_disciplines=True,
            has_not_appeared_field=True,
            has_not_submitted_field=True,
            signature_lines_count=2,
            grade_text_mode="full",
            is_active=True,
        ),
        "complex_exam": SheetTemplate(
            code="complex_exam",
            title="Ведомость комплексного экзамена",
            type="complex_exam",
            header_label_type="specialty_or_profession",
            has_ticket_number=True,
            has_multiple_disciplines=True,
            has_not_appeared_field=True,
            has_not_submitted_field=False,
            signature_lines_count=2,
            grade_text_mode="full",
            is_active=True,
        ),
    }
    session.add_all(templates.values())
    session.flush()
    return templates


def create_programs_and_groups(session) -> tuple[dict[str, Program], dict[str, Group]]:
    programs = {
        "PROGRAM_1": Program(
            code="38.02.05",
            title="Товароведение и экспертиза качества потребительских товаров",
            qualification="товаровед-эксперт",
            education_form="очная",
            duration_text="2 года 10 месяцев",
            total_hours=None,
            gia_type="защита дипломной работы",
            notes=(
                "Группа 1-ТЭК-23.\n"
                "По учебному плану: 7 экзаменов и 30 дифференцированных зачетов, в том числе комплексных.\n"
                "ГИА: 6 недель.\n"
                "Выполнение дипломной работы: 4 недели.\n"
                "Защита дипломной работы: 2 недели.\n"
                "Обучение по дисциплинам и МДК: 97 недель.\n"
                "Учебная практика: 8 недель.\n"
                "Производственная практика по профилю специальности: 3 недели.\n"
                "Преддипломная практика: 4 недели.\n"
                "Промежуточная аттестация: 5 недель.\n"
                "Каникулы: 24 недели."
            ),
        ),
        "PROGRAM_2": Program(
            code="38.02.08",
            title="Торговое дело",
            qualification="специалист торгового дела",
            education_form="очная",
            duration_text="2 года 10 месяцев",
            total_hours=4428,
            gia_type="демонстрационный экзамен профильного уровня + защита дипломной работы",
            notes=(
                "Группа 1-ТД-24.\n"
                "Дополнительная квалификация: 12721 Кассир торгового зала 2 разряда.\n"
                "Практика всего: 576 часов.\n"
                "Учебная практика: 216 часов.\n"
                "Производственная практика: 360 часов.\n"
                "Итоги аттестации: 16 экзаменов и 30 дифференцированных зачетов, включая комплексные.\n"
                "ГИА: 6 недель.\n"
                "Выполнение ВКР: 4 недели.\n"
                "Защита дипломной работы: 2 недели.\n"
                "1 курс: 1460 часов обучения + 16 часов промежуточной аттестации.\n"
                "2 курс: 1086 часов обучения + 30 часов промежуточной аттестации + 360 часов практик.\n"
                "3 курс: 996 часов обучения + 48 часов промежуточной аттестации + 216 часов практик + 216 часов ГИА."
            ),
        ),
    }
    session.add_all(programs.values())
    session.flush()

    groups = {
        "GROUP_1": Group(name="1-ТЭК-23", program_id=programs["PROGRAM_1"].id, start_year=2023, course_now=1, curator_name=None, notes="Состав группы подтвержден по загруженному списку ФИО. В группе 10 студентов."),
        "GROUP_2": Group(name="1-ТД-24", program_id=programs["PROGRAM_2"].id, start_year=2024, course_now=1, curator_name=None, notes=None),
    }
    session.add_all(groups.values())
    session.flush()
    return programs, groups


def create_semesters(session, groups: dict[str, Group]) -> dict[str, dict[int, Semester]]:
    semester_notes = {
        "GROUP_1": {1: "Старт группы. В основном идет общеобразовательный цикл. Основная аттестация по большинству дисциплин завершается во 2 семестре."},
        "GROUP_2": {1: "Часть дисциплин 1 курса завершается только во 2 семестре."},
    }
    result: dict[str, dict[int, Semester]] = {}
    for key, group in groups.items():
        result[key] = {}
        for number, course_number in [(1, 1), (2, 1), (3, 2), (4, 2), (5, 3), (6, 3)]:
            semester = Semester(group_id=group.id, number=number, course_number=course_number, title=f"{number} семестр", notes=semester_notes.get(key, {}).get(number))
            session.add(semester)
            session.flush()
            result[key][number] = semester
    return result


def create_students(session, groups: dict[str, Group], users: dict[str, User]) -> dict[str, list[Student]]:
    students: dict[str, list[Student]] = {"GROUP_1": [], "GROUP_2": []}
    for full_name in TEK_STUDENTS:
        student = Student(group_id=groups["GROUP_1"].id, full_name=full_name, status="active")
        session.add(student)
        session.flush()
        students["GROUP_1"].append(student)
    for full_name in TD_STUDENTS:
        student = Student(group_id=groups["GROUP_2"].id, full_name=full_name, status="active")
        session.add(student)
        session.flush()
        students["GROUP_2"].append(student)
    session.add(StudentAccountLink(user_id=users["student"].id, student_id=students["GROUP_1"][0].id))
    return students


def ensure_subject(session, subjects: dict[str, Subject], program: Program, code: str, title: str, block_type: str, notes: str | None = None) -> Subject:
    key = f"{program.id}:{code}"
    if key not in subjects:
        subjects[key] = Subject(program_id=program.id, code=code, title=title, block_type=block_type, notes=notes)
        session.add(subjects[key])
        session.flush()
    return subjects[key]


def add_curriculum_item(
    session,
    group: Group,
    semester: Semester,
    subject: Subject,
    control_form: ControlForm,
    *,
    hours: int | None = None,
    contact_hours: int | None = None,
    practice_hours: int | None = None,
    is_practice: bool = False,
    practice_type: str | None = None,
    complex_group_code: str | None = None,
    statement_template_code: str | None = None,
    is_complex_exam: bool = False,
    requires_ticket_number: bool = False,
    examiner_count: int = 1,
    requires_manual_confirmation: bool = False,
    notes: str | None = None,
) -> CurriculumItem:
    resolved_contact_hours = contact_hours
    resolved_practice_hours = practice_hours
    if hours is not None and contact_hours is None and practice_hours is None:
        if is_practice:
            resolved_practice_hours = hours
        else:
            resolved_contact_hours = hours

    resolved_statement_template_code = statement_template_code
    if not resolved_statement_template_code:
        if control_form.code == "dz":
            resolved_statement_template_code = "diff_credit"
        elif control_form.code == "kdz":
            resolved_statement_template_code = "complex_diff_credit"
        elif control_form.code == "exam":
            resolved_statement_template_code = "complex_exam" if is_complex_exam else "diff_credit"
        elif control_form.code == "credit_sheet":
            resolved_statement_template_code = "credit_sheet"

    existing = session.execute(
        select(CurriculumItem).where(
            CurriculumItem.group_id == group.id,
            CurriculumItem.semester_id == semester.id,
            CurriculumItem.subject_id == subject.id,
        )
    ).scalar_one_or_none()
    if existing:
        existing.control_form_id = control_form.id
        existing.hours = hours if hours is not None else existing.hours
        existing.contact_hours = resolved_contact_hours if resolved_contact_hours is not None else existing.contact_hours
        existing.practice_hours = resolved_practice_hours if resolved_practice_hours is not None else existing.practice_hours
        existing.is_practice = is_practice or existing.is_practice
        existing.practice_type = practice_type or existing.practice_type
        existing.complex_group_code = complex_group_code or existing.complex_group_code
        existing.statement_template_code = resolved_statement_template_code or existing.statement_template_code
        existing.is_complex_exam = is_complex_exam or existing.is_complex_exam
        existing.requires_ticket_number = requires_ticket_number or existing.requires_ticket_number
        existing.examiner_count = examiner_count if examiner_count else existing.examiner_count
        existing.requires_manual_confirmation = requires_manual_confirmation or existing.requires_manual_confirmation
        existing.notes = notes or existing.notes
        session.flush()
        return existing
    item = CurriculumItem(
        group_id=group.id,
        semester_id=semester.id,
        subject_id=subject.id,
        control_form_id=control_form.id,
        hours=hours,
        contact_hours=resolved_contact_hours,
        practice_hours=resolved_practice_hours,
        is_practice=is_practice,
        practice_type=practice_type,
        complex_group_code=complex_group_code,
        statement_template_code=resolved_statement_template_code,
        is_complex_exam=is_complex_exam,
        requires_ticket_number=requires_ticket_number,
        examiner_count=examiner_count,
        requires_manual_confirmation=requires_manual_confirmation,
        notes=notes,
    )
    session.add(item)
    session.flush()
    return item


def seed_tek_curriculum(session, program: Program, group: Group, semesters: dict[int, Semester], forms: dict[str, ControlForm], subjects: dict[str, Subject]) -> list[CurriculumItem]:
    items: list[CurriculumItem] = []
    base_subjects = [
        ("ОДБ.00", "Общеобразовательный цикл", "school"),
        ("ОГСЭ.00", "Общий гуманитарный и социально-экономический цикл", "social_humanitarian"),
        ("ЕН.00", "Математический и общий естественнонаучный цикл", "natural_science"),
        ("ОП.00", "Общепрофессиональные дисциплины", "professional_general"),
        ("ПМ.00", "Профессиональные модули", "professional_module"),
        ("УП.00", "Учебная практика", "practice"),
        ("ПП.00", "Производственная практика", "practice"),
        ("ПДП.00", "Преддипломная практика", "practice"),
        ("ГИА.00", "Государственная итоговая аттестация", "gia"),
    ]
    for code, title, block_type in base_subjects:
        ensure_subject(session, subjects, program, code, title, block_type)

    semester_map = {
        2: [
            ("ОДБ.01", "Русский язык", "school", "exam"),
            ("ОДБ.02", "Литература", "school", "dz"),
            ("ОДБ.03", "История", "school", "dz"),
            ("ОДБ.04", "Обществознание", "school", "dz"),
            ("ОДБ.05", "География", "school", "dz"),
            ("ОДБ.06", "Иностранный язык", "school", "dz"),
            ("ОДБ.08", "Основы безопасности и жизнедеятельности", "school", "dz"),
            ("ОДБ.09", "Химия", "school", "exam"),
            ("ОДБ.10", "Биология", "school", "dz"),
            ("ОДБ.11", "Физика", "school", "dz"),
            ("ОДБ.12", "Индивидуальный проект", "school", "dz"),
            ("ОДП.01", "Математика", "school", "exam"),
            ("ОДП.02", "Информатика", "school", "dz"),
        ],
        3: [
            ("ЕН.02", "Экологические основы природопользования", "natural_science", "dz"),
            ("ОП.02", "Теоретические основы товароведения", "professional_general", "kdz"),
            ("ОП.03", "Статистика", "professional_general", "kdz"),
            ("ОП.14", "Охрана труда", "professional_general", "dz"),
        ],
        4: [
            ("ОГСЭ.02", "История", "social_humanitarian", "dz"),
            ("ОГСЭ.05", "Психология делового общения", "social_humanitarian", "dz"),
            ("ОП.01", "Основы коммерческой деятельности", "professional_general", "kdz"),
            ("ОП.04", "Информационные технологии в профессиональной деятельности", "professional_general", "dz"),
            ("ОП.11", "Маркетинг", "professional_general", "dz"),
            ("ОП.13", "Санитария и гигиена", "professional_general", "dz"),
        ],
        5: [
            ("ЕН.01", "Математика", "natural_science", "dz"),
            ("ОП.05", "Документационное обеспечение управления", "professional_general", "dz"),
        ],
        6: [
            ("ОГСЭ.01", "Основы философии", "social_humanitarian", "dz"),
            ("ОГСЭ.03", "Иностранный язык", "social_humanitarian", "dz"),
            ("ОГСЭ.04", "Физическая культура", "social_humanitarian", "dz"),
            ("ОП.06", "Правовое обеспечение профессиональной деятельности", "professional_general", "kdz"),
            ("ОП.07", "Бухгалтерский учет", "professional_general", "kdz"),
            ("ОП.08", "Метрология и стандартизация", "professional_general", "dz"),
            ("ОП.09", "Безопасность жизнедеятельности", "professional_general", "dz"),
            ("ОП.10", "Основы торгового предпринимательства", "professional_general", "kdz"),
            ("ОП.12", "Рекламная деятельность", "professional_general", "kdz"),
        ],
    }

    for semester_number, data in semester_map.items():
        for code, title, block_type, form_code in data:
            subject = ensure_subject(session, subjects, program, code, title, block_type)
            items.append(add_curriculum_item(session, group, semesters[semester_number], subject, forms[form_code]))

    module_subjects = [
        ("ПМ.01", "Управление ассортиментом товаров"),
        ("ПМ.02", "Проведение экспертизы и оценки качества товаров"),
        ("ПМ.03", "Организация работ в подразделении организации"),
        ("ПМ.04", "Выполнение работ по профессиям продавец продовольственных товаров / продавец непродовольственных товаров"),
    ]
    for code, title in module_subjects:
        ensure_subject(session, subjects, program, code, title, "professional_module")

    ambiguous_complex_groups = [
        ("KDZ_GROUP_1", [("ОП.02", "Теоретические основы товароведения", "professional_general"), ("ОП.03", "Статистика", "professional_general")]),
        ("KDZ_GROUP_2", [("ОП.01", "Основы коммерческой деятельности", "professional_general"), ("ОП.11", "Маркетинг", "professional_general")]),
        ("KDZ_GROUP_3", [("ОП.06", "Правовое обеспечение профессиональной деятельности", "professional_general"), ("ОП.07", "Бухгалтерский учет", "professional_general")]),
        ("KDZ_GROUP_4", [("ОП.10", "Основы торгового предпринимательства", "professional_general"), ("ОП.12", "Рекламная деятельность", "professional_general")]),
        ("KDZ_GROUP_5", [("МДК.01.01", "Основы управления ассортиментом", "mdk"), ("МДК.01.02", "Техническое оснащение торговых предприятий", "mdk"), ("УП.01", "Учебная практика", "practice"), ("ПП.01", "Производственная практика", "practice")]),
        ("KDZ_GROUP_6", [("МДК.02.01", "Оценка качества товаров и основы экспертизы", "mdk"), ("УП.02", "Учебная практика", "practice"), ("ПП.02", "Производственная практика", "practice")]),
        ("KDZ_GROUP_7", [("МДК.03.01", "Управление структурным подразделением организации", "mdk"), ("УП.03", "Учебная практика", "practice"), ("ПДП", "Преддипломная практика", "practice")]),
        ("KDZ_GROUP_8", [("МДК.04.01", "Технология продажи продовольственных и непродовольственных товаров", "mdk"), ("УП.04", "Учебная практика", "practice"), ("ПП.04", "Производственная практика", "practice")]),
    ]
    for group_code, values in ambiguous_complex_groups:
        for code, title, block_type in values:
            subject = ensure_subject(session, subjects, program, code, title, block_type, notes="Семестр для элемента требует уточнения по учебному плану.")
            items.append(
                add_curriculum_item(
                    session,
                    group,
                    semesters[6],
                    subject,
                    forms["kdz"],
                    is_practice=block_type == "practice",
                    practice_type="учебная" if code.startswith("УП") else "производственная" if code.startswith("ПП") else "преддипломная" if code == "ПДП" else None,
                    complex_group_code=group_code,
                    requires_manual_confirmation=True,
                    notes="Добавлено в структуру комплексной аттестации. Семестр и объем требуют ручного подтверждения.",
                )
            )

    gia_subject = ensure_subject(session, subjects, program, "ГИА.01", "Защита дипломной работы", "gia")
    items.append(add_curriculum_item(session, group, semesters[6], gia_subject, forms["diploma_defense"], notes="Форма ГИА: защита дипломной работы."))
    return items


def seed_td_curriculum(session, program: Program, group: Group, semesters: dict[int, Semester], forms: dict[str, ControlForm], subjects: dict[str, Subject]) -> list[CurriculumItem]:
    items: list[CurriculumItem] = []
    base_subjects = [
        ("ОДБ.00", "Общеобразовательный цикл", "school"),
        ("СГ.00", "Социально-гуманитарный цикл", "social_humanitarian"),
        ("ОП.00", "Общепрофессиональный цикл", "professional_general"),
        ("П.00", "Профессиональный цикл", "professional_module"),
        ("ПМ.01", "Организация и осуществление торговой деятельности", "professional_module"),
        ("ПМ.02", "Товароведение и организация экспертизы качества потребительских товаров", "professional_module"),
        ("ПМ.03", "Осуществление продаж потребительских товаров и координация работы с клиентами", "professional_module"),
        ("ПМ.04", "Выполнение работ по профессии 12721 Кассир торгового зала", "professional_module"),
        ("УП.00", "Учебная практика", "practice"),
        ("ПП.00", "Производственная практика", "practice"),
        ("ГИА.00", "Государственная итоговая аттестация", "gia"),
    ]
    for code, title, block_type in base_subjects:
        ensure_subject(session, subjects, program, code, title, block_type)

    semester_map = {
        1: [("ОДБ.05", "География", "school", "dz")],
        2: [
            ("ОДБ.01", "Русский язык", "school", "exam"),
            ("ОДБ.02", "Литература", "school", "dz"),
            ("ОДБ.03", "История", "school", "kdz"),
            ("ОДБ.06", "Иностранный язык", "school", "dz"),
            ("ОДБ.07", "Физическая культура", "school", "dz"),
            ("ОДБ.08", "Основы безопасности и защита Родины", "school", "dz"),
            ("ОДБ.09", "Химия", "school", "dz"),
            ("ОДБ.10", "Биология", "school", "dz"),
            ("ОДБ.11", "Физика", "school", "dz"),
            ("ОДБ.12", "Математика", "school", "exam"),
            ("ОДБ.13", "Информатика", "school", "dz"),
            ("ОДБ.14", "Экономика", "school", "exam"),
            ("ОДБ.15", "Индивидуальный проект", "school", "dz"),
        ],
        3: [
            ("СГ.01", "История России", "social_humanitarian", "dz"),
            ("МДК.02.01", "Основы товароведения", "mdk", "dz"),
            ("УП.02", "Учебная практика", "practice", "dz"),
        ],
        4: [
            ("СГ.05", "Основы финансовой грамотности", "social_humanitarian", "dz"),
            ("ОП.02", "Прикладные компьютерные программы в профессиональной деятельности", "professional_general", "dz"),
            ("МДК.02.02", "Товароведение потребительских товаров", "mdk", "exam"),
            ("МДК.02.03", "Оценка качества и основы экспертизы потребительских товаров", "mdk", "exam"),
            ("МДК.02.04", "Управление ассортиментом товаров", "mdk", "dz"),
            ("ПП.02", "Производственная практика", "practice", "dz"),
            ("ПМ.02", "Экзамен по модулю", "professional_module", "module_exam"),
            ("МДК.04.01", "Технология организации работы кассира", "mdk", "exam"),
            ("МДК.04.02", "Эксплуатация контрольно-кассового оборудования", "mdk", "dz"),
            ("УП.04", "Учебная практика", "practice", "dz"),
            ("ПП.04", "Производственная практика", "practice", "dz"),
            ("ПМ.04", "Экзамен по модулю", "professional_module", "module_exam"),
        ],
        5: [
            ("СГ.02", "Иностранный язык в профессиональной деятельности", "social_humanitarian", "kdz"),
            ("СГ.03", "Безопасность жизнедеятельности", "social_humanitarian", "dz"),
            ("ОП.03", "Эксплуатация торгово-технологического оборудования и охрана труда", "professional_general", "exam"),
            ("ОП.09", "Логистика", "professional_general", "exam"),
            ("МДК.03.01", "Технология продаж потребительских товаров и координация работы с клиентами", "mdk", "dz"),
            ("УП.03", "Учебная практика", "practice", "kdz"),
            ("ПП.03", "Производственная практика", "practice", "kdz"),
            ("ПМ.03", "Экзамен по модулю", "professional_module", "module_exam"),
        ],
        6: [
            ("СГ.04", "Физическая культура", "social_humanitarian", "dz"),
            ("ОП.01", "Экономика и основы анализа финансово-хозяйственной деятельности торговой организации", "professional_general", "kdz"),
            ("ОП.04", "Автоматизация торгово-технологических процессов", "professional_general", "exam"),
            ("ОП.05", "Основы предпринимательства", "professional_general", "kdz"),
            ("ОП.06", "Правовое обеспечение профессиональной деятельности", "professional_general", "dz"),
            ("ОП.07", "Рекламная деятельность", "professional_general", "dz"),
            ("ОП.08", "Торговый менеджмент", "professional_general", "exam"),
            ("ОП.10", "Документационное обеспечение управления", "professional_general", "kdz"),
            ("ОП.11", "Маркетинг в торговле", "professional_general", "exam"),
            ("ОП.12ц", "Современные цифровые технологии в профессиональной деятельности", "professional_general", "dz"),
            ("МДК.01.01", "Организация торгово-сбытовой деятельности на внутреннем и внешнем рынках", "mdk", "kdz"),
            ("МДК.01.02", "Организация и осуществление продаж", "mdk", "exam"),
            ("МДК.01.03", "Организация и осуществление закупок для государственных, муниципальных и корпоративных нужд", "mdk", "kdz"),
            ("УП.01", "Учебная практика", "practice", "kdz"),
            ("ПП.01", "Производственная практика", "practice", "dz"),
            ("ПМ.01", "Экзамен по модулю", "professional_module", "module_exam"),
        ],
    }

    for semester_number, data in semester_map.items():
        for code, title, block_type, form_code in data:
            subject = ensure_subject(session, subjects, program, code, title, block_type)
            items.append(
                add_curriculum_item(
                    session,
                    group,
                    semesters[semester_number],
                    subject,
                    forms[form_code],
                    is_practice=block_type == "practice",
                    practice_type="учебная" if code.startswith("УП") else "производственная" if code.startswith("ПП") else None,
                    complex_group_code="PM03_KDZ" if code in {"МДК.03.01", "УП.03", "ПП.03"} else None,
                    notes="Комплексный дифференцированный зачет по ПМ.03." if code in {"УП.03", "ПП.03", "МДК.03.01"} else None,
                )
            )

    gia_demo = ensure_subject(session, subjects, program, "ГИА.01", "Демонстрационный экзамен профильного уровня", "gia")
    gia_defense = ensure_subject(session, subjects, program, "ГИА.02", "Защита дипломной работы", "gia")
    items.append(add_curriculum_item(session, group, semesters[6], gia_demo, forms["demo_exam"], notes="Допуск после завершения всех практик и освоения модулей."))
    items.append(add_curriculum_item(session, group, semesters[6], gia_defense, forms["diploma_defense"]))
    return items


def create_practices_and_gia(session, groups: dict[str, Group], semesters: dict[str, dict[int, Semester]], forms: dict[str, ControlForm]) -> None:
    session.add_all(
        [
            PracticeRecord(group_id=groups["GROUP_1"].id, semester_id=None, title="Учебная практика", practice_type="учебная", weeks=8, hours=None, final_control_form_id=forms["kdz"].id, notes="Практика должна завершаться дифференцированным или комплексным дифференцированным зачетом."),
            PracticeRecord(group_id=groups["GROUP_1"].id, semester_id=None, title="Производственная практика по профилю специальности", practice_type="производственная", weeks=3, hours=None, final_control_form_id=forms["dz"].id, notes="Завершается дифференцированным зачетом."),
            PracticeRecord(group_id=groups["GROUP_1"].id, semester_id=semesters["GROUP_1"][6].id, title="Преддипломная практика", practice_type="преддипломная", weeks=4, hours=None, final_control_form_id=forms["kdz"].id, notes="Входит в завершающий этап перед ГИА."),
            PracticeRecord(group_id=groups["GROUP_2"].id, semester_id=None, title="Учебная практика", practice_type="учебная", weeks=None, hours=216, final_control_form_id=forms["dz"].id, notes="Во 2 курсе: 2 недели в 1 семестре и 8 недель во 2 семестре. В 3 курсе: 3 недели в 1 семестре и 3 недели во 2 семестре."),
            PracticeRecord(group_id=groups["GROUP_2"].id, semester_id=None, title="Производственная практика", practice_type="производственная", weeks=None, hours=360, final_control_form_id=forms["dz"].id, notes="Практика завершается дифференцированным зачетом; в ПМ.03 используется комплексный дифференцированный зачет."),
        ]
    )
    session.flush()
    session.add_all(
        [
            GiaRecord(group_id=groups["GROUP_1"].id, has_demo_exam=False, has_diploma_defense=True, total_weeks=6, preparation_weeks=4, defense_weeks=2, notes="Форма ГИА: защита дипломной работы"),
            GiaRecord(group_id=groups["GROUP_2"].id, has_demo_exam=True, has_diploma_defense=True, total_weeks=6, preparation_weeks=4, defense_weeks=2, notes="ГИА: демонстрационный экзамен профильного уровня + защита дипломной работы"),
        ]
    )


def create_access_links(session, users: dict[str, User], groups: dict[str, Group], curriculum_items: list[CurriculumItem]) -> None:
    session.add_all(
        [
            CuratorGroupLink(user_id=users["curator"].id, group_id=groups["GROUP_1"].id),
            CuratorGroupLink(user_id=users["curator"].id, group_id=groups["GROUP_2"].id),
        ]
    )
    unique_assignments = {(item.group_id, item.subject_id) for item in curriculum_items}
    for group_id, subject_id in unique_assignments:
        session.add(TeacherAssignment(user_id=users["teacher"].id, group_id=group_id, subject_id=subject_id))


def create_demo_records(session, students: dict[str, list[Student]], curriculum_items: list[CurriculumItem]) -> None:
    items_by_group: dict[int, list[CurriculumItem]] = {}
    for item in curriculum_items:
        items_by_group.setdefault(item.group_id, []).append(item)

    sample_dates = [date(2026, 2, 10), date(2026, 2, 17)]
    for group_students in students.values():
        if not group_students:
            continue
        group_id = group_students[0].group_id
        target_items = items_by_group[group_id][:2]
        for index, student in enumerate(group_students):
            for item_index, item in enumerate(target_items):
                session.add(GradeRecord(student_id=student.id, curriculum_item_id=item.id, date=sample_dates[item_index], grade_value=str(5 - ((index + item_index) % 3)), comment="Демо-оценка для запуска MVP."))
                status = "present"
                reason = None
                if (index + item_index) % 7 == 0:
                    status = "absent"
                    reason = "Отсутствовал по уважительной причине"
                elif (index + item_index) % 5 == 0:
                    status = "late"
                    reason = "Опоздание"
                session.add(AttendanceRecord(student_id=student.id, curriculum_item_id=item.id, date=sample_dates[item_index], status=status, reason=reason))


def seed() -> None:
    with SessionLocal() as session:
        clear_database(session)
        roles = create_roles(session)
        users = create_users(session, roles)
        forms = create_control_forms(session)
        create_sheet_templates(session)
        programs, groups = create_programs_and_groups(session)
        semesters = create_semesters(session, groups)
        students = create_students(session, groups, users)
        subjects: dict[str, Subject] = {}

        curriculum_items: list[CurriculumItem] = []
        curriculum_items.extend(seed_tek_curriculum(session, programs["PROGRAM_1"], groups["GROUP_1"], semesters["GROUP_1"], forms, subjects))
        curriculum_items.extend(seed_td_curriculum(session, programs["PROGRAM_2"], groups["GROUP_2"], semesters["GROUP_2"], forms, subjects))
        create_practices_and_gia(session, groups, semesters, forms)
        create_access_links(session, users, groups, curriculum_items)
        create_demo_records(session, students, curriculum_items)
        session.commit()


if __name__ == "__main__":
    seed()
