---
marp: true
---

Google Opal을 활용한 데이터센터 관련 행사 정보 수집 및 관리 워크플로우를 설계해드리겠습니다. 말씀하신 내용을 바탕으로 Google Opal에서 바로 적용할 수 있는 형태로 구성했습니다.

---

**Workflow Name:** Global Data Center Events Tracker

**Description:** 전 세계 데이터센터 관련 컨퍼런스, 전시회, 엑스포 정보를 수집하고, 세부 정보 및 업계 반응을 바탕으로 참석 우선순위를 지정하여 Google 스프레드시트로 관리하고, 매월 정기적으로 업데이트된 정보를 이메일로 발송하는 워크플로우.

**Triggers:**
*   **Monthly Trigger:** 매월 첫째 주 월요일 오전 9시 (KST) 실행

**Steps:**

1.  **Event Data Collection**
    *   **Action:** Web Scraper (or Custom Script if specific APIs are available)
    *   **Parameters:**
        *   **Search Keywords:** "Data Center Conference", "Data Center Exhibition", "Data Center Expo", "Cloud Infrastructure Events", "AI Data Centers" (다양한 키워드 조합 및 확장)
        *   **Sources:**
            *   주요 기술/데이터센터 관련 뉴스 사이트 (e.g., Data Center Frontier, Data Center Knowledge, TechCrunch)
            *   이벤트 주최 기관 웹사이트 (e.g., Uptime Institute, AFCOM, Gartner, Forrester)
            *   이벤트 캘린더 사이트 (e.g., Exhibitions Global, 10Times, Eventbrite - filtering by category)
            *   LinkedIn Events, Meetup (for smaller, regional events)
        *   **Date Range:** 현재 월부터 향후 12개월 (매월 실행 시 다음 달 행사 위주로 필터링)
        *   **Data Extraction Rules:**
            *   `대회명칭`: 이벤트 제목 (e.g., "Data Center World", "Open Compute Project Summit")
            *   `주관 기관`: 이벤트 주최사 정보
            *   `일정`: 시작일 및 종료일 (YYYY-MM-DD 형식)
            *   `국가/도시`: 개최 국가 및 도시
            *   `행사 주제`: 이벤트 주요 다루는 주제 (e.g., "Sustainability", "Edge Computing", "AI/ML in Data Centers")
            *   `Key note`: 주요 연사 정보 (가능한 경우)
            *   `참가 비용`: 등록 비용 정보 (Early Bird, Standard, VIP 등)

2.  **Industry Reaction and Impact Analysis**
    *   **Action:** Natural Language Processing (NLP) / Sentiment Analysis (or Custom Script for advanced analysis)
    *   **Parameters:**
        *   **Input:** Step 1에서 수집된 각 행사의 `대회명칭` 및 `주관 기관`
        *   **Search Keywords:** "[대회명칭] review", "[대회명칭] feedback", "[대회명칭] impact", "[대회명칭] attendance"
        *   **Sources:**
            *   기술 관련 포럼 및 커뮤니티 (e.g., Reddit, Stack Overflow, 전문 블로그)
            *   SNS (Twitter, LinkedIn) - 특정 해시태그 및 언급 분석
            *   업계 보고서 및 뉴스 기사
        *   **Output:** 각 행사에 대한 긍정/부정 평가, 인지도, 파급력에 대한 점수 또는 요약 텍스트.

