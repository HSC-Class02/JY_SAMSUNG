#!/usr/bin/env python3
"""Validate and merge manually normalized historical DART rows (2010-2014).

The OpenDART periodic financial API does not cover these years. This script does
not scrape or fabricate historical values; it merges a CSV that has already
been transcribed/normalized and checked against the official filing/XBRL source.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / "data" / "financials.csv"
REQUIRED = {
    "company", "corp_code", "fiscal_year", "report_code", "report_type",
    "report_label", "period_num", "period_end", "receipt_no", "revenue",
    "operating_income", "net_income", "total_assets", "total_liabilities",
    "equity", "filing_url",
}
NUMERIC = [
    "fiscal_year", "period_num", "revenue", "gross_profit", "operating_income",
    "pretax_income", "net_income", "total_assets", "cash", "receivables",
    "inventory", "ppe", "total_liabilities", "current_assets",
    "current_liabilities", "short_debt", "long_debt", "equity", "interest_expense",
    "depreciation", "amortization", "cfo", "cfi", "cff", "capex_ppe",
    "capex_intangible",
]
PERIODS = {"11011": ("annual", "사업보고서", 4),
           "11012": ("half_year", "반기", 2),
           "11013": ("quarterly", "1분기", 1),
           "11014": ("third_quarter", "3분기", 3)}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path, help="Verified, normalized historical CSV")
    parser.add_argument("--output", type=Path, default=CURRENT, help="Output CSV (default: data/financials.csv)")
    args = parser.parse_args()
    if not args.csv.is_file():
        parser.error(f"Input file not found: {args.csv}")
    incoming = pd.read_csv(args.csv, dtype={"corp_code": str, "report_code": str}, encoding="utf-8-sig")
    missing = sorted(REQUIRED - set(incoming.columns))
    if missing:
        print("Missing required columns: " + ", ".join(missing), file=sys.stderr)
        return 2
    incoming["fiscal_year"] = pd.to_numeric(incoming["fiscal_year"], errors="coerce")
    if incoming["fiscal_year"].isna().any() or not incoming["fiscal_year"].between(2010, 2014).all():
        print("Historical import accepts only fiscal years 2010-2014.", file=sys.stderr)
        return 2
    if not (incoming["corp_code"].astype(str).str.zfill(8) == "00126380").all():
        print("All rows must be Samsung Electronics (corp_code 00126380).", file=sys.stderr)
        return 2
    unknown = sorted(set(incoming["report_code"].astype(str)) - set(PERIODS))
    if unknown:
        print("Unsupported report_code(s): " + ", ".join(unknown), file=sys.stderr)
        return 2
    incoming["corp_code"] = incoming["corp_code"].astype(str).str.zfill(8)
    for col in NUMERIC:
        if col in incoming:
            incoming[col] = pd.to_numeric(incoming[col], errors="coerce")
    if incoming.duplicated(["fiscal_year", "report_code"]).any():
        print("Duplicate fiscal_year/report_code rows in input; resolve before importing.", file=sys.stderr)
        return 2
    for code, (kind, label, number) in PERIODS.items():
        mask = incoming["report_code"].astype(str) == code
        incoming.loc[mask, "report_type"] = kind
        incoming.loc[mask, "report_label"] = label
        incoming.loc[mask, "period_num"] = number
    incoming["company"] = "삼성전자"
    incoming["filing_url"] = incoming.apply(
        lambda r: f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={r['receipt_no']}"
        if pd.notna(r.get("receipt_no")) and str(r.get("receipt_no")).strip() else r.get("filing_url", ""), axis=1)
    if args.output.exists():
        current = pd.read_csv(args.output, dtype={"corp_code": str, "report_code": str}, encoding="utf-8-sig")
        merged = pd.concat([current, incoming], ignore_index=True, sort=False)
    else:
        merged = incoming
    merged["fiscal_year"] = pd.to_numeric(merged["fiscal_year"], errors="coerce")
    merged["report_code"] = merged["report_code"].astype(str)
    merged = merged.drop_duplicates(["fiscal_year", "report_code"], keep="last")
    merged = merged.sort_values(["fiscal_year", "period_num"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(args.output, index=False, encoding="utf-8-sig")
    print(f"Merged {len(incoming)} verified historical rows; output now contains {len(merged)} rows: {args.output}")
    print("Verify imported values against the cited DART filing before publishing.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
