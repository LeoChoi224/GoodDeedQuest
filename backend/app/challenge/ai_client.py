from __future__ import annotations

# =========================================================
# [AI 팀원 추천 HTTP Client 구현 기준]
#
# 1. 역할
#    - Backend에서 AI 서버의 팀원 추천 API를 동기 HTTP 방식으로 호출합니다.
#    - 후보 조회, 권한 검증, 팀 상태 확인은 Challenge Service가 담당합니다.
#    - 이 Client는 HTTP 통신과 응답의 최상위 JSON 형식 확인만 담당합니다.
#
# 2. 호출 대상
#    - POST {AI_SERVICE_URL}/ai/challenge/recommend
#
# 3. 호출 방식
#    - Backend의 동기 Session·Service·Router 구조에 맞춰
#      httpx.Client를 사용하는 동기 호출 방식으로 구현했습니다.
#
# 4. 예외 처리
#    - 연결 실패, 응답 시간 초과, AI 서버 처리 불가,
#      요청 계약 오류와 예상하지 못한 응답을 Client 전용 예외로 구분합니다.
#    - Client 예외를 HTTPException으로 변환하는 작업은
#      ChallengeRecommendationService가 담당합니다.
#
# 5. 응답 검증
#    - Client는 응답이 JSON Object인지 확인합니다.
#    - 세부 필드, 점수 합계, 순위, 추천 수와 후보 사용자 여부는
#      Backend 응답 Schema와 ChallengeRecommendationService가 검증합니다.
# =========================================================

from typing import Any

import httpx

from backend.app.common.config import get_setting


# AI 추천 API의 상대 경로입니다.
CHALLENGE_RECOMMENDATION_PATH = "/ai/challenge/recommend"


# AI 추천 호출에 사용할 세부 Timeout 설정입니다.
CHALLENGE_RECOMMENDATION_TIMEOUT = httpx.Timeout(
    connect=3.0,
    read=45.0,
    write=10.0,
    pool=5.0,
)


class ChallengeRecommendationClientError(Exception):
    """AI 팀원 추천 Client에서 발생하는 모든 오류의 기본 예외입니다."""


class ChallengeRecommendationConnectionError(
    ChallengeRecommendationClientError
):
    """AI 서버에 연결하지 못했을 때 발생하는 예외입니다."""


class ChallengeRecommendationTimeoutError(
    ChallengeRecommendationClientError
):
    """AI 서버 응답 시간이 초과됐을 때 발생하는 예외입니다."""


class ChallengeRecommendationUnavailableError(
    ChallengeRecommendationClientError
):
    """AI 서버가 추천 처리를 수행할 수 없을 때 발생하는 예외입니다."""


class ChallengeRecommendationRequestError(
    ChallengeRecommendationClientError
):
    """Backend와 AI 서버 사이의 요청 데이터 계약이 맞지 않는 예외입니다."""


class ChallengeRecommendationResponseError(
    ChallengeRecommendationClientError
):
    """AI 서버가 예상하지 못한 상태나 응답 형식을 반환한 예외입니다."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
    ) -> None:
        """오류 메시지와 AI 서버 상태 코드를 저장합니다."""

        super().__init__(message)
        self.status_code = status_code


class ChallengeRecommendationAIClient:
    """AI 서버의 팀 챌린지 추천 API를 호출하는 동기 Client입니다."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout: httpx.Timeout = CHALLENGE_RECOMMENDATION_TIMEOUT,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        """호출 주소, Timeout, 선택적 테스트 Transport를 설정합니다."""

        # 테스트에서 주소를 직접 주입할 수 있도록 하고,
        # 실제 실행에서는 환경설정의 AI_SERVICE_URL을 사용합니다.
        configured_base_url = (
            base_url
            if base_url is not None
            else get_setting().AI_SERVICE_URL
        )

        # 마지막 슬래시를 제거해 API 경로 조합 시 이중 슬래시를 방지합니다.
        self.base_url = configured_base_url.rstrip("/")
        self.timeout = timeout
        self.transport = transport

    @property
    def recommendation_url(self) -> str:
        """팀원 추천 API의 전체 URL을 반환합니다."""

        return f"{self.base_url}{CHALLENGE_RECOMMENDATION_PATH}"

    def request_recommendations(
        self,
        *,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """AI 서버에 팀원 추천을 요청하고 JSON 응답을 반환합니다."""

        try:
            # 요청마다 Client를 안전하게 열고 닫아 연결 자원을 정리합니다.
            with httpx.Client(
                timeout=self.timeout,
                transport=self.transport,
            ) as client:
                response = client.post(
                    self.recommendation_url,
                    json=payload,
                    headers={
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                    },
                )

        except httpx.TimeoutException as exc:
            # 연결·읽기·쓰기·Pool 대기 시간 초과를 하나의 Timeout 예외로 변환합니다.
            raise ChallengeRecommendationTimeoutError(
                "AI 추천 서버의 응답 시간이 초과되었습니다."
            ) from exc

        except httpx.RequestError as exc:
            # DNS, 연결 거부, 네트워크 단절 등의 통신 오류를 변환합니다.
            raise ChallengeRecommendationConnectionError(
                "AI 추천 서버에 연결할 수 없습니다."
            ) from exc

        # AI 서버가 반환한 HTTP 상태 코드에 따라 의미 있는 예외로 변환합니다.
        self._raise_for_error_status(response)

        try:
            response_data = response.json()

        except ValueError as exc:
            # 성공 상태 코드라도 JSON이 아니면 정상적인 AI 응답으로 사용할 수 없습니다.
            raise ChallengeRecommendationResponseError(
                "AI 추천 서버가 올바른 JSON 응답을 반환하지 않았습니다.",
                status_code=response.status_code,
            ) from exc

        # 추천 응답의 최상위 구조는 JSON Object여야 합니다.
        if not isinstance(response_data, dict):
            raise ChallengeRecommendationResponseError(
                "AI 추천 서버의 응답 형식이 올바르지 않습니다.",
                status_code=response.status_code,
            )

        return response_data

    @staticmethod
    def _raise_for_error_status(
        response: httpx.Response,
    ) -> None:
        """AI 서버의 오류 상태 코드를 Client 전용 예외로 변환합니다."""

        # 정상적인 2xx 응답은 그대로 통과시킵니다.
        if 200 <= response.status_code < 300:
            return

        # 422는 Backend가 만든 Payload와 AI 요청 Schema가 맞지 않는 상태입니다.
        if response.status_code == 422:
            raise ChallengeRecommendationRequestError(
                "AI 추천 요청 데이터 형식이 올바르지 않습니다."
            )

        # AI Graph의 치명적 오류 등으로 AI 서버가 503을 반환한 경우입니다.
        if response.status_code == 503:
            raise ChallengeRecommendationUnavailableError(
                "AI 추천 서버가 현재 추천을 처리할 수 없습니다."
            )

        # 그 밖의 상태 코드는 예상하지 못한 서비스 간 응답 오류로 처리합니다.
        raise ChallengeRecommendationResponseError(
            "AI 추천 서버가 예상하지 못한 오류 응답을 반환했습니다.",
            status_code=response.status_code,
        )
