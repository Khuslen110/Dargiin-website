from app.models.enums import Gender, GroupType

FIELD_LABELS: dict[str, str] = {
    "reg_number": "Регистрийн дугаар",
    "last_name": "Овог",
    "first_name": "Нэр",
    "gender": "Хүйс",
    "birth_date": "Төрсөн огноо",
    "phone": "Утас",
    "district": "Дүүрэг",
    "khoroo": "Хороо",
    "address": "Хаяг",
    "job": "Ажил",
    "group_type": "Бүлгийн төрөл",
    "username": "Хэрэглэгчийн нэр",
    "password": "Нууц үг",
    "parent_reg_number": "Харьяалагдах хүний регистр",
}

HEADER_ALIASES: dict[str, str] = {}
for _key, _label in FIELD_LABELS.items():
    HEADER_ALIASES[_key.lower()] = _key
    HEADER_ALIASES[_label.lower()] = _key

REQUIRED_FIELDS = ("reg_number", "last_name", "first_name", "gender", "group_type")
MAX_TEXT_LENGTHS = {
    "last_name": 80,
    "first_name": 80,
    "district": 80,
    "khoroo": 80,
    "address": 255,
    "job": 120,
}

GROUP_TYPE_LABELS: dict[str, GroupType] = {
    "tumt": GroupType.TUMT,
    "түмт": GroupType.TUMT,
    "myangat": GroupType.MYANGAT,
    "мянгат": GroupType.MYANGAT,
    "zuut": GroupType.ZUUT,
    "зуут": GroupType.ZUUT,
    "aravt": GroupType.ARAVT,
    "аравт": GroupType.ARAVT,
    "member": GroupType.MEMBER,
    "гишүүн": GroupType.MEMBER,
}

GENDER_LABELS: dict[str, Gender] = {
    "male": Gender.MALE,
    "эрэгтэй": Gender.MALE,
    "эмэгтэй": Gender.FEMALE,
    "female": Gender.FEMALE,
    "other": Gender.OTHER,
    "бусад": Gender.OTHER,
}

GROUP_TYPE_EXPORT_LABELS = {
    GroupType.TUMT: "Түмт",
    GroupType.MYANGAT: "Мянгат",
    GroupType.ZUUT: "Зуут",
    GroupType.ARAVT: "Аравт",
    GroupType.MEMBER: "Гишүүн",
}

GENDER_EXPORT_LABELS = {
    Gender.MALE: "Эрэгтэй",
    Gender.FEMALE: "Эмэгтэй",
    Gender.OTHER: "Бусад",
}
