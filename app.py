import streamlit as st
import feedparser
import google.generativeai as genai
import json
import requests
import time
import re

# 1. 페이지 설정
st.set_page_config(page_title="News Dietitian", page_icon="⚖️", layout="wide")

# CSS 스타일 (가독성 유지)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Pretendard', sans-serif !important; color: #1a1a1a; }
    .insight-card { background-color: #f8f9fa; padding: 18px; border-radius: 10px; border-left: 4px solid #0f172a; margin-bottom: 12px; height: 100%; }
    .fact-header { font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; margin-bottom: 5px; }
    .fact-content { font-size: 15px; font-weight: 600; color: #0f172a; line-height: 1.4; }
</style>
""", unsafe_allow_html=True)

# API 설정
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("Secrets에서 API Key를 확인해주세요!")

# 🔍 [수정] 내 계정에서 실제로 쓸 수 있는 1.5-flash의 정확한 '이름표'를 찾는 함수
def get_real_model_name():
    try:
        for m in genai.list_models():
            # 이름에 1.5와 flash가 들어있고, 분석 기능이 있는 모델을 찾습니다.
            if '1.5' in m.name and 'flash' in m.name and 'generateContent' in m.supported_generation_methods:
                return m.name # 예: 'models/gemini-1.5-flash' 또는 'models/gemini-1.5-flash-latest'
        return "models/gemini-1.5-flash" # 정 못 찾으면 기본값
    except:
        return "models/gemini-1.5-flash"

# 🧼 AI 답변 보정 도구
def safe_parse_json(raw_text):
    try:
        clean_text = re.sub(r'```json\s*|```\s*', '', raw_text).strip()
        clean_text = clean_text.replace('\n', ' ').replace('\r', '')
        return json.loads(clean_text)
    except:
        return None

# ==========================================
# 🧠 AI 분석 (이름 찾기 로직 적용)
# ==========================================
@st.cache_data(show_spinner=False)
def analyze_news_with_ai(news_text):
    # 실시간으로 내 계정에 맞는 모델 이름을 가져옵니다.
    working_name = get_real_model_name()
    model = genai.GenerativeModel(working_name)
    
    prompt = f"초보자도 알기 쉽게 비유를 들어 이 뉴스를 JSON으로 분석해줘: {news_text[:1500]}"
    
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                response_mime_type="application/json"
            )
        )
        return safe_parse_json(response.text), working_name
    except Exception as e:
        return None, str(e)

# --- 화면 구성 ---
st.title("⚖️ NEWS DIETITIAN")

rss_url = "http://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=01&plink=RSSREADER"
resp = requests.get(rss_url)
news = feedparser.parse(resp.content)

if news.entries:
    cols = st.columns(3)
    for i, entry in enumerate(news.entries[:12]):
        with cols[i % 3]:
            with st.container(border=True):
                st.markdown(f"**{entry.title}**")
                
                # 버튼을 누를 때마다 새로 분석하도록 키 값을 조정
                if st.button("✨ 쉬운 분석", key=f"re_btn_{i}", use_container_width=True, type="primary"):
                    with st.spinner("AI가 정확한 모델 주소를 찾는 중..."):
                        res, model_info = analyze_news_with_ai(entry.description)
                        if res:
                            st.info(res.get('summary', '요약 준비 중...'))
                            st.caption(f"🤖 연결 성공: {model_info}")
                        else:
                            st.error(f"오류 발생: {model_info}")
                st.link_button("원문 보기", entry.link, use_container_width=True)