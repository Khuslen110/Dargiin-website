# Өгөгдлийн сан

PostgreSQL 18, SQLAlchemy 2, Alembic.

## Хүснэгтүүд

### `users`
| Талбар | Төрөл | Тайлбар |
|---|---|---|
| id | bigint PK | |
| username | varchar(64) unique | lowercase, 3–64, `[a-z0-9._-]` |
| full_name | varchar(120) | |
| password_hash | text | Argon2id |
| role | enum `ADMIN`, `LEADER`, `MEMBER` | |
| is_active | boolean | идэвхгүй хэрэглэгчийн session хүчингүй |
| leader_person_id | FK people null unique | LEADER/MEMBER-ийн холбогдох хүн; нэг хүнд нэг л хэрэглэгч |
| created_at / updated_at | timestamptz | UTC |

### `user_sessions`
| Талбар | Төрөл | Тайлбар |
|---|---|---|
| id | bigint PK | |
| user_id | FK users | `ON DELETE CASCADE` |
| token_hash | char(64) unique | SHA-256(token); token нь зөвхөн cookie-д |
| csrf_token | varchar(64) | session-д харьяалагдсан |
| expires_at / created_at / last_seen_at | timestamptz | |
| revoked_at | timestamptz null | logout/revoke |
| ip / user_agent | varchar | аудит/аюулгүй байдал, хэт урт биш |

### `people`
| Талбар | Төрөл | Тайлбар |
|---|---|---|
| id | bigint PK | дотоод ID; URL-д ашиглана |
| reg_number | varchar(10) unique | normalize: uppercase, space/hyphen устгасан |
| last_name | varchar(80) | Овог |
| first_name | varchar(80) | Нэр |
| gender | enum `MALE`, `FEMALE`, `OTHER` | |
| birth_date | date null | насыг тооцоолно, хадгалахгүй |
| phone | varchar(20) null | мэдрэмтгий |
| district | varchar(80) null | Дүүрэг |
| khoroo | varchar(80) null | Хороо |
| address | varchar(255) null | мэдрэмтгий |
| job | varchar(120) null | |
| group_type | enum `TUMT`, `MYANGAT`, `ZUUT`, `ARAVT`, `MEMBER` | хатуу 5 түвшин |
| parent_id | FK people null | шууд харьяалал; `ON DELETE RESTRICT` |
| created_by_id | FK users | `ON DELETE RESTRICT` |
| status | enum `ACTIVE`, `DELETED` | soft delete |
| deleted_at / deleted_by_id | timestamptz / FK users | |
| created_at / updated_at | timestamptz | |

### `person_closure`
| Талбар | Төрөл | Тайлбар |
|---|---|---|
| ancestor_id | FK people | PK хэсэг |
| descendant_id | FK people | PK хэсэг |
| depth | integer | 0 = өөрөө |

`ON DELETE CASCADE` (permanent delete үед). Индекс: `(ancestor_id, descendant_id)` PK, `(descendant_id)`.

### `audit_logs`
| Талбар | Төрөл | Тайлбар |
|---|---|---|
| id | bigint PK | |
| actor_id | FK users null | login failed үед null |
| action | varchar(50) | `PERSON_CREATE`, `PERSON_UPDATE`, ... |
| entity_type | varchar(30) / entity_id bigint null | |
| metadata | jsonb | мэдрэмтгий мэдээлэлгүй |
| ip | varchar(64) null | |
| created_at | timestamptz | |

Audit мөр засах/устгах endpoint байхгүй.

### `notifications`
| Талбар | Төрөл |
|---|---|
| id bigint PK | |
| user_id FK users CASCADE | |
| title varchar(120), body varchar(500) | |
| kind varchar(30) | `INFO`, `SUCCESS`, `WARNING` |
| read_at timestamptz null | |
| created_at timestamptz | |

### `import_jobs`
| Талбар | Төрөл | Тайлбар |
|---|---|---|
| id UUID PK | |
| user_id FK users | | |
| filename varchar(255) | | |
| file_path varchar(500) | | |
| status varchar(20) | `PREVIEWED`, `PROCESSING`, `COMPLETED`, `FAILED` | |
| total_rows / valid_rows / invalid_rows / imported_rows / accounts_created | int | |
| errors jsonb | эхний 100 алдаа | |
| created_at / completed_at | timestamptz | |

