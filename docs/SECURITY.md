# Аюулгүй байдлын загвар

## Нэвтрэлт

- Нууц үг Argon2id (`argon2-cffi`, RFC 9106 параметрүүд) hash. Нээлттэй текстийг хэзээ ч логлохгүй.
- Амжилттай login нь 32 байтын random opaque token үүсгэж, **SHA-256 hash**-ийг `user_sessions.token_hash`-д хадгална. Token нь зөвхөн `HttpOnly; SameSite=Lax; Path=/` cookie-д (`prod`: `Secure`) явна.
- Session хугацаа 8 цаг; 30 минутын idle update (last_seen), хугацаа дуусмагц 401.
- Logout нь session-ыг `revoked_at`-аар хүчингүй болгоно. Хэрэглэгчийг идэвхгүй болгох эсвэл нууц үг солих (ADMIN эсвэл шууд удирдагч) үед тухайн хэрэглэгчийн бүх session revoke.
- CSRF: login/logout-оос бусад mutating хүсэлтэд `X-CSRF-Token` header шаардана; утгыг session-д харьяалагдсан `csrf_token`-той харьцуулна. `Origin`-ыг зөвшөөрөгдсөн жагсаалттай харьцуулна.
- Login rate limit: IP+username түлхүүрээр 5 минутд 10 оролдлого; хэтэрвэл 429. In-memory (нэг instance) — үйлдвэрлэлд shared store шаардлагатайг тэмдэглэсэн.
- Session cookie нь `SameSite=Lax` + CSRF token; CORS зөвхөн тохируулсан origin, credentials-тэй.

## Эрх ба хамрах хүрээ

- Default deny. Бүх `/api` endpoint (health, login-оос бусад) session шаардана.
- Role: `ADMIN` бүх зүйл; `LEADER` өөрийн subtree-ийн бүрэн мэдээлэл, бусад subtree-ийн зөвхөн нэр/утас/хаяг; `TUMT` бүх subtree-ийн бүрэн; `MEMBER` нэг аравтын хүрээ.
- Өөрөө бүртгүүлэх endpoint байхгүй. ADMIN дурын active хүнд, LEADER зөвхөн өөрийн
  шууд доорх хүүхдэд нэвтрэх эрх үүсгэж, түүний нууц үгийг солино; бусад хэрэглэгчийг
  зөвхөн ADMIN удирдана.
- `users.leader_person_id` нь нэг хүнд нэг л хэрэглэгч (unique). `LEADER` заавал
  удирдах хүнтэй, `MEMBER` заавал гишүүнтэй холбогдоно; удирдагч зөвхөн өөрийн шууд
  доорх дараагийн түвшний бүртгэл нэмнэ.
- Эрх нь role болон `leader_person_id`-ээс автоматаар тодорхойлогдоно. LEADER
  өөрийн модонд засах эрхтэй; импорт/экспорт, устгах нь ADMIN-д л нээлттэй.
- Account үүсгэх/нууц үг солих нь target хүний шууд удирдагч эсвэл ADMIN-д нээлтэй.
  Leader өөрийн account, ач/зээ, хамааралгүй хүний account-ыг удирдахгүй. Бүх
  mutation CSRF болон server-side scope шалгалттай.
- Харах хүрээ бүх list, detail, update, export, dashboard, hierarchy query-д SQL түвшинд (`person_closure`) шалгана. Зөвхөн frontend нуух нь хамгаалалт биш.
- MEMBER-ийн хүрээнээс гадуур объектод **404**. LEADER-ийн хувьд өөрийн модноос гадуур объект хязгаарлагдмал талбартайгаар 200 буцаана.
- Parent сонгохдоо: хэрэглэгч тухайн parent-ыг харж байгаа эсэх, parent active эсэх, circular биш эсэхийг backend шалгана. Илгээсэн ID-д итгэхгүй.
- Шатлал хатуу: parent/group хослолыг `Түмт→Мянгат→Зуут→Аравт→Гишүүн` дүрмээр шалгана; `Гишүүн` доор хүн нэмэх, `Гишүүн`-ийг leader болгох боломжгүй.
- Удирдагч зөвхөн өөрийн болон шууд хүүхдийн мэдээллийг засна; харьяалал,
  бүлгийн төрөл, устгах үйлдлийг өөрчлөх боломжгүй.
- Хэрэглэгч өөрийн role/leader/status-ыг өөрчлөх боломжгүй. Сүүлийн ADMIN-ыг идэвхгүй болгох/role бууруулахыг хориглоно.
- Audit log-д зөвхөн ADMIN хандана; мөр засах/устгах API байхгүй.
- Устгах: soft delete ADMIN; permanent delete зөвхөн leaf + reg number текст баталгаажуулалт + ADMIN.

## Өгөгдлийн хамгаалалт

- Утас, хаяг нь ADMIN, LEADER, MEMBER-т нээлттэй. LEADER/MEMBER-ийн өөрийн модноос
  гадуурх бүртгэлд регистр, хүйс, төрсөн огноо, ажил, харьяаллын зам зэрэг нэмэлт
  талбарыг буцаахгүй; зөвхөн нэр, утас, хаяг, бүлэг харагдана. MEMBER-ийн хүрээнээс
  гадуур объект 404.
- Жагсаалтын response-д зөвхөн шаардлагатай талбар; бүтэн 500k хэзээ ч буцаахгүй.
- Audit metadata-д регистр, утас, хаяг, нууц үг, token хийхгүй. Зөвхөн ID, өөрчлөгдсөн талбарын нэр.
- Импортын `Нууц үг` баганын утгыг preview/алдааны хариултад буцаахгүй, зөвхөн Argon2id hash хадгална; импорт дууссаны дараа файлыг устгана.
- Логт query string/body-г бүтнээр бичихгүй; production-д structured log.
- Файл: зөвхөн `.csv`, `.xlsx`; 10 MB хязгаар; MIME/extension шалгах; filename-ыг UUID болгож хадгална (path traversal-аас сэргийлнэ).
- CSV/XLSX export-д formula injection-оос хамгаалж `= + - @ \t \r`-ээр эхэлсэн нүдийг `'`-ээр prefix хийнэ.
- SQLAlchemy parameterized query; raw SQL зөвхөн тогтмол, allowlist sort/column-той.

## Production-ын зөвлөмж

- `COOKIE_SECURE=true`, HTTPS, `ALLOWED_ORIGINS`-ыг нарийн тохируулах.
- `SECRET_KEY`-г санамсаргүй, env/secret manager-аас; repo-д хэзээ ч бичихгүй.
- PostgreSQL-ийг тусдаа хэрэглэгч/эрхээр, TLS-тэй холбох; `postgres` superuser-ээр app ажиллуулахгүй.
- Reverse proxy-д HSTS, security headers.
- Backup + restore туршилт, audit retention бодлого.
- Rate limiting-ийг shared store (Redis) руу шилжүүлэх; олон instance.
- `READ COMMITTED` хангалттай; unique constraint нь concurrency-г барина.

## Мэдэгдэж буй эрсдэл

- In-memory rate limiter нь олон процесс/instance дээр хуваалцахгүй.
- Session cookie-д `Secure` нь production-д л; dev дээр HTTP.
- Бүрэн MFA, password reset email урсгал байхгүй (ADMIN эсвэл шууд удирдагч reset хийнэ).
- Audit log нь append-only API түвшинд; DB түвшний immutable trigger байхгүй.
- 500k гүйцэтгэлийн баталгаа нь синтетик тестээр хязгаарлагдана.
