"""Fetch Samsung Electronics annual financial statements from OpenDART.

The fnlttSinglAcntAll endpoint documents annual financial data from 2015 onward.
Years 2010-2014 require a separate historical XBRL/report-processing pipeline.
"""
from __future__ import annotations

import os
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUTPUT = DATA_DIR / "samsung_annual_financials.csv"
API_URL = "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json"
CORP_CODE = "00126380"  # Samsung Electronics
REPORT_CODE = "11011"  # Annual business report
FS_DIV = "CFS"  # Consolidated statements
START_YEAR = 2015


def fetch_year(session: requests.Session, api_key: str, year: int) -> list[dict]:
    params = {
        "crtfc_key": api_key,
        "corp_code": CORP_CODE,
        "bsns_year": str(year),
        "reprt_code": REPORT_CODE,
        "fs_div": FS_DIV,
    }
    response = session.get(API_URL, params=params, timeout=40)
    response.raise_for_status()
    payload = response.json()
    status = payload.get("status")

    if status == "000":
        rows = payload.get("list", [])
        fetched_at = datetime.now().astimezone().isoformat(timespec="seconds")
        for row in rows:
            row["requested_year"] = year
            row["corp_code"] = CORP_CODE
            row["corp_name"] = "삼성전자"
            row["report_code"] = REPORT_CODE
            row["fs_div_requested"] = FS_DIV
            row["fetched_at"] = fetched_at
        return rows

    if status == "013":
        print(f"[INFO] {year}: API에 해당 연도 자료가 없습니다.")
        return []

    message = payload.get("message", "Unknown OpenDART error")
    raise RuntimeError(f"{year}년 OpenDART 오류 ({status}): {message}")


def main() -> int:
    api_key = os.environ.get("DART_API_KEY", "").strip()
    if not api_key:
        print("ERROR: DART_API_KEY 환경변수가 없습니다. GitHub Secret 이름을 확인하세요.", file=sys.stderr)
        return 2

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    end_year = datetime.now().year - 1
    all_rows: list[dict] = []

    with requests.Session() as session:
        for year in range(START_YEAR, end_year + 1):
            print(f"[INFO] {year}년 연간 연결재무제표 조회 중...")
            try:
                all_rows.extend(fetch_year(session, api_key, year))
            except Exception as exc:
                print(f"[ERROR] {exc}", file=sys.stderr)
                return 1
            time.sleep(0.25)

    if not all_rows:
        print("ERROR: 수집된 데이터가 없습니다. 인증키, API 사용 권한, 응답 상태를 확인하세요.", file=sys.stderr)
        return 1

    fresh = pd.DataFrame(all_rows)
    if OUTPUT.exists():
        try:
            previous = pd.read_csv(OUTPUT, dtype=str)
            combined = pd.concat([previous, fresh.astype(str)], ignore_index=True)
        except (pd.errors.EmptyDataError, pd.errors.ParserError):
            combined = fresh.astype(str)
    else:
        combined = fresh.astype(str)

    key_cols = [
        col for col in [
            "requested_year", "fs_div", "sj_div", "account_id",
            "account_nm", "thstrm_nm", "currency"
        ] if col in combined.columns
    ]
    if key_cols:
        combined = combined.drop_duplicates(subset=key_cols, keep="last")
    sort_cols = [c for c in ["requested_year", "sj_div", "account_nm"] if c in combined.columns]
    if sort_cols:
        combined = combined.sort_values(sort_cols)
    combined.to_csv(OUTPUT, index=False, encoding="utf-8-sig")

    print(f"[OK] CSV 저장 완료: {OUTPUT.relative_to(ROOT)}")
    print(f"[OK] 전체 행 수: {len(combined):,}")
    print("[NOTE] OpenDART 전체 재무제표 API는 2015년 이후 자료를 대상으로 합니다. 2010~2014년은 별도 과거 XBRL 처리 단계가 필요합니다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
