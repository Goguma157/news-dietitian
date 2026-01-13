import streamlit as st
import google.generativeai as genai

st.title("🩺 새 계정 API 모델 진단")

# 1. 새로 만든 키가 인식되는지 확인
try:
    my_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=my_key)
    st.info(f"🔑 인식된 키: {my_key[:5]}...")
except:
    st.error("Secrets에 새 API 키를 먼저 넣어주세요!")
    st.stop()

# 2. 이 키로 쓸 수 있는 모델 리스트 싹 긁어오기
if st.button("사용 가능한 모델 명단 보기"):
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 목록에 1.5가 있는지 체크
        has_1_5 = any("1.5" in name for name in models)
        
        st.write("### 현재 내 계정의 모델 리스트")
        st.json(models)
        
        if has_1_5:
            st.success("✅ 축하합니다! 이 계정에는 Gemini 1.5 모델이 포함되어 있습니다.")
            st.markdown("**이제 할당량 걱정 없이 마음껏 쓰실 수 있습니다!**")
        else:
            st.warning("⚠️ 아직 1.5 모델이 보이지 않습니다. 잠시 후 다시 확인해보세요.")
            
    except Exception as e:
        st.error(f"진단 중 오류: {e}")