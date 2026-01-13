import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Key Doctor", page_icon="🩺")

st.title("🩺 API Key 정밀 건강검진")

# 1. 키 가져오기
try:
    my_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=my_key)
    st.success(f"🔑 키 인식 성공! (앞 5자리: {my_key[:5]}...)")
except:
    st.error("Secrets에 키가 없습니다.")
    st.stop()

# 2. 모델 목록 조회
st.markdown("### 📋 구글 서버에서 가져온 '사용 가능 모델' 명단")

if st.button("진단 시작", type="primary"):
    try:
        all_models = genai.list_models()
        flash_1_5_found = False
        
        # 목록을 하나씩 출력
        model_names = []
        for m in all_models:
            # 대화(generateContent)가 가능한 모델만 필터링
            if 'generateContent' in m.supported_generation_methods:
                model_names.append(m.name)
                if 'gemini-1.5-flash' in m.name:
                    flash_1_5_found = True

        # 결과 보여주기
        st.json(model_names)
        
        st.markdown("---")
        st.markdown("### 👨‍⚕️ 진단 결과")
        
        if flash_1_5_found:
            st.success("✅ **정상입니다!** 목록에 'gemini-1.5-flash'가 포함되어 있습니다.")
            st.info("💡 결론: 키는 문제없습니다. 코드에서 이름을 부르는 방식 문제였을 확률이 큽니다. 아까 드린 '강제 고정 코드'를 쓰시면 100% 됩니다.")
        else:
            st.error("❌ **비정상입니다!** 목록에 'gemini-1.5-flash'가 없습니다.")
            st.warning("💡 결론: 이 키는 '실험용' 혹은 '옛날 프로젝트'에 묶여 있습니다. 새 프로젝트 생성이 제대로 안 되었을 수 있습니다.")
            
    except Exception as e:
        st.error(f"진단 중 에러 발생: {e}")