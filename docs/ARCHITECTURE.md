# Архитектур

## Ерөнхий зураг

```text
┌──────────────────────────┐        HTTPS + HttpOnly cookie        ┌─────────────────────────┐
│  React SPA (Vite build)  │ ────────────────────────────────────▶ │  FastAPI (modular)      │
│  TanStack Query, Router  │ ◀──────────────────────────────────── │  services / repos       │
└──────────────────────────┘            JSON / файл татах           └───────────┬─────────────┘
                                                                               │ SQLAlchemy
                                                                     ┌─────────▼──────────┐
                                                                     │ PostgreSQL 18      │
                                                                     │ people, closure,   │
                                                                     │ auth, audit, import│
                                                                     └────────────────────┘
```

- Нэг deploy нэгжтэй модульчлагдсан монолит. Frontend build-ийг production-д backend-ээс тусдаа static host эсвэл reverse proxy-оор үйлчилнэ.
- Development: Vite `:5173` нь `/api`-г `:8000` рүү proxy хийнэ. Ингэснээр cookie/CORS асуудалгүй.

## Backend давхаргууд

```text
app/main.py              app үүсгэх, middleware, router холболт
app/api/                 HTTP endpoint-ууд (request/response, status code)
app/api/deps.py          session, CSRF, permission dependency
app/schemas/             Pydantic request/response DTO
app/services/            бизнес логик, transaction boundary
app/repositories/        SQL query, eager loading, aggregation
app/models/              SQLAlchemy ORM
app/permissions/         role/scope/policy шалгалт
app/core/                config, security, validation, time, rate limit, errors
app/importer/            файл унших, мөр validation, import orchestration
```

Дүрэм:
- Route нь DTO хүлээж аваад service дуудаж, хариу буцаана. Том SQL, олон алхамт бизнес логик route-д байхгүй.
- Service нь authorization-ыг `permissions` модулиар шалгаж, repository-д `scope` нөхцөлийг дамжуулна.
- Repository нь өгөгдлийн сангийн нарийн ширийнийг нуухгүй, гэхдээ route-оос дуудагдахгүй.
- Бүх бичих үйлдэл transaction дотор. Нэг хүсэлтэд нэг session.
- Мэдрэмтгий талбарыг response schema үүсгэх үед mask хийнэ, DB-д бүтнээрээ хадгална.

## Frontend бүтэц

```text
src/main.tsx        QueryClient, Router, AuthProvider, ToastProvider
src/App.tsx         route тодорхойлолт, Protected/Admin guard
src/api/            fetch client (CSRF, алдааны DTO), TypeScript типүүд
src/auth/           AuthProvider, useAuth, session refresh
src/components/ui/  Button, Input, Select, Card, Modal, Badge, Toast, Pagination
src/components/layout/ AppShell, sidebar, topbar, notifications, profile menu
src/components/charts/ SVG/CSS диаграм (donut, bar, trend)
src/components/people/ ParentPicker, LeaderPicker
src/pages/          Login, Dashboard, PeopleList, PersonDetail/Form, Structure, Import, Users, Audit, Profile
src/lib/            labels, formatters, group colors/rules
src/test/           Vitest setup
```

- Server state: TanStack Query. UI state: React state. Форма: React Hook Form + Zod.
- Page нь component-уудыг compose хийнэ; жишээ нь `PeopleListPage` нь шүүлт, хүснэгт, `Pagination`-оос бүрдэнэ.
- Эрхтэй холбоотой товч нуух/идэвхгүй болгох нь зөвхөн UX; backend нь эрхийг заавал шалгана.

## Харьяаллын загвар

