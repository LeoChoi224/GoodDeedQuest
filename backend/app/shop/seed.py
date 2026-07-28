from sqlalchemy.orm import Session
from backend.app.shop.models import Item
import logging

logger = logging.getLogger(__name__)

# 20종 프로필 테두리 시드 데이터 명세
SHOP_SEED_ITEMS = [
    {
        "name": "브론즈 챌린저 테두리",
        "description": "선행 퀘스트의 첫발을 내딛는 용감한 챌린저를 위한 단단한 청동 테두리",
        "price_point": 300,
        "image_url": "https://raw.githubusercontent.com/LeoChoi224/GoodDeedQuest/main/assets/borders/border_bronze.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "새싹 희망 테두리",
        "description": "첫 봉사의 기쁨과 희망을 담은 파릇파릇한 새싹 모양 테두리",
        "price_point": 400,
        "image_url": "https://raw.githubusercontent.com/LeoChoi224/GoodDeedQuest/main/assets/borders/border_sprout.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "실버 가디언 테두리",
        "description": "지역 사회의 든든한 수호자를 위한 단정하고 은은한 은빛 테두리",
        "price_point": 500,
        "image_url": "https://raw.githubusercontent.com/LeoChoi224/GoodDeedQuest/main/assets/borders/border_silver.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "에메랄드 에코 테두리",
        "description": "환경 보호 퀘스트를 열정적으로 달성한 유저를 위한 싱그러운 에메랄드 테두리",
        "price_point": 700,
        "image_url": "https://raw.githubusercontent.com/LeoChoi224/GoodDeedQuest/main/assets/borders/border_emerald.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "벚꽃 봄날 테두리",
        "description": "따스한 나눔의 온기를 전하는 화사한 벚꽃 잎 모양 테두리",
        "price_point": 800,
        "image_url": "https://raw.githubusercontent.com/LeoChoi224/GoodDeedQuest/main/assets/borders/border_cherry.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "해바라기 태양 테두리",
        "description": "밝은 미소로 이웃을 환히 밝히는 해바라기 디자인 테두리",
        "price_point": 900,
        "image_url": "https://raw.githubusercontent.com/LeoChoi224/GoodDeedQuest/main/assets/borders/border_sunflower.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "골드 챔피언 테두리",
        "description": "선행을 꾸준히 실천한 유저에게 선사하는 빛나는 황금빛 프로필 테두리",
        "price_point": 1000,
        "image_url": "https://raw.githubusercontent.com/LeoChoi224/GoodDeedQuest/main/assets/borders/border_gold.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "푸른 파도 테두리",
        "description": "깨끗한 바다 정화 활동을 기념하는 시원한 파도 문양 테두리",
        "price_point": 1100,
        "image_url": "https://raw.githubusercontent.com/LeoChoi224/GoodDeedQuest/main/assets/borders/border_wave.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "루비 히어로 테두리",
        "description": "헌신적인 봉사 정신을 상징하는 뜨겁고 강렬한 루비 보석 테두리",
        "price_point": 1200,
        "image_url": "https://raw.githubusercontent.com/LeoChoi224/GoodDeedQuest/main/assets/borders/border_ruby.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "울창한 숲 테두리",
        "description": "푸른 지구를 지키는 대자연의 깊은 숲 기운이 담긴 테두리",
        "price_point": 1300,
        "image_url": "https://raw.githubusercontent.com/LeoChoi224/GoodDeedQuest/main/assets/borders/border_forest.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "사파이어 오션 테두리",
        "description": "깊은 봉사의 심연을 드러내는 고결하고 맑은 사파이어 테두리",
        "price_point": 1500,
        "image_url": "https://raw.githubusercontent.com/LeoChoi224/GoodDeedQuest/main/assets/borders/border_sapphire.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "별빛 밤하늘 테두리",
        "description": "어두운 곳에 희망의 빛을 비추는 별빛 밤하늘 은하 테두리",
        "price_point": 1600,
        "image_url": "https://raw.githubusercontent.com/LeoChoi224/GoodDeedQuest/main/assets/borders/border_starry.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "아메지스트 바이올렛 테두리",
        "description": "고귀한 나눔의 가치를 입증한 유저를 위한 자수정 테두리",
        "price_point": 1800,
        "image_url": "https://raw.githubusercontent.com/LeoChoi224/GoodDeedQuest/main/assets/borders/border_amethyst.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "무지개 약속 테두리",
        "description": "더 나은 세상을 함께 만들어가는 무지개빛 약속 테두리",
        "price_point": 2000,
        "image_url": "https://raw.githubusercontent.com/LeoChoi224/GoodDeedQuest/main/assets/borders/border_rainbow.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "불꽃 열정 테두리",
        "description": "식지 않는 봉사의 열정을 보여주는 불꽃 엠블럼 테두리",
        "price_point": 2200,
        "image_url": "https://raw.githubusercontent.com/LeoChoi224/GoodDeedQuest/main/assets/borders/border_flame.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "얼음 결정 테두리",
        "description": "투명하고 순수한 선행의 마음을 간직한 얼음 결정 테두리",
        "price_point": 2400,
        "image_url": "https://raw.githubusercontent.com/LeoChoi224/GoodDeedQuest/main/assets/borders/border_ice.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "다이아몬드 레전드 테두리",
        "description": "변치 않는 숭고한 선행을 상징하는 최고급 다이아몬드 테두리",
        "price_point": 2500,
        "image_url": "https://raw.githubusercontent.com/LeoChoi224/GoodDeedQuest/main/assets/borders/border_diamond.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "은하수 우주 테두리",
        "description": "무한한 선한 영향력을 펼치는 몽환적인 은하수 우주 테두리",
        "price_point": 2800,
        "image_url": "https://raw.githubusercontent.com/LeoChoi224/GoodDeedQuest/main/assets/borders/border_galaxy.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "드래곤 신화 테두리",
        "description": "챌린지 전설을 달성한 자에게 허락되는 전설의 드래곤 테두리",
        "price_point": 3500,
        "image_url": "https://raw.githubusercontent.com/LeoChoi224/GoodDeedQuest/main/assets/borders/border_dragon.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "선행 마스터 테두리",
        "description": "플랫폼 최고의 공익 실천가에게 수여되는 황금 왕관 마스터 테두리",
        "price_point": 5000,
        "image_url": "https://raw.githubusercontent.com/LeoChoi224/GoodDeedQuest/main/assets/borders/border_master.png",
        "is_active": True,
        "is_equipped": False,
    },
]


def seed_shop_items(db_or_repo) -> None:
    """
    상점 20종 프로필 테두리 시드 데이터 적재 함수 (Session 및 DatabaseRepository 타입 자동 변환 보정)
    """
    # =========================================================================
    # [수정] Session 객체와 DatabaseRepository 객체 모두 안전하게 호환 처리
    # =========================================================================
    session: Session = getattr(db_or_repo, "session", db_or_repo)

    existing_items = session.query(Item.name).all()
    existing_names = {name for (name,) in existing_items}

    new_objects = [Item(**seed) for seed in SHOP_SEED_ITEMS if seed["name"] not in existing_names]

    if new_objects:
        session.add_all(new_objects)
        session.commit()
        logger.info(f"성공: 상점 프로필 테두리 시드 데이터 {len(new_objects)}개가 신규 적재되었습니다.")
    else:
        logger.info("안내: 이미 20종 프로필 테두리 시드 데이터가 적재되어 있습니다.")
    # =========================================================================