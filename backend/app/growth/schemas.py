from datetime import date as date_type
from typing import List
from pydantic import BaseModel, ConfigDict


class DailyXp(BaseModel):
    date: date_type
    cumulative_xp: int


class GrowthStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    current_level: int
    current_xp: int
    next_level_xp: int
    weekly_xp_graph: List[DailyXp]


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    nickname: str
    current_level: int
    is_me: bool = False


class LeaderboardResponse(BaseModel):
    leaderboard: List[LeaderboardEntry]     # 상위 10명
    my_entry: LeaderboardEntry              # 항상 포함
    nearby_ranks: List[LeaderboardEntry]    # 내 순위가 top10 밖일 때만: 내 앞/뒤 1명씩(최대 3개). top10 안이면 빈 리스트
    total_users: int