## Индексүүд (гол)

- `people.reg_number` — unique (soft delete хийсэн ч дугаар нөөцлөгдөнө).
- `people (status, created_at DESC)`, `people (parent_id)`, `people (group_type)`, `people (district)`, `people (khoroo)`, `people (created_by_id)`.
- `to_tsvector('simple', last_name)`, `(first_name)`, `(address)`, `(job)` дээр GIN FTS индекс — нэр, хаяг, ажлын хайлтад.
- `people (birth_date)` индекс — насны мужаар шүүхэд.
- `people (reg_number text_pattern_ops)` индекс — регистрийн prefix хайлтад.
- `lower(district)`, `lower(khoroo)` дээр `text_pattern_ops` индекс — prefix хайлтад.
- Утасны хайлт ADMIN, LEADER, MEMBER-т нээлттэй бөгөөд `ILIKE '%…%'` ашиглана.
- `person_closure (ancestor_id, descendant_id)` PK, `(descendant_id)` — path болон subtree.
- `audit_logs (created_at DESC)`, `(actor_id, created_at DESC)`, `(entity_type, entity_id)`.
- `notifications (user_id, read_at, created_at DESC)`.

`lower(username)` unique index (username normalization).

## Бүрэн бүтэн байдал ба дүрэм

- Регистрийн дугаарыг DB-д unique, application-д normalize + формат шалгалт.
- Бүлгийн шатлал хатуу: `TUMT → MYANGAT → ZUUT → ARAVT → MEMBER`; `TUMT` root, `MEMBER` leaf. Хүн нэмэх/зөөх/төрөл солих бүрт шалгана.
- `users.leader_person_id` unique; `LEADER` нь `TUMT/MYANGAT/ZUUT/ARAVT`, `MEMBER` нь `MEMBER` төрлийн идэвхтэй хүнтэй холбогдоно. LEADER өөрийн closure subtree-г бүтнээр, бусад модыг хязгаарлагдмал талбараар харна; `TUMT` бүх модыг бүтнээр харна.
- Soft delete: `status='DELETED'`. Энгийн query `status='ACTIVE'`-оор шүүнэ. Регистрийн дугаар давхар бүртгэгдэхгүйн тулд unique хэвээр.
- Restore: зөвхөн устгасан мөр; ижил дугаартай өөр мөр үүсэх боломжгүй (unique).
- Permanent delete: зөвхөн leaf (хүүхэдгүй), leader-т холбогдоогүй, ADMIN + reg number баталгаажуулалт. Audit-д үйлдэл үлдэнэ (хувийн мэдээлэлгүй).
- Parent устгах үед хүүхдүүд автоматаар устахгүй; тэдний `parent_id` хэвээр, parent нь DELETED төлөвтэй харагдана. ADMIN restore хийх боломжтой.
- Хүн нэмэх/зөөх transaction дотор closure-тойгоо хамт.
- `ON DELETE RESTRICT` parent, creator, leader_person дээр.

## Migration

```bash
cd backend
.venv/bin/alembic upgrade head
```

`migrations/versions/0001_initial.py` нь үндсэн хүснэгт, enum, индексийг;
`0002_hierarchy_leaders_search.py` нь `MEMBER` enum, `leader_person_id`,
birth-date/prefix/address/job индексүүдийг нэмнэ; `0003_simplify_users.py` нь
`USER`-ийг `LEADER` болгож, `user_scopes` болон илүүдэл permission flag-уудыг хасна.

> **Хязгаарлалт:** энэ орчинд `pg_trgm` extension суулгах эрх байхгүй (sudo
> шаардана). Иймд овог/нэрийн хайлт нь PostgreSQL-ийн built-in
> `to_tsvector('simple', …)` + prefix query, дүүрэг/хороо нь `lower(...)` prefix
> индексээр ажиллана. Утасны contains хайлт зөвхөн эрхтэй хэрэглэгчид нээлттэй.
