#!/usr/bin/env python3
"""
AI 전문가 위원회 - 5개 전문가 에이전트 병렬 실행 시스템
"""

import asyncio
import os
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv
import yfinance as yf
from anthropic import APIStatusError

from agents import (
    WarrenBuffettAgent,
    PeterLynchAgent, 
    RayDalioAgent,
    JamesSimonsAgent,
    MarkMinerviniAgent
)

class ExpertCouncil:
    """
    AI 전문가 위원회 - 5개 전문가 에이전트를 병렬로 실행
    """
    
    def __init__(self):
        """전문가 위원회 초기화"""
        load_dotenv()
        
        # API 키 로드
        self.openai_key = os.getenv('OPENAI_API_KEY')
        self.anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        self.google_key = os.getenv('GOOGLE_API_KEY')
        
        # 전문가 에이전트들 초기화 (v6.2 최종 안정화 전략 적용)
        self.agents = {
            # 모든 전문가 -> Claude Sonnet 4 통일 (안정성 우선)
            'warren_buffett': WarrenBuffettAgent(self.anthropic_key, model="claude-sonnet-4-20250514"),
            'ray_dalio': RayDalioAgent(self.anthropic_key, model="claude-sonnet-4-20250514"),
            'peter_lynch': PeterLynchAgent(self.anthropic_key, model="claude-sonnet-4-20250514"),
            'james_simons': JamesSimonsAgent(self.anthropic_key, model="claude-sonnet-4-20250514"),
            'mark_minervini': MarkMinerviniAgent(self.anthropic_key, model="claude-sonnet-4-20250514")
        }
        
        # 폴백 모델 전략 설정 (v6.2 최종 안정화)
        self.fallback_map = {
            "claude-sonnet-4-20250514": ("gpt-5", self.openai_key)
        }
        self.chairman_primary_model = "claude-sonnet-4-20250514"
        self.chairman_fallback_model = "gpt-5"
    
    async def analyze_stock_parallel(self, stock_name: str, require_approval: bool = True) -> Dict[str, Any]:
        """
        주어진 종목에 대해 5개 전문가가 병렬로 분석 수행
        
        Args:
            stock_name (str): 분석할 종목명
            require_approval (bool): 실제 API 사용 전 승인 요청 여부
            
        Returns:
            Dict[str, Any]: 모든 전문가의 분석 결과와 종합 정보
        """
        if require_approval:
            print(f"⚠️ 실제 API 사용 안내")
            print("=" * 50)
            print(f"📈 분석할 종목: {stock_name}")
            print(f"💰 예상 비용: 5개 전문가 + 최종 의장 API 호출 비용")
            print(f"🔍 v6.2 최종 안정화 + 폴백 전략:")
            print(f"   • 주력 전문가: Claude Sonnet 4-20250514 (모든 전문가 통일)")
            print(f"   • 👑 주력 의장: Claude Sonnet 4-20250514")
            print(f"   --------------------------------------------------")
            print(f"   • 🆘 백업 전문가/의장: GPT-5 (주력 모델 실패 시)")
            print("=" * 50)
            
            approval = input("실제 API를 사용하여 분석을 진행하시겠습니까? (y/N): ").strip().lower()
            
            if approval not in ['y', 'yes']:
                print("❌ 분석이 취소되었습니다.")
                return {
                    "stock_name": stock_name,
                    "analysis_timestamp": datetime.now().isoformat(),
                    "total_experts": 0,
                    "successful_analyses": 0,
                    "failed_analyses": 0,
                    "expert_analyses": [],
                    "failed_experts": [],
                    "system_status": "사용자에 의해 취소됨"
                }
            
            print(f"✅ 승인되었습니다. 분석을 시작합니다...")
        
        print(f"🤖 AI 전문가 위원회가 '{stock_name}' 종목을 분석 중...")
        print("=" * 60)
        
        # 각 전문가의 분석 작업을 비동기로 실행
        tasks = []
        for agent_name, agent in self.agents.items():
            task = asyncio.create_task(
                self._analyze_with_agent(agent, stock_name, agent_name)
            )
            tasks.append(task)
        
        # 모든 분석이 완료될 때까지 대기
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 결과 처리
        successful_results = []
        failed_results = []
        
        for result in results:
            if isinstance(result, Exception):
                failed_results.append({
                    "expert_name": "알 수 없음",
                    "error": str(result),
                    "status": "error"
                })
            elif result.get("status") == "success":
                successful_results.append(result)
            else:
                failed_results.append(result)
        
        # 종합 결과 생성
        council_result = {
            "stock_name": stock_name,
            "analysis_timestamp": datetime.now().isoformat(),
            "total_experts": len(self.agents),
            "successful_analyses": len(successful_results),
            "failed_analyses": len(failed_results),
            "expert_analyses": successful_results,
            "failed_experts": failed_results,
            "system_status": self._get_system_status(len(successful_results), len(self.agents))
        }
        
        return council_result
    
    async def get_chairman_verdict(self, stock_info: dict, successful_reports: list) -> dict:
        """
        성공한 전문가 보고서들을 종합하여 최종 결론을 내리는 '의장' 에이전트를 호출합니다.
        """
        stock_name = stock_info['name']
        last_price = stock_info['price']
        currency = stock_info['currency']
        timestamp = stock_info['timestamp']
        
        chairman_persona = f"""
# ROLE
당신은 세계 최고 수준의 투자 전문가 5명으로 구성된 'Analyst Council'의 의장(Chairman)입니다. 당신의 최종 결정은 고객의 중요한 투자 판단에 직접적인 영향을 미칩니다. 당신의 임무는 극도의 신중함, 객관성, 그리고 깊이 있는 통찰력을 바탕으로 최종 투자 보고서를 작성하는 것입니다.

# CONTEXT
당신에게는 5명의 위원(가치 투자자, 성장 투자자, 거시 경제 분석가, 퀀트, 기술적 분석가)이 제출한 개별 분석 보고서가 주어집니다. 각 보고서는 서로 다른 관점과 데이터를 기반으로 하며, 때로는 의견이 서로 충돌할 수 있습니다.

# INSTRUCTION
주어진 5개의 보고서를 종합하여, 아래의 "OUTPUT FORMAT"에 맞춰 최종 투자 보고서를 작성하십시오.

# GUIDELINES & CONSTRAINTS
- **단순 요약 금지**: 각 보고서를 단순히 요약하여 나열하는 것을 절대 금합니다. 보고서들의 내용을 비교, 대조, 종합하여 당신만의 새로운 상위 레벨의 통찰력(Higher-level Insight)을 생성해야 합니다.
- **편향 경계**: 단순히 다수결(Voting)로 의견을 결정하지 마십시오. 소수의 반대 의견에 담긴 논리와 리스크를 반드시 심도 있게 분석하고 보고서에 반영해야 합니다.
- **결정 회피 금지**: 모든 분석 끝에, 반드시 명확하고 실행 가능한(Actionable) 최종 투자 결론을 내려야 합니다. '상황에 따라 다르다' 와 같은 모호한 결론은 허용되지 않습니다.
- **객관적 언어 사용**: 감정적이거나 과장된 표현을 피하고, 데이터와 논리에 기반한 객관적인 어조를 유지하십시오.

# OUTPUT FORMAT
반드시 아래의 마크다운 형식을 엄격하게 준수하여 보고서를 작성하십시오.

---

## Analyst Council 최종 투자 보고서
**분석 대상**: {stock_name}  
**분석 기준**: {timestamp} (최근 종가: {last_price:.2f} {currency})

### 1. 최종 투자 결론 (Final Verdict)
* **투자 의견**: [예: 신중한 매수 (Cautious Buy)]
* **핵심 요약 (3줄)**:
    - [최종 투자 의견에 대한 핵심 이유 1]
    - [최종 투자 의견에 대한 핵심 이유 2]
    - [최종 투자 의견에 대한 핵심 이유 3]

### 2. 투자의견 일치점 (Consensus View)
다수의 전문가들이 공통적으로 동의하는 긍정적 요인(Bull Case)들입니다.
- **강점 1**: [예: 강력한 경제적 해자와 시장 지배력]
- **강점 2**: [예: 지속적인 현금 흐름과 재무 안정성]
- **강점 3**: [예: 데이터 센터 부문의 명확한 성장 동력]

### 3. 핵심 리스크 및 반대 의견 (Contrarian View & Risks)
소수 의견이나 공통적으로 지적된 가장 큰 리스크(Bear Case)들입니다.
- **리스크 1**: [예: 현재 주가는 성장 기대치를 과도하게 반영한 고평가 상태 (피터 린치 지적)]
- **리스크 2**: [예: 경쟁 심화로 인한 시장 점유율 하락 가능성 (마크 미너비니 지적)]
- **리스크 3**: [예: 미-중 기술 갈등과 같은 거시 경제의 불확실성 (레이 달리오 지적)]

### 4. 최종 결정의 핵심 변수 (Key Deciding Factor)
이 투자의 성패는 궁극적으로 다음 변수에 따라 결정될 것입니다.
- [예: "결론적으로, 이 투자의 성패는 AI 반도체 시장의 성장이 현재의 높은 밸류에이션을 정당화할 수 있는 속도로 지속될 수 있는지에 달려 있습니다."]

### 5. 전문가별 의견 요약표
(주석: 아래 '사용한 모델' 열에는 각 전문가가 실제로 사용한 모델명을 정확히 기입하십시오. 주력 모델 실패 시 백업 모델명이 들어갈 수 있습니다.)

| 전문가 | 사용한 모델 | 최종 의견 |
| :--- | :--- | :--- |
| 워렌 버핏 (가치) | [실제 사용한 모델명] | [분석된 최종 의견] |
| 피터 린치 (성장) | [실제 사용한 모델명] | [분석된 최종 의견] |
| 레이 달리오 (거시) | [실제 사용한 모델명] | [분석된 최종 의견] |
| 제임스 사이먼스 (퀀트) | [실제 사용한 모델명] | [분석된 최종 의견] |
| 마크 미너비니 (모멘텀) | [실제 사용한 모델명] | [분석된 최종 의견] |

---
"""
        
        try:
            # --- 로그 추가 1 ---
            print("   - 📜 5명의 보고서를 취합하여 의장에게 전달할 브리핑 자료를 만들고 있습니다...")
            
            # 5개 보고서를 결합할 때 '사용한 모델' 정보 추가
            combined_reports = f"# 분석 대상: {stock_name}\n\n"
            for report in successful_reports:
                combined_reports += f"## {report['expert_name']}의 분석 보고서 (사용한 모델: {report['model_used']})\n\n{report['analysis']}\n\n---\n\n"
            
            # 1. 주력 의장 모델 시도
            try:
                print("   - 👑 주력 의장 모델(Claude Sonnet 4)이 최종 결론을 도출하고 있습니다...")
                from anthropic import AsyncAnthropic
                client = AsyncAnthropic(api_key=self.anthropic_key, timeout=180.0)
                response = await client.messages.create(
                    model=self.chairman_primary_model,
                    max_tokens=4000,
                    temperature=0.3,
                    system=chairman_persona,
                    messages=[{"role": "user", "content": combined_reports}]
                )
                final_report = response.content[0].text if response.content else "의장 보고서 생성에 실패했습니다."
                print("   - ✅ 의장 보고서 생성이 완료되었습니다!")
                return {"chairman_report": final_report, "status": "success"}
            except Exception as e:
                print(f"   - ⚠️ 주력 의장 모델 실패. 백업 의장 모델로 전환합니다. (사유: {e})")
                # 2. 백업 의장 모델 시도
                try:
                    print("   - 🔄 백업 의장 모델(GPT-5)로 최종 결론을 재시도합니다...")
                    from openai import AsyncOpenAI
                    client = AsyncOpenAI(api_key=self.openai_key)
                    response = await client.chat.completions.create(
                        model=self.chairman_fallback_model,
                        max_completion_tokens=4000,
                        temperature=0.3,
                        messages=[
                            {"role": "system", "content": chairman_persona},
                            {"role": "user", "content": combined_reports}
                        ]
                    )
                    final_report = response.choices[0].message.content
                    print("   - ✅ 백업 의장 보고서 생성이 완료되었습니다!")
                    return {"chairman_report": final_report, "status": "success"}
                except Exception as backup_e:
                    return {"chairman_report": None, "status": "error", "error_message": f"백업 의장 모델 실패: {backup_e}"}
        except Exception as e:
            return {"chairman_report": None, "status": "error", "error_message": str(e)}
    
    async def _analyze_with_agent(self, agent, stock_name: str, agent_name: str) -> Dict[str, Any]:
        """
        개별 전문가의 분석을 비동기로 실행하고, 주력 모델 실패 시 백업 모델로 전환합니다.
        """
        try:
            # 1. 주력 모델 시도
            print(f"   - ➡️ {agent.expert_name}: 주력 모델({agent.model})로 분석 시작...")
            result = await agent.analyze_stock(stock_name)
            if result['status'] == 'error': 
                raise Exception(result['error_message'])
            return result
        except Exception as e:
            print(f"   - ⚠️ {agent.expert_name}: 주력 모델 분석 실패. 백업 모델로 전환합니다. (사유: {e})")
            # 2. 백업 모델 시도
            backup_model_info = self.fallback_map.get(agent.model)
            if not backup_model_info:
                return {
                    "expert_name": agent_name, 
                    "status": "error", 
                    "error_message": "백업 모델이 지정되지 않음", 
                    "model_used": agent.model
                }
            backup_model, backup_key = backup_model_info
            try:
                # 백업 모델로 에이전트 정보 임시 변경
                agent.model, agent.api_key = backup_model, backup_key
                agent._initialize_client()
                print(f"   - 🔄 {agent.expert_name}: 백업 모델({backup_model})로 분석 재시도...")
                result = await agent.analyze_stock(stock_name)
                return result
            except Exception as backup_e:
                return {
                    "expert_name": agent_name, 
                    "status": "error", 
                    "error_message": f"백업 모델 분석 실패: {backup_e}", 
                    "model_used": backup_model
                }
            finally:
                # 항상 원래 모델 정보로 복원
                original_agent = next(item for item in self.agents.values() if item.expert_name == agent.expert_name)
                agent.model, agent.api_key = original_agent.model, self.anthropic_key
                agent._initialize_client()
    
    def _get_system_status(self, successful_count: int, total_count: int) -> str:
        """
        시스템 상태 메시지 생성
        
        Args:
            successful_count (int): 성공한 분석 수
            total_count (int): 전체 전문가 수
            
        Returns:
            str: 시스템 상태 메시지
        """
        if successful_count == total_count:
            return f"✅ 본 분석은 {total_count}명의 AI 전문가 전원의 의견을 종합한 결과입니다."
        else:
            failed_count = total_count - successful_count
            return f"⚠️ 주의: {total_count}명 중 {successful_count}명의 의견만을 종합한 결과입니다. (누락: {failed_count}명)"
    
    def save_analysis_history(self, analysis_result: Dict[str, Any]) -> None:
        """
        분석 결과를 히스토리 파일에 저장
        
        Args:
            analysis_result (Dict[str, Any]): 분석 결과
        """
        history_file = "ANALYSIS_HISTORY.md"
        
        # 기존 히스토리 읽기
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            content = "# AI 전문가 위원회 - 분석 결과 히스토리\n\n이 파일은 각 전문가 에이전트의 분석 결과와 앙상블 리포트를 기록합니다.\n\n## 분석 히스토리\n\n---\n"
        
        # 새로운 분석 결과 추가
        timestamp = analysis_result["analysis_timestamp"]
        stock_name = analysis_result["stock_name"]
        system_status = analysis_result["system_status"]
        
        # 주가 정보가 있으면 추가
        stock_info_text = ""
        if "stock_info" in analysis_result:
            stock_info = analysis_result["stock_info"]
            stock_info_text = f"""
**분석 대상**: {stock_info.get('name', stock_name)} ({stock_info.get('ticker', 'N/A')})
**분석 기준**: {stock_info.get('timestamp', timestamp)}
**최근 종가**: {stock_info.get('price', 0):.2f} {stock_info.get('currency', 'USD')}

"""
        
        new_entry = f"""
## {timestamp} - {stock_name} 분석 결과

{stock_info_text}**시스템 상태**: {system_status}

"""
        
        # 의장 보고서가 있으면 먼저 추가
        if "chairman_report" in analysis_result and analysis_result["chairman_report"]:
            new_entry += f"""
### 👑 Analyst Council 최종 종합 보고서

{analysis_result["chairman_report"]}

---

### 전문가별 개별 분석 결과

"""
        else:
            new_entry += f"""
### 전문가별 분석 결과

"""
        
        # 각 전문가의 분석 결과 추가
        for expert_analysis in analysis_result["expert_analyses"]:
            expert_name = expert_analysis.get("expert_name", "알 수 없는 전문가")
            analysis_text = expert_analysis.get("analysis", "")
            
            # analysis_text가 None이거나 빈 문자열인 경우 처리
            if not analysis_text or analysis_text.strip() == "":
                analysis_text = "분석 결과를 가져올 수 없습니다."
            
            new_entry += f"""
#### {expert_name}
{analysis_text}

---
"""
        
        # 실패한 전문가 정보 추가
        if analysis_result["failed_experts"]:
            new_entry += "\n### 실패한 전문가\n"
            for failed_expert in analysis_result["failed_experts"]:
                expert_name = failed_expert.get("expert_name", "알 수 없음")
                error_msg = failed_expert.get("error_message", failed_expert.get("error", "알 수 없는 오류"))
                new_entry += f"- **{expert_name}**: {error_msg}\n"
            new_entry += "\n"
        
        # 파일에 저장
        with open(history_file, 'w', encoding='utf-8') as f:
            f.write(content + new_entry)
        
        print(f"📝 분석 결과가 {history_file}에 저장되었습니다.")

