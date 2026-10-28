# Хөгжүүлэлтийн заавар

## Шаардлага

- Node.js 22+, npm 10+
- Python 3.14+ (uv ашиглана)
- PostgreSQL 18 (локал, `localhost:5432`)
- Docker шаардлагагүй (энэ орчинд суулгагдаагүй)

## Анхны тохиргоо

```bash
# 1. Өгөгдлийн сан
PGPASSWORD=postgres psql -h localhost -U postgres -c "CREATE DATABASE people_registry;"
PGPASSWORD=postgres psql -h localhost -U postgres -c "CREATE DATABASE people_registry_test;"

# 2. Backend
cd backend
uv venv --python 3.14 .venv
uv pip install --python .venv/bin/python -r requirements.txt
cp ../.env.example .env        # утгуудыг локал орчинд тааруулна
.venv/bin/alembic upgrade head
.venv/bin/python -m app.cli create-admin --username admin --full-name "Системийн администратор"
.venv/bin/python -m scripts.seed_demo   # сонголтоор: 100 demo хүн + 31 leader

# 3. Frontend
cd ../frontend
npm install
# VITE_API_URL тохируулахгүй бол Vite /api-г http://127.0.0.1:8000 руу proxy хийнэ.
```

> `create-admin` нь нууц үгийг интерактив асууна (эсвэл `--password-stdin`). Нууц үгийг команд мөрөнд шууд бичихгүй байхыг зөвлөнө. Dev seed-д `ADMIN_INITIAL_PASSWORD` env ашиглаж болно.

## Ажиллуулах

```bash
# Terminal 1
cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000

# Terminal 2
cd frontend && npm run dev
```

- Frontend: http://localhost:5173 эсвэл http://127.0.0.1:5173
- API docs: http://localhost:8000/api/docs (dev)
- Health: http://localhost:8000/api/health

## Тест

```bash
cd backend
.venv/bin/pytest -q                              # people_registry_test DB
.venv/bin/ruff check app tests migrations scripts

cd ../frontend
npm run lint
npm test                                         # Vitest (11 tests)
npm run build                                    # tsc -b && vite build
```

`npm run build` нь TypeScript typecheck-ийг хамт хийнэ. `vitest` нь jsdom дээр
Login, API client, Pagination, форматлалтын тестийг ажиллуулна.

Backend test нь `DATABASE_URL`-ийг `TEST_DATABASE_URL` env-ээр сольж, schema-г тусгайлан бэлдэнэ. Тестийн өгөгдлийн санг бүү ашигла.

## Synthetic 500k performance

```bash
createdb people_registry_bench
cd backend
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/people_registry_bench \
  .venv/bin/alembic upgrade head
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/people_registry_bench \
  .venv/bin/python scripts/benchmark_500k.py
```

`--force` нь benchmark өгөгдлийг дахин үүсгэнэ. Скрипт зөвхөн нэрэндээ
`bench` агуулсан database дээр ажиллана. Дэлгэрэнгүй дүн, EXPLAIN төлөвлөгөө:
`docs/PERFORMANCE.md`.

## Шалгалтын бүртгэл

| Огноо | Шалгалт | Үр дүн |
|---|---|---|
| 2026-10-20 | Environment inspection | Node 22.23.1, Python 3.14.8, PostgreSQL 18.6, Docker байхгүй |
| 2026-10-20 | Database creation | `people_registry`, `people_registry_test` үүссэн |
| 2026-10-20 | Backend pytest | **52 passed** (auth, people, hierarchy rules, leaders, admin, import/export, dashboard) |
| 2026-10-20 | Backend ruff | `app tests migrations scripts` — passed |
| 2026-10-20 | Frontend build | `tsc -b && vite build` — passed |
| 2026-10-20 | Frontend lint | ESLint — passed |
| 2026-10-20 | Frontend tests | **11 passed** (Vitest) |
| Dashboard charts | SVG/CSS diagram, URL drilldown, scoped stats |
| 2026-10-20 | 500k benchmark | Гол query-үүд < 100 ms; dashboard ~329 ms; 5 түвшний бүтэц |
| 2026-10-20 | Demo seed | 100 хүн + 31 удирдагч; `scripts/seed_demo.py` |

## Асуудал засах

- `psycopg.OperationalError` — PostgreSQL ажиллаж байгаа, `DATABASE_URL` зөв эсэхийг шалгана.
- Cookie илгээгдэхгүй — frontend нь Vite proxy (`/api`) ашиглаж байгаа эсэх, `credentials: include` эсэхийг шалгана.
- CSRF 403 — `pr_csrf` cookie болон `X-CSRF-Token` header таарч байгаа эсэх.
- Migration зөрүү — `alembic current`, `alembic upgrade head`; тестийн DB-д `alembic upgrade head` дахин ажиллуулна.
- Импорт 400 — файлын толгойн нэр, кодчилол (UTF-8), мөрийн тоо (≤50,000), хэмжээ (≤10 MB) шалгана.
- Экспорт/импорт 403 — зөвхөн ADMIN эрх шаардана.
- `parent-candidates` 403 — нэвтэрсэн хэрэглэгч харьяалал сонгох эрхтэй байх шаардана.
- Login дээр `Хүсэлтийн эх сурвалж зөвшөөрөгдөөгүй` — `ALLOWED_ORIGINS`-д
  ашиглаж буй origin (`http://localhost:5173`, `http://127.0.0.1:5173`)-ыг нэмнэ.
- Удирдагч хүн нэмэхэд 400 — зөвхөн өөрийн шууд доорх дараагийн түвшин
  (`Мянгат→Зуут`, `Зуут→Аравт`, `Аравт→Гишүүн`) нэмэгдэнэ.
