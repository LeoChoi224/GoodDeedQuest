"""
VMS(사회복지자원봉사인증관리) 크롤러 - 2단계: 목록 + 상세 파싱 + DB 저장(upsert) + 만료 공고 삭제

확인된 사실:
- https://www.vms.or.kr/partspace/recruit.do , recruitView.do 모두 서버 사이드 렌더링
  -> requests + BeautifulSoup 만으로 충분, Selenium 불필요
- 목록 실제 쿼리 파라미터(상세페이지 "목록" 버튼 링크에서 확인):
  area, areagugun, areadiv(구버전, 항상 빈값), termgbn, searchType, searchValue,
  acttype, volacttype, sttdte, enddte, rcritsttdte, rcritenddte, page, pageSize, status
  -> area/areagugun 은 지역 필터지만, 크롤러는 "채우는 역할"이라 지역 필터 없이 전국 전체 수집.
     즉 VMS_AREA_CODE 매핑은 필요 없음(지역 매칭은 상세페이지 텍스트를 Region 테이블과 매칭해서 처리).
- 목록 카드에는 시/도 단위만 나옴, 시군구/기관명/자격요건/활동내용은 상세페이지에서만 확인 가능

DB 저장 방침 (마이그레이션 없이):
1) VolunteerCenter.center_id(기존 PK)에 VMS seq를 그대로 저장 -> 별도 vms_seq 컬럼 불필요,
   PK 유니크 제약이 중복 방지를 대신 해줌
2) 종료일은 vol_date 문자열("YYYY-MM-DD ~ YYYY-MM-DD")에서 split("~")로 바로 파싱
   -> 별도 vol_end_date 컬럼 불필요

지역 매칭 / 주소 / 좌표 방침 (카카오 키워드 검색 우선):
- 봉사장소명(안되면 봉사활동처명)으로 카카오 로컬 키워드 검색 API를 호출해서
  실제 도로명주소를 받아오고, 그 주소에서 시도/시군구를 뽑아 Region과 매칭함.
  이러면 "창원시"처럼 구가 빠진 VMS 텍스트도 카카오가 돌려주는 정확한 주소
  (예: "경상남도 창원시 진해구 ...")로 정확히 매칭되고, 위경도도 동시에 확보됨.
- 카카오 검색이 실패하면(장소명이 검색 안 되는 경우 등) VMS 봉사지역 텍스트 기반
  파싱으로 폴백(주소/좌표는 못 채우고 지역만이라도 매칭 시도).
- 카카오 REST API 키는 backend/app/common/config.py의 Settings에
  KAKAO_REST_API_KEY(SecretStr)로 등록해서 .env에서 읽어옴.

주의:
- VolunteerCenter.region_id 는 NOT NULL 이라, 카카오/VMS 텍스트 둘 다로 지역을
  못 찾으면 해당 공고는 저장을 건너뜀(스킵 로그 출력)

# ⭐ 수정 1(병렬화): "3) 상세 수집" 단계를 ThreadPoolExecutor로 병렬화.
# ⭐ 수정 2(varchar 초과 크래시 대응): detail_url을 seq 기반으로 짧게 재구성 + 모든 문자열
# 필드를 컬럼 길이만큼 방어적으로 자르는 _trunc() 추가.
# ⭐ 수정 3(속도 개선, 2026-08-04 실측 6280초/3969건): 같은 기관명이 여러 공고에 반복돼서
# 카카오 검색을 매번 새로 하고 있었음 -> 쿼리 문자열 기준 캐시 추가. 실패 후보 대기시간을
# 줄이려고 카카오 타임아웃 10초 -> 5초로 단축. max_workers 기본 8 -> 16.
"""
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta

import requests
from bs4 import BeautifulSoup

LIST_URL = "https://www.vms.or.kr/partspace/recruit.do"
DETAIL_URL = "https://www.vms.or.kr/partspace/recruitView.do"
KAKAO_KEYWORD_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"
HEADERS = {
    # 일부 공공/공익 사이트는 기본 User-Agent(python-requests/...)를 막는 경우가 있어 브라우저처럼 위장
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}


# =========================================================
# 1. 목록 페이지
# =========================================================

