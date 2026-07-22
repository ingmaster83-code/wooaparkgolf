#!/usr/bin/env python3
"""
parse_parkgolf.py - 13개 지자체별 파크골프장 원본 CSV를 하나의 _rawdata/parkgolf.json으로 통합

사용법:
  python scripts/parse_parkgolf.py
"""
import sys, csv, json, re
from pathlib import Path
from io import StringIO

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).parent.parent
RAW = ROOT / "raw"
OUT = ROOT / "_rawdata" / "parkgolf.json"

GU_PATTERN = re.compile(r"[가-힣]+(?:시|군|구)(?=\s|$)")

PROVINCE_NAMES = {
    "서울특별시", "부산광역시", "대구광역시", "인천광역시", "광주광역시", "대전광역시",
    "울산광역시", "세종특별자치시", "경기도", "강원특별자치도", "강원도",
    "충청북도", "충청남도", "전북특별자치도", "전라북도", "전라남도",
    "경상북도", "경상남도", "제주특별자치도",
}


def read_csv_rows(path: Path):
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "cp949"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise RuntimeError(f"인코딩 실패: {path.name}")
    reader = csv.DictReader(StringIO(text))
    return [row for row in reader if any((v or "").strip() for v in row.values())]


def norm_key(k: str) -> str:
    return re.sub(r"\s+", "", k or "")


def get(row: dict, *keys, default=""):
    normed = {norm_key(k): v for k, v in row.items()}
    for k in keys:
        v = normed.get(norm_key(k))
        if v and str(v).strip():
            return str(v).strip()
    return default


def extract_sigungu_from_text(text: str) -> str:
    if not text:
        return ""
    for m in GU_PATTERN.finditer(text):
        candidate = m.group(0)
        if candidate not in PROVINCE_NAMES:
            return candidate
    return ""


def normalize_sigungu(v: str) -> str:
    v = (v or "").strip()
    if not v:
        return ""
    if v[-1] not in ("시", "군", "구"):
        v = v + "구"
    return v


def to_float(v):
    try:
        return float(str(v).strip())
    except (ValueError, TypeError):
        return None


# 파일별 설정: province(도) 고정값, sigungu 소스(컬럼명 or 'address'/'fixed:xxx')
FILE_CONFIGS = [
    {
        "file": "가평군시설관리공단_가평파크골프장_20260721.csv",
        "province": "경기도", "sigungu": "fixed:가평군",
        "name": ["파크골프장명"], "address": ["소재지 지번주소"],
        "holes": ["홀수"], "area": ["면적"], "tel": ["전화번호"], "manager": ["관리기관명"],
        "lat": ["위도"], "lng": ["경도"], "fee": ["이용요금"],
        "resv_method": ["예약방식"], "resv_url": ["예약페이지 링크"],
    },
    {
        "file": "강원특별자치도_파크골프장 현황_20250307.csv",
        "province": "강원특별자치도", "sigungu": ["시군"],
        "name": ["시설명"], "address": ["주소"],
        "holes": ["홀 수"], "area": ["규모(미터제곱)"], "tel": ["연락처"],
    },
    {
        "file": "경상남도 거창군_파크골프장_20250801.csv",
        "province": "경상남도", "sigungu": "fixed:거창군",
        "name": ["시설명"], "address": ["소재지도로명주소", "소재지지번주소"],
        "holes": ["규모(홀)"], "area": ["면적(제곱미터)"], "tel": ["전화번호"], "manager": ["관리기관"],
        "lat": ["위도"], "lng": ["경도"],
    },
    {
        "file": "경상북도_파크골프장 현황_20250310.csv",
        "province": "경상북도", "sigungu": ["시군"],
        "name": ["파크골프장명"], "address": ["주소"],
        "holes": ["홀수"], "manager": ["운영기관"],
    },
    {
        "file": "대구광역시 북구_파크골프장_20250801.csv",
        "province": "대구광역시", "sigungu": "fixed:북구",
        "name": ["시 설 명"], "address": ["지번 주소"],
        "holes": ["홀수"], "area": ["규 모"], "manager": ["운영기관"], "tel": ["운영기관 연락처"],
        "lat": ["위도"], "lng": ["경도"],
    },
    {
        "file": "대구광역시_파크골프장_20250305.csv",
        "province": "대구광역시", "sigungu": "address",
        "name": ["파크골프장명"], "address": ["파크골프장 주소"],
        "holes": ["파크골프장 홀수"], "area": ["파크골프장 규모(제곱미터)"], "manager": ["운영기관"], "tel": ["연락처"],
    },
    {
        "file": "동작구시설관리공단_파크골프장 표준데이터_20260720.csv",
        "province": "서울특별시", "sigungu": "fixed:동작구",
        "name": ["업장명"], "address": ["위치"],
        "holes": ["홀"], "area": ["면적"], "tel": ["전화"], "fee": ["이용요금"],
        "resv_method": ["예약방법"],
    },
    {
        "file": "서울특별시_파크골프장 현황_20230508.csv",
        "province": "서울특별시", "sigungu": "manager_or_address",
        "name": ["시 설 명"], "address": ["위 치"],
        "holes": ["홀수"], "area": ["규 모"], "manager": ["운영기관"], "open_date": ["개장일"],
    },
    {
        "file": "세종특별자치시_파크골프장 현황_20250314.csv",
        "province": "세종특별자치시", "sigungu": "fixed:",
        "name": ["시설명"], "address": ["주소"],
        "holes": ["홀수"], "area": ["규모(제곱미터)"], "manager": ["운영기관"], "tel": ["연락처"],
    },
    {
        "file": "인천광역시_파크골프장 현황_20250310.csv",
        "province": "인천광역시", "sigungu": "address",
        "name": ["시설명"], "address": ["위치"],
        "holes": ["홀수"], "area": ["규모"], "manager": ["운영기관"], "tel": ["연락처"], "open_date": ["개장"],
    },
    {
        "file": "전남광주통합특별시_파크골프장 현황_20250311.csv",
        "province": "광주광역시", "sigungu": "address",
        "name": ["시설명"], "address": ["위치"],
        "holes": ["홀수"], "area": ["규모"], "manager": ["운영기관"], "tel": ["연락처"],
    },
    {
        "file": "전남광주통합특별시_파크골프장현황_20260226.csv",
        "province": "전라남도", "sigungu": ["시군"],
        "name": ["파크골프장명"], "address": ["주소"],
        "holes": ["홀수"],
    },
    {
        "file": "전북특별자치도_파크골프장 현황_20250228.csv",
        "province": "전북특별자치도", "sigungu": ["시군"],
        "name": ["시설명"], "address": ["주소"],
        "holes": ["홀수"], "area": ["면적(제곱미터)"], "open_date": ["설치연도(개장연도)"],
    },
]


