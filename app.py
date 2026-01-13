import streamlit as st
import google.generativeai as genai
import time

st.set_page_config(page_title="최후의 모델 찾기", page_icon="🕵️")

st.title("🕵️ 범인(작동하는 모델) 색출 작전")

# 1. API 키 가져오기
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    st.success(f"🔑 키 인식됨: {api_key[:5]}... (Secrets 설정 확인 완료)")
except:
    st.error("Secrets에 API Key가 없습니다!")
    st.stop()

# 2. 전수조사 시작
if st.button("🚀 작동하는 모델 찾기 시작", type="primary"):
    log_area = st.empty()
    logs = []
    
    try:
        # 모델 목록 조회
        models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        logs.append(f"📋 조회된 모델 수: {len(models)}개")
        
        found_working_model = False
        
        for m in models:
            model_name = m.name
            display_name = m.displayName
            
            with st.spinner(f"테스트 중: {display_name} ({model_name})..."):
                try:
                    # 테스트 전송
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content("Hello")
                    
                    if response.text:
                        st.balloons()
                        st.markdown("### 🎉 찾았다! 작동하는 모델!")
                        st.success(f"✅ 모델명: `{model_name}`")
                        st.json({
                            "display_name": display_name,
                            "full_name": model_name,
                            "test_response": response.text
                        })
                        st.info("👇 아래 코드를 복사해서 사용하세요!")
                        st.code(f'model = genai.GenerativeModel("{model_name}")', language='python')
                        found_working_model = True
                        break # 성공하면 바로 중단
                        
                except Exception as e:
                    logs.append(f"❌ 실패 ({model_name}): {str(e)[:50]}...")
                    log_area.text("\n".join(logs))
                    time.sleep(0.5) # 너무 빠르면 차단되니 살짝 대기
        
        if not found_working_model:
            st.error("💀 모든 모델 테스트 실패. API 설정(Enable) 문제일 가능성이 큽니다.")
            st.write("상세 에러 로그:")
            st.code("\n".join(logs))

    except Exception as e:
        st.error(f"목록 조회조차 실패했습니다. API 키가 잘못되었거나 프로젝트 권한 문제입니다.\n에러: {e}")