def main():
    """
    메인 실행 함수
    """
    print("🤖 AI 전문가 위원회 기반 투자 분석 에이전트")
    print("=" * 60)
    
    # API 키 확인
    load_dotenv()
    openai_key = os.getenv('OPENAI_API_KEY')
    
    if not openai_key or openai_key == 'your_openai_api_key_here':
        print("❌ OPENAI_API_KEY가 설정되지 않았습니다.")
        print("📝 .env 파일에 실제 API 키를 입력하세요.")
        return
    
    # 사용자 입력 받기
    stock_name = input("\n📈 분석할 종목명을 입력하세요: ").strip()
    
    if not stock_name:
        print("❌ 종목명을 입력해주세요.")
        return
    
    # 전문가 위원회 생성
    council = ExpertCouncil()
    
    async def run_analysis():
        print(f"\n🔄 {stock_name} 종목 분석을 시작합니다...")
        result = await council.analyze_stock_parallel(stock_name, require_approval=True)
        
        # 결과 출력
        print(f"\n📊 분석 완료!")
        print(f"종목: {result['stock_name']}")
        print(f"시스템 상태: {result['system_status']}")
        print(f"성공한 분석: {result['successful_analyses']}/{result['total_experts']}")
        
        # 각 전문가의 분석 결과 출력
        for expert_analysis in result["expert_analyses"]:
            print(f"\n🔍 {expert_analysis['expert_name']} 분석:")
            print("-" * 50)
            print(expert_analysis["analysis"])
        
        # 실패한 전문가 정보 출력
        if result["failed_experts"]:
            print(f"\n⚠️ 실패한 전문가:")
            for failed_expert in result["failed_experts"]:
                expert_name = failed_expert.get("expert_name", "알 수 없음")
                error_msg = failed_expert.get("error_message", failed_expert.get("error", "알 수 없는 오류"))
                print(f"  - {expert_name}: {error_msg}")
        
        # 히스토리 저장
        council.save_analysis_history(result)
        
        return result
    
    # 비동기 실행
    try:
        result = asyncio.run(run_analysis())
        print(f"\n🎉 전문가 위원회 분석이 완료되었습니다!")
        print(f"📝 분석 결과가 ANALYSIS_HISTORY.md에 저장되었습니다.")
    except Exception as e:
        print(f"❌ 분석 중 오류 발생: {str(e)}")

