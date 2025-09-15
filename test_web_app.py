#!/usr/bin/env python3
"""
Streamlit 웹 애플리케이션 테스트 스크립트
"""

import requests
import time
import subprocess
import sys

def test_streamlit_app():
    """Streamlit 앱이 정상적으로 실행되는지 테스트"""
    
    print("🧪 Streamlit 웹 애플리케이션 테스트 시작...")
    
    # 1. Streamlit 프로세스 시작
    print("1️⃣ Streamlit 프로세스 시작 중...")
    try:
        process = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", "app.py", 
            "--server.port", "8503", "--server.headless", "true"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 2. 서버 시작 대기
        print("2️⃣ 서버 시작 대기 중... (10초)")
        time.sleep(10)
        
        # 3. HTTP 요청 테스트
        print("3️⃣ HTTP 요청 테스트...")
        try:
            response = requests.get("http://localhost:8503", timeout=10)
            if response.status_code == 200:
                print("✅ 웹 애플리케이션이 정상적으로 실행 중입니다!")
                print(f"📱 브라우저에서 http://localhost:8503 접속 가능")
                return True
            else:
                print(f"❌ HTTP 응답 오류: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ HTTP 요청 실패: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Streamlit 실행 실패: {e}")
        return False
    finally:
        # 4. 프로세스 정리
        print("4️⃣ 프로세스 정리 중...")
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            process.kill()

def test_imports():
    """필요한 모듈들이 정상적으로 import되는지 테스트"""
    
    print("🔍 모듈 import 테스트...")
    
    try:
        import streamlit as st
        print("✅ streamlit import 성공")
    except ImportError as e:
        print(f"❌ streamlit import 실패: {e}")
        return False
    
    try:
        from expert_council import ExpertCouncil
        print("✅ expert_council import 성공")
    except ImportError as e:
        print(f"❌ expert_council import 실패: {e}")
        return False
    
    try:
        from agents import WarrenBuffettAgent
        print("✅ agents import 성공")
    except ImportError as e:
        print(f"❌ agents import 실패: {e}")
        return False
    
    return True

def main():
    """메인 테스트 함수"""
    
    print("=" * 60)
    print("🚀 Analyst Council 웹 애플리케이션 테스트")
    print("=" * 60)
    
    # 1. 모듈 import 테스트
    if not test_imports():
        print("❌ 모듈 import 테스트 실패")
        return False
    
    # 2. Streamlit 앱 테스트
    if not test_streamlit_app():
        print("❌ Streamlit 앱 테스트 실패")
        return False
    
    print("=" * 60)
    print("🎉 모든 테스트 통과!")
    print("📱 웹 애플리케이션을 사용하려면:")
    print("   python3 run_app.py")
    print("   또는")
    print("   streamlit run app.py")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    main()
