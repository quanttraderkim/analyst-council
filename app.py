import streamlit as st
import asyncio
import os
import sys
from pathlib import Path

# 현재 디렉토리를 Python 경로에 추가
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from expert_council import ExpertCouncil

# 페이지 설정
st.set_page_config(
    page_title="Analyst Council",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일링
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .expert-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #1f77b4;
    }
    .chairman-report {
        background-color: #fff3cd;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border: 2px solid #ffc107;
    }
    .success-message {
        color: #28a745;
        font-weight: bold;
    }
    .error-message {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def run_async_analysis(council, stock_info):
    """비동기 분석을 실행하고, 필요 시 의장 보고서까지 생성하는 함수"""
    async def async_analysis():
        try:
            # 5명의 전문가 분석 실행
            result = await council.analyze_stock_parallel(stock_info['ticker'], require_approval=False)

            # 성공한 전문가가 3명 이상이면 의장 보고서 생성
            successful_reports = result.get('expert_analyses', [])
            if len(successful_reports) >= 3:
                chairman_result = await council.get_chairman_verdict(stock_info, successful_reports)
                if chairman_result.get("status") == "success":
                    result["chairman_report"] = chairman_result["chairman_report"]
            
            return result
        except Exception as e:
            return {"error": str(e)}
    
    # asyncio 이벤트 루프 실행
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(async_analysis())
        loop.close()
        return result
    except Exception as e:
        return {"error": f"비동기 실행 오류: {str(e)}"}

def main():
    # 메인 헤더
    st.markdown('<h1 class="main-header">📊 Analyst Council</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # 사이드바 - API 키 입력
    with st.sidebar:
        st.header("🔑 API 키 설정")
        st.markdown("분석을 위해 다음 API 키들이 필요합니다:")
        
        openai_key = st.text_input(
            "OpenAI API Key",
            type="password",
            help="OpenAI API 키를 입력하세요",
            placeholder="sk-..."
        )
        
        anthropic_key = st.text_input(
            "Anthropic API Key", 
            type="password",
            help="Anthropic API 키를 입력하세요",
            placeholder="sk-ant-..."
        )
        
        st.markdown("---")
        st.markdown("### 📋 사용 모델")
        st.markdown("""
        **전문가 모델 (v6.2):**
        - 워렌 버핏: Claude Sonnet 4
        - 피터 린치: GPT-5
        - 레이 달리오: Claude Sonnet 4
        - 제임스 사이먼스: Claude Sonnet 4
        - 마크 미너비니: Claude Sonnet 4
        
        **의장 모델:**
        - Claude Sonnet 4 (주), GPT-5 (백업)
        """)
        
        st.markdown("---")
        st.markdown("### 💡 사용법")
        st.markdown("""
        1. API 키를 입력하세요
        2. 분석할 종목의 티커를 입력하세요
        3. '분석 시작' 버튼을 클릭하세요
        4. 결과를 확인하세요
        """)
    
    # 메인 컨텐츠
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("🎯 종목 분석")
        
        # 종목 티커 입력
        stock_ticker = st.text_input(
            "분석할 종목의 티커를 입력하세요",
            placeholder="예: AAPL, NVDA, TSLA, MSFT",
            help="주식 티커 심볼을 입력하세요 (예: Apple=AAPL, NVIDIA=NVDA)"
        )
        
        # 분석 시작 버튼
        analyze_button = st.button(
            "🚀 분석 시작",
            type="primary",
            use_container_width=True
        )
    
    with col2:
        st.header("📈 실시간 정보")
        if stock_ticker:
            try:
                import yfinance as yf
                ticker = yf.Ticker(stock_ticker)
                info = ticker.info
                
                if 'currentPrice' in info:
                    st.metric(
                        "현재가",
                        f"${info['currentPrice']:.2f}",
                        f"{info.get('regularMarketChange', 0):.2f}"
                    )
                    st.metric(
                        "시가총액",
                        f"${info.get('marketCap', 0):,}"
                    )
                else:
                    st.warning("종목 정보를 가져올 수 없습니다.")
            except Exception as e:
                st.warning(f"종목 정보 로딩 실패: {str(e)}")
    
    # 분석 실행
    if analyze_button:
        # 입력 검증
        if not openai_key or not anthropic_key:
            st.error("❌ OpenAI API 키와 Anthropic API 키를 모두 입력해주세요.")
            return
        
        if not stock_ticker:
            st.error("❌ 분석할 종목의 티커를 입력해주세요.")
            return
        
        stock_ticker_upper = stock_ticker.upper()
        
        # yfinance로 주가 정보 가져오기
        try:
            import yfinance as yf
            from datetime import datetime
            ticker_obj = yf.Ticker(stock_ticker_upper)
            info = ticker_obj.info
            history = ticker_obj.history(period="1d")
            stock_info = {
                'name': info.get('longName', stock_ticker_upper), 
                'ticker': stock_ticker_upper,
                'price': history['Close'].iloc[-1] if not history.empty else 0.0,
                'currency': info.get('currency', 'USD'),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception:
            st.error("주가 정보 조회에 실패했습니다. 유효한 티커인지 확인해주세요.")
            return
        
        # ExpertCouncil 인스턴스 생성
        council = ExpertCouncil()
        council.openai_key = openai_key
        council.anthropic_key = anthropic_key
        
        # 분석 실행
        with st.spinner("🔄 Analyst Council이 분석 중입니다... 이 과정은 1-2분 소요될 수 있습니다."):
            result = run_async_analysis(council, stock_info)
        
        # 결과 표시
        if "error" in result:
            st.error(f"❌ 분석 중 오류가 발생했습니다: {result['error']}")
            return
        
        st.markdown("---")
        st.header("✨ 분석 결과")
        
        # 의장 보고서가 있으면 출력
        if "chairman_report" in result and result["chairman_report"]:
            st.markdown(result["chairman_report"], unsafe_allow_html=True)
        # 의장 보고서는 없지만, 개별 보고서가 있을 경우
        elif result.get('expert_analyses'):
            st.warning(f"⚠️ {result.get('system_status')}")
            st.markdown("#### 전문가별 개별 분석 결과")
            for report in result['expert_analyses']:
                with st.expander(f"**{report['expert_name']}** (사용한 모델: {report['model_used']})"):
                    st.markdown(report['analysis'])
        # 성공한 분석이 아무것도 없을 경우
        else:
            st.error("❌ 분석에 성공한 전문가가 없어 보고서를 생성할 수 없습니다.")
        
        # 실패한 전문가 정보 표시
        if result.get('failed_experts'):
            with st.expander("실패한 전문가 정보 보기"):
                st.json(result['failed_experts'])
        
        # 히스토리 저장
        try:
            result["stock_info"] = stock_info
            council.save_analysis_history(result)
            st.success("✅ 분석 결과가 `ANALYSIS_HISTORY.md`에 저장되었습니다.")
        except Exception as e:
            st.warning(f"히스토리 저장 실패: {str(e)}")

if __name__ == "__main__":
    main()
