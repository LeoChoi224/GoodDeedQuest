import enum

class CompetitionStatus(str, enum.Enum):
    IN_PROGRESS = "IN_PROGRESS"
    SETTLING = "SETTLING"