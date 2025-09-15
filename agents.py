#!/usr/bin/env python3
"""
AI 전문가 위원회 - 개별 전문가 에이전트 구현 (리팩토링 버전)
"""

import os
import asyncio
import json
from datetime import datetime
from abc import ABC, abstractmethod
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import yfinance as yf
from typing import Dict, Any, List

class BaseAgent(ABC):
    """
    모든 전문가 에이전트의 기본 추상 클래스
    """
    
    def __init__(self, api_key: str, model: str, expert_name: str, expert_type: str):
        """
        BaseAgent 초기화
        
        Args:
            api_key (str): API 키
            model (str): 사용할 모델 이름
            expert_name (str): 전문가 이름
            expert_type (str): 전문가 유형
        """
        self.api_key = api_key
        self.model = model
        self.expert_name = expert_name
        self.expert_type = expert_type
        self.persona = self._get_persona()
        
        # API 클라이언트 초기화 (모델에 따라 다르게 설정)
        self._initialize_client()
    
    def _initialize_client(self):
        """모델에 따라 적절한 API 클라이언트를 초기화"""
        if "gpt" in self.model.lower():
            self.client = AsyncOpenAI(api_key=self.api_key)
        elif "claude" in self.model.lower():
            self.client = AsyncAnthropic(api_key=self.api_key, timeout=180.0)
        elif "gemini" in self.model.lower():
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel(self.model)
        else:
            # 기본값으로 OpenAI 사용
            self.client = AsyncOpenAI(api_key=self.api_key)
    
    @abstractmethod
    def _get_persona(self) -> str:
        """
        하위 클래스에서 각 전문가의 페르소나를 정의합니다.
        
        Returns:
            str: 전문가의 페르소나 프롬프트
        """
        pass
    
    async def analyze_stock(self, stock_name: str) -> Dict[str, Any]:
        """
        주어진 종목에 대한 분석을 비동기로 수행
        
        Args:
            stock_name (str): 분석할 종목명
            
        Returns:
            Dict[str, Any]: 분석 결과
        """
        try:
            # 사용자 프롬프트 생성
            user_prompt = self._create_user_prompt(stock_name)
            
            # API 호출 (모델에 따라 다르게 처리)
            if "gpt" in self.model.lower():
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.persona},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_completion_tokens=2000
                )
                analysis_result = response.choices[0].message.content
                
            elif "claude" in self.model.lower():
                response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=2000,
                    temperature=0.7,
                    system=self.persona,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                analysis_result = response.content[0].text
                
            elif "gemini" in self.model.lower():
                response = await self.client.generate_content_async(
                    f"{self.persona}\n\n{user_prompt}",
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=2000,
                        temperature=0.7
                    ),
                    safety_settings={
                        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    }
                )
                analysis_result = response.text
                
            else:
                # 기본값으로 OpenAI 사용
                response = await self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": self.persona},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_completion_tokens=2000
                )
                analysis_result = response.choices[0].message.content
            
            # analysis_result가 None이거나 빈 문자열인 경우 처리
            if not analysis_result or analysis_result.strip() == "":
                analysis_result = f"[{self.expert_name}] 분석 결과를 생성할 수 없습니다. API 응답이 비어있습니다."
            
            return {
                "expert_name": self.expert_name,
                "expert_type": self.expert_type,
                "analysis": analysis_result,
                "status": "success",
                "model_used": self.model
            }
            
        except Exception as e:
            return {
                "expert_name": self.expert_name,
                "expert_type": self.expert_type,
                "analysis": None,
                "status": "error",
                "error_message": str(e),
                "model_used": self.model
            }
    
    def _create_user_prompt(self, stock_name: str) -> str:
        """
        yfinance로 실시간 데이터를 가져와 종목 분석을 위한 사용자 프롬프트를 생성합니다.
        """
        try:
            ticker = yf.Ticker(stock_name)
            info = ticker.info
            history = ticker.history(period="5d") # 최근 5일치 데이터
            company_name = info.get('longName', stock_name)
            last_close_price = history['Close'].iloc[-1] if not history.empty else "N/A"
            currency = info.get('currency', 'USD')
            prompt_header = f"""
아래 '분석 기준 정보'를 바탕으로 주어진 종목을 분석해주세요. 당신의 평가는 반드시 이 기준 정보를 반영해야 합니다.

분석 기준 정보
분석 기준일: {datetime.now().strftime('%Y-%m-%d')}

최근 종가: {last_close_price:.2f} {currency}

분석 대상
종목명: {company_name} ({stock_name})
"""
        except Exception as e:
            print(f"⚠️ yfinance 데이터 조회 실패: {e}. 종목명만으로 분석을 진행합니다.")
            prompt_header = f"""

분석 대상
종목명: {stock_name}
"""

        analysis_requests = """
분석 요청사항:
기업의 사업 모델과 핵심 경쟁우위 분석

재무 건전성 및 수익성 평가

제공된 최근 종가를 기준으로 한 투자 가치 평가 (밸류에이션)

투자 의견 (강력매수/매수/보유/매도/강력매도)

주요 리스크 요인

분석 결과는 구체적이고 실용적인 조언을 포함하여 제시해주세요.
"""
        return prompt_header + analysis_requests

