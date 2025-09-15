#!/usr/bin/env python3
"""
Analyst Council Streamlit 웹 애플리케이션 실행 스크립트
"""

import subprocess
import sys
import os

def main():
    """Streamlit 앱을 실행합니다."""
    try:
        # Streamlit 앱 실행
        cmd = [sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", "8501"]
        
        print("🚀 Analyst Council 웹 애플리케이션을 시작합니다...")
        print("📱 브라우저에서 http://localhost:8501 을 열어주세요")
        print("⏹️  종료하려면 Ctrl+C를 누르세요")
        print("-" * 50)
        
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n👋 애플리케이션이 종료되었습니다.")
    except Exception as e:
        print(f"❌ 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    main()
