# AI 전문가 위원회 기반 투자 분석 에이전트

## 프로젝트 개요
5개의 서로 다른 투자 철학을 가진 AI 전문가 에이전트를 동시에 실행하고, 그 결과를 종합하여 균형 잡힌 투자 분석 리포트를 생성하는 시스템입니다.

## 핵심 기능
- **5개 전문가 에이전트**: 워렌 버핏(가치), 피터 린치(성장), 레이 달리오(거시), 제임스 사이먼스(퀀트), 마크 미너비니(모멘텀)
- **병렬 처리**: asyncio를 사용한 동시 분석 실행
- **v6.2 최종 안정화 API 전략**: 모든 전문가가 Claude Sonnet 4 사용, GPT-5 폴백
- **실시간 주가 데이터**: yfinance를 통한 실시간 주가 정보 통합
- **의장 메타 에이전트**: 5개 전문가 의견을 종합한 최종 투자 결론 도출
- **자동 폴백 시스템**: API 실패 시 자동으로 백업 모델로 전환
- **투명한 오류 처리**: API 실패 시에도 부분 결과 제공
- **분석 히스토리**: 모든 분석 결과를 자동으로 저장

## 설치 및 실행

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정
```bash
# env.example 파일을 .env로 복사
cp env.example .env

# .env 파일을 편집하여 실제 API 키 입력
# - OPENAI_API_KEY
# - ANTHROPIC_API_KEY  
# - GOOGLE_API_KEY
```

### 3. 실행
```bash
python3 expert_council.py
```

## 프로젝트 구조
```
analyst-council/
├── agents.py              # 핵심 로직: 5개 전문가 에이전트 구현
├── expert_council.py      # 핵심 로직: 전문가 위원회 및 병렬 처리
├── requirements.txt       # Python 의존성
├── env.example           # 환경 변수 예시 파일
├── .env                  # 실제 API 키 (생성 필요)
├── ANALYSIS_HISTORY.md   # 분석 결과 히스토리
├── PROJECT_HISTORY.md    # 프로젝트 개발 히스토리
└── README.md            # 이 파일
```

## 사용법

### 대화형 분석 (권장)
```bash
python3 expert_council.py
```
- 티커 또는 회사명 입력
- 실시간 주가 정보 확인
- 5개 전문가 병렬 분석
- 의장 종합 보고서 생성

### 프로그래밍 방식 사용
```python
from expert_council import ExpertCouncil
import asyncio

async def analyze_stock():
    council = ExpertCouncil()
    result = await council.analyze_stock_parallel("AAPL", require_approval=False)
    
    print(f"시스템 상태: {result['system_status']}")
    for analysis in result['expert_analyses']:
        print(f"\n{analysis['expert_name']}:")
        print(analysis['analysis'])

# 실행
asyncio.run(analyze_stock())
```

## API 전략 (v6.2 최종 안정화)

### 주력 모델
- **모든 전문가**: Claude Sonnet 4-20250514 (안정성 우선)
- **의장**: Claude Sonnet 4-20250514

### 폴백 모델
- **전문가/의장 백업**: GPT-5 (주력 모델 실패 시)

### 특징
- **과부하 방지**: Claude Haiku 모델 제거로 529 오류 완전 해결
- **자동 전환**: API 실패 시 즉시 백업 모델로 전환
- **안정성 최우선**: 검증된 모델만 사용

## 분석 결과 예시

### 전문가별 개별 분석
- **워렌 버핏**: 가치 투자 관점에서 내재가치 분석
- **피터 린치**: 성장 투자 관점에서 PEG 비율 및 성장성 분석
- **레이 달리오**: 거시경제 관점에서 부채 사이클 및 인플레이션 분석
- **제임스 사이먼스**: 퀀트 분석 관점에서 수치적 모델링
- **마크 미너비니**: 모멘텀 관점에서 기술적 분석

### 의장 종합 보고서
- **최종 투자 결론**: 명확한 매수/매도/보유 의견
- **일치점 분석**: 다수 전문가의 공통 의견
- **반대 의견**: 소수 의견 및 리스크 분석
- **핵심 변수**: 투자 성패의 결정 요인
- **전문가별 요약표**: 각 전문가의 모델과 의견

## 개발 완료 단계
1. ✅ **프로젝트 기본 구조 및 환경 설정**
2. ✅ **단일 전문가 에이전트 기능 구현**
3. ✅ **5개 전문가 에이전트 병렬 처리 구현**
4. ✅ **BaseAgent 리팩토링 및 하이브리드 API 준비**
5. ✅ **하이브리드 API 전략 구현 (v3.0 → v4.0 → v5.1 → v6.2)**
6. ✅ **결과 종합 및 리포트 생성 (의장 메타 에이전트)**
7. ✅ **투명한 오류 처리 기능 구현**
8. ✅ **실시간 주가 데이터 통합 (yfinance)**
9. ✅ **자동 폴백 시스템 구현**
10. ✅ **API 안정성 최적화 (Claude Haiku 과부하 해결)**

## 기술 스택
- **Python 3.8+**
- **OpenAI API** (GPT-5)
- **Anthropic API** (Claude Sonnet 4)
- **Google Generative AI** (Gemini)
- **yfinance** (실시간 주가 데이터)
- **asyncio** (비동기 병렬 처리)

## 라이선스
MIT License

## 기여하기
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 문의
프로젝트에 대한 문의사항이 있으시면 GitHub Issues를 통해 연락해주세요.