class WarrenBuffettAgent(BaseAgent):
    """
    워렌 버핏 스타일의 가치 투자 전문가 에이전트
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        super().__init__(
            api_key=api_key,
            model=model,
            expert_name="워렌 버핏 (가치 투자)",
            expert_type="value_investor"
        )
    
    def _get_persona(self) -> str:
        return """
당신은 워렌 버핏의 투자 철학을 따르는 가치 투자 전문가입니다.

핵심 투자 원칙:
1. 장기적 관점: 최소 10년 이상 보유할 수 있는 기업만 투자
2. 내재가치 분석: 기업의 진정한 가치를 정확히 평가
3. 안전마진: 내재가치 대비 충분히 저평가된 가격에만 투자
4. 경영진 신뢰: 능력 있고 정직한 경영진이 있는 기업
5. 사업 이해도: 자신이 완전히 이해할 수 있는 사업 모델
6. 경쟁우위: 지속 가능한 모어(Moat)를 가진 기업
7. 재무 건전성: 낮은 부채비율과 안정적인 현금흐름

분석 시 고려사항:
- P/E, P/B, ROE, ROA, 부채비율 등 재무 지표
- 기업의 사업 모델과 경쟁우위
- 경영진의 능력과 기업 문화
- 산업 전망과 시장 지위
- 배당 정책과 주주 친화적 정책

투자 의견은 다음 중 하나로 제시:
- 강력 매수: 내재가치 대비 30% 이상 저평가
- 매수: 내재가치 대비 10-30% 저평가  
- 보유: 공정가치 수준
- 매도: 내재가치 대비 고평가
- 강력 매도: 내재가치 대비 30% 이상 고평가

분석 결과는 구체적이고 실용적인 조언을 제공하며, 장기적 관점에서의 투자 가치를 중심으로 평가합니다.
"""

class PeterLynchAgent(BaseAgent):
    """
    피터 린치 스타일의 성장 투자 전문가 에이전트
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        super().__init__(
            api_key=api_key,
            model=model,
            expert_name="피터 린치 (성장 투자)",
            expert_type="growth_investor"
        )
    
    def _get_persona(self) -> str:
        return """
당신은 피터 린치의 투자 철학을 따르는 성장 투자 전문가입니다.

핵심 투자 원칙:
1. 성장성 중심: 매출과 이익이 지속적으로 성장하는 기업
2. PEG 비율: P/E 비율을 성장률로 나눈 PEG 비율이 1 이하인 기업
3. 사업 이해도: 자신이 이해할 수 있는 사업 모델
4. 경쟁우위: 지속 가능한 경쟁우위를 가진 기업
5. 재무 건전성: 부채가 적고 현금흐름이 좋은 기업
6. 시장 규모: 성장 가능한 큰 시장에 있는 기업
7. 경영진: 주주 친화적이고 능력 있는 경영진

분석 시 고려사항:
- 매출 성장률, 이익 성장률, PEG 비율
- 시장 점유율과 성장 잠재력
- 신제품 개발과 혁신 능력
- 해외 진출 가능성
- 배당 정책과 주주 친화적 정책

투자 의견은 다음 중 하나로 제시:
- 강력 매수: PEG < 0.5, 높은 성장률
- 매수: PEG 0.5-1.0, 안정적 성장
- 보유: PEG 1.0-1.5, 적정 성장
- 매도: PEG > 1.5, 성장 둔화
- 강력 매도: 성장 정체, 경쟁력 약화

분석 결과는 성장 잠재력과 투자 가치를 중심으로 평가합니다.
"""

class RayDalioAgent(BaseAgent):
    """
    레이 달리오 스타일의 거시 경제 전문가 에이전트
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        super().__init__(
            api_key=api_key,
            model=model,
            expert_name="레이 달리오 (거시 경제)",
            expert_type="macro_economist"
        )
    
    def _get_persona(self) -> str:
        return """
당신은 레이 달리오의 투자 철학을 따르는 거시 경제 전문가입니다.

핵심 투자 원칙:
1. 거시 경제 분석: 경제 사이클과 시장 전체 상황 분석
2. 리스크 관리: 다양한 자산 클래스에 분산 투자
3. 시장 사이클: 장기 부채 사이클과 단기 비즈니스 사이클 고려
4. 통화 정책: 중앙은행 정책과 금리 변화 분석
5. 지리적 분산: 글로벌 경제 상황과 지역별 리스크
6. 인플레이션: 물가 상승과 실질 수익률 고려
7. 시스템적 리스크: 금융 시스템의 안정성 평가

분석 시 고려사항:
- GDP 성장률, 인플레이션, 실업률
- 중앙은행 정책과 금리 동향
- 환율 변동과 무역 수지
- 정치적 리스크와 규제 환경
- 기술 혁신과 산업 구조 변화
- 인구 구조와 사회적 트렌드

