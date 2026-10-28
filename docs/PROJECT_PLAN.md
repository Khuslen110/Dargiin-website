# Хүмүүсийн бүртгэлийн систем — Төслийн төлөвлөгөө

Сүүлд шинэчилсэн: 2026-10-20 (Phase 0–8 + шатлал/удирдагч/хайлтын өргөтгөл)

## 1. Одоогийн байдал (Phase 0 үр дүн)

- Ажлын сан `/home/khuslen/Project1` эхлэх үед **хоосон** байсан.
- Node.js 22.23.1, npm 10.9.8, Python 3.14.8, uv, PostgreSQL 18.6 локал сервер ажиллаж байна.
- Docker суулгагдаагүй тул Docker Compose-оор биш, локал PostgreSQL + хоёр процесс (FastAPI, Vite) ашиглана.
- PostgreSQL `postgres/postgres` хэрэглэгчээр холбогдож, `people_registry`, `people_registry_test` өгөгдлийн сангуудыг үүсгэсэн.
- Git репозитор эхлээгүй. Энэ ажилд commit хийхгүй.

## 2. Архитектурын шийдвэрүүд (товч)

| Сэдэв | Шийдвэр |
|---|---|
| Хэлбэр | Модульчлагдсан монолит: FastAPI backend + React SPA |
| Өгөгдлийн сан | PostgreSQL, SQLAlchemy 2, Alembic |
| Нэвтрэлт | DB-д хадгалсан opaque session token, HttpOnly cookie + CSRF double-submit |
| Нууц үг | Argon2id (`argon2-cffi`) |
| Эрх | `ADMIN` / `LEADER` / `MEMBER`; LEADER, MEMBER нь `leader_person_id`-ээр тодорхойлогдоно |
| Хамрах хүрээ | `ADMIN` бүгд; `TUMT` бүх мод; бусад `LEADER` өөрийн мод бүтнээр + бусдыг хязгаарлагдмал; `MEMBER` нэг аравт |
| Харьяалал | `people.parent_id` + `person_closure` closure table |
| Устгал | Soft delete; permanent delete зөвхөн ADMIN, хүүхэдгүй, тодорхой баталгаажуулалттай |
| Регистрийн дугаар | normalize (uppercase, space/hyphen арилгах) + DB unique; soft delete хийсэн ч дугаар нөөцлөгдөнө |
| Импорт | CSV/XLSX preview → баталгаажуулалт → chunked insert; файл `var/imports`-д түр хадгална |
| 500k гүйцэтгэл | server-side pagination, FTS/prefix индекс, closure scope query, aggregation SQL |

Дэлгэрэнгүй: `docs/ARCHITECTURE.md`, `docs/DATABASE.md`, `docs/SECURITY.md`, `docs/DEVELOPMENT.md`, `docs/PERFORMANCE.md`.

## 3. Таамаглал ба нээлттэй асуудлууд

1. **Регистрийн дугаарын формат**: Монгол регистрийн дугаарыг `2 кирилл үсэг + 8 цифр` гэж таамаглаж, normalize хийсний дараа шалгана. Шалгах оронгийн (checksum) алгоритмыг баталгаажаагүй тул хийхгүй. Шаардлагатай бол `app/core/validation.py` дээр нэмнэ.
2. **Бүлгийн төрлүүд** нь хатуу шатлал: `Түмт → Мянгат → Зуут → Аравт → Гишүүн`. `Түмт` root, `Гишүүн` leaf; зөвхөн дараагийн түвшин шууд хүүхэд байна.
3. **Хэрэглэгчийг зөвхөн ADMIN үүсгэнэ** (өөрөө бүртгүүлэх урсгалгүй). `users.leader_person_id` нь удирдагч хүнтэй unique холбогдоно. Удирдагч зөвхөн өөрийн шууд доорх дараагийн түвшний бүртгэл нэмнэ; ADMIN л харьяалал/төрөл сольж, root үүсгэнэ. LEADER өөрийн subtree-г бүтнээр, бусад модыг нэр/утас/хаягаар харна; TUMT бүх модыг бүтнээр харна.
4. **Утас/хаяг** нь холбоо барих үндсэн мэдээлэл; ADMIN, LEADER, MEMBER харна. Бусад модны регистр, хүйс, төрсөн огноо, ажил зэргийг зөвхөн ADMIN, TUMT болон тухайн модны эзэн бүтнээр харна; импорт/экспорт зөвхөн ADMIN.
5. **Timezone**: DB-д UTC (`timestamptz`), харуулахад `Asia/Ulaanbaatar` (UTC+8).
6. 500,000 бичлэгийн туршилтыг synthetic өгөгдлөөр хийнэ; бодит хүний мэдээлэл ашиглахгүй.

## 4. Явцын checklist

### Phase 0 — Inspection & planning
- [x] Workspace inspection
- [x] Environment capability check
- [x] Docs үүсгэх

