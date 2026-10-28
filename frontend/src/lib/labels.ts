import type {
  Gender,
  GroupType,
  ImportStatus,
  PersonStatus,
  Role,
} from "../api/types";

export const GROUP_LABELS: Record<GroupType, string> = {
  TUMT: "Түмт",
  MYANGAT: "Мянгат",
  ZUUT: "Зуут",
  ARAVT: "Аравт",
  MEMBER: "Гишүүн",
};

export const GROUP_DESCRIPTIONS: Record<GroupType, string> = {
  TUMT: "10,000 гишүүнтэй нэгж",
  MYANGAT: "1,000 гишүүнтэй нэгж",
  ZUUT: "100 гишүүнтэй нэгж",
  ARAVT: "10 гишүүнтэй нэгж",
  MEMBER: "Бүлгийн энгийн гишүүн",
};

export const GENDER_LABELS: Record<Gender, string> = {
  MALE: "Эрэгтэй",
  FEMALE: "Эмэгтэй",
  OTHER: "Бусад",
};

export const STATUS_LABELS: Record<PersonStatus, string> = {
  ACTIVE: "Идэвхтэй",
  DELETED: "Устгасан",
};

export const ROLE_LABELS: Record<Role, string> = {
  ADMIN: "Админ",
  LEADER: "Удирдагч",
  MEMBER: "Гишүүн",
};

export const IMPORT_STATUS_LABELS: Record<ImportStatus, string> = {
  PREVIEWED: "Урьдчилсан",
  PROCESSING: "Боловсруулж байна",
  COMPLETED: "Дууссан",
  FAILED: "Амжилтгүй",
};

export const AUDIT_ACTION_LABELS: Record<string, string> = {
  AUTH_LOGIN_SUCCESS: "Нэвтэрсэн",
  AUTH_LOGIN_FAILED: "Нэвтрэх оролдлого амжилтгүй",
  AUTH_LOGOUT: "Гарсан",
  AUTH_PASSWORD_CHANGED: "Нууц үг сольсон",
  PERSON_CREATE: "Иргэн бүртгэсэн",
  PERSON_UPDATE: "Иргэний мэдээлэл зассан",
  RELATIONSHIP_CHANGE: "Харьяалал өөрчилсөн",
  PERSON_DELETE: "Иргэн устгасан",
  PERSON_RESTORE: "Иргэн сэргээсэн",
  PERSON_PURGE: "Иргэн бүр мөсөн устгасан",
  USER_CREATE: "Хэрэглэгч үүсгэсэн",
  USER_UPDATE: "Хэрэглэгч зассан",
  USER_DISABLE: "Хэрэглэгч идэвхгүй болгосон",
  USER_ENABLE: "Хэрэглэгч идэвхжүүлсэн",
  USER_PASSWORD_RESET: "Нууц үг шинэчилсэн",
  IMPORT_START: "Импорт эхлүүлсэн",
  IMPORT_COMPLETE: "Импорт дуусгасан",
  EXPORT: "Экспорт хийсэн",
};

export const AUDIT_ENTITY_LABELS: Record<string, string> = {
  person: "Иргэн",
  user: "Хэрэглэгч",
  import: "Импорт",
  auth: "Нэвтрэлт",
};

export const SORT_OPTIONS = [
  { value: "created_at", label: "Бүртгэсэн огноо" },
  { value: "last_name", label: "Овог" },
  { value: "first_name", label: "Нэр" },
  { value: "reg_number", label: "Регистрийн дугаар" },
  { value: "district", label: "Дүүрэг" },
  { value: "khoroo", label: "Хороо" },
  { value: "birth_date", label: "Төрсөн огноо" },
];
