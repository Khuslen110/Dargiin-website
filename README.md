# Хүмүүсийн бүртгэл ба харьяаллын удирдлагын систем

Монгол хэлээр ажиллах, ~500,000 хүний бүртгэлийг дэмжих, эрх/хамрах хүрээтэй, орчин үеийн удирдлагын систем.

- **Frontend:** React 18, TypeScript, Vite 6, Tailwind CSS 3, TanStack Query 5, React Router 6, React Hook Form, Zod
- **Backend:** Python 3.14, FastAPI, SQLAlchemy 2, Alembic, Pydantic v2
- **DB:** PostgreSQL 18
- **Аюулгүй байдал:** Argon2id, DB session + HttpOnly cookie, CSRF, role/scope authorization, audit log

## Хурдан эхлэх

```bash
# DB (нэг удаа)
PGPASSWORD=postgres psql -h localhost -U postgres -c "CREATE DATABASE people_registry;"

# Backend
cd backend
uv venv --python 3.14 .venv
uv pip install --python .venv/bin/python -r requirements.txt
cp ../.env.example .env
.venv/bin/alembic upgrade head
.venv/bin/python -m app.cli create-admin --username admin --full-name "Системийн администратор"
.venv/bin/python -m scripts.seed_demo          # сонголтоор: 100 demo хүн + 31 удирдагч
.venv/bin/uvicorn app.main:app --reload --port 8000

# Frontend (шинэ terminal)
cd frontend
npm install
npm run dev
```

Нээх: http://localhost:5173 эсвэл http://127.0.0.1:5173

Demo seed хийсэн бол удирдагчийн нэвтрэлт: `tumt.01`, `myangat.01`, `zuut.01`,
`aravt.01`; нууц үг `Demo2026!Pass` (production-д ашиглахгүй).

Дэлгэрэнгүй: [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) · [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) · [docs/DATABASE.md](docs/DATABASE.md) · [docs/SECURITY.md](docs/SECURITY.md) · [docs/PROJECT_PLAN.md](docs/PROJECT_PLAN.md) · [docs/PERFORMANCE.md](docs/PERFORMANCE.md)

## Боломжууд

- Хянах самбар: хүйс, нас, дүүрэг/хороо, шатлал, 7 хоногийн динамик диаграм; дарж жагсаалт руу drilldown хийх боломж
- Хүмүүсийн бүртгэл: регистр/нэр/хаяг/ажил/хүйс/нас/харьяаллын нарийвчилсан хайлт, шүүлт, эрэмбэ, хуудаслалт
- Харьяаллын бүтэц: `Түмт → Мянгат → Зуут → Аравт → Гишүүн` хатуу шатлал, өнгөт мод, шууд гишүүд, зам, циклээс хамгаалал
- Удирдагч хэрэглэгч: хүн бүрт нэг leader binding; зөвхөн шууд доорх дараагийн түвшний бүртгэл нэмэх, тухайн хүүхдэд нэвтрэх эрх үүсгэх/нууц үг солих
- Хэрэглэгчийн эрх: `ADMIN` бүгдийг; `LEADER` өөрийн модны бүрэн мэдээлэл, бусад модны нэр/утас/хаяг; `TUMT` бүх модны бүрэн; `MEMBER` нэг аравтын хүрээ; audit, soft delete/restore/purge
- CSV/XLSX импорт/экспорт (ADMIN; preview + алдааны тайлан, formula injection-оос хамгаалалт; импортод `Хэрэглэгчийн нэр`/`Нууц үг` багана өгвөл нэвтрэх хэрэглэгч үүснэ)
- Мэдэгдэл, хариу үйлдэлтэй UI, монгол хэлний нэгдсэн бараан аналитик загвар
- 500,000 бүртгэлд зориулсан server-side pagination болон FTS/closure индекс
- Демо өгөгдөл: 100 хүн (1 Түмт, 3 Мянгат, 9 Зуут, 18 Аравт, 69 Гишүүн) + 31 удирдагч аккаунт

## Төслийн бүтэц

```text
backend/app/{api,core,models,schemas,repositories,services,permissions,importer}
backend/{migrations,tests,scripts}
frontend/src/{api,auth,components,pages,lib,test}
docs/
```

## Шалгалт

```bash
cd backend && .venv/bin/pytest -q && .venv/bin/ruff check app tests migrations scripts
cd frontend && npm run lint && npm test && npm run build
```

500k гүйцэтгэлийн дэлгэрэнгүй: [docs/PERFORMANCE.md](docs/PERFORMANCE.md).

> Энэ системийг production-д гарахаас өмнө `docs/SECURITY.md`-ийн production зөвлөмж, `docs/DEVELOPMENT.md`-ийн шалгалтуудыг гүйцэтгэнэ.
# Dargiin-website
