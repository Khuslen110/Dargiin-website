from enum import Enum


class Role(str, Enum):
    ADMIN = "ADMIN"
    LEADER = "LEADER"
    MEMBER = "MEMBER"


class GroupType(str, Enum):
    TUMT = "TUMT"
    MYANGAT = "MYANGAT"
    ZUUT = "ZUUT"
    ARAVT = "ARAVT"
    MEMBER = "MEMBER"


class Gender(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class PersonStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DELETED = "DELETED"


class NotificationKind(str, Enum):
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"


class ImportStatus(str, Enum):
    PREVIEWED = "PREVIEWED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
