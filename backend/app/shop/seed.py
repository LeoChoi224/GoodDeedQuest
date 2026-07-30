from sqlalchemy.orm import Session
from backend.app.shop.models import Item
import logging

logger = logging.getLogger(__name__)

"""30종 프로필 테두리 시드 데이터 최종 명세"""
SHOP_SEED_ITEMS = [
    {
        "name": "아이언 노비스 테두리",
        "description": "단단하고 투박한 무쇠 엠블럼이 조각된 입문자용 아이언 테두리",
        "price_point": 1000,
        "image_url": "/static/borders/border_1.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "브론즈 챌린저 테두리",
        "description": "선행 퀘스트의 첫발을 내딛는 용감한 챌린저를 위한 단단한 청동 테두리",
        "price_point": 2000,
        "image_url": "/static/borders/border_2.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "새싹 희망 테두리",
        "description": "첫 봉사의 기쁨과 희망을 담은 파릇파릇한 새싹 모양 테두리",
        "price_point": 2000,
        "image_url": "/static/borders/border_3.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "해바라기 태양 테두리",
        "description": "밝은 미소로 이웃을 환히 밝히는 해바라기 디자인 테두리",
        "price_point": 3000,
        "image_url": "/static/borders/border_4.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "실버 가디언 테두리",
        "description": "지역 사회의 든든한 수호자를 위한 단정하고 은은한 은빛 테두리",
        "price_point": 5000,
        "image_url": "/static/borders/border_5.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "울창한 숲 테두리",
        "description": "푸른 지구를 지키는 대자연의 깊은 숲 기운이 담긴 테두리",
        "price_point": 5000,
        "image_url": "/static/borders/border_6.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "별빛 밤하늘 테두리",
        "description": "어두운 곳에 희망의 빛을 비추는 별빛 밤하늘 은하 테두리",
        "price_point": 7500,
        "image_url": "/static/borders/border_7.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "골드 챔피언 테두리",
        "description": "선행을 꾸준히 실천한 유저에게 선사하는 빛나는 황금빛 프로필 테두리",
        "price_point": 10000,
        "image_url": "/static/borders/border_8.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "푸른 파도 테두리",
        "description": "깨끗한 바다 정화 활동을 기념하는 시원한 파도 문양 테두리",
        "price_point": 10000,
        "image_url": "/static/borders/border_9.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "얼음 결정 테두리",
        "description": "투명하고 순수한 선행의 마음을 간직한 얼음 결정 테두리",
        "price_point": 12500,
        "image_url": "/static/borders/border_10.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "에메랄드 에코 테두리",
        "description": "환경 보호 퀘스트를 열정적으로 달성한 유저를 위한 싱그러운 에메랄드 테두리",
        "price_point": 15000,
        "image_url": "/static/borders/border_11.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "벚꽃 봄날 테두리",
        "description": "따스한 나눔의 온기를 전하는 화사한 벚꽃 잎 모양 테두리",
        "price_point": 15000,
        "image_url": "/static/borders/border_12.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "사파이어 오션 테두리",
        "description": "깊은 봉사의 심연을 드러내는 고결하고 맑은 사파이어 테두리",
        "price_point": 17500,
        "image_url": "/static/borders/border_13.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "플래티넘 가디언 테두리",
        "description": "청백색 백금 광채와 미스티 블루 보석이 고결하게 빛나는 플래티넘 테두리",
        "price_point": 20000,
        "image_url": "/static/borders/border_14.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "불꽃 열정 테두리",
        "description": "식지 않는 봉사의 열정을 보여주는 불꽃 엠블럼 테두리",
        "price_point": 20000,
        "image_url": "/static/borders/border_15.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "은하수 우주 테두리",
        "description": "무한한 선한 영향력을 펼치는 몽환적인 은하수 우주 테두리",
        "price_point": 22500,
        "image_url": "/static/borders/border_16.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "다이아몬드 레전드 테두리",
        "description": "변치 않는 숭고한 선행을 상징하는 최고급 다이아몬드 테두리",
        "price_point": 25000,
        "image_url": "/static/borders/border_17.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "무지개 약속 테두리",
        "description": "더 나은 세상을 함께 만들어가는 무지개빛 약속 테두리",
        "price_point": 25000,
        "image_url": "/static/borders/border_18.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "아메지스트 바이올렛 테두리",
        "description": "고귀한 나눔의 가치를 입증한 유저를 위한 자수정 테두리",
        "price_point": 30000,
        "image_url": "/static/borders/border_19.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "루비 히어로 테두리",
        "description": "헌신적인 봉사 정신을 상징하는 뜨겁고 강렬한 루비 보석 테두리",
        "price_point": 40000,
        "image_url": "/static/borders/border_20.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "선행 마스터 테두리",
        "description": "플랫폼 최고의 공익 실천가에게 수여되는 황금 왕관 마스터 테두리",
        "price_point": 40000,
        "image_url": "/static/borders/border_21.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "그랜드마스터 정점 테두리",
        "description": "공익 실천의 최정상에 도달한 자에게 부여되는 붉은 보석과 그랜드마스터 휘장 테두리",
        "price_point": 45000,
        "image_url": "/static/borders/border_22.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "드래곤 신화 테두리",
        "description": "챌린지 전설을 달성한 자에게 허락되는 전설의 드래곤 테두리",
        "price_point": 50000,
        "image_url": "/static/borders/border_23.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "할로윈 호박 나이트 테두리",
        "description": "[할로윈 한정] 잭오랜턴 호박과 칠흑 같은 박쥐 아우라가 감싸는 할로윈 테두리",
        "price_point": 30000,
        "image_url": "/static/borders/border_24.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "크리스마스 성탄 테두리",
        "description": "[크리스마스 한정] 반짝이는 성탄 종과 크리스마스 리스/눈꽃 장식 테두리",
        "price_point": 30000,
        "image_url": "/static/borders/border_25.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "새해 복주머니 희망 테두리",
        "description": "[새해 한정] 전통 비단 복주머니와 황금 노리개 매듭이 유려한 새해 테두리",
        "price_point": 30000,
        "image_url": "/static/borders/border_26.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "여름 썸머 비치 테두리",
        "description": "[여름 한정] 에메랄드 빛 휴양지 바다, 야자수, 진주 조개가 어우러진 썸머 테두리",
        "price_point": 30000,
        "image_url": "/static/borders/border_27.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "추석 단풍 풍요 테두리",
        "description": "[추석 한정] 탐스러운 보름달과 붉은 단풍잎이 흩날리는 가을 풍요 테두리",
        "price_point": 30000,
        "image_url": "/static/borders/border_28.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "발렌타인 핑크 하트 테두리",
        "description": "[발렌타인 한정] 달콤한 초콜릿 리본과 분홍빛 큐피트 하트 테두리",
        "price_point": 30000,
        "image_url": "/static/borders/border_29.png",
        "is_active": True,
        "is_equipped": False,
    },
    {
        "name": "사이버펑크 네온 테두리",
        "description": "[스페셜 한정] 화려한 푸른빛과 분홍빛 홀로그램 네온 튜브가 발광하는 사이버 테두리",
        "price_point": 30000,
        "image_url": "/static/borders/border_30.png",
        "is_active": True,
        "is_equipped": False,
    },
]


def seed_shop_items(db_or_repo) -> None:
    """
    상점 30종 프로필 테두리 시드 데이터 업서트(Upsert) 적재 함수
    """
    # Session 객체와 DatabaseRepository 객체 모두 안전하게 호환 처리
    session: Session = getattr(db_or_repo, "session", db_or_repo)

    updated_count = 0
    created_count = 0

    for seed in SHOP_SEED_ITEMS:
        item = session.query(Item).filter(Item.name == seed["name"]).first()
        if item:
            item.price_point = seed["price_point"]
            item.image_url = seed["image_url"]
            item.description = seed["description"]
            item.is_active = seed["is_active"]
            updated_count += 1
        else:
            new_item = Item(**seed)
            session.add(new_item)
            created_count += 1

    session.commit()
    logger.info(f"성공: 상점 프로필 테두리 시드 데이터 (신규 {created_count}개 생성 / 기존 {updated_count}개 업서트 갱신 완료)")