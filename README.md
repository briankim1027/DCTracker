# DCTracker

데이터센터 관련 글로벌 행사를 수집해 Google Sheets 및 이메일로 전달하는 자동화 스크립트입니다. 팀/외부 인원에게 배포할 때는 아래 순서를 참고하세요.

## 사전 준비

1. **Python 환경**: Python 3.11 이상 권장. 새 가상환경을 만들고 pip install -r requirements.txt로 의존성을 설치합니다.
2. **Google Cloud 설정**:
   - Google Cloud Console에서 새 프로젝트를 준비합니다.
   - Google Sheets API, Gmail API, Google Drive API를 활성화합니다.
   - OAuth 클라이언트 ID(데스크톱 앱)를 생성해 JSON 파일을 내려받은 후 적절한 위치에 저장합니다.
   - client_secrets.json 파일명을 유지하거나, 다른 이름을 사용할 경우 스크립트 상 경로를 조정하세요.
3. **환경 변수**: .env.example을 복사해 .env로 만들고, 다음 값을 채웁니다.
   `
   GOOGLE_APPLICATION_CREDENTIALS="<OAuth JSON 경로>"
   SPREADSHEET_ID=""        # (선택) 이미 만들어 둔 시트가 있다면 지정
   RECIPIENT_EMAILS=["user1@example.com", "user2@example.com"]
   REFERENCE_DATE=""         # (선택) 테스트용 기준 날짜
   `

## 실행 방법

`ash
python run_workflow.py
`

- 최초 실행 시 브라우저가 열리며 Google 인증을 거쳐 	oken.json이 생성됩니다.
- 스크립트는 지정된 기간(기본 12개월) 내의 이벤트를 수집해 Google Sheets에 업로드하고, RECIPIENT_EMAILS에 명시된 모든 주소로 이메일을 발송합니다.
- 특정 월만 테스트하려면 다음과 같이 실행합니다.
  `ash
  REFERENCE_DATE=2025-11-01 python run_workflow.py
  `

## 생성 파일 및 폴더

- output/ 폴더는 자동으로 생성되지 않으며, 실행 결과는 Google Sheets 및 이메일로 전송됩니다.
- Google API 인증 정보(client_secrets.json, 	oken.json)는 배포본에 포함하지 마세요.

## 기타 팁

- 크롤링 대상 사이트 HTML 구조가 변경되면 un_workflow.py에서 파싱 로직을 조정해야 합니다.
- 요청이 많은 환경에서는 구글 API 할당량을 초과할 수 있으므로, 별도 프로젝트를 사용하거나 호출 간 대기 시간을 조절하세요.

