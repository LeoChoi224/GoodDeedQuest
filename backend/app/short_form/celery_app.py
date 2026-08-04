# backend/app/short_form/celery_app.py

"""
Celery 앱 설정 파일.

역할: "무엇을 할지"(tasks.py)가 아니라 "그 작업을 어떻게 실행할지"를 정의한다.
    - 어떤 메시지 큐(broker)에 작업 요청이 쌓이는지
    - 작업 실행 결과(backend)를 어디에 저장할지
    - 어떤 파일에 @celery_app.task로 정의된 작업들이 있는지(include)

워커 실행 시 이 파일을 기준으로 커맨드를 실행한다:
    celery -A backend.app.short_form.celery_app worker --loglevel=info
"""

from celery import Celery

from backend.app.common.config import get_setting

# ⭐ 수정: 워커 프로세스는 backend.main(FastAPI 앱)을 거치지 않고 이 파일에서 바로
# 기동되기 때문에, ShortForm.user 등 relationship이 문자열로 참조하는 User/UserBadge
# 같은 다른 도메인 모델이 한 번도 import되지 않아 SQLAlchemy 매퍼 등록이 안 된 상태였다.
# (실제로 render_shortform_task가 ShortForm을 조회하는 순간
#  "InvalidRequestError: failed to locate a name ('User')"로 워커가 죽는 문제 발생)
# backend.main을 그대로 import하면 main -> short_form.router -> service -> tasks ->
# 이 파일(celery_app)로 다시 돌아오는 순환 import가 생겨서 대신 라우터를 전혀 거치지
# 않는 models_registry(모든 도메인 모델만 모아 import하는 전용 모듈)를 사용한다.
import backend.app.models_registry  # noqa: F401,E402 - 모든 도메인 모델을 미리 등록해 매퍼 오류 방지

# get_setting()은 @lru_cache가 걸려있어 매번 새로 만들지 않고
# 캐싱된 Settings 인스턴스를 반환한다. 모듈 로드 시 한 번만 호출해서 재사용.
settings = get_setting()

celery_app = Celery(
    "gooddeedquest",  # 이 Celery 앱의 이름 (프로젝트 식별용, 아무 문자열이나 가능)

    # broker: service.py에서 render_shortform_task.delay()를 호출하면
    # 작업 요청이 이 주소(Redis)로 전달되어 큐에 쌓인다.
    # 워커 프로세스가 이 큐를 계속 감시하다가 새 작업이 들어오면 꺼내서 실행한다.
    broker=settings.REDIS_URL,

    # backend: task 실행이 끝난 뒤 결과(성공/실패, 반환값)를 저장할 곳.
    # 지금 구조에서는 task 결과를 ShortForm.status(DB)에 직접 기록하기 때문에
    # 이 backend 값을 실제로 조회(.get())할 일은 없지만, 나중에 필요해질 수
    # 있어 broker와 동일한 Redis를 재사용해 미리 설정해둔다.
    backend=settings.REDIS_URL,

    # include: @celery_app.task로 데코레이팅된 함수가 어느 파일에 있는지 알려준다.
    # 이 목록에 없으면 워커가 해당 task를 인식하지 못해 실행 요청이 와도 처리할 수 없다.
    # 지금은 render_shortform_task 하나뿐이라 tasks.py만 등록.
    include=["backend.app.short_form.tasks"],
)

# Celery 공통 동작 설정
celery_app.conf.update(
    task_serializer="json",     # task 파라미터를 JSON으로 직렬화해 큐에 전달
    result_serializer="json",   # task 결과도 JSON으로 직렬화
    accept_content=["json"],    # 다른 포맷(pickle 등)은 보안상 허용하지 않고 JSON만 받음
    timezone="Asia/Seoul",      # 로그/스케줄링 시각을 한국 시간 기준으로 표시
    enable_utc=True,            # 내부적으로는 UTC로 저장 (timezone 변환 안전성 확보)
)