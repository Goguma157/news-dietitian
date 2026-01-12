import streamlit as st
import google.generativeai as genai
import importlib.metadata

st.title("🏥 긴급 점검: 내 로봇의 상태는?")

# 1. 설치된 도구 버전 확인
try:
    version = importlib.metadata.version('google-generativeai')
    st.info(f"📦 현재 설치된 도구 버전: {version}")
    
    # 버전이 0.7.0보다 낮은지 확인
    if version < "0.7.0":
        st.error("🚨 버전이 너무 낮습니다! requirements.txt가 반영되지 않았어요.")
    else:
        st.success("✅ 버전은 최신입니다. (0.7.0 이상)")
except:
    st.error("설치된 버전을 확인할 수 없습니다.")

# 2. 내 열쇠로 쓸 수 있는 모델 명단 조회
st.divider()
st.write("🔑 API 키로 사용 가능한 모델을 조회합니다...")

try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    # 모델 목록 가져오기
    available_models = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            available_models.append(m.name)
            
    if len(available_models) > 0:
        st.success(f"🎉 조회 성공! 사용 가능한 모델 ({len(available_models)}개):")
        st.code(available_models)
    else:
        st.warning("⚠️ 조회는 됐는데, 사용 가능한 모델이 하나도 없다고 나옵니다.")
        
except Exception as e:
    st.error(f"🚨 조회 실패 (에러 내용): {e}")
    st.write("팁: 에러가 400번대라면 API Key가 잘못되었거나 만료되었을 수 있습니다.")