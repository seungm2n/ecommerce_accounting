# ecommerce_accounting


# 시스템 아키텍처 및 실행 가이드

---

## A. 시스템 아키텍처

### 기술 스택
- **언어:** Python 3.10  
  이유: 자동 분류 로직에서 추후 제외 키워드나 예외 처리를 구현할 때, 단순한 문자열 매칭을 넘어서 자연어 처리나 AI API 연동이 필요할 수 있다고 생각했습니다. Python은 OpenAI API, NLP 라이브러리, 텍스트 분류 모델 등과 연동이 용이하다고 판단하였으며, 데이터 가공이나 처리도 빠르게 구현할 수 있어 이러한 방향성을 고려해 선택하게 되었습니다.
- **웹 프레임워크:** FastAPI  
  이유: 비동기 지원이 뛰어나고, 데이터 유효성 검사가 내장되어 있어 예외 처리나 데이터 안정성을 확보하기 용이합니다. 또한, Swagger UI가 자동 생성되어 테스트와 검토가 편리하다는 점에서 실무 테스트 과제에 적합하다고 판단했습니다.
- **DB:** SQLite  
  이유: 초기 개발과 테스트 단계에서는 복잡한 설정 없이 파일 기반으로 바로 사용할 수 있는 SQLite가 효율적이라고 생각했습니다. 추후 운영 환경으로 전환 시에는 표준 SQL DB를 선택할 수 있습니다. (ex. PostgreSQL, MYSQL 등)
- **ORM:** SQLAlchemy  
  이유: Python 기반 ORM 중 가장 안정적이라고 생각하여 선택하게 되었습니다. SQLAlchemy는 스키마 정의와 쿼리 유지보수가 쉬워서 확장성 면에서도 적합하다고 판단했습니다.
- **테스트 및 배포:** Docker 컨테이너  
  이유: 테스트하시는 분들이 환경 설정 문제 없이 동일한 환경에서 실행하실 수 있도록 Docker를 선택했습니다. 또한, 시스템 의존성을 분리할 수 있어서 배포 편의성뿐만 아니라 테스트 신뢰성도 높일 수 있다고 생각했습니다.

### DB 스키마
```sql
CREATE TABLE CLIENT (
    CLIENT_ID VARCHAR(16) PRIMARY KEY,
    CLIENT_NAME VARCHAR(255) NOT NULL
);

CREATE TABLE COMPANY (
    COMPANY_ID VARCHAR(16) PRIMARY KEY,
    COMPANY_NAME VARCHAR(255) NOT NULL,
    CLIENT_ID VARCHAR(16) NOT NULL,
    FOREIGN KEY (CLIENT_ID) REFERENCES CLIENT(CLIENT_ID)
);

CREATE TABLE CATEGORY (
    CATEGORY_ID VARCHAR(16) PRIMARY KEY,
    CATEGORY_NAME VARCHAR(255) NOT NULL,
    COMPANY_ID VARCHAR(16) NOT NULL,
    FOREIGN KEY (COMPANY_ID) REFERENCES COMPANY(COMPANY_ID)
);

CREATE TABLE TRANSACTION (
    TRANSACTION_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    TRANSACTION_DATE VARCHAR(20) NOT NULL,
    CLIENT_ID VARCHAR(16),
    COMPANY_ID VARCHAR(16),
    CATEGORY_ID VARCHAR(16),
    DEPOSIT INTEGER,
    WITHDRAWAL INTEGER,
    BALANCE INTEGER,
    DESCRIPTION VARCHAR(255),
    IS_MATCHED VARCHAR(1) DEFAULT 'N',
    CREATE_DATE VARCHAR(20) NOT NULL,
    CREATE_BY VARCHAR(50) DEFAULT 'SYSTEM',
    UPDATE_DATE VARCHAR(20) NOT NULL,
    UPDATE_BY VARCHAR(50) DEFAULT 'SYSTEM',
    RAW TEXT,
    FOREIGN KEY (CLIENT_ID) REFERENCES CLIENT(CLIENT_ID),
    FOREIGN KEY (COMPANY_ID) REFERENCES COMPANY(COMPANY_ID),
    FOREIGN KEY (CATEGORY_ID) REFERENCES CATEGORY(CATEGORY_ID)
);
```
- 한 고객사가 운영하는 여러 사업체를 운영할 경우, 여러 사업체를 지원할 수 있도록 CLIENT 테이블을 추가하고, 문제 발생 시 추적을 위해 COMPANY와 CATEGORY가 CLIENT에 연동되도록 설계하였습니다.
- 또한, 테스트 시에는 가상의 고객사를 존재시키지 않아 문제가 될 수 있어 NOT NULL 조건은 제외하고 컨테이너에 올렸습니다.
---
## B. 핵심 자동 분류 로직
- 거래내역(적요, 금액 등)과 분류 규칙(JSON) 기반 자동 분류

