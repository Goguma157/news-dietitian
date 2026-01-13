import streamlit as st
import requests
import json

st.set_page_config(page_title="Key Hardcode Test")

# 🚨 [중요] 여기에 API 키를 직접 붙여넣으세요! (테스트 후 반드시 삭제)
# 예: MY_DIRECT_KEY = "AIzaSyDxxxxxxxxx..."
MY_DIRECT_KEY = "AIzaSyBbODkWxnzNz0ZPRH88VcBk_SFYniulDjM"

st.title("🧨 키 하드코딩 테스트")
st.warning("테스트가 끝나면 코드에서 키를 반드시 지우세요!")

if st.button("직접 연결 시도"):
    # 1. 모델 주소 (가장 표준적인 1.5 Flash)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={MY_DIRECT_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{"parts": [{"text": "Hello, are you working?"}]}]
    }

    try:
        st.write(f"접속 시도 중... (키: {MY_DIRECT_KEY[:5]}...)")
        
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        if response.status_code == 200:
            st.balloons()
            st.success("✅ **성공했습니다!**")
            st.json(response.json())
            st.markdown("### 💡 결론")
            st.info("Streamlit Secrets(설정)에 문제가 있었습니다. 코드는 정상이었습니다.")
        else:
            st.error(f"❌ **실패 (HTTP {response.status_code})**")
            st.code(response.text)
            st.markdown("### 💡 결론")
            st.error("이 키 자체가 '생성(Generate)' 권한이 없습니다. 구글 클라우드에서 API 사용 설정(Enable)이 풀렸거나, 결제 계정 이슈일 수 있습니다.")
            
    except Exception as e:
        st.error(f"통신 오류: {e}")