1. **Хэн нэмсэн** — `people.created_by_id` (audit-д бүрэн түүх).
2. **Шууд харьяалагдах хүн** — `people.parent_id`. A → B, C бол A-ийн шууд гишүүд B, C. B → D бол D нь B-ийн шууд гишүүн, A-ийн биш.
3. **Хатуу шатлал** — `Түмт → Мянгат → Зуут → Аравт → Гишүүн`. Зөвхөн дараагийн түвшин шууд хүүхэд байна; `Гишүүн` leaf, `Түмт` root. Дүрмийг `app/core/group_rules.py` төвлөрүүлнэ.
4. **Удирдагч/гишүүн хэрэглэгч** — `users.leader_person_id` нь нэг хүнтэй unique холбогдоно. Удирдагч зөвхөн өөрийн шууд доорх дараагийн түвшний хүн нэмнэ; өөрийн болон шууд хүүхдийн мэдээллийг засна. Мөн шууд хүүхдэд нэвтрэх эрх үүсгэж, нууц үгийг нь солино; бусад account-ыг ADMIN удирдана. Харьяалал/бүлгийн төрлийг зөвхөн ADMIN солино.
5. **Хандах эрх** — `users.leader_person_id` + closure table. `ADMIN` бүх модыг,
   `TUMT` бүх модыг бүтнээр, бусад `LEADER` өөрийн модыг бүтнээр болон бусад модыг
   хязгаарлагдмал талбараар, `MEMBER` нэг аравтын хүрээг харна.

Closure table нь:
- `(ancestor_id, descendant_id, depth)`; өөрөө өөртэйгөө `depth=0` мөртэй.
- Хүн нэмэхэд parent-ийн бүх ancestor мөрүүдийг хуулж бичнэ.
- Scope шалгалт: `person.id IN (SELECT descendant_id FROM person_closure WHERE ancestor_id IN (scope roots))`.
- Parent солих үед subtree-ийн closure-ыг transaction дотор дахин байгуулна.
- Circular parent-ыг `person_closure`-оор урьдчилан илрүүлнэ.

Closure хүснэгт нь 500k хүн, 5 түвшинтэй (root→Гишүүн гүн 4) үед ~2.44 сая мөр болно. Энэ нь индексжсэн EXISTS query-д тохиромжтой.

## Өгөгдлийн урсгал: хүн бүртгэх

```text
POST /api/people
  → auth session + CSRF
  → PeopleCreate schema (Pydantic normalization)
  → PeopleService.create
      → register number normalization/validation
      → parent/group rule check:
          ADMIN: valid node anywhere; root must be Түмт
          LEADER: leader person is the only parent; group must be next level
      → duplicate check + DB unique constraint (IntegrityError → 409)
      → INSERT person
      → INSERT closure (self + parent ancestors)
      → audit event
  → 201 PersonDetail (masked according to permissions)
```

## Алдааны формат

```json
{ "detail": "Монгол хэлээр хэрэглэгчид ойлгомжтой мессеж", "code": "OPTIONAL_MACHINE_CODE", "fields": {"reg_number": "..."} }
```

- 400/422 validation, 401 session, 403 permission, 404 scope/байхгүй, 409 conflict, 429 rate limit, 500 ерөнхий.
- Scope-оос гадуур ID-д 404 буцаана (IDOR мэдээлэл алдахаас сэргийлж).

## Импорт/экспорт

- Импорт: файлыг `var/imports/{job_uuid}.{ext}`-д хадгална. Preview нь streaming уншиж, header/мөр бүрийг validation хийнэ; `import_jobs`-д тоо, алдааны дээж, статус хадгална. Confirm нь файлыг дахин уншиж, 500 мөрийн chunk-аар insert хийнэ. `Нууц үг` бүхий мөр бүрт тухайн хүний төрлөөр `LEADER` эсвэл `MEMBER` хэрэглэгч үүсгэж, нууц үгийг Argon2id-аар hashлана. Нэг мөрний алдаа бусдыг унагахгүй; эцсийн тайланд valid/invalid болон үүссэн хэрэглэгчийн тоо гарна.
- Экспорт: зөвхөн хэрэглэгчийн харж болох мөрүүд, дээд тал 50,000. CSV-д UTF-8 BOM, `= + - @`-ээр эхэлсэн нүдийг `'` prefix-ээр хамгаална. XLSX мөн адил.