### 동작 방식
- rules.json 파일에는 사업체 ID와 연결된 카테고리별 키워드 리스트가 정의되어 있습니다.
- 분류 대상 거래의 적요(description)을 기준으로 각 규칙 키워드와 일치하는 항목을 탐색하고, 가장 먼저 매칭된 항목을 사업체 및 카테고리로 분류합니다.
- 일치하는 규칙이 없는 경우, 해당 거래는 '미분류' 상태로 처리하며 is_matched = 'N'으로 기록됩니다.
- 분류가 끝난 거래는 DB에 저장되어 이후 조회 API에서 사용할 수 있도록 했습니다.

### 확장 아이디어
- 제외 키워드 처리: 특정 키워드가 존재할 경우 해당 거래를 자동 분류 대상에서 제외하기는 쉽지만, 특정 패턴이 존재하는 키워드라면 상용화되어 있는 AI를 통해 분류를 요청하여 분류되어진 키워드를 가지고 분류해야할 것으로 보여집니다.
- 주기성 분석을 통한 분류: 매달 반복적으로 발생하는 거래(정기 송금, 월 구독료 등)는 주기성을 기반으로 자동 분류 처리되도록 확장 가능합니다.
  - 예: 특정 거래가 월 단위로 동일 금액/상호명으로 반복된다면 이를 학습하여 자동 분류합니다.
- 상호명 + 지점명 매칭 로직: 적요 필드에 있는 거래처 명칭이 본사/지점과 혼합된 경우, 정규식 패턴이나 맵핑 테이블을 통해 정확히 구분합니다.
  - 예: “스타벅스 홍대점” → 스타벅스 으로 통일되도록 처리합니다.

---
## C. 보안 강화 방안

1. 저장 방식 (파일 및 비밀번호 분리 저장)
- 공인인증서 파일은 서버 내 디스크에 직접 저장하지 않고, 암호화된 스토리지(예: AWS S3, GCP Cloud Storage 등)에 저장합니다.
- 비밀번호는 절대 평문으로 저장하지 않으며, 단방향 해시 함수를 사용해 안전하게 보관합니다. 해시 시에는 Secret Key를 함께 적용하여 보안성을 강화합니다.
- 민감한 데이터는 클라우드 KMS를 통해 관리되며, 서버 내부에서도 복호화가 불가능하도록 설계합니다.
- 인증서 파일은 업로드 시 AES-256 방식으로 서버 측 암호화를 수행하고, 복호화는 인증 수행 시점에만 메모리 내에서 일시적으로 처리됩니다.

2. 접근 제어 및 권한 관리
- 인증서 관련 API는 모두 JWT 기반 인증 또는 OAuth2 인증이 완료된 사용자만 접근 가능하도록 제한합니다.
- 인증서 저장 경로 또는 파일에는 서버 프로세스만 접근 가능한 권한만 부여합니다.

3. 전송 및 복호화 보안
- 클라이언트에서 인증서를 업로드할 때는 HTTPS 통신을 강제하여 전송 구간 암호화 적용합니다.
- 복호화는 오직 인증 처리 순간에만, 메모리 상에서 수행되며, 처리 후 즉시 제거됩니다.
- 인증서 파일은 일정 시간이 지나면 자동 삭제되도록 TTL 정책을 적용합니다.

4. 키 관리
- AES 암복호화에 사용하는 키는 클라우드 키 관리 시스템(AWS KMS 등)에서 관리하고, 로컬에 키를 저장하지 않도록 설계합니다.
- 필요 시에는 Rotate Key 정책을 사용하여 주기적으로 키를 교체할 수 있도록 합니다.

5. 감시 로그 및 이상 탐지
- 모든 인증서 접근, 복호화 시도, 인증 처리 요청 등에 대해 감시 로그를 남깁니다.
- 비정상적인 접근(예: 평소와 다른 시간, 위치, 다량의 요청 등)에 대해 실시간 푸시 알림 또는 차단이 가능하도록 설정합니다.

---
## D. 문제상황 해결책 제시

### 즉시 대응 조치
- 해당 시스템을 즉시 격리하거나 오프라인 전환하여 추가적인 피해 확산을 차단합니다.
- 데이터 접근 로그, 인증 로그, DB 트랜잭션 기록 등을 신속하게 수집 및 백업하여 증거를 확보합니다.
- 해당 기능이 노출된 대시보드/서비스 접근을 일시 차단하고, 고객사에 비밀번호 변경 및 보안 점검 요청을 전달합니다.

### 원인 분석
- 우선적으로 API 및 DB 쿼리 레벨에서 사업체 구분 필터링 로직 누락 여부를 점검합니다.
- 접근 권한 로직을 재검토하여 권한 오남용, 세션 공유, 인증 우회 등의 가능성을 확인합니다.
- 서버 및 네트워크 로그를 분석해 외부/내부 비정상 접근 패턴이 있었는지 확인합니다.
- Git 또는 배포 기록을 추적하여 최근 수정 사항이 본 이슈에 영향을 미쳤는지 파악합니다.

