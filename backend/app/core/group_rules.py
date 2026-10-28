from app.models.enums import GroupType

UNIT_GROUP_TYPES = (
    GroupType.TUMT,
    GroupType.MYANGAT,
    GroupType.ZUUT,
    GroupType.ARAVT,
)

GROUP_LEVELS: dict[GroupType, int] = {
    GroupType.TUMT: 1,
    GroupType.MYANGAT: 2,
    GroupType.ZUUT: 3,
    GroupType.ARAVT: 4,
    GroupType.MEMBER: 5,
}

NEXT_GROUP_TYPE: dict[GroupType, GroupType | None] = {
    GroupType.TUMT: GroupType.MYANGAT,
    GroupType.MYANGAT: GroupType.ZUUT,
    GroupType.ZUUT: GroupType.ARAVT,
    GroupType.ARAVT: GroupType.MEMBER,
    GroupType.MEMBER: None,
}

PARENT_GROUP_TYPE: dict[GroupType, GroupType | None] = {
    GroupType.TUMT: None,
    GroupType.MYANGAT: GroupType.TUMT,
    GroupType.ZUUT: GroupType.MYANGAT,
    GroupType.ARAVT: GroupType.ZUUT,
    GroupType.MEMBER: GroupType.ARAVT,
}

GROUP_TYPE_LABELS: dict[GroupType, str] = {
    GroupType.TUMT: "Түмт",
    GroupType.MYANGAT: "Мянгат",
    GroupType.ZUUT: "Зуут",
    GroupType.ARAVT: "Аравт",
    GroupType.MEMBER: "Гишүүн",
}


def next_group_type(group_type: GroupType) -> GroupType | None:
    return NEXT_GROUP_TYPE[group_type]


def is_valid_child(parent_group: GroupType, child_group: GroupType) -> bool:
    return NEXT_GROUP_TYPE.get(parent_group) == child_group


def can_be_leader(group_type: GroupType) -> bool:
    return group_type in UNIT_GROUP_TYPES


def group_type_error(parent_group: GroupType) -> str:
    child = NEXT_GROUP_TYPE.get(parent_group)
    if child is None:
        return f"{GROUP_TYPE_LABELS[parent_group]} доор хүн нэмэх боломжгүй."
    return (
        f"{GROUP_TYPE_LABELS[parent_group]} доор зөвхөн "
        f"{GROUP_TYPE_LABELS[child]} төрлийн хүн нэмнэ."
    )
