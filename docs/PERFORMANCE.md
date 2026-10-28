# Гүйцэтгэлийн хэмжилт — 500,000 бүртгэл

Хэмжилтийн огноо: 2026-10-20

## Орчин

| Зүйл | Утга |
|---|---|
| PostgreSQL | 18.6, локал `127.0.0.1:5432` |
| Database | `people_registry_bench` |
| Python | 3.14.8 |
| Backend | FastAPI + SQLAlchemy 2, psycopg 3 |
| Өгөгдөл | 100% synthetic, бодит хүний мэдээлэлгүй |

## Өгөгдлийн бүтэц

- Нийт 500,000 иргэн.
- 50 Түмт (root), 500 Мянгат, 5,000 Зуут, 50,000 Аравт, 444,450 энгийн гишүүн.
- `person_closure`: 2,438,300 мөр.
- Регистр: `БН` + 8 цифр, жишээ `БН00012345`.
- Овог/нэр: 20 түгээмэл монгол нэрээр round-robin; FTS-ийн хамгийн муу тохиолдолд ойролцоо (25,000 ижил овог).
- Дүүрэг: 9 утга; хороо: 30 утга.

## Хэмжилтийн арга

`backend/scripts/benchmark_500k.py` нь:

1. `COPY`-гоор 500,000 мөрийг нэг transaction-д оруулна.
2. Recursive CTE-ээр closure table-ийг үүсгэнэ.
3. `ANALYZE` хийсний дараа SQL болон repository/service query-г тус бүр 3 удаа ажиллуулж **хамгийн бага** хугацааг авна.
4. Admin болон `scope root=1` хэрэглэгчийн аль алиныг шалгана.

Дахин ажиллуулах:

```bash
createdb people_registry_bench
cd backend
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/people_registry_bench \
  .venv/bin/alembic upgrade head
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/people_registry_bench \
  .venv/bin/python scripts/benchmark_500k.py
```

`--force` нь одоо байгаа benchmark өгөгдлийг устгаж дахин үүсгэнэ. Скрипт нь
аюулгүй байдлын үүднээс зөвхөн нэрэндээ `bench` агуулсан database дээр ажиллана.

## Үр дүн

### SQL

| Query | Хугацаа |
|---|---:|
| `COUNT(*)` идэвхтэй бүртгэл (500,000) | 37.9 ms |
| Регистрээр яг таарах | 0.2 ms |
| FTS: овгоор `Бат` (25,000 тохирол) | 24.8 ms |
| Дүүрэг prefix `Хан-Уул` | 42.4 ms |

### Repository / service

| Query | Хугацаа | Тайлбар |
|---|---:|---|
| Жагсаалт, ADMIN, 1-р хуудас | 40.5 ms | Нийт 500,000 |
| Жагсаалт, scope root=1, 1-р хуудас | 25.9 ms | Нийт 10,111 |
| Хайлт: овог `Бат`, scope root=1 | 74.4 ms | Нийт 506 |
| Хайлт: регистр (яг) | 1.0 ms | Нийт 1 |
| Шууд гишүүд (Аравт #5551) | 1.1 ms | 9 мөр |
| Харьяаллын зам (гүн leaf) | 1.3 ms | 4 мөр |
| Closure descendant count root=1 | 1.4 ms | — |
| Dashboard, ADMIN (бүх диаграм) | 329 ms | 500,000 идэвхтэй; 6 aggregate query |

## Гол query-ийн төлөвлөгөө

### Scope-той жагсаалт

```sql
SELECT ... FROM people
WHERE status = 'ACTIVE'
  AND id IN (SELECT descendant_id FROM person_closure WHERE ancestor_id = 1)
ORDER BY created_at DESC, id DESC
LIMIT 20;
```

Planner нь `Person.status/created_at` индексээр эрэмбэлж, `person_closure` PK
`(ancestor_id, descendant_id)`-ээр гишүүнчлэлийг шалгана. 20 мөр авахад
~7 ms (Execution Time). Нийт count нь жагсаалтын нийт хугацааны ихэнхийг эзэлдэг.

### FTS + scope

```
Bitmap Index Scan on ix_people_last_name_fts
  (to_tsvector('simple', last_name) @@ to_tsquery('simple', 'Бат:*'))
  rows=25000
Nested Loop -> Index Only Scan person_closure_pkey
Execution Time: 17.957 ms
```

GIN FTS индекс ашиглагдаж, дараа нь closure-оор scope шалгана. Prefix query
(`Бат:*`) нь `pg_trgm`гүй орчинд ч сайн ажиллана.

### Регистр

```
Index Scan using uq_people_reg_number on people
Execution Time: 0.054 ms
```

## Дүгнэлт

- 500,000 бүртгэлтэй үед бүх гол query 100 ms-ээс доош байна.
- Бүрэн dashboard нь хэд хэдэн aggregate-ийг нэгтгэдэг тул ~329 ms; хүйс/шатлал/
  дүүрэг/хороог `GROUPING SETS`-ээр нэг scan, насыг нэг `FILTER` scan-аар
  тооцож 617 ms-ээс бууруулсан.
- Хамгийн удаан нь FTS + scope хайлт (74 ms), учир нь олон тохирол дээр нийт
  count-ийг closure subtree-ээр тоолно. Хэрэв цаашид хурдасгах бол:
  - `person_closure` дээр `(ancestor_id)` cover index нэмэх,
  - эсвэл UI-д нийт count-ийг ойролцоо/кэшлэсэн утгаар харуулах.
- Импорт/экспорт 50,000 мөрийн хязгаартай тул synchronous request дотор
  аюулгүй ажиллана.