### 재발 방지 대책
- 사업체별 데이터 필터링 로직을 API, ORM, SQL 등 모든 계층에서 이중 검증 구조로 구현합니다.
- 보안/권한 관련 테스트 케이스를 자동화하여 배포 전에 항상 점검되도록 합니다.
- 코드 리뷰 시 보안 관련 항목을 별도로 체크리스트화하여 사전 검토 절차를 강화합니다.
- 운영 서버에 대해서는 이상 징후를 실시간 탐지할 수 있는 모니터링 시스템을 도입합니다.
- 정기적인 보안 교육과 실습을 통해 개발자와 운영자 모두 보안 감수성을 유지하도록 합니다.

---
## 3. 실행 및 테스트 가이드

### 서버 주소  
- 서버 주소 : **https://13b740a7f6bf.ngrok-free.app**  
- API Docs : **https://13b740a7f6bf.ngrok-free.app/docs**
---

### 3.1. 로컬 파일로 테스트하는 방법

#### 준비:
- 아래 두 파일을 현재 디렉토리에 준비하세요:
  - `bank_transactions.csv`
  - `rules.json`

#### 실행 명령어:
```bash
curl -X POST https://13b740a7f6bf.ngrok-free.app/api/v1/accounting/process \
  -F "bank_transactions=@bank_transactions.csv" \
  -F "rules=@rules.json"
```
- 위 명령은 현재 저장되어진 디렉토리에서 파일을 읽어 서버에 업로드합니다.

### 3.2. 서버 내 기본 파일로 테스트하기(메일에 첨부해주신 파일)
서버 컨테이너에 내장된 예시 파일을 사용할 경우:

```bash
curl -X POST https://13b740a7f6bf.ngrok-free.app/api/v1/accounting/process
```
- 서버 내부에 정의되어 있는 /app/data/bank_transactions.csv 및 /app/data/rules.json 파일을 사용하여 처리합니다.

### 3.3 분류 결과 조회하기
특정 사업체의 분류된 회계 데이터를 조회하려면:

```bash
curl -X GET "https://13b740a7f6bf.ngrok-free.app/api/v1/accounting/records?companyId=com_1"
```
- com_1 부분은 조회하고 싶은 사업체 ID로 변경 가능합니다.
---
## 4. AI(LLM 등)를 활용해서 위 과제를 진행한 경우, 아래에 해당사항이 있다면 작성해주세요.

AI가 제안한 기본 코드 구조와 전반적인 설계 방향을 참고하여 개발을 시작했고,  
덕분에 개발 초기 방향 설정과 기본적인 함수 구현이나 DB 스키마를 빠르게 구성하여 진행될 수 있었습니다.

하지만 실제 개발 과정에서 AI가 제안한 내용과 다르게 직접 수정하거나 보완한 부분도 있었습니다.  
특히 데이터베이스 트랜잭션 처리 중 id 필드가 NOT NULL 제약 조건이 있다는 점을 발견했는데,  
AI는 이 필드가 필수가 아니거나 NULL이 가능하다고 가정하고 설계한 부분이 있었습니다. 

제가 생각한 스키마에서는 필수 값이었기 때문에, 이 부분을 반영하여 모델과 처리 로직을 수정했습니다.   
이러한 부분은 AI가 현장의 세부 제약 조건까지 완벽히 이해하기 어렵다는 점에서 직접 확인을 통해 수정하였습니다.  
또한, AI가 처음 제안한 프롬프트나 구현 내용이 일부 실제 환경과 맞지 않거나 세부 구현에 누락된 부분이 있어, 이를 보완하기 위해 프롬프트를 재작성하거나 코드를 다듬는 과정을 거쳤습니다. 

예를 들어, 파일 처리 로직과 에러 핸들링 부분을 강화하고, 실제 배포 환경에서 발생하는 경로 문제나 의존성 문제를 직접 해결했습니다.  
이론적으로는 AI가 제안한 구조가 이상적이고 깔끔했으나, 현실적으로는 다양한 환경 차이와 제약 조건으로 인해 여러 차례 직접 테스트하고 수정해야 했습니다.  
이런 점에서 AI가 기본 뼈대를 잘 잡아주었지만, 현장 경험이 부족한 AI의 한계를 보완하는 역할을 제가 수행했다고 생각합니다.

client 테이블을 구성한 이유는 요구사항에 한 고객사라는 부분도 있기도 하였으며, 미래에 해당 프로젝트가 더욱 확장되고 신뢰받아 상용화될 수 있는 과정이 도달한다면 고객사를 위한 테이블이 되어질 수 있을 것이라고 생각했습니다. 