SEOUL_GU = ["종로구","중구","용산구","성동구","광진구","동대문구","중랑구","성북구","강북구",
            "도봉구","노원구","은평구","서대문구","마포구","양천구","강서구","구로구","금천구",
            "영등포구","동작구","관악구","서초구","강남구","송파구","강동구"]


def match_seoul_gu(text: str) -> str:
    if not text:
        return ""
    for gu in SEOUL_GU:
        if gu in text or gu[:-1] in text:
            return gu
    return ""


def build_record(row, cfg, idx):
    name = get(row, *cfg["name"])
    if not name:
        return None
    address = get(row, *cfg.get("address", []))
    manager = get(row, *cfg.get("manager", []))

    sg_cfg = cfg["sigungu"]
    if isinstance(sg_cfg, list):
        sigungu = get(row, *sg_cfg)
    elif sg_cfg == "address":
        sigungu = extract_sigungu_from_text(address)
    elif sg_cfg == "manager_or_address":
        sigungu = match_seoul_gu(manager) or match_seoul_gu(address)
    elif sg_cfg.startswith("fixed:"):
        sigungu = sg_cfg.split(":", 1)[1]
    else:
        sigungu = ""

    rec = {
        "id": idx,
        "name": name,
        "doNm": cfg["province"],
        "sigunguNm": sigungu,
        "address": address,
        "holes": get(row, *cfg.get("holes", [])),
        "area": get(row, *cfg.get("area", [])),
        "tel": get(row, *cfg.get("tel", [])),
        "manager": get(row, *cfg.get("manager", [])),
        "openDate": get(row, *cfg.get("open_date", [])),
        "fee": get(row, *cfg.get("fee", [])),
        "reservationMethod": get(row, *cfg.get("resv_method", [])),
        "reservationUrl": get(row, *cfg.get("resv_url", [])),
        "lat": to_float(get(row, *cfg.get("lat", []))) if cfg.get("lat") else None,
        "lng": to_float(get(row, *cfg.get("lng", []))) if cfg.get("lng") else None,
        "source": cfg["file"],
    }
    return rec


def slugify(name: str, idx: int) -> str:
    s = re.sub(r"[^\w가-힣]+", "-", name).strip("-")
    return f"{idx}-{s}"


def main():
    all_records = []
    idx = 0
    for cfg in FILE_CONFIGS:
        path = RAW / cfg["file"]
        if not path.exists():
            print(f"  [건너뜀] 파일 없음: {cfg['file']}")
            continue
        rows = read_csv_rows(path)
        count = 0
        for row in rows:
            rec = build_record(row, cfg, idx)
            if rec:
                all_records.append(rec)
                idx += 1
                count += 1
        print(f"  {cfg['file']}: {count}건")

    seen_slugs = set()
    for i, rec in enumerate(all_records):
        slug = slugify(rec["name"], i)
        if slug in seen_slugs:
            slug = f"{slug}-{i}"
        seen_slugs.add(slug)
        rec["slug"] = slug

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(all_records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n총 {len(all_records)}건 -> {OUT}")

    by_do = {}
    for r in all_records:
        by_do[r["doNm"]] = by_do.get(r["doNm"], 0) + 1
    for do, cnt in sorted(by_do.items()):
        print(f"  {do}: {cnt}개")


if __name__ == "__main__":
    main()
