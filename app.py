from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data" / "samsung_annual_financials.csv"

st.set_page_config(page_title="삼성전자 DART 재무분석", page_icon="📊", layout="wide")
st.title("삼성전자 DART 재무분석")
st.caption("OpenDART 사업보고서 기반 · 연결재무제표(CFS) · 연간 보고서")

if not DATA_FILE.exists():
    st.warning("아직 수집 데이터가 없습니다. GitHub Actions에서 Monthly DART Update를 실행하거나 fetch_financials.py를 실행하세요.")
    st.info("참고: OpenDART 전체 재무제표 API는 2015년 이후 자료를 제공합니다. 2010~2014년은 별도 과거 XBRL 처리 단계가 필요합니다.")
    st.stop()

try:
    df = pd.read_csv(DATA_FILE, dtype=str, encoding="utf-8-sig")
except Exception as exc:
    st.error(f"CSV를 읽지 못했습니다: {exc}")
    st.stop()

if df.empty:
    st.warning("CSV가 비어 있습니다. 데이터 수집 워크플로를 확인하세요.")
    st.stop()

year_col = "requested_year"
if year_col in df.columns:
    years = sorted(df[year_col].dropna().astype(str).unique())
    st.metric("수집 연도", f"{len(years)}개")
    st.caption(f"데이터 범위: {years[0]}–{years[-1]}" if years else "연도 정보 없음")

preferred = {
    "매출액": ["매출액", "수익(매출액)", "영업수익"],
    "영업이익": ["영업이익", "영업이익(손실)"],
    "당기순이익": ["당기순이익", "당기순이익(손실)", "연결당기순이익"],
    "자산총계": ["자산총계"],
    "부채총계": ["부채총계"],
    "자본총계": ["자본총계"],
}

account_col = "account_nm"
amount_col = "thstrm_amount"
if account_col not in df.columns or amount_col not in df.columns:
    st.error("CSV에 예상 계정명(account_nm) 또는 당기 금액(thstrm_amount) 열이 없습니다.")
    st.dataframe(df.head(20), use_container_width=True)
    st.stop()

df[amount_col] = pd.to_numeric(
    df[amount_col].astype(str).str.replace(",", "", regex=False).str.replace(" ", "", regex=False),
    errors="coerce",
)
df[year_col] = pd.to_numeric(df[year_col], errors="coerce")
available_years = sorted(int(y) for y in df[year_col].dropna().unique())
if not available_years:
    st.warning("표시할 연도 정보가 없습니다.")
    st.stop()

selected_years = st.slider(
    "조회 연도 범위",
    min_value=min(available_years),
    max_value=max(available_years),
    value=(min(available_years), max(available_years)),
)
view = df[df[year_col].between(selected_years[0], selected_years[1])].copy()

def find_account(candidates: list[str]) -> pd.DataFrame:
    result = view[view[account_col].isin(candidates)].copy()
    if result.empty:
        return result
    return result.sort_values(year_col).drop_duplicates(subset=[year_col], keep="last")

metric_labels = list(preferred.keys())
cols = st.columns(3)
for idx, label in enumerate(metric_labels):
    matches = find_account(preferred[label])
    if matches.empty:
        cols[idx % 3].metric(label, "자료 없음")
    else:
        latest = matches.sort_values(year_col).iloc[-1]
        value = latest[amount_col]
        currency = latest.get("currency", "KRW")
        display = f"{value:,.0f} {currency}" if pd.notna(value) else "자료 없음"
        cols[idx % 3].metric(f"{label} ({int(latest[year_col])})", display)

st.subheader("계정별 연도 데이터")
if "sj_div" in view.columns:
    statement_options = ["전체"] + sorted(view["sj_div"].dropna().astype(str).unique().tolist())
    statement = st.selectbox("재무제표 구분", statement_options)
    if statement != "전체":
        view = view[view["sj_div"].astype(str) == statement]

account_options = sorted(view[account_col].dropna().astype(str).unique().tolist())
defaults = [x for x in ["매출액", "영업이익", "당기순이익", "자산총계", "부채총계", "자본총계"] if x in account_options]
selected_accounts = st.multiselect("표시할 계정", account_options, default=defaults)
if selected_accounts:
    chart = view[view[account_col].isin(selected_accounts)].pivot_table(
        index=year_col, columns=account_col, values=amount_col, aggfunc="first"
    ).sort_index()
    st.line_chart(chart)
else:
    st.caption("계정을 선택하면 연도별 추이를 볼 수 있습니다.")

st.subheader("원본 데이터")
st.dataframe(view, use_container_width=True, hide_index=True)
st.download_button(
    "현재 데이터 CSV 다운로드",
    data=view.to_csv(index=False).encode("utf-8-sig"),
    file_name="samsung_annual_financials.csv",
    mime="text/csv",
)
st.caption("주의: 재무제표의 계정명·표시 방식은 연도별 공시 기준에 따라 달라질 수 있습니다. 분석 전 원문 공시를 확인하세요.")
