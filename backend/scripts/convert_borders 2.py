import os
import glob
import math
from PIL import Image

# 터미널 명령어: PYTHONPATH=. /opt/miniconda3/envs/Good-Deed-Quest/bin/python3 backend/scripts/convert_borders.py && PYTHONPATH=. /opt/miniconda3/envs/Good-Deed-Quest/bin/python3 -c "import backend.app.models_registry; from backend.app.common.database import SessionLocal; from backend.app.shop.seed import seed_shop_items; db = SessionLocal(); seed_shop_items(db); db.close(); print('=== DB Item 테이블 시드 갱신 완료 ===')"
def process_transparent_borders():
    """30종 프로필 테두리 최신 자산 자동 탐색 및 투명 PNG 일괄 변환 스크립트"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    borders_dir = os.path.abspath(os.path.join(base_dir, "..", "app", "static", "borders"))
    
    os.makedirs(borders_dir, exist_ok=True)

    mapping = {
        1: "border_1_iron_novice",
        2: "border_2_bronze_challenger",
        3: "border_3_sprout_hope",
        4: "border_4_sunflower_sun",
        5: "border_5_silver_guardian",
        6: "border_6_lush_forest",
        7: "border_7_starry_night",
        8: "border_8_gold_champion",
        9: "border_9_blue_wave",
        10: "border_10_ice_crystal",
        11: "border_11_emerald_eco",
        12: "border_12_cherry_blossom",
        13: "border_13_sapphire_ocean",
        14: "border_14_platinum_guardian",
        15: "border_15_fire_passion",
        16: "border_16_galaxy_cosmic",
        17: "border_17_diamond_legend",
        18: "border_18_rainbow_promise",
        19: "border_19_amethyst_violet",
        20: "border_20_ruby_hero",
        21: "border_21_good_deed_master",
        22: "border_22_grandmaster_apex",
        23: "border_23_dragon_mythic",
        24: "border_24_halloween_pumpkin",
        25: "border_25_christmas_xmas",
        26: "border_26_newyear_pouch",
        27: "border_27_summer_beach",
        28: "border_28_chuseok_harvest",
        29: "border_29_valentine_heart",
        30: "border_30_cyberpunk_neon"
    }

    print(f"=== 상대 경로 정적 자산 Target: {borders_dir} ===")
    converted_count = 0

    for idx, key in mapping.items():
        matches = glob.glob(os.path.join(borders_dir, f"*{key}*"))
        
        if matches:
            matches = sorted(matches, key=os.path.getmtime, reverse=True)
            src_path = matches[0]
            
            img = Image.open(src_path).convert("RGBA")
            img = img.resize((512, 512), Image.Resampling.LANCZOS)
            pixels = img.load()

            # 테두리 문양 보존 - 순수 칠흑색/검은색 배경만 투명 채널(Alpha 0) 변환
            for x in range(512):
                for y in range(512):
                    r, g, b, a = pixels[x, y]
                    if r < 35 and g < 35 and b < 35:
                        pixels[x, y] = (0, 0, 0, 0)

            target_filename = f"border_{idx}.png"
            dest_path = os.path.join(borders_dir, target_filename)
            img.save(dest_path, "PNG", optimize=True)
            converted_count += 1
            print(f"[{idx}/30] 성공: {target_filename} (투명화 완료)")
        else:
            print(f"[{idx}/30] 경고: [{key}] 자산 파일 미발견")

    print(f"=== 완료: 총 {converted_count}/30개 자산 변환 완결 ===")

if __name__ == "__main__":
    process_transparent_borders()