[![Dashboard](https://img.shields.io/badge/%F0%9F%94%97%20%EB%8C%80%EC%8B%9C%EB%B3%B4%EB%93%9C-%EB%B0%94%EB%A1%9C%EA%B0%80%EA%B8%B0-2864dc?style=for-the-badge)](https://hsc-class02.github.io/JY_SAMSUNG/)

# Samsung Electronics DART Financial Agent

삼성전자 사업·반기·분기보고서의 주요 재무수치를 OpenDART API에서 수집해 CSV로 저장하고 GitHub Pages 대시보드에서 추세 그래프와 기간별 테이블을 제공합니다.

## Dashboard
**[🔗 대시보드 바로가기](https://hsc-class02.github.io/JY_SAMSUNG/)**

최초 배포 전에 저장소 Settings → Pages → Build and deployment → Source에서 GitHub Actions를 선택해야 합니다. 저장소 오른쪽 About의 홈페이지 링크도 위 URL로 설정하세요.

## Schedule and setup
- 매월 1일 03:00 UTC (한국시간 12:00)에 자동 실행
- Actions → Monthly DART Update → Run workflow로 수동 실행 가능
- 저장소 Settings → Secrets and variables → Actions에 DART_API_KEY라는 이름으로 OpenDART 키 등록
- 키는 코드나 로그에 직접 입력하지 마세요.

## Data coverage limitation
OpenDART의 정기보고서 재무정보 API는 2015년 이후 자료를 제공합니다. 현재 collector는 2015년부터 사업보고서(11011), 반기보고서(11012), 1분기보고서(11013), 3분기보고서(11014)를 요청합니다. 2010~2014년 데이터는 과거 공시 원본/XBRL을 별도로 내려받아 변환하는 추가 파이프라인이 필요하며, 현재 값이 채워진 것으로 간주하지 않습니다. 공식 가이드: https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS003&apiId=2019017

## Local run
Python 3.12 recommended.

    python -m pip install -r requirements.txt

macOS/Linux: export DART_API_KEY="YOUR_KEY" then run python scripts/fetch_financials.py

Windows PowerShell: $env:DART_API_KEY="YOUR_KEY" then run python scripts/fetch_financials.py

## Report codes
- 11011 annual business report
- 11012 half-year report
- 11013 first-quarter report
- 11014 third-quarter report

Income statement and cash-flow figures in interim reports can be year-to-date cumulative. Review the source filing before comparing periods. Financial ratios and FCF/EBITDA/net-debt estimates are approximate and can be missing where account names differ. PER, PBR and EV/EBITDA need market price/market-cap data and are not included yet.

## Domestic peer firms
| Company | Comparison rationale | Useful measures |
|---|---|---|
| SK hynix | Memory semiconductor peer | revenue, margins, CAPEX, CFO, ROIC |
| DB HiTek | Foundry-focused semiconductor manufacturer | margin, investment, asset turnover |
| LG Electronics | Consumer electronics and appliances | growth, operating margin, working capital |
| LG Display | Display-panel business | debt, CAPEX, FCF |
| Samsung SDI | Electronics components and batteries | investment intensity, net debt, FCF |

Peer firms are comparison candidates only; their financial values are not yet automatically collected. Interpret differences in business mix and capital intensity carefully.

## Official links
- OpenDART: https://opendart.fss.or.kr/
- Samsung Electronics investor information: https://www.samsung.com/sec/ir/


## Historical data import (2010-2014)
OpenDART's standard periodic financial-information API documents coverage from 2015 onward. The repository therefore does **not** fabricate 2010-2014 figures. For those years, obtain Samsung Electronics' official annual-report/XBRL source from DART/OpenDART, normalize the verified values into the schema in `data/historical_template.csv`, and retain the filing receipt number and source link.

The importer validates that all rows belong to Samsung Electronics, limits fiscal years to 2010-2014, checks required columns and report codes, rejects duplicate year/report rows in the input, and merges the verified rows into `data/financials.csv`:
```bash
python scripts/import_historical_csv.py path/to/verified_historical.csv
```
After importing, copy the resulting file to `dashboard/data/financials.csv` and commit both CSVs so GitHub Pages can publish them. **Do not treat blank template rows as real financial data.** Check each imported value and accounting unit against the official filing before publishing. The importer is a normalization/validation step, not an automatic XBRL parser.

Official resources:
- OpenDART financial-information guide: https://opendart.fss.or.kr/guide/main.do?apiGrpCd=DS003
- OpenDART financial data and XBRL downloads: https://opendart.fss.or.kr/disclosureinfo/fnltt/xbrlnote/main.do
- DART disclosure search: https://dart.fss.or.kr/
