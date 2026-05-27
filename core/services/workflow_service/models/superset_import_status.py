import enum


class SupersetImportStatus(str, enum.Enum):
    NONE = "none"
    PENDING = "pending"
    IMPORTING = "importing"
    IMPORTED = "imported"
    FAILED = "failed"
