from __future__ import annotations

# =========================================================
# [반드시 확인 및 검토할 사항]
#
# 1. 이 Repository는 DB 조회·생성·수정·삭제만 담당.
#    - 권한 확인, 비밀번호 검증, 정원 확인, 상태 판단은 Service에서 처리.
#    - Service에서 Team 생성 후 팀장을 TeamMember에 LEADER 역할로 추가.
#    - Service에서 정원 및 중복 참가 여부를 확인한 뒤 바로 멤버를 추가.
#    - 비밀번호 해시 검증 또는 유효한 초대 여부를 Service에서 확인한 뒤 TeamMember를 추가.
#    - 현재 인원과 max_members를 비교하여 Service가 참가를 차단.
#    - 마지막 팀원이 나가면 Service에서 delete_team()을 호출하여 팀을 실제 삭제합니다.
#    - TeamInvite와 TeamMember는 FK의 CASCADE 설정으로 함께 삭제됩니다.
#    - 퀘스트 완료 시 팀 삭제 기능은 Quest 완료 기능과 연동할 때 추가해야 합니다.
#
# 2. 이 Repository에서는 flush()까지만 수행합니다.
#    - Repository는 commit()과 rollback()을 직접 호출하지 않습니다.
#    - 최종 commit()과 오류 발생 시 rollback()은 common/database.py의 get_db()가 요청 단위로 처리합니다.
#
# 3. 방장이 팀을 나가는 경우
#    - 가장 먼저 참가한 다음 멤버를 새로운 LEADER로 변경합니다.
#    - Team.leader_id도 새로운 방장의 user_id로 변경해야 합니다.
#
# 4. TeamInvite에는 (team_id, user_id) UniqueConstraint가 있습니다.
#    - 거절 또는 만료된 사용자를 다시 초대할 때 새 행을 생성하면
#      중복 오류가 발생하므로 renew_invite()로 기존 초대를 재사용.
#
# 5. 방 목록에 표시할 퀘스트 제목, 카테고리 아이콘, 장소, 시행 일자 등은 Quest 모델의 실제 컬럼 구조가 완성되었을때 JOIN.
#     - 현재 Repository는 Team 정보와 현재 인원 수를 반환.
#     - 퀘스트 상세 정보는 QuestRepository 또는 Service에서 결합.
#
# 6. AI 팀원 추천 Repository
#    - 추천 가능한 사용자 후보 조회와 최근 30일 승인 활동 조회만 담당합니다.
#    - 후보 사용자의 지역 이름도 함께 조회하여 AI 지역 점수 계산에 사용합니다.
#    - 추천 점수, Top-K, Embedding 비교, 추천 이유 생성은 처리하지 않습니다.
#    - 최근 기간과 최근 거절 기간의 기준 시각은 Service에서 계산하여 전달합니다.
#    - 현재 Team에는 활동 장소 좌표가 없으므로 정확한 거리 계산은 이후 좌표 연동이 필요합니다.
#
# =========================================================

from datetime import datetime
from typing import Literal

from sqlalchemy import Select, exists, func, or_, select, update

from sqlalchemy.orm import Session

from backend.app.challenge.enums import (
    TeamInviteStatus,
    TeamMemberRole,
    TeamStatus,
)
from backend.app.challenge.models import (
    Team,
    TeamInvite,
    TeamMember,
)

from backend.app.auth.enums import UserRole
from backend.app.auth.models import User
from backend.app.quest.models import Category, Quest
from backend.app.quest_verification.enums import SubmissionStatus
from backend.app.quest_verification.models import QuestSubmission
from backend.app.map.models import Region

# 팀 정렬 옵션을 최신순, 오래된순, 이름순 세 값으로 제한. Literal["최신순", "오래된 순", "이름순"]
TeamSortType = Literal["latest", "oldest", "name"]