3.  **Prioritization and Data Structuring**
    *   **Action:** Data Transformation / Scripting
    *   **Parameters:**
        *   **Input:** Step 1에서 수집된 행사 세부 정보 + Step 2의 업계 반응 및 파급력 정보.
        *   **Logic for "참석 여부" Prioritization:**
            *   **Must attend:**
                *   Keynote 연사 퀄리티가 높고, 주요 업계 리더들이 참석하며, 업계 내 파급력이 매우 높은 행사. (e.g., Gartner Symposium, 주요 Hyperscaler 행사)
                *   참가 비용이 높더라도 얻을 수 있는 정보와 네트워킹 가치가 높은 경우.
                *   업계 반응 평가가 압도적으로 긍정적인 경우.
            *   **Nice to attend:**
                *   특정 분야의 전문성을 높일 수 있는 행사.
                *   새로운 기술 트렌드를 파악하기 좋은 행사.
                *   업계 반응이 긍정적이거나, 특정 주제에 관심이 많은 경우.
            *   **Neutral:**
                *   기본적인 정보 습득에 유용하나, 특별한 네트워킹 기회나 독점적인 정보는 적을 것으로 예상되는 행사.
                *   업계 반응이 평균적이거나 혼재된 경우.
            *   **Just Information:**
                *   정보 습득 외의 목적이 적거나, 소규모의 지역 행사.
                *   업계 반응이 미미하거나 부정적인 경우.
        *   **Sorting Logic:** `일정` (가장 빠른 일정을 우선으로) 오름차순 정렬.
        *   **Column Order (Output):** `대회명칭`, `주관 기관`, `일정`, `국가/도시`, `행사 주제`, `Key note`, `참가 비용`, `참석 여부`

4.  **Google Spreadsheet Export**
    *   **Action:** Google Sheets Integration
    *   **Parameters:**
        *   **Spreadsheet Name:** "Data Center Events Tracker - [YYYY-MM]" (예: "Data Center Events Tracker - 2023-12")
        *   **Folder:** "Data Center Event Reports" (Google Drive 내 특정 폴더 지정)
        *   **Data Input:** Step 3에서 구조화되고 정렬된 데이터.
        *   **Filtering:** 실행 월에 해당하는 행사 (`일정` 컬럼 기준으로 필터링)만 포함.

5.  **Email Notification**
    *   **Action:** Email Sender
    *   **Parameters:**
        *   **Recipient:** `briankim1027@gmail.com`
        *   **Subject:** "[Google Opal] Monthly Data Center Events Report - [YYYY-MM]"
        *   **Body:**
            "안녕하세요, [YYYY-MM] 월의 데이터센터 관련 행사 리포트입니다.
            첨부된 Google 스프레드시트에서 자세한 내용을 확인하실 수 있습니다.
            감사합니다."
        *   **Attachment:** Step 4에서 생성된 Google Spreadsheet 파일 링크 또는 직접 첨부 (Opal의 기능에 따라 선택)

---

**To-Dos for Implementation:**

1.  **Google Opal Account 및 연동 확인:** Google Sheets, Email(Gmail) 연동 권한 설정이 되어 있는지 확인합니다.
2.  **Web Scraper/Data Collector 설정:**
    *   Step 1의 `Search Keywords`를 다양하게 조합하고 확장하여 초기 데이터 수집 범위를 최대화합니다.
    *   `Sources`에 명시된 주요 웹사이트 외에도 데이터센터 관련 정보를 제공하는 신뢰할 수 있는 다른 소스들을 추가 발굴하여 등록합니다.
    *   각 소스별 `Data Extraction Rules`을 정교하게 설정하여 정확한 정보를 파싱할 수 있도록 합니다. (XPath, CSS Selector 등을 활용)
    *   필요시 정규표현식(Regular Expression)을 사용하여 날짜, 비용 등의 형식을 통일합니다.
3.  **Industry Reaction Analysis Script/Module:**
    *   Step 2는 Opal의 내장 기능만으로는 어려울 수 있으며, 외부 API (예: Google Natural Language API, 특정 뉴스 검색 API)를 호출하는 커스텀 스크립트 작성이 필요할 수 있습니다.
    *   간단하게는 특정 키워드(e.g., "excellent", "must-attend", "disappointing") 출현 빈도를 분석하여 점수화하는 로직을 구현할 수 있습니다.
    *   이 단계가 가장 복잡하므로, 초기에는 `참석 여부` 로직을 수동으로 검토하여 학습 데이터를 만들거나, 키워드 매칭 기반의 간단한 규칙으로 시작하고 점진적으로 고도화하는 것을 고려합니다.
