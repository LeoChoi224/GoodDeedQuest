"""
모든 도메인의 SQLAlchemy 모델을 한 곳에서 import 해 등록한다.

SQLAlchemy는 relationship("User")나 ForeignKey("region.region_id")처럼
문자열로 참조하는 대상을, "지금까지 파이썬에 로드된 클래스/테이블" 중에서 찾는다.
따라서 A 도메인 모델이 B 도메인 테이블을 FK로 참조하면, B 모델 파일이
어딘가에서 반드시 import 되어 있어야 한다.

라우터가 아직 자기 도메인 모델을 안 쓰는 경우(badge/shop 등)도 있어서,
서버 기동 시 이 파일을 한 번 import 하면 모든 테이블이 확실히 등록된다.
main.py에서 이 모듈을 import 하는 것으로 충분하다.
"""
# noqa: F401 (아래 import들은 "등록" 목적이라 직접 사용하지 않음)
from backend.app.auth import models as _auth_models  # noqa: F401
from backend.app.admin import models as _admin_models  # noqa: F401
from backend.app.badge import models as _badge_models  # noqa: F401
from backend.app.challenge import models as _challenge_models  # noqa: F401
from backend.app.community import models as _community_models  # noqa: F401
from backend.app.map import models as _map_models  # noqa: F401
from backend.app.quest import models as _quest_models  # noqa: F401
from backend.app.quest_verification import models as _quest_verification_models  # noqa: F401
from backend.app.shop import models as _shop_models  # noqa: F401
from backend.app.short_form import models as _short_form_models  # noqa: F401
