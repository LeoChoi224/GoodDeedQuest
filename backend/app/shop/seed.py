import logging
from backend.app.common.repository import DatabaseRepository
from backend.app.shop.models import Item

logger = logging.getLogger(__name__)


def seed_shop_items(item_repo: DatabaseRepository[Item]) -> None:
    """
    상점 프로필 테두리 목업 데이터를 DB에 적재하는 멱등성 보장 시드 함수
    """
    existing_items = item_repo.filter()
    if existing_items and len(existing_items) > 0:
        logger.info("상점 시드 데이터가 이미 존재합니다. 시드 적재를 건너끕니다.")
        return

    dummy_items = [
        {
            "name": "골드 챔피언 테두리",
            "description": "선행을 꾸준히 실천한 유저에게 선사하는 빛나는 황금빛 프로필 테두리",
            "price_point": 1000,
            "image_url": "https://raw.githubusercontent.com/LeoChoi224/GoodDeedQuest/main/assets/border_gold.png",
            "is_active": True,
            "is_equipped": False,
        },
        {
            "name": "실버 가디언 테두리",
            "description": "지역 사회의 든든한 수호자를 위한 단정하고 은은한 실버 프로필 테두리",
            "price_point": 500,
            "image_url": "https://raw.githubusercontent.com/LeoChoi224/GoodDeedQuest/main/assets/border_silver.png",
            "is_active": True,
            "is_equipped": False,
        },
        {
            "name": "브론즈 챌린저 테두리",
            "description": "선행 퀘스트의 첫발을 내딛는 용감한 챌린저를 위한 브론즈 프로필 테두리",
            "price_point": 300,
            "image_url": "https://raw.githubusercontent.com/LeoChoi224/GoodDeedQuest/main/assets/border_bronze.png",
            "is_active": True,
            "is_equipped": False,
        },
        {
            "name": "에메랄드 에코 테두리",
            "description": "환경 보호 퀘스트를 열정적으로 달성한 유저를 위한 청량한 에메랄드 테두리",
            "price_point": 700,
            "image_url": "https://raw.githubusercontent.com/LeoChoi224/GoodDeedQuest/main/assets/border_emerald.png",
            "is_active": True,
            "is_equipped": False,
        },
    ]

    for item_data in dummy_items:
        item_repo.create(item_data)

    logger.info(f"상점 프로필 테두리 목업 시드 데이터 {len(dummy_items)}개 적재 완료")