def fetch_list_page(page: int, sttdte: str, enddte: str, page_size: int = 12, status: int = 1) -> str:
    """목록 페이지 1페이지 분량 HTML 가져오기. status=1은 모집중만.

    area/areagugun 등 지역필터는 일부러 비워둠(전국 전체 수집).
    """
    params = {
        "sttdte": sttdte,          # 활동기간 시작
        "enddte": enddte,          # 활동기간 종료
        "rcritsttdte": "",         # 모집기간 시작(필터 안 씀)
        "rcritenddte": "",         # 모집기간 종료(필터 안 씀)
        "pageSize": page_size,     # 실사용 여부 불확실(항상 12개씩 오는 것으로 보임), 혹시 몰라 유지
        "page": page,
        "status": status,
        "area": "",                # 시도 필터 - 전국 수집이라 비움
        "areagugun": "",           # 시군구 필터 - 전국 수집이라 비움
        "areadiv": "",             # 구버전 파라미터, 항상 빈값으로 관찰됨
        "termgbn": "",
        "searchType": "title",     # 실제 브라우징 시 항상 딸려오는 기본값
        "searchValue": "",
        "acttype": "",             # 활동분야 필터
        "volacttype": "",          # 활동유형(대면/비대면) 필터
    }
    resp = requests.get(LIST_URL, params=params, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding  # 한글 깨짐 방지
    return resp.text


def parse_list_page(html: str) -> list[dict]:
    """카드 목록 HTML -> 딕셔너리 리스트로 파싱"""
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("li.card")
    results = []

    for card in cards:
        a_tag = card.find("a")
        if a_tag is None or not a_tag.get("href"):
            continue

        href = a_tag["href"]
        seq_match = re.search(r"seq=(\d+)", href)
        if seq_match is None:
            continue
        seq = int(seq_match.group(1))

        chips = card.select("div.chips span.chip")
        region_sido = chips[0].get_text(strip=True) if len(chips) >= 1 else None
        activity_type = chips[1].get_text(strip=True) if len(chips) >= 2 else None

        title_tag = card.select_one("h3.title")
        title = None
        if title_tag is not None:
            badge = title_tag.find("span", class_="badge-b")
            if badge is not None:
                badge.extract()
            title = title_tag.get_text(strip=True)

        org_tag = card.select_one("div.org")
        org = org_tag.get_text(strip=True) if org_tag else None

        period = None
        m_left = card.select_one("div.m-left")
        if m_left is not None:
            h5 = m_left.find("h5")
            if h5 is not None:
                h5.extract()
            period = m_left.get_text(strip=True)

        count_tag = card.select_one("span.count")
        applied_count = capacity = None
        if count_tag is not None:
            count_text = count_tag.get_text(strip=True)
            m = re.search(r"(\d+)\s*/\s*(\d+)", count_text)
            if m:
                applied_count, capacity = int(m.group(1)), int(m.group(2))

        state_tag = card.select_one("span.state")
        status_text = state_tag.get_text(strip=True) if state_tag else None

        results.append({
            "seq": seq,
            "region_sido": region_sido,
            "activity_type": activity_type,
            "title": title,
            "org": org,
            "period": period,
            "applied_count": applied_count,
            "capacity": capacity,
            "status_text": status_text,
            "detail_url": f"{DETAIL_URL}?seq={seq}",
        })

    return results


def crawl_list_all(days_window: int = 30, page_size: int = 12, sleep_sec: float = 0.5,
                    max_pages: int = 500) -> list[dict]:
    """오늘부터 days_window일 구간, 모집중(status=1)인 공고 전체를 페이지네이션하며 수집(목록 정보만)"""
    sttdte = date.today().isoformat()
    enddte = (date.today() + timedelta(days=days_window)).isoformat()

    all_results = []
    seen_seqs: set[int] = set()
    page = 1
    while page <= max_pages:
        html = fetch_list_page(page=page, sttdte=sttdte, enddte=enddte, page_size=page_size)
        items = parse_list_page(html)
        if not items:
            print(f"[list page {page}] 카드 0개 -> 종료")
            break

        page_seqs = [item["seq"] for item in items]
        already_seen = [s for s in page_seqs if s in seen_seqs]
        print(f"[list page {page}] {len(items)}건, seq 범위 {page_seqs[0]}~{page_seqs[-1]}, 중복 {len(already_seen)}개")

        if len(already_seen) == len(items):
            print("!! 이전 페이지와 완전히 동일한 결과 -> page 파라미터가 안 먹히는 것으로 판단, 중단")
            break

        for item in items:
            if item["seq"] not in seen_seqs:
                seen_seqs.add(item["seq"])
                all_results.append(item)

        page += 1
        time.sleep(sleep_sec)

    if page > max_pages:
        print(f"!! 안전장치: max_pages({max_pages}) 도달해서 강제 종료")

    return all_results


# =========================================================
# 2. 상세 페이지
# =========================================================

def fetch_detail_page(seq: int) -> str:
    resp = requests.get(DETAIL_URL, params={"seq": seq}, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding
    return resp.text


def parse_detail_page(html: str) -> dict:
    """상세페이지 HTML -> 필요한 필드 딕셔너리로 파싱

    상세페이지 구조(실제 View Source 기준):
    - 제목/모집상태: <div class="page-head"><span class="badge">모집중</span><h2 class="title">...</h2>
    - 핵심 정보 표: <table class="eval-kv"> 안에 tr.pair 마다 th/td 2쌍씩
      (활동기간, 모집기간, 활동분야, 봉사활동처, 활동주기, 봉사지역, 봉사장소, 봉사대상, 필요/신청 인원, 활동유형)
    - 자격조건 표: <table class="tbl-basic"> 안에 th/td 1쌍씩
      (봉사자연령, 봉사자성별, 자격요건, 사전교육)
    - 본문: <div class="board-content">
    """
    soup = BeautifulSoup(html, "html.parser")

    def _clean(text: str | None) -> str | None:
        """한 태그 안에 여러 줄 텍스트가 들어있을 때 개행/탭을 공백 하나로 정리.
        get_text(strip=True)는 양 끝만 자르고 내부 개행은 안 지워주기 때문에 필요."""
        if text is None:
            return None
        cleaned = re.sub(r"\s+", " ", text).strip()
        return cleaned or None

    title_tag = soup.select_one(".page-head .title")
    title = _clean(title_tag.get_text()) if title_tag else None

    status_tag = soup.select_one(".page-head .badge")
    status_text = _clean(status_tag.get_text()) if status_tag else None

    # eval-kv 표 파싱: 한 tr 안에 th,td,th,td 순서로 2쌍
    kv: dict[str, str] = {}
    for tr in soup.select("table.eval-kv tr.pair"):
        cells = tr.find_all(["th", "td"])
        for i in range(0, len(cells) - 1, 2):
            key = _clean(cells[i].get_text())
            val = _clean(cells[i + 1].get_text())
            if key:
                kv[key] = val

    # tbl-basic 표 파싱: 한 tr에 th 1개 + td 1개(헤더 tr은 th만 2개라 자동 스킵됨)
    qual: dict[str, str] = {}
    for tr in soup.select("table.tbl-basic tr"):
        th = tr.find("th")
        td = tr.find("td")
        if th is not None and td is not None:
            key = _clean(th.get_text())
            if key:
                qual[key] = _clean(td.get_text())

    content_tag = soup.select_one(".board-content")
    content = None
    if content_tag is not None:
        note = content_tag.select_one(".note-warn")
        if note is not None:
            note.extract()
        content = content_tag.get_text(separator="\n", strip=True)

    return {
        "title": title,
        "status_text": status_text,
        "vol_period": kv.get("활동기간"),          # "2026-07-21 ~ 2026-12-31" -> vol_date 컬럼에 그대로 저장
        "recruit_period": kv.get("모집기간"),
        "vol_field": kv.get("활동분야"),
        "vol_org": kv.get("봉사활동처"),             # -> vol_name 컬럼
        "vol_cycle": kv.get("활동주기"),
        "vol_region": kv.get("봉사지역"),            # "[경남] 경상남도 창원시" 형태
        "vol_place": kv.get("봉사장소"),
        "vol_target": kv.get("봉사대상"),            # -> target 컬럼
        "capacity_text": kv.get("필요/신청 인원"),
        "activity_type": kv.get("활동유형"),
        "age_req": qual.get("봉사자연령"),
        "gender_req": qual.get("봉사자성별"),
        "qual_req": qual.get("자격요건"),
        "edu_req": qual.get("사전교육"),
        "content": content,                         # -> vol_act 컬럼
    }


def parse_region_text(vol_region_text: str) -> tuple[str | None, str | None]:
    """"[경남] 경상남도 창원시" -> ("경상남도", "창원시") 로 분리

    시군구가 "고양시 일산동구"처럼 두 단어일 수도 있어서, 첫 단어(시/도 전체명)만 떼고
    나머지를 통째로 시군구명으로 취급.
    """
    if not vol_region_text:
        return None, None
    m = re.match(r"\[(.+?)\]\s*(.+)", vol_region_text.strip())
    if not m:
        return None, None
    rest = m.group(2).strip()
    parts = rest.split(maxsplit=1)
    sido_full = parts[0] if len(parts) >= 1 else None
    gugun = parts[1] if len(parts) >= 2 else None
    return sido_full, gugun


# =========================================================
# 2-1. 카카오 로컬 키워드 검색 (주소/좌표 보강 + 지역 매칭 정확도 향상)
# =========================================================

def _kakao_api_key() -> str | None:
    from backend.app.common.config import get_setting

    key = get_setting().KAKAO_REST_API_KEY
    if key is None:
        return None
    # SecretStr이면 실제 값 꺼내기, 이미 str이면 그대로
    return key.get_secret_value() if hasattr(key, "get_secret_value") else key


# ⭐ 신규: 쿼리 문자열 기준 카카오 검색 결과 캐시. 같은 기관이 공고를 여러 번 올리는 경우가
# 많아서(예: "청주종합사회복지관"), 같은 검색어를 스레드 여러 개가 매번 새로 요청하는 낭비를 줄임.
# 스레드풀에서 동시에 접근하므로 Lock으로 보호.
_kakao_cache: dict[str, dict | None] = {}
_kakao_cache_lock = threading.Lock()


def kakao_keyword_search(query: str) -> dict | None:
    """카카오 로컬 키워드 검색 - 장소명으로 주소/좌표 조회. 검색결과 1순위만 사용.
    키가 없거나 요청 실패하면 조용히 None 반환(전체 크롤링이 이거 때문에 멈추면 안 되니까).

    # ⭐ 수정: 쿼리 문자열 캐시 추가 + 타임아웃 10초 -> 5초 (실패 후보들 기다리는 시간 단축)."""
    with _kakao_cache_lock:
        if query in _kakao_cache:
            return _kakao_cache[query]

    api_key = _kakao_api_key()
    if not api_key or not query:
        return None
    headers = {"Authorization": f"KakaoAK {api_key}"}
    try:
        resp = requests.get(
            KAKAO_KEYWORD_URL, params={"query": query, "size": 1}, headers=headers, timeout=5
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  (카카오 검색 실패: {query!r} - {e})")
        with _kakao_cache_lock:
            _kakao_cache[query] = None
        return None
    docs = (resp.json() or {}).get("documents") or []
    result = docs[0] if docs else None
    with _kakao_cache_lock:
        _kakao_cache[query] = result
    return result


# 카카오는 시도명을 축약형으로 줌(예: "경남 창원시 진해구 ..."). 서울/부산/경기처럼
# 축약형이 정식명칭(SGIS 기준 city_name)의 접두어와 그대로 겹치는 건 LIKE 매칭으로 우연히
# 통과되지만, 경남/경북/충남/충북/전남은 정식명칭 중간 글자("상"/"청"/"라")가 빠지는 축약이라
# 접두어가 아니게 되고 LIKE 매칭이 깨짐 -> 명시적으로 정식명칭으로 치환해줘야 함.
SIDO_ABBR_TO_FULL = {
    "경남": "경상남도",
    "경북": "경상북도",
    "충남": "충청남도",
    "충북": "충청북도",
    "전남": "전라남도",
}


def parse_sido_gugun_from_address(address_name: str | None) -> tuple[str | None, str | None]:
    """카카오가 돌려준 실제 주소 -> (시도, 시군구) 분리.

    예: "경남 창원시 진해구 풍호동 1" -> ("경상남도", "창원시 진해구")   # 카카오 축약형 -> 정식명칭 치환
        "경기도 하남시 신장동 100" -> ("경기도", "하남시")
        "세종특별자치시 한솔동 123" -> ("세종특별자치시", "세종시")  # 세종은 구/군 레벨이 없음

    "일반구가 있는 시"(창원시/천안시/안양시/부천시/수원시/성남시/안산시/고양시/용인시/
    청주시/전주시/포항시)는 두 번째 토큰이 "...시"이고 세 번째 토큰이 "...구"면 둘을 합침.
    """
    if not address_name:
        return None, None
    tokens = address_name.split()
    if not tokens:
        return None, None

    sido = SIDO_ABBR_TO_FULL.get(tokens[0], tokens[0])
    if "세종" in sido:
        return sido, "세종시"  # region_seed.csv에 "세종시" 단일 행으로 들어있음

    if len(tokens) >= 3 and tokens[1].endswith("시") and tokens[2].endswith("구"):
        gugun = f"{tokens[1]} {tokens[2]}"
    elif len(tokens) >= 2:
        gugun = tokens[1]
    else:
        gugun = None
    return sido, gugun


# 봉사장소명 끝에 붙는 "실제 장소명이 아닌" 위치 설명 접미어들.
# 예: "거점 1호 키움센터 내" -> 카카오에 "...내"까지 붙여서 검색하면 안 찾아짐.
# "내"를 실제 장소명의 일부로 착각하기 쉬운데, "건물 안"이라는 뜻이라 지워야 검색됨.
# 공백 있이("광장 부근") 붙든 없이("광장부근") 붙든 둘 다 잡아야 해서 정규식으로 처리.
PLACE_NAME_SUFFIX_PATTERN = re.compile(
    r"\s*(내부|내|지하\d*층?|지하|옆|앞|인근|부근|근처|일대|\d+층)$"
)


def clean_place_name(name: str | None) -> str | None:
    """장소명 끝의 위치 설명 접미어를 반복적으로 제거.
    "OO센터 내" -> "OO센터", "OO복지관 1층" -> "OO복지관", "광장부근" -> "광장" """
    if not name:
        return None
    cleaned = name.strip()
    while True:
        new_cleaned = PLACE_NAME_SUFFIX_PATTERN.sub("", cleaned).strip()
        if new_cleaned == cleaned or not new_cleaned:
            break
        cleaned = new_cleaned
    return cleaned or None


def _kakao_candidates(place_name: str | None) -> list[str]:
    """clean_place_name 결과로부터 검색 후보 문자열 리스트 생성 (resolve_via_kakao / kakao_lookup_raw 공용)."""
    cleaned = clean_place_name(place_name)
    if not cleaned:
        return []
    candidates = [cleaned]
    no_space = cleaned.replace(" ", "")
    if no_space != cleaned:
        candidates.append(no_space)
    first_word = cleaned.split()[0] if " " in cleaned else None
    if first_word and len(first_word) >= 2:
        candidates.append(first_word)
    return candidates


def resolve_via_kakao(db, place_name: str | None) -> dict | None:
    """장소명으로 카카오 검색 -> 주소 파싱 -> region_id까지 매칭.
    성공하면 {"region_id", "address_name", "lat", "lng"} 반환, 실패하면 None.

    검색 시도 순서 (첫 성공에서 멈춤):
    1) 위치 설명 접미어("내"/"앞"/"N층" 등) 제거한 이름
    2) 공백까지 다 제거한 이름 (예: "거점 1호" -> "거점1호")
    3) 그래도 안 되면 첫 단어만 (예: "광안리해수욕장 광장" -> "광안리해수욕장")
       -> 뒤 단어가 부가 설명이고 앞 단어가 진짜 랜드마크인 경우가 많아서

    # ⭐ 참고: 병렬 크롤링(run_crawl)에서는 이 함수를 직접 쓰지 않고, 네트워크 부분만 떼어낸
    # kakao_lookup_raw() + DB 매칭만 하는 resolve_via_kakao_doc()로 나눠서 씀.
    # 이 함수 자체는 backfill_missing_fields() 등 기존 순차 처리 코드가 그대로 쓰므로 유지.
    """
    candidates = _kakao_candidates(place_name)
    if not candidates:
        return None

    doc = None
    for query in candidates:
        doc = kakao_keyword_search(query)
        if doc is not None:
            break
    if doc is None:
        return None

    return resolve_via_kakao_doc(db, doc, place_name or "")


def kakao_lookup_raw(place_name: str | None) -> dict | None:
    """장소명 후보들로 카카오 키워드 검색 '만' 수행 (DB 접근 없음, 네트워크만).
    스레드풀에서 병렬 실행하기 위해 resolve_via_kakao()에서 네트워크 부분만 떼어낸 버전."""
    candidates = _kakao_candidates(place_name)
    for query in candidates:
        doc = kakao_keyword_search(query)
        if doc is not None:
            return doc
    return None


def resolve_via_kakao_doc(db, doc: dict | None, place_name: str) -> dict | None:
    """kakao_lookup_raw() 등으로 이미 받아온 카카오 검색결과(doc)로 region_id까지 매칭
    (DB 접근만 함, 네트워크 요청 없음 -> 메인 스레드에서 순차 실행용)."""
    if doc is None:
        return None

    address_name = doc.get("road_address_name") or doc.get("address_name")
    sido, gugun = parse_sido_gugun_from_address(address_name)
    region_id = resolve_region_id(db, sido, gugun, extra_text=place_name or "")
    if region_id is None:
        return None

    try:
        lat = float(doc["y"]) if doc.get("y") else None  # 카카오: y=위도
        lng = float(doc["x"]) if doc.get("x") else None  # 카카오: x=경도
    except (TypeError, ValueError):
        lat = lng = None

    return {"region_id": region_id, "address_name": address_name, "lat": lat, "lng": lng}


# =========================================================
# 3. 종료일 파싱 (마이그레이션 없이 vol_date 문자열 그대로 활용)
# =========================================================

def parse_end_date(vol_date_text: str) -> date | None:
    """'2026-07-24 ~ 2026-12-31' 같은 문자열에서 종료일만 뽑아 date로 변환"""
    if not vol_date_text or "~" not in vol_date_text:
        return None
    end_str = vol_date_text.split("~")[-1].strip()
    try:
        return datetime.strptime(end_str, "%Y-%m-%d").date()
    except ValueError:
        return None


# =========================================================
# 4. DB 저장 (region_id 는 실제 프로젝트 모델/세션 import 필요)
# =========================================================

# 2026-07-01부로 광주광역시+전라남도가 "전남광주통합특별시"로 실제 통합됨(40년 만의 재통합,
# 인구 316만 규모). 구/시/군 명칭과 관할구역 자체는 그대로 유지됨(광주 5개구, 전남 시/군 그대로).
# SGIS 시드 데이터는 "2025년 6월" 기준이라 이 신설 통합시가 반영이 안 돼있어서, City 테이블에
# "전남광주통합특별시"라는 행 자체가 없음 -> City를 새로 안 만들고, 이 이름이 들어오면
# 기존 광주(city_id=24)+전남(city_id=36) 지역을 같이 검색하도록 예외처리.
MERGED_JEONNAM_GWANGJU_CITY_IDS = [24, 36]  # 광주광역시(24), 전라남도(36)
MERGED_JEONNAM_GWANGJU_ALIASES = ("전남광주", "광주전남")


def resolve_region_id(db, sido_full: str | None, gugun: str | None, extra_text: str = "") -> int | None:
    """시도/시군구 텍스트로 Region.region_id 조회.

    SGIS 행정구역 코드 기준으로 City/Region을 시드했다는 전제(city_name="경상남도" 식 정식명칭,
    region_name="창원시 진해구" 식 정식명칭)로 짜여있음.

    주의 1: 창원시/고양시/수원시처럼 일반구(구가 있는 시)는 SGIS에 "창원시 진해구"처럼
    구 단위로만 존재하고 "창원시"라는 행이 따로 없음. 근데 VMS 봉사지역 텍스트는
    "창원시"까지만 나오고 구 이름은 안 나와서, region_name이 gugun으로 "시작"하는
    행이 여러 개 걸림(의창구/성산구/마산합포구/마산회원구/진해구) -> 이 경우
    extra_text(봉사장소/제목 등)에 구 이름이 들어있는지 찾아서 좁히고, 그래도 못
    좁히면 매칭 포기(None, 스킵)함. 잘못된 구로 잘못 매칭시키는 것보단 스킵하는 게 안전.

    주의 2 (중요): region_name 매칭에 순수 LIKE '%gugun%'(부분일치)를 쓰면 안 됨.
    "서구"를 찾을 때 "달서구"(대구)/"강서구"(부산)까지 같이 걸리고, "양주시"를 찾을 때
    "남양주시"까지 같이 걸려서 엉뚱하게 모호한 매칭으로 처리되고 결국 스킵되는 버그가
    있었음. 그래서 "완전히 같음" 또는 "gugun + 공백으로 시작"(일반구 케이스)만 인정함.
    """
    from sqlalchemy import or_

    from backend.app.map.models import City, Region  # 순환 import 방지 위해 함수 내부에서 import

    if not sido_full or not gugun:
        return None

    region_name_filter = or_(Region.region_name == gugun, Region.region_name.like(f"{gugun} %"))

    if any(alias in sido_full for alias in MERGED_JEONNAM_GWANGJU_ALIASES):
        # "전남광주통합특별시" 계열 -> 광주+전남 지역을 같이 검색
        candidates = (
            db.query(Region)
            .filter(Region.city_id.in_(MERGED_JEONNAM_GWANGJU_CITY_IDS), region_name_filter)
            .all()
        )
    else:
        city = db.query(City).filter(City.city_name.like(f"%{sido_full}%")).first()
        if city is None:
            return None
        candidates = (
            db.query(Region)
            .filter(Region.city_id == city.city_id, region_name_filter)
            .all()
        )

    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0].region_id

    # 여러 개 매칭됨 (예: "창원시" -> 진해구/의창구/성산구/마산합포구/마산회원구)
    # region_name에서 gugun 부분을 뺀 나머지(구 이름)가 extra_text에 들어있는지로 좁히기
    matched = []
    for c in candidates:
        suffix = c.region_name.replace(gugun, "", 1).strip()
        core = re.sub(r"(구|군|시)$", "", suffix)  # "진해구" -> "진해"
        if core and core in extra_text:
            matched.append(c)
    if len(matched) == 1:
        return matched[0].region_id
    return None  # 여전히 모호함 -> 스킵 (로그로 확인 후 수동 처리)


def _trunc(text: str | None, max_len: int) -> str | None:
    """DB 컬럼 길이 초과로 INSERT가 깨지는 것 방지용 방어적 자르기."""
    if text is None:
        return None
    return text if len(text) <= max_len else text[:max_len]


def build_center_fields(
    db, list_item: dict, detail: dict,
    kakao_result: dict | None = None, kakao_precomputed: bool = False,
) -> dict | None:
    """목록+상세 파싱 결과를 VolunteerCenter 컬럼에 맞게 조립. region_id 못 찾으면 None 반환(스킵)

    지역/주소/좌표 확보 순서:
    1) 카카오 키워드 검색: 봉사장소명 -> 안되면 봉사활동처명으로 재시도
    2) 그래도 실패하면 VMS 봉사지역 텍스트 기반 파싱으로 폴백 (주소/좌표는 못 채움)

    kakao_precomputed=True면 kakao_result 인자를 그대로 사용하고 이 함수 안에서 카카오 검색을
    다시 하지 않음 (병렬 크롤링에서 스레드가 미리 계산해둔 결과 재사용용).
    """
    if not kakao_precomputed:
        kakao_result = (
            resolve_via_kakao(db, detail.get("vol_place"))
            or resolve_via_kakao(db, detail.get("vol_org"))
        )

    if kakao_result is not None:
        region_id = kakao_result["region_id"]
        vol_address = kakao_result["address_name"]
        latitude = kakao_result["lat"]
        longitude = kakao_result["lng"]
    else:
        sido_full, gugun = parse_region_text(detail.get("vol_region"))
        extra_text = " ".join(x for x in [detail.get("vol_place"), detail.get("title"), detail.get("vol_org")] if x)
        region_id = resolve_region_id(db, sido_full, gugun, extra_text=extra_text)
        if region_id is None:
            return None
        # 카카오 실패 시의 임시 주소 텍스트 (좌표는 없음)
        vol_address = " ".join(x for x in [detail.get("vol_region"), detail.get("vol_place")] if x)
        latitude = longitude = None

    qual_parts = [
        f"연령: {detail.get('age_req')}" if detail.get("age_req") else None,
        f"성별: {detail.get('gender_req')}" if detail.get("gender_req") else None,
        f"자격요건: {detail.get('qual_req')}" if detail.get("qual_req") else None,
        f"사전교육: {detail.get('edu_req')}" if detail.get("edu_req") else None,
    ]
    vol_qual = " / ".join(p for p in qual_parts if p)

    return {
        "region_id": region_id,
        "vol_name": _trunc(detail.get("vol_org") or list_item.get("org"), 200),
        "vol_title": _trunc(detail.get("title") or list_item.get("title"), 500),
        "vol_address": _trunc(vol_address, 255),
        "target": _trunc(detail.get("vol_target"), 200),
        "vms_url": _trunc(list_item.get("detail_url"), 500),
        "vol_qual": _trunc(vol_qual or None, 500),
        "vol_act": _trunc(detail.get("content"), 2000),
        "vol_date": _trunc(detail.get("vol_period"), 1000),
        "latitude": latitude,
        "longitude": longitude,
    }


def upsert_volunteer_center(db, seq: int, fields: dict):
    """center_id=seq 를 그대로 PK로 사용해서 insert/update"""
    from backend.app.map.models import VolunteerCenter

    center = db.get(VolunteerCenter, seq)
    if center is None:
        center = VolunteerCenter(center_id=seq, **fields)
        db.add(center)
    else:
        for k, v in fields.items():
            setattr(center, k, v)
    db.commit()


def delete_expired_centers(db):
    """vol_date 문자열의 종료일이 오늘보다 이전인 공고 전부 삭제"""
    from backend.app.map.models import VolunteerCenter

    centers = db.query(VolunteerCenter).all()
    today = date.today()
    expired_ids = [
        c.center_id for c in centers
        if (end := parse_end_date(c.vol_date)) is not None and end < today
    ]
    if expired_ids:
        db.query(VolunteerCenter).filter(VolunteerCenter.center_id.in_(expired_ids)).delete(
            synchronize_session=False
        )
        db.commit()
    print(f"마감 공고 {len(expired_ids)}건 삭제")


# =========================================================
# 5. 전체 파이프라인
# =========================================================

def fetch_item_bundle(item: dict, detail_sleep_sec: float = 0.1) -> dict:
    """스레드풀에서 실행되는 작업 단위. 네트워크 요청(상세페이지 + 카카오 검색)만 하고
    DB는 절대 건드리지 않음(SQLAlchemy Session은 스레드 세이프하지 않으므로)."""
    seq = item["seq"]
    try:
        html = fetch_detail_page(seq)
    except requests.RequestException as e:
        return {"item": item, "detail": None, "kakao_doc": None, "error": str(e)}

    detail = parse_detail_page(html)
    kakao_doc = kakao_lookup_raw(detail.get("vol_place")) or kakao_lookup_raw(detail.get("vol_org"))

    if detail_sleep_sec:
        time.sleep(detail_sleep_sec)  # 서버 부담 줄이기용 최소한의 딜레이 (스레드별로 걸림)

    return {"item": item, "detail": detail, "kakao_doc": kakao_doc, "error": None}


def run_crawl(db, days_window: int = 30, sleep_sec: float = 0.5, max_pages: int = 500,
              refetch_existing: bool = False, max_workers: int = 16, detail_sleep_sec: float = 0.1):
    """전체 파이프라인.

    refetch_existing=False(기본값)면 이미 DB에 저장돼 있는 seq는 상세페이지를 다시 안 가져오고
    건너뜀. 한번 등록된 공고 내용은 거의 안 바뀌고(마감은 delete_expired_centers가 별도 처리),
    이렇게 안 하면 5000건 넘는 데이터를 매번 전부 다시 상세크롤링하게 돼서 매일 도는 배치로는
    너무 느림. 최초 1회만 전체를 다 긁고, 그 다음부터는 그날 새로 올라온 것만 상세크롤링하면
    되므로 훨씬 빨라짐.

    # ⭐ 수정: max_workers 기본값 8 -> 16. 카카오 검색 캐시(_kakao_cache) + 타임아웃 단축(5초)이
    # 같이 들어가서 동시처리를 늘려도 예전만큼 오래 대기하는 워커가 줄어들 것으로 기대.
    """
    print("=== 1) 마감 공고 정리 ===")
    delete_expired_centers(db)

    print("\n=== 2) 목록 수집 ===")
    list_items = crawl_list_all(days_window=days_window, sleep_sec=sleep_sec, max_pages=max_pages)
    print(f"목록 총 {len(list_items)}건")

    if not refetch_existing:
        from backend.app.map.models import VolunteerCenter
        existing_ids = {row[0] for row in db.query(VolunteerCenter.center_id).all()}
        before = len(list_items)
        list_items = [item for item in list_items if item["seq"] not in existing_ids]
        print(f"이미 저장된 {before - len(list_items)}건은 상세크롤링 건너뜀 (남은 {len(list_items)}건만 진행)")

    total = len(list_items)
    print(f"\n=== 3) 상세 수집(병렬 {max_workers}개) + DB 저장(순차) ===")
    saved, skipped = 0, 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(fetch_item_bundle, item, detail_sleep_sec): item
            for item in list_items
        }
        for done_count, future in enumerate(as_completed(futures), start=1):
            result = future.result()
            item = result["item"]
            seq = item["seq"]

            if result["error"] is not None:
                skipped += 1
                print(f"[{done_count}/{total}] seq={seq} 요청 실패 -> 스킵 ({result['error']})")
                continue

            detail = result["detail"]
            place_name = detail.get("vol_place") or detail.get("vol_org") or ""
            kakao_result = resolve_via_kakao_doc(db, result["kakao_doc"], place_name)

            fields = build_center_fields(db, item, detail, kakao_result=kakao_result, kakao_precomputed=True)
            if fields is None:
                skipped += 1
                print(f"[{done_count}/{total}] seq={seq} region 매칭 실패 -> 스킵 (봉사지역: {detail.get('vol_region')})")
            else:
                upsert_volunteer_center(db, seq, fields)
                saved += 1

    print(f"\n완료: 저장 {saved}건, 스킵 {skipped}건")


def backfill_missing_fields(db, sleep_sec: float = 0.5):
    """이미 저장된 공고 중 vol_title이 비어있거나 latitude가 비어있는 것만 골라
    다시 상세크롤링+카카오 검색해서 채워넣는 일회성 백필 스크립트.

    실행 예:
        python -c "from backend.app.common.database import SessionLocal; from backend.app.map.crawler.vms_crawler import backfill_missing_fields; db = SessionLocal(); backfill_missing_fields(db); db.close()"
    """
    from backend.app.map.models import VolunteerCenter

    targets = (
        db.query(VolunteerCenter)
        .filter((VolunteerCenter.vol_title.is_(None)) | (VolunteerCenter.latitude.is_(None)))
        .all()
    )
    print(f"제목/위경도 없는 기존 공고 {len(targets)}건 백필 시작")

    updated, skipped = 0, 0
    for i, center in enumerate(targets, start=1):
        seq = center.center_id
        try:
            html = fetch_detail_page(seq)
        except requests.RequestException as e:
            skipped += 1
            print(f"[{i}/{len(targets)}] seq={seq} 요청 실패 -> 스킵 ({e})")
            time.sleep(sleep_sec)
            continue

        detail = parse_detail_page(html)
        center.vol_title = detail.get("title")  # 제목은 카카오 성패와 무관하게 항상 채움

        kakao_result = (
            resolve_via_kakao(db, detail.get("vol_place"))
            or resolve_via_kakao(db, detail.get("vol_org"))
        )
        if kakao_result is None:
            skipped += 1
            print(f"[{i}/{len(targets)}] seq={seq} 카카오 검색 실패 -> 좌표는 못 채움(제목만 채움)")
        else:
            center.region_id = kakao_result["region_id"]
            center.vol_address = kakao_result["address_name"]
            center.latitude = kakao_result["lat"]
            center.longitude = kakao_result["lng"]
            updated += 1
        db.commit()
        time.sleep(sleep_sec)

    print(f"\n백필 완료: 좌표까지 채움 {updated}건, 제목만 채움/좌표 실패 {skipped}건")


if __name__ == "__main__":
    from backend.app.common.database import SessionLocal

    db = SessionLocal()
    try:
        run_crawl(db)
    finally:
        db.close()