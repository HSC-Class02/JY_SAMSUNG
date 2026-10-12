from __future__ import annotations
import os, sys, time
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "financials.csv"
API = "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json"
CORP_CODE = "00126380"
REPORTS = [("11013", "quarterly", "1분기"), ("11012", "half_year", "반기"), ("11014", "third_quarter", "3분기"), ("11011", "annual", "사업보고서")]
START_YEAR = 2015  # OpenDART periodic financial API coverage begins in 2015.

ALIASES = {
 "revenue":["매출액","수익(매출액)","영업수익"], "gross_profit":["매출총이익","매출총손익"],
 "operating_income":["영업이익","영업이익(손실)"], "pretax_income":["법인세비용차감전순이익","법인세비용차감전순손익"],
 "net_income":["당기순이익","당기순이익(손실)","분기순이익","반기순이익"],
 "total_assets":["자산총계"], "cash":["현금및현금성자산"], "receivables":["매출채권"], "inventory":["재고자산"],
 "ppe":["유형자산"], "total_liabilities":["부채총계"], "current_assets":["유동자산"], "current_liabilities":["유동부채"],
 "short_debt":["단기차입금","유동성장기부채"], "long_debt":["장기차입금","사채"], "equity":["자본총계"],
 "interest_expense":["이자비용"], "depreciation":["감가상각비"], "amortization":["무형자산상각비"],
 "cfo":["영업활동현금흐름"], "cfi":["투자활동현금흐름"], "cff":["재무활동현금흐름"],
 "capex_ppe":["유형자산의 취득","유형자산 취득"], "capex_intangible":["무형자산의 취득","무형자산 취득"]
}
PERIOD_KEYS = {"revenue","gross_profit","operating_income","pretax_income","net_income","interest_expense","depreciation","amortization","cfo","cfi","cff","capex_ppe","capex_intangible"}

def num(value):
    if value is None: return None
    s=str(value).strip().replace(",","")
    if not s or s in {"-","—"}: return None
    try: return float(s)
    except ValueError: return None

def fetch(session, key, year, code):
    params={"crtfc_key":key,"corp_code":CORP_CODE,"bsns_year":str(year),"reprt_code":code,"fs_div":"CFS"}
    response=session.get(API,params=params,timeout=45)
    response.raise_for_status()
    obj=response.json()
    if obj.get("status")=="000": return obj.get("list",[])
    if obj.get("status")=="013": return []
    # Retry separate statements when consolidated statements are not available.
    params["fs_div"]="OFS"
    response=session.get(API,params=params,timeout=45)
    response.raise_for_status()
    obj=response.json()
    if obj.get("status")=="000": return obj.get("list",[])
    if obj.get("status")=="013": return []
    raise RuntimeError(f"OpenDART {year}/{code}: {obj.get('status')} {obj.get('message')}")

def account_values(rows):
    out={}
    for key, aliases in ALIASES.items():
        for row in rows:
            if str(row.get("account_nm","")).strip() in aliases:
                out[key]=num(row.get("thstrm_amount"))
                if key in PERIOD_KEYS:
                    out[key+"_ytd"]=num(row.get("thstrm_add_amount"))
                out["currency"]=row.get("currency") or "KRW"
                out["fs_div"]=row.get("fs_div","")
                break
    return out

def derive(row):
    def v(k): return row.get(k)
    def pct(a,b): return (v(a)/v(b)*100) if v(a) is not None and v(b) not in (None,0) else None
    row["gross_margin_pct"]=pct("gross_profit","revenue")
    row["operating_margin_pct"]=pct("operating_income","revenue")
    row["net_margin_pct"]=pct("net_income","revenue")
    row["current_ratio_pct"]=pct("current_assets","current_liabilities")
    row["debt_to_equity_pct"]=pct("total_liabilities","equity")
    row["debt_ratio_pct"]=pct("total_liabilities","total_assets")
    row["cfo_to_net_income_pct"]=pct("cfo","net_income")
    row["ebitda_approx"]=sum(x for x in [v("operating_income"),v("depreciation"),v("amortization")] if x is not None) if any(v(x) is not None for x in ["operating_income","depreciation","amortization"]) else None
    caps=[abs(v(x) or 0) for x in ["capex_ppe","capex_intangible"]]
    row["capex_total"]=sum(caps) if any(v(x) is not None for x in ["capex_ppe","capex_intangible"]) else None
    row["fcf_approx"]=v("cfo")-row["capex_total"] if v("cfo") is not None and row["capex_total"] is not None else None
    row["net_debt_approx"]=(v("short_debt") or 0)+(v("long_debt") or 0)-(v("cash") or 0) if any(v(x) is not None for x in ["short_debt","long_debt","cash"]) else None
    row["interest_coverage"]=v("operating_income")/abs(v("interest_expense")) if v("operating_income") is not None and v("interest_expense") not in (None,0) else None
    return row

def main():
    key=os.getenv("DART_API_KEY","").strip()
    if not key:
        print("DART_API_KEY Secret/environment variable is missing.",file=sys.stderr); return 2
    now=datetime.now(timezone.utc)
    last_year=now.year if now.month>=4 else now.year-1
    output=[]
    with requests.Session() as session:
        for year in range(START_YEAR,last_year+1):
            for code,category,label in REPORTS:
                try: rows=fetch(session,key,year,code)
                except Exception as exc:
                    print(f"[WARN] {year} {label}: {exc}",file=sys.stderr); continue
                if not rows:
                    time.sleep(.12); continue
                record={"company":"삼성전자","corp_code":CORP_CODE,"fiscal_year":year,"report_code":code,"report_type":category,"report_label":label,"period_num":{"11013":1,"11012":2,"11014":3,"11011":4}[code],"period_end":rows[0].get("thstrm_dt",""),"receipt_no":rows[0].get("rcept_no",""),"fetched_at":now.isoformat()}
                record.update(account_values(rows))
                record["filing_url"]="https://dart.fss.or.kr/dsaf001/main.do?rcpNo="+record["receipt_no"] if record["receipt_no"] else ""
                output.append(record)
                time.sleep(.15)
    if not output:
        print("No financial data collected. Check the DART_API_KEY, API quota and Actions logs.",file=sys.stderr); return 1
    df=pd.DataFrame(output)
    # For interim income/cash-flow items, use cumulative-to-date values and subtract the prior filing to estimate standalone period values.
    for year, grp in df.groupby("fiscal_year"):
        grp=grp.sort_values("period_num")
        previous={}
        for idx,r in grp.iterrows():
            for keycol in PERIOD_KEYS:
                ytd=r.get(keycol+"_ytd")
                if pd.isna(ytd): continue
                df.loc[idx,keycol]=ytd-previous[keycol] if keycol in previous and r["report_code"] in {"11012","11014","11011"} else ytd
                previous[keycol]=ytd
    df=df.drop_duplicates(subset=["fiscal_year","report_code"],keep="last").sort_values(["fiscal_year","period_num"])
    df=pd.DataFrame([derive(r.to_dict()) for _,r in df.iterrows()])
    OUT.parent.mkdir(parents=True,exist_ok=True)
    df.to_csv(OUT,index=False,encoding="utf-8-sig")
    print(f"Saved {len(df)} report rows to {OUT.relative_to(ROOT)}")
    print("Coverage note: OpenDART periodic financial API starts in 2015. 2010-2014 requires a separately validated historical XBRL import.")
    return 0

if __name__=="__main__": raise SystemExit(main())
