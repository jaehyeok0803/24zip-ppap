# 24.zip 주거지원 정책 조회

## Vercel 배포

ZIP을 풀어 `index.html`, `api/`, `policy/`, `vercel.json`이 같은 폴더에 오도록 저장소에 올립니다. Vercel 프로젝트의 Root Directory로 그 폴더를 지정합니다. Framework Preset은 Other입니다. 배포 설정은 `node build.mjs`로 정적 파일을 `dist`로 복사합니다. API는 Python 표준 라이브러리로 실행합니다. 환경변수를 Production 또는 테스트할 Preview 환경에 저장한 뒤 재배포합니다. HTML을 더블클릭해서 여는 경우 API는 실행되지 않습니다. 로컬에서는 프로젝트 루트에서 `vercel dev`를 사용합니다.

| Vercel 환경변수 | 값과 발급처 |
|---|---|
| SEOUL_API_KEY | 서울 열린데이터광장 인증키. 기존에 등록한 이름을 재사용합니다. |
| SEOUL_WELFARE_LIST_SERVICE | OA-23013 Open API 탭 샘플 URL의 영문 서비스명. 비워 두면 공식 페이지에서 추출을 시도합니다. |
| SEOUL_WELFARE_DETAIL_SERVICE | OA-23014의 영문 서비스명. 데이터셋 번호나 한글 제목과 구분합니다. |
| SEOUL_WELFARE_ID_FIELD | 원본 서비스 ID 필드가 servId/SERV_ID/serviceId와 다른 경우 공식 응답에 기재된 키를 지정합니다. |
| GEMINI_API_KEY | Google AI Studio의 무료 등급 프로젝트 키. 무료로 운영하려면 결제를 활성화하지 않은 프로젝트를 사용합니다. |
| GEMINI_MODEL | 무료 등급을 지원하는 활성 모델 ID. 확인한 가격표 예시는 `gemini-3.5-flash`입니다. 프로젝트별 실제 이용 가능 여부는 AI Studio에서 확인합니다. |

서울시 목록·상세는 서울시 명세의 HTTP 8088 포트를 서버에서 사용합니다. 이 구간은 전송 암호화를 제공하지 않습니다. 사용자 프로필은 서울시 및 중앙부처 API로 전달하지 않습니다. 인증키가 포함된 주소를 로그에 기록하지 않습니다. 지도 인증 설정은 별도로 사용합니다.

## 중앙부처 공식 공고 검색

마이홈 모집 목록 첫 화면에서 확인 가능한 최대 6개 링크와 기존에 확인한 공고 19631을 조회합니다. LH 공급 및 서울 지역을 확인한 원문에서 Gemini가 핵심 항목을 골라 요약합니다. Google Search 도구를 호출하지 않습니다. Gemini 오류 시 공식 원문의 기본 요약을 제공합니다. 운영 범위는 마이홈 입주자 모집공고이며, 후보는 공고 검토 중에 표시합니다.

## 사용 흐름과 자료 범위

지도나 자치구 결과에서 ‘내 조건 확인하기’를 누릅니다. 앞 화면의 최대 보증금·최대 월세와 선택 지역을 전달합니다. 자격 화면에서는 25개 구를 선택할 수 있습니다. 예산은 실제 체결한 계약금액과 별개입니다. 만원 단위를 유지하며, 계약금액을 요구하는 공고에 예산을 대입하지 않습니다. 공고에 따라 추가 질문이 생기면 ‘정보 보완하기’에서 입력합니다.

| 출처 | 구현 범위 |
|---|---|
| 서울 1인가구 포털 | 서울시 전월세 안심계약 도움서비스의 연도별 신청기간, 지원 내용, 선택 지역에 해당하는 실제 신청서와 신청 동의 단계 확인. 1인가구와 독립 예정 1인가구의 조건 판정. |
| 영등포구1인가구지원센터 | 2026 전입 1인가구 웰컴키트 모집마감 제외. 본문 마감 공지가 남아 있어 화면 상단 ‘모집중’과 충돌하는 회차입니다. |
| 서울주거포털 | 청년 임차보증금 이자지원의 나이·본인 소득을 사전 대조합니다. 현재 접수와 전체 자격을 확정할 수 없어 검토 중에만 표시합니다. |
| 서울 열린데이터광장 | 목록 및 상세 전체 페이지 수집, 원본 ID 조인, 주거 관련 후보 추출. 공식 회차와 자격 근거 매핑이 없는 데이터는 최종 추천에 들어가지 않습니다. |

현재 자동으로 긍정 판정하는 사업은 서울시 전월세 안심계약 도움서비스입니다. 서울시 카탈로그의 새 사업을 모두 자동 판정하지 않습니다. 사업별 기준·회차·접수 상태를 검토해 `policy/catalogue-rounds.json`이나 출처별 검증 함수에 추가해야 범위가 늘어납니다. 조회한 전체 카탈로그 건수는 최종 추천 건수가 아닙니다. 링크를 누르면 서버가 공고와 신청처를 재조회합니다. 연결 실패, 지역 변경, 날짜 경과, 모집 마감 시 이전 추천으로 이동하지 않습니다.

## 입력과 API 응답

`POST /api/policies`, Content-Type은 application/json입니다.

