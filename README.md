# Электронный паспорт группы СПО

MVP веб-приложения для колледжа на `Next.js + FastAPI + PostgreSQL`, где в одном интерфейсе собраны:

- паспорт группы
- состав группы
- учебный план по семестрам
- формы промежуточной аттестации
- практики
- ГИА
- карточка студента
- электронный журнал
- посещаемость
- роли и права доступа

Система строится по принципу: одна база данных, но разные кабинеты и уровни доступа для `admin`, `curator`, `teacher`, `student`, `parent`.

## Что уже есть в MVP

- JWT авторизация
- роли и базовое ограничение доступа
- 2 реальные образовательные программы
- 2 реальные группы: `1-ТЭК-23` и `1-ТД-24`
- 27 студентов, импортированных только по ФИО
- 6 семестров для каждой группы
- учебные планы по семестрам
- формы контроля: экзамен, ДЗ, кДЗ, экзамен по модулю, демонстрационный экзамен, защита диплома
- практики и записи по ГИА
- карточки студентов
- журнал, посещаемость и оценки
- демо-данные сразу после первого запуска

## Стек

- frontend: `Next.js 14`, `TypeScript`
- backend: `FastAPI`, `SQLAlchemy 2`, `Alembic`
- database: `PostgreSQL`
- auth: `JWT`
- infra: `Docker`, `docker-compose`

## Структура проекта

```text
.
├─ backend/
│  ├─ alembic/
│  ├─ app/
│  │  ├─ api/
│  │  ├─ core/
│  │  ├─ db/
│  │  ├─ models/
│  │  ├─ schemas/
│  │  └─ services/
│  ├─ Dockerfile
│  ├─ requirements.txt
│  └─ .env.example
├─ frontend/
│  ├─ app/
│  ├─ components/
│  ├─ lib/
│  ├─ Dockerfile
│  └─ .env.local.example
├─ docs/
├─ docker-compose.yml
├─ .env.example
└─ README.md
```

## Основные страницы

- `/login`
- `/dashboard`
- `/groups`
- `/groups/[id]`
- `/groups/[id]/students`
- `/students/[id]`
- `/groups/[id]/curriculum`
- `/groups/[id]/semesters`
- `/groups/[id]/practices`
- `/groups/[id]/gia`
- `/journal`
- `/attendance`
- `/grades`
- `/admin/users`
- `/admin/programs`

## Seed-аккаунты

- `admin / admin123`
- `curator / curator123`
- `teacher / teacher123`
- `student / student123`

## Быстрый запуск через Docker

1. Создайте `.env` в корне проекта на основе `.env.example`.
2. Выполните:

```bash
docker compose up --build
```

3. Откройте:

- frontend: [http://localhost:3000](http://localhost:3000)
- backend docs: [http://localhost:8000/docs](http://localhost:8000/docs)

При старте backend автоматически:

1. применяет миграции `alembic`
2. загружает seed-данные
3. запускает `uvicorn`

## Локальный запуск без Docker

### 1. PostgreSQL

Создайте базу данных `teacher_cabinet`.

### 2. Backend

Скопируйте `backend/.env.example` в `backend/.env`, затем выполните:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
python -m app.db.seed
uvicorn app.main:app --reload
```

### 3. Frontend

Скопируйте `frontend/.env.local.example` в `frontend/.env.local`, затем выполните:

```powershell
cd frontend
npm install
npm run dev
```

## Что загружается в seed

- 5 ролей
- 4 демо-пользователя
- 2 программы
- 2 группы
- 27 студентов
- 12 семестров
- формы контроля
- предметы, МДК, профессиональные модули, практики и ГИА
- реальные семестровые учебные планы для двух групп
- демо-записи оценок и посещаемости

## Особенности реализации

- личные данные вроде телефонов и дат рождения не используются
- в seed для студентов загружаются только ФИО
- спорные позиции учебного плана помечаются через `requires_manual_confirmation = true`
- интерфейс сделан светлым, спокойным и с крупными кнопками
- структура проекта рассчитана на дальнейшее расширение кабинета куратора, преподавателя, студента и родителя