투자 의견은 다음 중 하나로 제시:
- 강력 매수: 거시 환경 매우 유리
- 매수: 거시 환경 양호
- 보유: 거시 환경 중립
- 매도: 거시 환경 부정적
- 강력 매도: 거시 환경 매우 부정적

분석 결과는 거시 경제 관점에서의 리스크와 기회를 중심으로 평가합니다.
"""

class JamesSimonsAgent(BaseAgent):
    """
    제임스 사이먼스 스타일의 퀀트 전문가 에이전트
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        super().__init__(
            api_key=api_key,
            model=model,
            expert_name="제임스 사이먼스 (퀀트)",
            expert_type="quantitative_analyst"
        )
    
    def _get_persona(self) -> str:
        return """
당신은 제임스 사이먼스의 투자 철학을 따르는 퀀트 전문가입니다.

핵심 투자 원칙:
1. 데이터 기반 분석: 정량적 데이터와 통계적 모델 활용
2. 패턴 인식: 시장에서 반복되는 패턴과 상관관계 분석
3. 수학적 모델: 복잡한 수학적 모델을 통한 예측
4. 리스크 관리: 정교한 리스크 모델과 포지션 사이징
5. 알고리즘 트레이딩: 체계적이고 자동화된 투자 전략
6. 백테스팅: 과거 데이터를 통한 전략 검증
7. 지속적 최적화: 모델의 지속적인 개선과 업데이트

분석 시 고려사항:
- 기술적 지표 (RSI, MACD, 볼린저 밴드 등)
- 가격 패턴과 추세 분석
- 거래량과 변동성 분석
- 상관관계와 회귀 분석
- 시장 효율성과 이상 현상
- 리스크 지표 (VaR, 베타, 샤프 비율 등)

투자 의견은 다음 중 하나로 제시:
- 강력 매수: 강력한 양의 신호
- 매수: 양의 신호
- 보유: 중립 신호
- 매도: 음의 신호
- 강력 매도: 강력한 음의 신호

분석 결과는 정량적 데이터와 수학적 모델을 중심으로 평가합니다.
"""

class MarkMinerviniAgent(BaseAgent):
    """
    마크 미너비니 스타일의 모멘텀/기술 전문가 에이전트
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        super().__init__(
            api_key=api_key,
            model=model,
            expert_name="마크 미너비니 (모멘텀/기술)",
            expert_type="momentum_technical"
        )
    
    def _get_persona(self) -> str:
        return """
당신은 마크 미너비니의 투자 철학을 따르는 모멘텀/기술 전문가입니다.

핵심 투자 원칙:
1. 모멘텀 투자: 강한 상승 모멘텀을 가진 종목 선호
2. 기술적 분석: 차트 패턴과 기술적 지표 중심 분석
3. 상대 강도: 시장 대비 상대적 강도 분석
4. 거래량 분석: 거래량과 가격 움직임의 상관관계
5. 추세 추종: 명확한 상승 추세를 보이는 종목
6. 리스크 관리: 손절매와 수익 실현 전략
7. 시장 타이밍: 시장 전체의 방향성과 타이밍

분석 시 고려사항:
- 상대 강도 지수 (RSI)
- 이동평균선과 골든크로스
- 거래량 패턴과 브레이크아웃
- 지지선과 저항선
- 차트 패턴 (컵앤핸들, 플래그 등)
- 시장 전체의 모멘텀

투자 의견은 다음 중 하나로 제시:
- 강력 매수: 강한 상승 모멘텀
- 매수: 양의 모멘텀
- 보유: 중립 모멘텀
- 매도: 음의 모멘텀
- 강력 매도: 강한 하락 모멘텀

분석 결과는 기술적 분석과 모멘텀을 중심으로 평가합니다.
"""

def test_warren_buffett_agent():
    """
    워렌 버핏 에이전트 테스트 함수
    """
    # API 키 로드
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key or api_key == 'your_openai_api_key_here':
        print("❌ OPENAI_API_KEY가 설정되지 않았습니다.")
        print("📝 .env 파일에 실제 API 키를 입력하세요.")
        return
    
    # 에이전트 생성
    agent = WarrenBuffettAgent(api_key)
    
    # 테스트 종목 분석
    test_stock = "애플"
    print(f"🤖 {agent.expert_name}이 '{test_stock}' 종목을 분석 중...")
    print("=" * 60)
    
    async def run_analysis():
        result = await agent.analyze_stock(test_stock)
        
        if result["status"] == "success":
            print(f"✅ 분석 완료!")
            print(f"전문가: {result['expert_name']}")
            print(f"모델: {result['model_used']}")
            print("\n📊 분석 결과:")
            print("-" * 40)
            print(result["analysis"])
        else:
            print(f"❌ 분석 실패: {result['error_message']}")
    
    # 비동기 실행
    asyncio.run(run_analysis())

if __name__ == "__main__":
    test_warren_buffett_agent()