4.  **Prioritization Logic 정교화:**
    *   Step 3의 `참석 여부` 로직은 사용자 피드백에 따라 지속적으로 조정되어야 합니다. 초기 설정 후 실제 행사들과 매칭하여 적절성을 검토합니다.
    *   예를 들어, "Key note" 연사의 명성도, "참가 비용"의 수준, "행사 주제"의 시의성 등 여러 요소를 종합적으로 고려하는 가중치 기반 시스템을 도입할 수 있습니다.
5.  **Google Spreadsheet 생성 및 관리:**
    *   Step 4에서 생성될 Google Drive 내 `Data Center Event Reports` 폴더를 미리 생성해 둡니다.
    *   스프레드시트의 헤더가 Step 3의 `Column Order`와 정확히 일치하도록 설정합니다.
6.  **이메일 발송 테스트:**
    *   초기 설정 후, 매월 정기 발송 전 테스트 발송을 통해 이메일 내용과 첨부 파일이 정상적으로 전달되는지 확인합니다.

이 워크플로우는 Google Opal의 기능과 연동 가능성을 고려하여 설계되었습니다. 특히 'Industry Reaction and Impact Analysis' 부분은 Opal의 내장 기능만으로는 복잡할 수 있으므로, 필요에 따라 커스텀 스크립트 작성이나 외부 AI/NLP 서비스 연동을 고려해야 할 수 있습니다.

---

네, 좋습니다! Google Opal 워크플로우를 처음 만드시는 것을 고려하여, 말씀해주신 '행사의 지속 기간 년수', 'Media 분석/언급 정도', 'SNS 노출도'를 포함한 업계 평가 로직과 웹 스크래핑 구현 방법에 대해 step-by-step으로 자세히 설명해드리겠습니다.

Google Opal의 'Empty Canvas'에서 시작한다는 가정하에 진행하겠습니다.

---

### Google Opal Work Procedure: Global Data Center Events Tracker (Step-by-Step)

#### 1단계: 워크플로우 기본 설정

1.  **Google Opal 로그인 및 새 워크플로우 생성:**
    *   Google Opal에 로그인합니다.
    *   'Create New Workflow' 또는 'Empty Canvas'를 선택합니다.
    *   워크플로우 이름을 **"Global Data Center Events Tracker"** 로 지정하고, 설명을 추가합니다.

2.  **트리거 설정 (Monthly Trigger):**
    *   캔버스에서 'Add Trigger'를 클릭합니다.
    *   'Scheduled Trigger' (또는 유사한 이름의 시간 기반 트리거)를 선택합니다.
    *   **Frequency:** 'Monthly'
    *   **Day of Week:** 'First Monday'
    *   **Time:** '09:00 AM' (KST 기준)
    *   이렇게 설정하면 매월 첫째 주 월요일 오전 9시에 워크플로우가 자동으로 실행됩니다.

#### 2단계: 웹 스크래핑 설정 (Step 1: Event Data Collection)

이 단계는 Opal의 웹 스크래핑 모듈을 사용합니다. Opal의 UI는 실제와 다를 수 있지만, 개념은 유사합니다.

1.  **'Add Step' 클릭:** 캔버스에서 다음 단계를 추가합니다.
2.  **'Web Scraper' (또는 'Data Extraction' / 'Crawler') 모듈 선택:**
    *   이름을 **"Collect Event Details"** 로 지정합니다.