```json
{"profile":{"district":"동작구","locationIntent":"yes","age":27,"personalIncome":3000,"noHome":"yes","monthly":50,"deposit":1000,"single":"yes"}}
```

district만 필수입니다. 문자열 값은 yes/no, locationIntent는 현재 거주 또는 전입할 지역으로 선택했는지를 뜻합니다. 현재 주민등록 여부는 이 값으로 추정하지 않습니다. age는 현재 만 나이, personalIncome과 householdIncome은 각각 개인·가구 세전 연소득(만원), monthly와 deposit은 예산 상한(만원), people은 가구원 수입니다. moved는 전입신고일(YYYY-MM-DD), fromOther는 다른 구에서 전입했는지입니다. 누락 또는 null은 미입력이고 0원은 실제 값입니다. 신청 직전에는 같은 본문에 recheckId를 추가합니다.

응답의 state는 results, input, empty, failed입니다. 조회 중은 브라우저에서 표시하고 부분 장애는 partial로 표시합니다. recommendations에는 식별자, 회차, 기관, 지역, 유형, 실제 혜택, 각 조건 및 출처, 접수 기간·상태·확인 시각, 신청 방법·링크, 설명이 들어갑니다. requiredFields는 추가 입력 필드→질문입니다. sources에는 공급자별 상태·오류·조회 범위, excluded에는 접수 상태로 제외된 공고가 들어갑니다. 총 장애는 HTTP 503, 잘못된 입력은 HTTP 400입니다. Gemini 장애는 개별 추천의 explanationSource에 표시합니다. 모델에는 판정된 문장과 정책 ID만 전달합니다. 선택한 문장과 근거 ID가 일치해야 표시합니다. 설명 캐시 및 분당 호출 제한은 서버 인스턴스 단위입니다.

## 변경 파일

- app.js, index.html, policy-ui.js — 주거비 입력 보존, 기존 결과·지도에서 정책 화면 연결, 추가 질문과 결과 표시, 재확인.
- api/policies.py — Vercel 요청 처리 및 안전한 오류 응답.
- policy/sources.py, discovery.py — 공식 목록·상세 조회, 페이지 검증, 후보 선별.
- policy/notices.py, contract.py, finance.py, catalogue-rounds.json — 공고 근거, 지역 범위, 지원 내용, 조건, 접수 및 링크 검증.
- policy/service.py, explain.py — 조회 통합, 상태별 응답, Gemini 설명 및 기본 설명.
- vercel.json, build.mjs — 정적 화면과 API 배포 설정.
- tests/test_policy.py — 운영 데이터와 분리된 자동 검증.

## 검증과 실제 추적 예

동작구를 선택한 1인가구 전입 예정자의 경우, 서울시 공고의 전월세 계약상담·집보기 동행 내용과 거주 예정 1인가구 문구를 확인합니다. 서울 1인가구 포털에서 동작구 신청 링크를 추출하고, 링크의 구 이름과 신청 동의 단계를 재검사합니다. 연도별 접수기간 안이고 신청 단계가 확인되면 결과 카드에 한국시간을 기록합니다. 공식 신청 페이지를 열기 직전 같은 조건으로 다시 검사합니다.

영등포구 웰컴키트는 안내 페이지의 접수기간이 남았더라도 운영기관의 모집마감 고지가 우선합니다. 이 회차를 재개하려면 운영기관의 새로운 공식 근거를 확인해야 합니다.

자동 검증은 `python -m unittest discover -s tests -v`로 실행합니다. 입력 누락과 0 구분, 지역과 가구소득, 만료·조기 마감·상태 불명, 지역 변경, 공식 API 오류·페이지네이션, 신청 직전 실패, Gemini의 변조 응답을 포함합니다. 네트워크 응답 대역으로 확인한 테스트와 실제 공고 열람은 구분합니다. 이번 작업에서는 인증된 공공 API 실호출, 무료 Gemini 실호출, Vercel 배포 URL에서의 통합 실행까지 확인하지 못했습니다.

## 공식 자료

- [서울시 복지서비스 목록](https://data.seoul.go.kr/dataList/OA-23013/S/1/datasetView.do) · [상세](https://data.seoul.go.kr/dataList/OA-23014/S/1/datasetView.do)
- [서울시 1인가구 지원 내용과 지역별 신청 경로](https://1in.seoul.go.kr/front/sport/sportView.do?sport_id=a97db018d11c44af845fd028fde7104c) · [2026 신청기간](https://youth.seoul.go.kr/infoData/plcyInfo/view.do?key=2309150002&plcyBizId=20261021005400214222)
- [영등포구 웰컴키트 운영기관 공고](https://ydp1in.or.kr/program/256)
- [서울시 청년 임차보증금 이자지원](https://housing.seoul.go.kr/site/main/content/sh01_040901) · [마이홈 입주자 모집 공고](https://m.myhome.go.kr/hws/portal/sch/selectRsdtRcritNtcDetailView.do?pblancId=19631)
- [Gemini 가격표](https://ai.google.dev/gemini-api/docs/pricing) · [AI Studio](https://aistudio.google.com/apikey) · [Vercel Python](https://vercel.com/docs/functions/runtimes/python)