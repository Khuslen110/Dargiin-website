import re

# Монгол кириллийн үсгүүд. Регистрийн дугаар нь 2 үсэг + 8 цифр гэсэн
# таамаглал дээр шалгана (checksum алгоритм баталгаажаагүй).
REG_NUMBER_RE = re.compile(r"^[А-ЯЁӨҮ]{2}\d{8}$")
USERNAME_RE = re.compile(r"^[a-z0-9._-]{3,64}$")
PHONE_RE = re.compile(r"^\+?\d{6,15}$")

_SPACE_RE = re.compile(r"\s+")


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = _SPACE_RE.sub(" ", value).strip()
    return cleaned or None


def normalize_reg_number(value: str) -> str:
    return re.sub(r"[\s\-_]", "", value).upper()


def validate_reg_number(value: str) -> str:
    normalized = normalize_reg_number(value)
    if not REG_NUMBER_RE.fullmatch(normalized):
        raise ValueError("Регистрийн дугаар 2 кирилл үсэг, 8 цифрээс бүрдэх ёстой (жишээ: УБ12345678).")
    return normalized


def normalize_username(value: str) -> str:
    return value.strip().lower()


def validate_username(value: str) -> str:
    normalized = normalize_username(value)
    if not USERNAME_RE.fullmatch(normalized):
        raise ValueError("Хэрэглэгчийн нэр 3–64 тэмдэгт, зөвхөн латин жижиг үсэг, цифр, . _ - агуулна.")
    return normalized


def normalize_phone(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = re.sub(r"[\s\-()]", "", value.strip())
    return cleaned or None


def validate_phone(value: str | None) -> str | None:
    cleaned = normalize_phone(value)
    if cleaned is None:
        return None
    if PHONE_RE.fullmatch(cleaned) is None:
        raise ValueError("Утасны дугаар 6–15 цифр, эхэндээ + байж болно.")
    return cleaned