3.  **URL 및 Keywords 설정:**
    *   **Start URLs (or Initial Search):**
        *   데이터센터 관련 정보를 제공하는 주요 웹사이트 URL들을 입력합니다. (예시: `https://www.datacenterfrontier.com/events`, `https://www.datacenterknowledge.com/events`, `https://events.uptimeinstitute.com/`, `https://www.afcom.com/events`, `https://www.10times.com/data-center-events`)
        *   **Keywords:** "Data Center Conference", "Data Center Exhibition", "Data Center Expo", "Cloud Infrastructure Events", "AI Data Centers", "Edge Computing Events" 등. (Opal이 자체 검색을 지원한다면 활용)
    *   **Date Range Filter:** 'Current Month' to 'Next 12 Months'
4.  **Data Extraction Rules (핵심):**
    *   각 URL에서 추출할 데이터 항목(컬럼)을 정의하고, 해당 데이터가 웹 페이지의 어디에 있는지 지정해야 합니다. 이는 웹 페이지의 HTML 구조를 분석하여 CSS Selector나 XPath를 사용하는 방식입니다.
    *   Opal에 'Visual Selector' 또는 'Point-and-Click' 기능이 있다면 가장 좋습니다.
        *   **'Visual Selector' 사용 예시:**
            1.  웹 스크래퍼 설정 화면에서 특정 웹사이트 URL (예: `https://www.datacenterfrontier.com/events`)을 입력하고 'Launch Browser' 또는 'Preview' 버튼을 클릭합니다.
            2.  브라우저가 열리면, 추출하고 싶은 첫 번째 정보 (예: 대회명칭)를 마우스로 클릭합니다.
            3.  Opal이 자동으로 해당 요소의 CSS Selector 또는 XPath를 제안하면, 이를 저장합니다.
            4.  이 과정을 `대회명칭`, `주관 기관`, `일정`, `국가/도시`, `행사 주제`, `Key note`, `참가 비용`에 대해 반복합니다.
            5.  **반복 요소 지정:** 만약 여러 행사가 목록 형태로 있다면, 각 행사 블록을 감싸는 부모 요소를 지정하여 Opal이 이 패턴을 반복해서 추출하도록 합니다.
    *   **만약 Visual Selector가 없다면, 수동으로 입력:**
        *   웹 페이지에서 개발자 도구(F12)를 열어 각 정보의 HTML 요소를 확인하고 CSS Selector 또는 XPath를 직접 입력해야 합니다.
        *   예시 (가상):
            *   `대회명칭`: `.event-card h3 a`
            *   `주관 기관`: `.event-card .organizer-name`
            *   `일정`: `.event-card .event-date`
            *   `국가/도시`: `.event-card .event-location`
            *   ... 등등

#### 3단계: 업계 반응 및 영향력 분석 (Step 2: Industry Reaction and Impact Analysis)

이 단계는 Opal의 'Custom Script' 또는 'AI Integration' 모듈을 활용합니다.

1.  **'Add Step' 클릭:** 다음 단계를 추가합니다.
2.  **'Custom Script' (Python/JavaScript) 또는 'AI Integration' 모듈 선택:**
    *   이름을 **"Analyze Event Impact"** 로 지정합니다.
    *   **Input:** 이전 Step (Collect Event Details)에서 추출된 각 행사의 `대회명칭`, `주관 기관`