async def run_interactive_council_analysis():
    """
    대화형 전문가 위원회 분석 함수
    """
    print("🤖 AI 전문가 위원회 기반 투자 분석 에이전트")
    print("=" * 60)
    
    # API 키 확인
    load_dotenv()
    openai_key = os.getenv('OPENAI_API_KEY')
    
    if not openai_key or openai_key == 'your_openai_api_key_here':
        print("❌ OPENAI_API_KEY가 설정되지 않았습니다.")
        print("📝 .env 파일에 실제 API 키를 입력하세요.")
        return
    
    # --- 지능형 티커 입력 및 검증 로직 ---
    ticker_str = None
    while True:
        user_input = input("\n📈 분석할 종목의 티커(예: AAPL) 또는 회사명(예: Apple)을 입력하세요: ").strip()
        if not user_input:
            print("❌ 입력이 없습니다. 다시 시도해주세요.")
            continue
        try:
            # yfinance로 입력된 값의 정보 확인 시도
            print(f"🔍 '{user_input}' 정보를 조회하는 중...")
            ticker_obj = yf.Ticker(user_input)
            info = ticker_obj.info
            # .info에 내용이 없으면 유효하지 않은 티커로 간주
            if not info or info.get('shortName') is None:
                raise ValueError("유효한 티커 정보를 찾을 수 없습니다.")
            company_name = info.get('longName', user_input)
            confirmed_ticker = info.get('symbol', user_input.upper())
            # 사용자에게 확인 요청
            approval = input(f"   -> '{company_name} ({confirmed_ticker})' 종목이 맞습니까? (Y/n): ").strip().lower()
            if approval in ['y', 'yes', '']: # 그냥 엔터도 '예'로 간주
                ticker_str = confirmed_ticker
                break
            else:
                print("   -> 🔄 다시 입력해주세요.")
                continue
        except Exception as e:
            print(f"   -> ❌ '{user_input}'에 해당하는 종목을 찾을 수 없습니다. 정확한 티커나 회사명으로 다시 시도해주세요.")
            # print(f"(디버그 정보: {e})") # 디버깅 시 주석 해제
    
    # --- 주가 정보 수집 ---
    try:
        ticker_obj = yf.Ticker(ticker_str)
        info = ticker_obj.info
        history = ticker_obj.history(period="1d")
        
        stock_info = {
            'name': info.get('longName', ticker_str),
            'ticker': ticker_str,
            'price': history['Close'].iloc[-1] if not history.empty else 0.0,
            'currency': info.get('currency', 'USD'),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        print(f"⚠️ 주가 정보 조회 실패: {e}. 기본 정보로 진행합니다.")
        stock_info = {
            'name': ticker_str,
            'ticker': ticker_str,
            'price': 0.0,
            'currency': 'USD',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    # --- (기존 로직 계속) 전문가 위원회 생성 ---
    council = ExpertCouncil()
    
    # 분석 실행
    result = await council.analyze_stock_parallel(ticker_str, require_approval=True)
    
    # 사용자가 취소한 경우
    if result.get('system_status') == "사용자에 의해 취소됨":
        print("분석이 취소되었습니다.")
        return

    successful_reports = result.get('expert_analyses', [])
    
    # 성공한 분석 결과 수에 따라 분기 처리
    if len(successful_reports) >= 3:
        # === 의장 보고서 생성 ===
        print("\n👑 3명 이상의 전문가 의견이 모여 의장 보고서를 생성합니다...")
        chairman_result = await council.get_chairman_verdict(stock_info, successful_reports)
        
        if chairman_result.get("status") == "success":
            final_report_text = chairman_result["chairman_report"]
            print("\n" + "="*60)
            print("📜 Analyst Council 최종 종합 보고서")
            print("="*60)
            print(final_report_text)
            
            # 히스토리 저장을 위해 chairman_report 추가
            result["chairman_report"] = final_report_text
        else:
            print("❌ 의장 보고서 생성에 실패했습니다. 개별 보고서를 출력합니다.")
            # 실패 시 아래 폴백 로직으로 이동
            for report in successful_reports:
                print(f"\n--- [ {report['expert_name']}의 의견 ] ---")
                print(report['analysis'])

    elif 1 <= len(successful_reports) < 3:
        # === 개별 보고서만 제공 (폴백) ===
        print("\n⚠️ 의장 보고서 생성 최소 인원(3명)에 미치지 못하여, 성공한 전문가의 개별 보고서를 전달합니다.")
        for report in successful_reports:
            print(f"\n--- [ {report['expert_name']}의 의견 ] ---")
            print(report['analysis'])
            
    else:
        # === 분석 완전 실패 ===
        print("\n❌ 분석에 성공한 전문가가 없어 보고서를 생성할 수 없습니다.")

    # 히스토리 저장 (stock_info 포함)
    result["stock_info"] = stock_info
    council.save_analysis_history(result)
    
    print(f"\n🎉 전문가 위원회 분석이 완료되었습니다!")
    print(f"📝 분석 결과가 ANALYSIS_HISTORY.md에 저장되었습니다.")
    
    return result

if __name__ == "__main__":
    asyncio.run(run_interactive_council_analysis())
