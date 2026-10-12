# Samsung Electronics DART Financial Analysis

삼성전자 사업보고서의 연간 연결재무제표를 OpenDART API로 수집하고 CSV로 관리하며, Streamlit 대시보드에서 연도별 계정 추이를 확인하는 프로젝트입니다.

## 현재 포함된 기능

- OpenDART API를 통한 삼성전자 (corp_code=00126380) 연간 연결재무제표 수집
- 데이터 파일: data/samsung_annual_financials.csv
- 수집 스크립트: scripts/fetch_financials.py
- Streamlit 대시보드: app.py
- 매월 1일 자동 실행 및 수동 실행: .github/workflows/monthly-update.yml
- 인증키는 GitHub Actions Secret DART_API_KEY에서만 읽음

## 중요한 과거 데이터 범위 안내

OpenDART의 fnlttSinglAcntAll 전체 재무제표 API는 2015년 이후 연도 자료를 대상으로 합니다. 따라서 이 API만으로 2010~2014년 데이터를 채울 수는 없습니다. 2010~2014년을 포함한 완전한 시계열을 만들려면 해당 기간의 공시목록과 원본 XBRL/첨부 재무자료를 별도로 확보·파싱하고 계정명을 표준화하는 추가 작업이 필요합니다. 현재 수집기는 지원되는 API 범위인 2015년 이후 데이터를 수집하며, 과거 기간이 완성된 것처럼 데이터를 만들어내지 않습니다.

## 1. GitHub Secret 설정

저장소의 Settings → Secrets and variables → Actions → New repository secret에서 다음을 등록합니다.

- Name: DART_API_KEY
- Secret: OpenDART에서 발급받은 인증키

인증키를 소스코드, CSV, README, 로그에 직접 입력하지 마세요. 이 프로젝트는 키 값을 출력하지 않습니다.

## 2. 데이터 수집 실행

GitHub에서 Actions → Monthly DART Update → Run workflow를 선택합니다. 정상 실행되면 CSV가 변경된 경우에만 GitHub Actions가 커밋합니다.

자동 실행 예약은 매월 1일 03:00 UTC(한국시간 12:00)입니다. GitHub Actions의 예약 실행은 플랫폼 사정에 따라 지연될 수 있으므로, 중요한 작업은 수동 실행 결과도 확인하세요.

## 3. 로컬에서 실행

Python 3.12 이상 권장:

```bash
python -m pip install -r requirements.txt
```

macOS/Linux:
```bash
export DART_API_KEY="발급받은_인증키"
python scripts/fetch_financials.py
streamlit run app.py
```

Windows PowerShell:
```powershell
$env:DART_API_KEY="발급받은_인증키"
python scripts/fetch_financials.py
streamlit run app.py
```

인증키를 명령 기록이나 공유 화면에 노출하지 않도록 주의하세요.

## 4. 대시보드 배포

GitHub 저장소의 Settings → Pages에서 배포 소스를 설정하거나, Streamlit Community Cloud 같은 Streamlit 호스팅에 저장소를 연결해 app.py를 배포할 수 있습니다. Streamlit 호스팅을 이용할 경우 앱의 실행 환경에 requirements.txt가 포함되어야 합니다.

GitHub Pages는 정적 사이트 호스팅이므로 Python/Streamlit 앱을 그대로 실행할 수 없습니다. Streamlit 앱을 공개하려면 Streamlit을 실행할 수 있는 호스팅을 사용하세요.

## 데이터 해석 시 유의사항

- 연결재무제표(CFS), 연간 사업보고서(보고서 코드 11011)를 기본으로 합니다.
- 계정명과 계정 구조가 연도별로 달라질 수 있어 단순 계정명 비교만으로 완벽한 시계열을 보장하지 않습니다.
- 금액 단위는 API 응답의 원문 값을 유지하며, 분석 시 통화·단위·계정 정의를 확인하세요.
- 본 프로젝트는 교육·분석 목적이며 투자 조언이 아닙니다.

## 공식 문서

- OpenDART: https://opendart.fss.or.kr/
- 전체 재무제표 API 가이드: https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS003&apiId=2019020