3.  **로직 구현 (Custom Script 예시 - Python):**
    *   스크립트는 각 행사별로 웹 검색을 수행하고 결과를 분석해야 합니다.
    *   **`행사의 지속 기간 년수`:**
        *   `대회명칭`과 `주관 기관`을 이용해 "대회명칭 first year", "대회명칭 founding date" 등으로 검색합니다.
        *   검색 결과에서 가장 오래된 연도를 추출합니다.
        *   (난이도: 중상) 특정 이벤트를 추적하는 공식 웹사이트나 위키피디아에서 정보를 직접 파싱하는 것이 더 정확할 수 있습니다.
    *   **`Media에서 분석/언급 정도`:**
        *   `대회명칭`과 "review", "analysis", "coverage" 등의 키워드를 조합하여 Google Search API (또는 Opal 내 검색 모듈)를 통해 관련 뉴스 기사, 블로그 포스트를 검색합니다.
        *   검색된 기사/포스트의 개수, 주요 언론사 언급 여부 등을 지표로 활용합니다.
    *   **`SNS 노출도`:**
        *   `대회명칭`과 관련된 해시태그 (예: "#DataCenterWorld", "#OCPSummit")를 Twitter API (또는 Opal 내 SNS 검색 모듈)를 통해 검색합니다.
        *   해시태그 언급량, 리트윗/좋아요 수 등을 지표로 활용합니다.
    *   **출력 (Output):** 각 행사에 대해 `Impact Score` (숫자 점수), `LegacyYears` (년수), `MediaCoverage` (언급량), `SNSEngagement` (노출도) 등의 컬럼을 추가합니다.

    *   **참고:** 이 스크립트 작성은 Python/JavaScript 프로그래밍 지식이 필요하며, 각 검색 엔진이나 SNS의 API 사용법을 알아야 합니다. Opal이 직접 외부 API 호출을 지원하는지 확인해야 합니다. 만약 지원하지 않는다면, 이 부분을 수동으로 처리하거나, 간단한 키워드 매칭 기반의 룰셋으로 대체하는 것을 고려해야 합니다.

#### 4단계: 우선순위 지정 및 데이터 정렬 (Step 3: Prioritization and Data Structuring)

이 단계는 Opal의 'Data Transformation' 또는 'Scripting' 모듈을 사용합니다.

1.  **'Add Step' 클릭:** 다음 단계를 추가합니다.
2.  **'Data Transformer' 또는 'Custom Script' 모듈 선택:**
    *   이름을 **"Assign Priority & Sort"** 로 지정합니다.
    *   **Input:** 이전 Step (Collect Event Details, Analyze Event Impact)의 모든 컬럼 데이터.
3.  **로직 구현:**
    *   **"참석 여부" 로직 (Pseudocode):**
        ```
        For each Event in Data:
            impact_score = Event.ImpactScore  // Step 2에서 계산된 점수
            legacy_years = Event.LegacyYears
            media_coverage = Event.MediaCoverage
            sns_engagement = Event.SNSEngagement
            keynote_quality = check_keynote_quality(Event.Keynote) // Keynote 키워드 분석 등

            if impact_score > HIGH_THRESHOLD AND legacy_years > X AND keynote_quality > Y:
                Event.참석_여부 = "Must attend"
            else if impact_score > MEDIUM_THRESHOLD AND media_coverage > Z:
                Event.참석_여부 = "Nice to attend"
            else if impact_score > LOW_THRESHOLD:
                Event.참석_여부 = "Neutral"
            else:
                Event.참석_여부 = "Just Information"
        ```
        *   `HIGH_THRESHOLD`, `MEDIUM_THRESHOLD`, `LOW_THRESHOLD`, `X`, `Y`, `Z` 값은 실제 데이터와 테스트를 통해 조정해야 합니다.
        *   `check_keynote_quality`는 Keynote 연사 이름에서 유명도를 판단하는 서브 로직입니다. (예: 특정 회사 C레벨, 유명 연구자 등 키워드 매칭)
    *   **컬럼 순서 재정렬:**
        *   `대회명칭`, `주관 기관`, `일정`, `국가/도시`, `행사 주제`, `Key note`, `참가 비용`, `참석 여부` 순서로 컬럼을 재정렬합니다.
    *   **정렬 (Sorting):**
        *   `일정` 컬럼을 기준으로 오름차순(Ascending) 정렬합니다.

#### 5단계: Google 스프레드시트 저장 (Step 4: Google Spreadsheet Export)