### Phase 1 — Foundation
- [x] Backend package/config/DB session/health endpoint
- [x] Alembic тохиргоо, анхны migration
- [x] `.env.example`, README, dev scripts
- [x] Frontend Vite + TS + Tailwind суурь
- [x] Frontend ↔ backend proxy холболт

### Phase 2 — Design system
- [x] UI primitives (Button, Input, Select, Card, Dialog, Table, Badge, Toast, Pagination)
- [x] Sidebar/topbar/responsive layout
- [x] Light theme (Mongolian government-style navy/brand palette)
- [x] Site-wide dark analytics theme

### Phase 3 — DB & auth
- [x] Models + migration (users, sessions, scopes, people, closure, audit, notifications, imports)
- [x] Argon2id password, login/logout, session revocation, CSRF
- [x] Auth rate limiting
- [x] Backend auth/permission tests

### Phase 4 — People registry
- [x] Search/list/filter/sort/pagination API
- [x] Create/detail/update API, duplicate check
- [x] Frontend list/search/form/detail
- [x] Tests

### Phase 5 — Hierarchy & leadership
- [x] Closure maintenance, cycle prevention
- [x] Strict `Түмт → Мянгат → Зуут → Аравт → Гишүүн` types
- [x] Leader user binding, direct-child-only creation/edit
- [x] Direct members, path, scope enforcement; subtree/direct search filters
- [x] Hierarchy UI (өнгөт мод, lazy expansion, тайлбар)
- [x] Tests

### Phase 6 — Administration
- [x] User management + scopes
- [x] Leader direct-child account create/password reset, ADMIN fallback
- [x] Audit log
- [x] Soft delete/restore/purge
- [x] Tests

### Phase 7 — Import/export & notifications
- [x] CSV/XLSX preview, validation, error report
- [x] `Хэрэглэгчийн нэр`/`Нууц үг` баганаар импортоос нэвтрэх хэрэглэгч үүсгэх
- [x] Export with formula-injection protection (CSV + XLSX)
- [x] In-app notifications
- [x] Tests

### Phase 8 — Security & performance
- [x] Full backend test suite (58 tests)
- [x] Frontend tests (11 tests), typecheck, lint, production build
- [x] Synthetic 500k benchmark + EXPLAIN documentation (`docs/PERFORMANCE.md`)
- [x] Site-wide dark analytics theme

### Phase 9 — Dashboard analytics
- [x] Gender, age, district, khoroo, hierarchy distribution APIs
- [x] 7-day registration trend
- [x] Custom SVG/CSS charts, responsive layout
- [x] Chart drilldown to filtered people list
- [x] Scoped dashboard tests

## 5. Тестийн үр дүн

| Шалгалт | Үр дүн |
|---|---|
| Backend pytest | 52 passed |
| Backend ruff (`app`, `tests`, `migrations`, `scripts`) | passed |
| Frontend typecheck/build | passed (`tsc -b && vite build`) |
| Frontend ESLint | passed |
| Frontend Vitest | 11 passed |
| 500k benchmark | Бүх гол query < 100 ms; бүрэн dashboard ~329 ms (дэлгэрэнгүй: `docs/PERFORMANCE.md`) |

Эцсийн шалгалтын дэлгэрэнгүйг `docs/DEVELOPMENT.md`-ийн «Шалгалтын бүртгэл» хэсгээс үзнэ.

## 6. Мэдэгдэж буй хязгаарлалтууд

- Rate limiter нь процесс доторх (in-memory); олон instance дээр Redis шаардана. Одоогоор нэг instance-ийн modular monolith.
- Импортын дээд хэмжээ 50,000 мөр/файл; илүү том бол background worker (жишээ нь Celery) шаардана.
- Экспортын дээд хэмжээ 50,000 мөр; илүү их өгөгдлийг хуваан экспортолно.
- Session token-ууд зөвхөн hash хэлбэрээр DB-д хадгалагдана.
- Docker Compose байхгүй (Docker суулгагдаагүй); локал PostgreSQL ашиглана.
- `pg_trgm` extension боломжгүй тул FTS/prefix индекс ашигласан. Хэрэв триграм
  хайлт шаардлагатай бол `CREATE EXTENSION pg_trgm` эрхтэй орчинд нэмэлт
  migration хийж болно.
- Count query нь scoped жагсаалтын гол зардал (500k дээр ~26 ms, нэмэлт
  шүүлттэй үед ~75 ms). Ирээдүйд кэш эсвэл estimate ашиглаж болно.
- Demo seed нь `Demo2026!Pass` нийтлэг нууц үгтэй 31 удирдагч аккаунт үүсгэдэг;
  зөвхөн локал демо/туршилтад ашиглана.
- Импорт/экспорт синхрон; 50,000 мөрийн дээд хязгаартай. Background worker
  нэмэх боломжтой.
