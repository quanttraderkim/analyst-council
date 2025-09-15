# AI 전문가 위원회 기반 투자 분석 에이전트

## 프로젝트 개요
5개의 서로 다른 투자 철학을 가진 AI 전문가 에이전트를 동시에 실행하고, 그 결과를 종합하여 균형 잡힌 투자 분석 리포트를 생성하는 시스템입니다.

## 핵심 기능
- **5개 전문가 에이전트**: 워렌 버핏(가치), 피터 린치(성장), 레이 달리오(거시), 제임스 사이먼스(퀀트), 마크 미너비니(모멘텀)
- **병렬 처리**: asyncio를 사용한 동시 분석 실행
- **하이브리드 API**: 각 전문가별로 다른 AI 모델 사용 가능
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
python expert_council.py
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

### 기본 사용법
```python
from expert_council import ExpertCouncil
import asyncio

async def analyze_stock():
    council = ExpertCouncil()
    result = await council.analyze_stock_parallel("애플")
    
    print(f"시스템 상태: {result['system_status']}")
    for analysis in result['expert_analyses']:
        print(f"\n{analysis['expert_name']}:")
        print(analysis['analysis'])

# 실행
asyncio.run(analyze_stock())
```

### 개별 전문가 사용법
```python
from agents import WarrenBuffettAgent
import asyncio

async def single_analysis():
    agent = WarrenBuffettAgent(api_key="your_key", model="gpt-4o")
    result = await agent.analyze_stock("애플")
    print(result['analysis'])

# 실행
asyncio.run(single_analysis())
```

## 개발 단계
1. ✅ 프로젝트 기본 구조 및 환경 설정
2. ✅ 단일 전문가 에이전트 기능 구현
3. ✅ 5개 전문가 에이전트 병렬 처리 구현
4. ✅ BaseAgent 리팩토링 및 하이브리드 API 준비
5. ⏳ 하이브리드 API 전략 구현
6. ⏳ 결과 종합 및 리포트 생성
7. ⏳ 투명한 오류 처리 기능 구현