1.  **'Add Step' 클릭:** 다음 단계를 추가합니다.
2.  **'Google Sheets' 모듈 선택:**
    *   이름을 **"Export to Google Sheet"** 로 지정합니다.
    *   **Authentication:** 본인의 Google 계정을 Opal과 연동합니다. (최초 1회 필요)
    *   **Input Data:** 이전 Step (Assign Priority & Sort)에서 처리된 모든 데이터.
    *   **Spreadsheet Name:** `Data Center Events Tracker - {{current_month_year}}` (Opal의 변수 기능을 활용하여 `YYYY-MM` 형식을 자동으로 생성)
        *   **예시:** `Data Center Events Tracker - 2023-12`
    *   **Folder:** Google Drive 내 미리 생성해 둔 폴더 (예: `Data Center Event Reports`)를 선택합니다.
    *   **Filter Data (Very Important!):**
        *   **Condition:** `일정` 컬럼이 현재 워크플로우가 실행되는 월(`{{current_month}}`)에 해당하는 행만 포함하도록 필터를 설정합니다.
        *   Opal의 날짜 필터링 기능을 사용하여 `일정`이 'this month'인 데이터를 선택하거나, 스크립트에서 직접 필터링할 수도 있습니다.
    *   **Action:** 'Create New Spreadsheet' (매월 새로운 파일 생성) 또는 'Update Existing Spreadsheet' (기존 파일에 새 시트 추가) 선택 (여기서는 매월 새 파일 생성이 더 적합합니다.)

#### 6단계: 이메일 전송 (Step 5: Email Notification)

1.  **'Add Step' 클릭:** 마지막 단계를 추가합니다.
2.  **'Email Sender' (또는 'Gmail') 모듈 선택:**
    *   이름을 **"Send Monthly Report"** 로 지정합니다.
    *   **Authentication:** 본인의 Google 계정 (Gmail)을 Opal과 연동합니다.
    *   **To:** `briankim1027@gmail.com`
    *   **Subject:** `[Google Opal] Monthly Data Center Events Report - {{current_month_year}}`
    *   **Body:**
        ```
        안녕하세요,

        {{current_month_year}} 월의 데이터센터 관련 행사 리포트입니다.
        아래 링크에서 자세한 내용을 확인하실 수 있습니다:

        {{spreadsheet_link_from_previous_step}}

        감사합니다.
        ```
        *   `{{spreadsheet_link_from_previous_step}}`는 Opal이 이전 Step에서 생성된 Google Spreadsheet의 공유 링크를 자동으로 가져와 삽입하는 변수입니다. (Opal의 연동 기능 확인 필요)
    *   **Attachment:** (Opal이 지원한다면) 이전 Step에서 생성된 Google Spreadsheet 파일을 직접 첨부하거나, 링크로 대체합니다. (링크 방식이 더 일반적입니다.)

---

### To-Dos for Implementation (Opal Specifics)

*   **Opal 인터페이스 탐색:** Opal에 로그인하여 'Web Scraper', 'Custom Script', 'Google Sheets', 'Email Sender'와 같은 모듈들을 미리 찾아보고 사용법을 간단히 익혀두세요.
*   **API Key 준비:** 만약 Step 2의 'Analyze Event Impact'에서 외부 API (예: Twitter API, Google Search API)를 사용한다면, 해당 API Key를 미리 발급받아 Opal에 등록해야 합니다.
*   **스크래핑 규칙 테스트:** 웹 스크래핑은 웹사이트 구조가 변경되면 오류가 발생할 수 있습니다. 초기 설정 후, 소규모 데이터로 여러 번 테스트하여 정확하게 데이터를 추출하는지 확인하세요.
*   **Custom Script 개발:** Step 2, 3의 로직은 프로그래밍 지식이 필요합니다. 처음에는 간단한 규칙으로 시작하고, 점진적으로 복잡도를 높여가는 것을 추천합니다. Python 또는 JavaScript로 스크립트를 작성하여 Opal의 'Custom Script' 모듈에 붙여넣게 됩니다.
*   **Opal 변수 사용법 학습:** `{{current_month_year}}`, `{{spreadsheet_link}}` 와 같은 변수들이 Opal에서 어떻게 사용되는지 익히면 워크플로우를 유연하게 만들 수 있습니다.