class TeamRepository:
    """팀 정보와 팀 상태를 관리하는 Repository."""

    # *는 "이 뒤의 매개변수는 이름(키워드)을 붙여서 전달해야 한다." 는 의미이며, 
    # 매개변수가 많은 함수에서 실수를 방지 및 가독성을 위해 자주 사용하는 문법이다.
    @staticmethod
    # 새로운 팀 정보를 만들어 DB에 추가하는 메서드.
    def create_team(
        session: Session,
        *,
        leader_id: int,
        quest_id: int,
        name: str,
        password_hash: str | None,
        notification: str,
        region: str,
        is_public: bool,
        max_members: int,
        expires_at: datetime | None,
    ) -> Team:
        """
        새로운 팀을 생성합니다.

        Team 레코드만 생성하며,
        생성자를 LEADER 멤버로 추가하는 작업은 Service에서 처리합니다.

        commit()은 common/database.py의 get_db()가 처리합니다.
        """

        # 전달받은 값으로 새로운 Team 모델 객체를 생성합니다.
        team = Team(
            leader_id=leader_id,
            quest_id=quest_id,
            name=name,
            password_hash=password_hash,
            notification=notification,
            region=region,
            is_public=is_public,
            max_members=max_members,
            expires_at=expires_at,
        )

        session.add(team)

        session.flush()
        session.refresh(team)

        return team

    @staticmethod
    # 팀 ID를 이용해 팀 한 건을 조회하는 메서드.
    def get_team_by_id(
        session: Session,
        team_id: int,
    ) -> Team | None:
        stmt = select(Team).where(
            Team.team_id == team_id,
        )
        result = session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    # 검색·필터·정렬 조건에 맞는 팀 목록과 현재 인원을 조회.
    def get_teams(
        session: Session,
        *,
        quest_id: int | None = None,
        status: TeamStatus | None = TeamStatus.RECRUITING,
        is_public: bool | None = None,
        region: str | None = None,
        search: str | None = None,
        sort_by: TeamSortType = "latest",
        offset: int = 0,
        limit: int = 20,
    ) -> list[tuple[Team, int]]:
        """
        팀 목록과 각 팀의 현재 참가 인원을 조회합니다.

        반환값:
            [
                (Team 객체, 현재 인원),
                ...
            ]

        지원 조건:
        - 특정 퀘스트의 팀 조회
        - 팀 상태 필터
        - 공개/비공개 필터
        - 활동 지역 필터
        - 팀 이름 검색
        - 최신순, 오래된순, 이름순 정렬

        퀘스트 카테고리 검색은 Quest 모델과 JOIN이 필요하므로
        Quest 모델 구조가 확정된 뒤 추가.
        """

        # 각 팀에 소속된 멤버 수를 계산하는 COUNT 표현식.
        member_count = func.count(
            TeamMember.team_member_id
        ).label("member_count")

        stmt: Select = (
            select(
                Team,
                member_count,
            )
            .outerjoin(
                TeamMember,
                TeamMember.team_id == Team.team_id,
            )
            .group_by(Team.team_id)
        )

        # 퀘스트 ID가 전달된 경우에만 퀘스트 필터를 적용.
        if quest_id is not None:
            stmt = stmt.where(
                Team.quest_id == quest_id,
            )

        if status is not None:
            stmt = stmt.where(
                Team.status == status,
            )

        # 공개 여부가 전달된 경우에만 공개·비공개 필터를 적용.
        if is_public is not None:
            stmt = stmt.where(
                Team.is_public == is_public,
            )

        # 지역값이 전달된 경우에만 지역 필터 처리를 시작.
        if region is not None:
            normalized_region = region.strip()

            if normalized_region:
                stmt = stmt.where(
                    Team.region == normalized_region,
                )

        # 검색어가 전달된 경우에만 팀 이름 검색 처리를 시작.
        if search is not None:
            normalized_search = search.strip()

            if normalized_search:
                stmt = stmt.where(
                    Team.name.ilike(
                        f"%{normalized_search}%"
                    )
                )

        # 정렬값이 oldest이면 오래된 팀부터 조회.
        if sort_by == "oldest":
            stmt = stmt.order_by(
                Team.created_at.asc(),
                Team.team_id.asc(),
            )

        # 정렬값이 name이면 팀 이름의 오름차순으로 조회.
        elif sort_by == "name":
            stmt = stmt.order_by(
                Team.name.asc(),
                Team.team_id.desc(),
            )

        # 앞의 조건에 해당하지 않는 기본 경우를 처리.
        else:
            stmt = stmt.order_by(
                Team.created_at.desc(),
                Team.team_id.desc(),
            )

        # 페이지네이션을 위해 건너뛸 개수와 최대 조회 개수를 적용.
        stmt = stmt.offset(offset).limit(limit)

        result = session.execute(stmt)

        return [
            (team, int(count))
            for team, count in result.all()
        ]

    @staticmethod
    # 특정 사용자가 참가하고 있는 팀 목록과 현재 인원을 조회.
    def get_user_teams(
        session: Session,
        *,
        user_id: int,
        status: TeamStatus | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[tuple[Team, int]]:

        # 각 팀에 소속된 멤버 수를 계산하는 COUNT 표현식.
        member_count = func.count(
            TeamMember.team_member_id
        ).label("member_count")

        # 사용자의 참가 여부 확인용으로 TeamMember 테이블의 별칭.
        user_membership = TeamMember.__table__.alias(
            "user_membership"
        )

        stmt = (
            select(
                Team,
                member_count,
            )
            # 두 테이블에서 조건이 일치하는 데이터만 결합하는 INNER JOIN을 적용.
            .join(
                user_membership,
                user_membership.c.team_id == Team.team_id,
            )
            # 멤버가 없는 팀도 포함하도록 LEFT OUTER JOIN을 적용.
            .outerjoin(
                TeamMember,
                TeamMember.team_id == Team.team_id,
            )
            .where(
                user_membership.c.user_id == user_id,
            )
            .group_by(Team.team_id)
            .order_by(
                Team.created_at.desc(),
                Team.team_id.desc(),
            )
            # 앞에서부터 지정한 개수만큼 결과를 건너뜁니다.
            .offset(offset)
            # 최대로 가져올 결과 개수를 제한합니다.
            .limit(limit)
        )

        if status is not None:
            stmt = stmt.where(
                Team.status == status,
            )

        result = session.execute(stmt)

        return [
            (team, int(count))
            for team, count in result.all()
        ]

    @staticmethod
    # 조회된 팀 객체의 진행 상태를 변경.
    def update_team_status(
        session: Session,
        *,
        team: Team,
        status: TeamStatus,
    ) -> Team:
        """팀의 진행 상태를 변경합니다."""

        team.status = status

        session.flush()
        session.refresh(team)

        return team

    @staticmethod
    # Team 테이블에 저장된 팀장 ID를 변경.
    def update_team_leader(
        session: Session,
        *,
        team: Team,
        new_leader_id: int,
    ) -> Team:
        """
        Team 테이블의 방장 ID를 변경합니다.

        TeamMember의 역할 변경은
        TeamMemberRepository.update_member_role()에서 별도로 처리.
        """

        team.leader_id = new_leader_id

        session.flush()
        session.refresh(team)

        return team

    @staticmethod
    # 팀 데이터를 실제 DB 삭제 대상으로 등록.
    def delete_team(
        session: Session,
        *,
        team: Team,
    ) -> None:
        """
        팀을 실제 삭제합니다.

        사용 시점:
        - 마지막 팀원이 나간 경우
        - 해당 팀의 퀘스트가 완료된 경우

        TeamInvite와 TeamMember는 DB의 ON DELETE CASCADE 설정에 따라
        함께 삭제.
        """

        session.delete(team)
        session.flush()


# 팀 초대의 생성·조회·상태 변경을 담당하는 Repository.
class TeamInviteRepository:

    @staticmethod
    # 새로운 팀 초대 데이터를 생성.
    def create_invite(
        session: Session,
        *,
        team_id: int,
        user_id: int,
        expires_at: datetime | None,
    ) -> TeamInvite:
        """
        새로운 팀 초대를 생성합니다.

        초대 상태는 모델의 기본값인 PENDING으로 생성.
        """

        invite = TeamInvite(
            team_id=team_id,
            user_id=user_id,
            expires_at=expires_at,
        )

        session.add(invite)

        session.flush()
        session.refresh(invite)

        return invite

    @staticmethod
    # 초대 ID로 초대 한 건을 조회.
    def get_invite_by_id(
        session: Session,
        invite_id: int,
    ) -> TeamInvite | None:
        stmt = select(TeamInvite).where(
            TeamInvite.invite_id == invite_id,
        )

        result = session.execute(stmt)

        return result.scalar_one_or_none()

    @staticmethod
    # 특정 팀이 특정 사용자에게 보낸 초대가 있는지 조회.
    def get_invite_by_team_and_user(
        session: Session,
        *,
        team_id: int,
        user_id: int,
    ) -> TeamInvite | None:

        stmt = select(TeamInvite).where(
            TeamInvite.team_id == team_id,
            TeamInvite.user_id == user_id,
        )

        result = session.execute(stmt)

        return result.scalar_one_or_none()

    @staticmethod
    # 특정 사용자가 받은 대기 중 초대 목록을 조회.
    def get_user_pending_invites(
        session: Session,
        *,
        user_id: int,
        offset: int = 0,
        limit: int = 20,
    ) -> list[TeamInvite]:
        """
        사용자가 받은 처리 대기 중인 초대 목록을 조회합니다.

        초대한 사용자 목록을 팀장에게 보여주는 기능은 없으므로
        팀 기준 초대 목록 조회 메서드는 포함하지 않았습니다.
        """

        stmt = (
            # 조회할 모델 또는 계산값을 SELECT 대상에 지정.
            select(TeamInvite)
            .where(
                TeamInvite.user_id == user_id,
                TeamInvite.status
                == TeamInviteStatus.PENDING,
            )
            .order_by(
                TeamInvite.created_at.desc(),
                TeamInvite.invite_id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )

        result = session.execute(stmt)

        return list(result.scalars().all())

    @staticmethod
    # 팀 초대의 상태값을 변경.
    def update_invite_status(
        session: Session,
        *,
        invite: TeamInvite,
        status: TeamInviteStatus,
    ) -> TeamInvite:
        """
        초대 상태를 변경합니다.

        사용자 요청으로 가능한 상태:
        - ACCEPTED
        - REJECTED

        서버 내부 처리로 가능한 상태:
        - EXPIRED

        상태 변경 가능 여부는 Service에서 확인.
        """

        invite.status = status

        session.flush()
        session.refresh(invite)

        return invite

    @staticmethod
    def renew_invite(
        session: Session,
        *,
        invite: TeamInvite,
        expires_at: datetime | None,
    ) -> TeamInvite:
        """
        기존의 거절되었거나 만료된 초대를 다시 PENDING 상태로 변경.

        TeamInvite의 (team_id, user_id) UniqueConstraint 때문에
        동일한 사용자에게 새 초대 행을 추가하는 대신 기존 행을 재사용합니다.

        Service에서는 기존 초대가 ACCEPTED 또는 PENDING인지 먼저 확인해야 합니다.
        """

        # 기존 초대를 다시 응답 대기 상태로 변경.
        invite.status = TeamInviteStatus.PENDING
        # 재초대에 사용할 새로운 만료 시간을 저장.
        invite.expires_at = expires_at

        session.flush()
        session.refresh(invite)

        return invite

    @staticmethod
    # 만료 시간이 지난 대기 중 초대를 한 번에 만료 처리.
    def expire_pending_invites(
        session: Session,
        *,
        current_time: datetime,
    ) -> int:
        stmt = (
            update(TeamInvite)
            .where(
                TeamInvite.status == TeamInviteStatus.PENDING,
                TeamInvite.expires_at.is_not(None),
                TeamInvite.expires_at <= current_time,
            )
            .values(
                status=TeamInviteStatus.EXPIRED,
            )
            .execution_options(
                synchronize_session=False,
            )
        )

        result = session.execute(stmt)
        session.flush()

        return int(result.rowcount or 0)


# 팀 멤버의 추가·조회·역할 변경·삭제를 담당하는 Repository.
class TeamMemberRepository:
    """팀 참가 멤버 정보를 관리하는 Repository."""

    @staticmethod
    # 사용자를 팀 멤버로 추가.
    def add_member(
        session: Session,
        *,
        team_id: int,
        user_id: int,
        role_in_team: TeamMemberRole = TeamMemberRole.MEMBER,
    ) -> TeamMember:
        """
        사용자를 팀 멤버로 추가합니다.

        일반 참가자는 MEMBER,
        팀 생성자는 LEADER 역할로 추가합니다.

        commit()은 common/database.py의 get_db()가 처리합니다.
        """

        member = TeamMember(
            team_id=team_id,
            user_id=user_id,
            role_in_team=role_in_team,
        )

        session.add(member)

        session.flush()
        session.refresh(member)

        return member

    @staticmethod
    # 팀 멤버 ID로 멤버 한 건을 조회.
    def get_member_by_id(
        session: Session,
        team_member_id: int,
    ) -> TeamMember | None:

        stmt = select(TeamMember).where(
            TeamMember.team_member_id == team_member_id,
        )

        result = session.execute(stmt)

        return result.scalar_one_or_none()

    @staticmethod
    # 특정 사용자가 특정 팀에 참가 중인지 조회.
    def get_member_by_team_and_user(
        session: Session,
        *,
        team_id: int,
        user_id: int,
    ) -> TeamMember | None:
        """
        특정 사용자가 해당 팀에 참가 중인지 조회합니다.

        사용 위치:
        - 중복 참가 확인
        - 팀원 권한 확인
        - 팀장 권한 확인
        - 팀 탈퇴
        - 사용자 초대 전 기존 멤버 여부 확인
        """

        stmt = select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id,
        )

        result = session.execute(stmt)

        return result.scalar_one_or_none()

    @staticmethod
    # 특정 팀에 참가한 전체 멤버를 정렬하여 조회.
    def get_team_members(
        session: Session,
        *,
        team_id: int,
    ) -> list[TeamMember]:

        stmt = (
            select(TeamMember)
            .where(
                TeamMember.team_id == team_id,
            )
            .order_by(
                TeamMember.role_in_team.asc(),
                TeamMember.joined_at.asc(),
                TeamMember.team_member_id.asc(),
            )
        )

        result = session.execute(stmt)

        return list(result.scalars().all())

    @staticmethod
    # 특정 팀의 현재 참가 인원을 숫자로 조회.
    def count_team_members(
        session: Session,
        *,
        team_id: int,
    ) -> int:
        """
        특정 팀의 현재 참가 인원을 반환합니다.

        Service에서 Team.max_members와 비교하여
        방이 가득 찼는지 확인할 때 사용.
        """

        stmt = (
            select(
                func.count(TeamMember.team_member_id)
            )
            .where(
                TeamMember.team_id == team_id,
            )
        )

        result = session.execute(stmt)

        return int(result.scalar_one())

    @staticmethod
    # 현재 팀장을 제외하고 다음 팀장 후보를 조회.
    def get_next_leader_candidate(
        session: Session,
        *,
        team_id: int,
        excluding_user_id: int,
    ) -> TeamMember | None:
        """
        방장이 나갈 때 다음 방장 후보를 결정하는 데 사용.
        """

        stmt = (
            select(TeamMember)
            .where(
                TeamMember.team_id == team_id,
                TeamMember.user_id != excluding_user_id,
            )
            .order_by(
                TeamMember.joined_at.asc(),
                TeamMember.team_member_id.asc(),
            )
            # 최대로 가져올 결과 개수를 제한.
            .limit(1)
        )

        result = session.execute(stmt)

        return result.scalar_one_or_none()

    @staticmethod
    # 팀 멤버의 역할을 변경.
    def update_member_role(
        session: Session,
        *,
        member: TeamMember,
        role_in_team: TeamMemberRole,
    ) -> TeamMember:
        """
        팀 멤버의 역할을 변경합니다.

        현재 프로젝트에서는 방장이 나갈 때
        다음 입장자를 LEADER로 변경하는 용도로 사용.
        """

        member.role_in_team = role_in_team

        session.flush()
        session.refresh(member)

        return member

    @staticmethod
    # 팀 멤버 데이터를 실제 DB 삭제 대상으로 등록.
    def remove_member(
        session: Session,
        *,
        member: TeamMember,
    ) -> None:
        """
        팀에서 멤버를 제거합니다.

        일반 멤버인지 방장인지 판단하거나,
        방장 위임이 필요한지는 Service에서 처리.
        """

        session.delete(member)
        session.flush()



class ChallengeRecommendationRepository:
    """AI 팀원 추천에 필요한 DB 조회를 담당하는 Repository.

    이 Repository는 다음 데이터만 조회.

    - 추천 대상 팀과 연결된 Quest·Category 정보
    - 추천 가능한 사용자 후보
    - 후보 사용자의 최근 승인된 Quest 수행 기록

    - 추천 점수 계산, Top-K 선정, Embedding 비교 및 추천 이유 생성은
    - AI Server에서 처리합니다.
    
    - Repository는 추천에 필요한 데이터만 조회하여
    - Service에 전달하는 역할만 담당합니다.
    """

    @staticmethod
    def get_team_recommendation_context(
        session: Session,
        *,
        team_id: int,
    ) -> tuple[Team, Quest, Category, int] | None:
        """
        추천 대상 팀과 Quest·Category·현재 인원을 조회합니다.
        팀이 존재하지 않으면 None을 반환합니다.
        """

        member_count = func.count(
            TeamMember.team_member_id
        ).label("member_count")

        # 팀과 연결된 Quest·Category 및 현재 인원을 한 번에 조회.
        stmt = (
            select(
                Team,
                Quest,
                Category,
                member_count,
            )
            .join(
                Quest,
                Quest.quest_id == Team.quest_id,
            )
            .join(
                Category,
                Category.category_id == Quest.category_id,
            )
            .outerjoin(
                TeamMember,
                TeamMember.team_id == Team.team_id,
            )
            .where(
                Team.team_id == team_id,
            )
            .group_by(
                Team.team_id,
                Quest.quest_id,
                Category.category_id,
            )
        )

        result = session.execute(stmt)
        row = result.one_or_none()

        if row is None:
            return None

        team, quest, category, current_members = row

        return (
            team,
            quest,
            category,
            int(current_members),
        )

    @staticmethod
    def list_recommendation_candidates(
        session: Session,
        *,
        requester_id: int,
        team_id: int,
        quest_id: int,
        rejected_since: datetime,
    ) -> list[tuple[User, str | None]]:
        """AI 팀원 추천 대상이 될 수 있는 사용자를 조회.

        Repository 단계에서 제외하는 사용자:

        - 추천을 요청한 사용자 본인
        - 비활성 사용자
        - 관리자
        - 현재 팀 또는 같은 Quest의 다른 팀 참가자
        - 현재 팀의 PENDING 초대 대상
        - 현재 팀의 ACCEPTED 초대 대상
        - 현재 팀 초대를 최근 일정 기간 내 거절한 사용자

        관심 카테고리, 난이도, 활동 시간, 위치 등이 일치하지 않는 사용자는
        후보에서 제외하지 않고 이후 규칙 기반 점수에 반영.
        """

        # 같은 Quest의 어떤 팀에라도 참가한 사용자인지 확인.
        same_quest_member_exists = exists(
            select(1)
            .select_from(TeamMember)
            .join(
                Team,
                Team.team_id == TeamMember.team_id,
            )
            .where(
                TeamMember.user_id == User.user_id,
                Team.quest_id == quest_id,
            )
        )

        # 현재 팀에서 추천 후보 제외 대상인 초대가 있는지 확인.
        unavailable_invite_exists = exists(
            select(1)
            .select_from(TeamInvite)
            .where(
                TeamInvite.team_id == team_id,
                TeamInvite.user_id == User.user_id,
                or_(
                    TeamInvite.status.in_(
                        [
                            TeamInviteStatus.PENDING,
                            TeamInviteStatus.ACCEPTED,
                        ]
                    ),
                    (
                        (TeamInvite.status == TeamInviteStatus.REJECTED)
                        & (TeamInvite.updated_at >= rejected_since)
                    ),
                ),
            )
        )

        # 추천 후보 사용자와 지역 이름을 함께 조회.
        stmt = (
            select(
                User,
                Region.region_name.label("region_name"),
                )
            # 후보 사용자의 지역 이름을 함께 조회하기 위해 Region을 JOIN.
            .outerjoin(
                Region,
                Region.region_id == User.region_id,
            )
            .where(
                User.user_id != requester_id,
                User.is_active.is_(True),
                User.role == UserRole.USER,
                ~same_quest_member_exists,
                ~unavailable_invite_exists,
            )
            .order_by(
                User.user_id.asc(),
            )
        )

        result = session.execute(stmt)

        # (User, region_name) 형태로 반환합니다.
        return list(result.all())

    @staticmethod
    def list_recent_candidate_activities(
        session: Session,
        *,
        candidate_user_ids: list[int],
        since: datetime,
    ) -> list[tuple[QuestSubmission, Quest, Category]]:
        """후보 사용자들의 최근 승인된 Quest 수행 기록을 조회합니다.

        조회 조건

        - 추천 후보 사용자
        - 최근 30일 이내 제출한 기록
        - 최종 인증이 승인(ACCEPTED)된 기록

        Repository에서는 최근 수행 기록만 조회해서 반환합니다.

        이후 Service에서는 이 조회 결과를 이용해

        - 어떤 카테고리를 많이 수행했는지
        - 어떤 난이도를 많이 수행했는지
        - 언제 주로 활동했는지

        를 계산하여 AI Server에 전달합니다.
        """

        # 후보가 없으면 불필요한 DB 조회 없이 빈 목록을 반환.
        if not candidate_user_ids:
            return []

        # 최근 승인된 수행 기록과 연결된 Quest·Category를 조회.
        stmt = (
            select(
                QuestSubmission,
                Quest,
                Category,
            )
            .join(
                Quest,
                Quest.quest_id == QuestSubmission.quest_id,
            )
            .join(
                Category,
                Category.category_id == Quest.category_id,
            )
            .where(
                QuestSubmission.user_id.in_(candidate_user_ids),
                QuestSubmission.final_status == SubmissionStatus.ACCEPTED,
                QuestSubmission.submitted_at >= since,
            )
            .order_by(
                QuestSubmission.user_id.asc(),
                QuestSubmission.submitted_at.desc(),
                QuestSubmission.submission_id.desc(),
            )
        )

        result = session.execute(stmt)

        return list(result.all())