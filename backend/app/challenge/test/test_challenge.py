from __future__ import annotations

"""Challenge 도메인의 핵심 비즈니스 규칙을 확인하는 단위 테스트.

실제 PostgreSQL이나 Redis에 연결하지 않고 Repository와 Session을 Mock으로
대체합니다. 따라서 팀 생성·참가·나가기·초대 처리 규칙을 빠르게 검증할 수
있습니다.
"""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from backend.app.challenge.enums import (
    TeamInviteStatus,
    TeamMemberRole,
    TeamStatus,
)
from backend.app.challenge.repository import (
    TeamInviteRepository,
    TeamMemberRepository,
    TeamRepository,
)
from backend.app.challenge.schema import (
    TeamCreate,
    TeamInviteCreate,
    TeamInviteStatusUpdate,
)
from backend.app.challenge.service import ChallengeTeamService


# 테스트에서 반복해서 사용하는 활성 사용자 객체를 만듭니다.
def make_user(user_id: int = 1, *, is_active: bool = True) -> SimpleNamespace:
    return SimpleNamespace(
        user_id=user_id,
        is_active=is_active,
    )


# 테스트에서 반복해서 사용하는 팀 객체를 만듭니다.
def make_team(**overrides: object) -> SimpleNamespace:
    values: dict[str, object] = {
        "team_id": 10,
        "leader_id": 1,
        "quest_id": 100,
        "name": "테스트 팀",
        "password_hash": None,
        "notification": "잘 부탁드립니다.",
        "region": "서울",
        "is_public": True,
        "max_members": 4,
        "status": TeamStatus.RECRUITING,
        "expires_at": datetime.now(timezone.utc) + timedelta(days=1),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_public_team_rejects_password() -> None:
    """공개 팀에는 입장 비밀번호를 설정할 수 없습니다."""

    with pytest.raises(ValidationError):
        TeamCreate(
            quest_id=1,
            name="공개 팀",
            password="1234",
            region="서울",
            is_public=True,
        )


def test_private_team_requires_password() -> None:
    """비공개 팀은 입장 비밀번호가 반드시 필요합니다."""

    with pytest.raises(ValidationError):
        TeamCreate(
            quest_id=1,
            name="비공개 팀",
            region="서울",
            is_public=False,
        )


def test_invite_status_request_allows_only_accept_or_reject() -> None:
    """사용자는 PENDING이나 EXPIRED를 요청값으로 보낼 수 없습니다."""

    accepted = TeamInviteStatusUpdate(status=TeamInviteStatus.ACCEPTED)
    assert accepted.status == TeamInviteStatus.ACCEPTED

    with pytest.raises(ValidationError):
        TeamInviteStatusUpdate(status=TeamInviteStatus.PENDING)


def test_create_team_adds_creator_as_leader(monkeypatch: pytest.MonkeyPatch) -> None:
    """팀 생성자는 Team 생성 후 LEADER 멤버로 추가되어야 합니다."""

    session = Mock()
    current_user = make_user()
    team = make_team()
    create_team_mock = Mock(return_value=team)
    add_member_mock = Mock(return_value=SimpleNamespace())

    monkeypatch.setattr(TeamRepository, "create_team", create_team_mock)
    monkeypatch.setattr(TeamMemberRepository, "add_member", add_member_mock)

    team_data = TeamCreate(
        quest_id=100,
        name="테스트 팀",
        region="서울",
        is_public=True,
    )

    result = ChallengeTeamService.create_team(
        session,
        team_data=team_data,
        current_user=current_user,
    )

    assert result is team
    add_member_mock.assert_called_once_with(
        session,
        team_id=team.team_id,
        user_id=current_user.user_id,
        role_in_team=TeamMemberRole.LEADER,
    )


def test_inactive_user_cannot_join_team(monkeypatch: pytest.MonkeyPatch) -> None:
    """비활성화된 사용자는 공개·비공개 여부와 관계없이 참가할 수 없습니다."""

    session = Mock()
    current_user = make_user(is_active=False)
    get_team_mock = Mock(return_value=make_team())
    monkeypatch.setattr(TeamRepository, "get_team_by_id", get_team_mock)

    with pytest.raises(HTTPException) as exc_info:
        ChallengeTeamService.join_team(
            session,
            team_id=10,
            password=None,
            current_user=current_user,
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "비활성화된 사용자는 팀에 참가할 수 없습니다."
    get_team_mock.assert_not_called()


def test_join_team_rejects_when_capacity_is_full(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """현재 인원이 최대 인원 이상이면 새 멤버 참가를 차단합니다."""

    session = Mock()
    current_user = make_user(user_id=2)
    team = make_team(max_members=4)

    monkeypatch.setattr(TeamRepository, "get_team_by_id", Mock(return_value=team))
    monkeypatch.setattr(
        TeamMemberRepository,
        "get_member_by_team_and_user",
        Mock(return_value=None),
    )
    monkeypatch.setattr(
        TeamMemberRepository,
        "count_team_members",
        Mock(return_value=4),
    )

    with pytest.raises(HTTPException) as exc_info:
        ChallengeTeamService.join_team(
            session,
            team_id=team.team_id,
            password=None,
            current_user=current_user,
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "팀 정원이 모두 찼습니다."


def test_join_private_team_rejects_wrong_password(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """비공개 팀의 비밀번호가 틀리면 참가를 차단합니다."""

    session = Mock()
    current_user = make_user(user_id=2)
    team = make_team(is_public=False, password_hash="hashed-password")

    monkeypatch.setattr(TeamRepository, "get_team_by_id", Mock(return_value=team))
    monkeypatch.setattr(
        TeamMemberRepository,
        "get_member_by_team_and_user",
        Mock(return_value=None),
    )
    monkeypatch.setattr(
        TeamMemberRepository,
        "count_team_members",
        Mock(return_value=1),
    )
    monkeypatch.setattr(
        "backend.app.challenge.service.verify_password",
        Mock(return_value=False),
    )

    with pytest.raises(HTTPException) as exc_info:
        ChallengeTeamService.join_team(
            session,
            team_id=team.team_id,
            password="wrong-password",
            current_user=current_user,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "팀 비밀번호가 일치하지 않습니다."


def test_leader_leave_delegates_to_earliest_member(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """팀장이 나가면 가장 먼저 참가한 다음 팀원에게 팀장 권한을 위임합니다."""

    session = Mock()
    current_user = make_user(user_id=1)
    team = make_team(leader_id=1)
    current_member = SimpleNamespace(
        user_id=1,
        role_in_team=TeamMemberRole.LEADER,
    )
    next_leader = SimpleNamespace(
        user_id=2,
        role_in_team=TeamMemberRole.MEMBER,
    )

    monkeypatch.setattr(TeamRepository, "get_team_by_id", Mock(return_value=team))
    monkeypatch.setattr(
        TeamMemberRepository,
        "get_member_by_team_and_user",
        Mock(return_value=current_member),
    )
    monkeypatch.setattr(
        TeamMemberRepository,
        "count_team_members",
        Mock(return_value=2),
    )
    monkeypatch.setattr(
        TeamMemberRepository,
        "get_next_leader_candidate",
        Mock(return_value=next_leader),
    )
    update_role_mock = Mock(return_value=next_leader)
    update_leader_mock = Mock(return_value=team)
    remove_member_mock = Mock()
    monkeypatch.setattr(TeamMemberRepository, "update_member_role", update_role_mock)
    monkeypatch.setattr(TeamRepository, "update_team_leader", update_leader_mock)
    monkeypatch.setattr(TeamMemberRepository, "remove_member", remove_member_mock)

    ChallengeTeamService.leave_team(
        session,
        team_id=team.team_id,
        current_user=current_user,
    )

    update_role_mock.assert_called_once_with(
        session,
        member=next_leader,
        role_in_team=TeamMemberRole.LEADER,
    )
    update_leader_mock.assert_called_once_with(
        session,
        team=team,
        new_leader_id=next_leader.user_id,
    )
    remove_member_mock.assert_called_once_with(session, member=current_member)


def test_last_member_leave_deletes_team(monkeypatch: pytest.MonkeyPatch) -> None:
    """마지막 팀원이 나가면 멤버만 삭제하지 않고 팀 자체를 삭제합니다."""

    session = Mock()
    current_user = make_user()
    team = make_team()
    current_member = SimpleNamespace(
        user_id=1,
        role_in_team=TeamMemberRole.LEADER,
    )
    delete_team_mock = Mock()
    remove_member_mock = Mock()

    monkeypatch.setattr(TeamRepository, "get_team_by_id", Mock(return_value=team))
    monkeypatch.setattr(
        TeamMemberRepository,
        "get_member_by_team_and_user",
        Mock(return_value=current_member),
    )
    monkeypatch.setattr(
        TeamMemberRepository,
        "count_team_members",
        Mock(return_value=1),
    )
    monkeypatch.setattr(TeamRepository, "delete_team", delete_team_mock)
    monkeypatch.setattr(TeamMemberRepository, "remove_member", remove_member_mock)

    ChallengeTeamService.leave_team(
        session,
        team_id=team.team_id,
        current_user=current_user,
    )

    delete_team_mock.assert_called_once_with(session, team=team)
    remove_member_mock.assert_not_called()


def test_rejected_invite_is_renewed_instead_of_inserted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UniqueConstraint 충돌을 피하기 위해 거절된 초대 행을 재사용합니다."""

    session = Mock()
    current_user = make_user(user_id=1)
    invited_user = make_user(user_id=2)
    session.get.return_value = invited_user
    team = make_team(leader_id=1)
    old_invite = SimpleNamespace(status=TeamInviteStatus.REJECTED)
    renewed_invite = SimpleNamespace(
        invite_id=20,
        status=TeamInviteStatus.PENDING,
    )
    renew_mock = Mock(return_value=renewed_invite)
    create_mock = Mock()

    monkeypatch.setattr(TeamRepository, "get_team_by_id", Mock(return_value=team))
    monkeypatch.setattr(
        TeamMemberRepository,
        "get_member_by_team_and_user",
        Mock(return_value=None),
    )
    monkeypatch.setattr(
        TeamMemberRepository,
        "count_team_members",
        Mock(return_value=1),
    )
    monkeypatch.setattr(
        TeamInviteRepository,
        "get_invite_by_team_and_user",
        Mock(return_value=old_invite),
    )
    monkeypatch.setattr(TeamInviteRepository, "renew_invite", renew_mock)
    monkeypatch.setattr(TeamInviteRepository, "create_invite", create_mock)

    result = ChallengeTeamService.create_team_invite(
        session,
        invite_data=TeamInviteCreate(team_id=team.team_id, user_id=2),
        current_user=current_user,
    )

    assert result is renewed_invite
    renew_mock.assert_called_once()
    create_mock.assert_not_called()


def test_accept_invite_adds_member_and_updates_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """초대 수락 시 멤버 추가 후 초대 상태를 ACCEPTED로 변경합니다."""

    session = Mock()
    current_user = make_user(user_id=2)
    invite = SimpleNamespace(
        invite_id=30,
        team_id=10,
        user_id=2,
        status=TeamInviteStatus.PENDING,
    )
    team = make_team(team_id=10)
    accepted_invite = SimpleNamespace(status=TeamInviteStatus.ACCEPTED)
    add_member_mock = Mock(return_value=SimpleNamespace())
    update_status_mock = Mock(return_value=accepted_invite)

    monkeypatch.setattr(
        ChallengeTeamService,
        "expire_pending_invites",
        staticmethod(Mock(return_value=0)),
    )
    monkeypatch.setattr(
        TeamInviteRepository,
        "get_invite_by_id",
        Mock(return_value=invite),
    )
    monkeypatch.setattr(TeamRepository, "get_team_by_id", Mock(return_value=team))
    monkeypatch.setattr(
        TeamMemberRepository,
        "get_member_by_team_and_user",
        Mock(return_value=None),
    )
    monkeypatch.setattr(
        TeamMemberRepository,
        "count_team_members",
        Mock(return_value=1),
    )
    monkeypatch.setattr(TeamMemberRepository, "add_member", add_member_mock)
    monkeypatch.setattr(
        TeamInviteRepository,
        "update_invite_status",
        update_status_mock,
    )

    result = ChallengeTeamService.respond_team_invite(
        session,
        invite_id=invite.invite_id,
        update_data=TeamInviteStatusUpdate(status=TeamInviteStatus.ACCEPTED),
        current_user=current_user,
    )

    assert result is accepted_invite
    add_member_mock.assert_called_once_with(
        session,
        team_id=team.team_id,
        user_id=current_user.user_id,
        role_in_team=TeamMemberRole.MEMBER,
    )
    update_status_mock.assert_called_once_with(
        session,
        invite=invite,
        status=TeamInviteStatus.ACCEPTED,
    )


def test_expire_pending_invites_passes_utc_time(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Service는 현재 UTC 시각을 Repository에 전달하고 변경 개수를 반환합니다."""

    session = Mock()
    expire_mock = Mock(return_value=3)
    monkeypatch.setattr(
        TeamInviteRepository,
        "expire_pending_invites",
        expire_mock,
    )

    result = ChallengeTeamService.expire_pending_invites(session)

    assert result == 3
    passed_time = expire_mock.call_args.kwargs["current_time"]
    assert passed_time.tzinfo is timezone.utc
