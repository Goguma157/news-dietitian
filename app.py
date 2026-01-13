import streamlit as st
import feedparser
import google.generativeai as genai
from google.generativeai.types import RequestOptions # 정식 경로 설정을 위해 필요
import json
import requests
import time
import re

# 1. 페이지 설정
st.set_page_config(page_title="News Dietitian", page_icon="⚖️", layout="wide")

# CSS 스타일 유지
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Pretendard', sans-serif !important; color: #1a1a1a; }
    .insight-card { background-color: #f8f9fa; padding: 18px; border-radius: 10px; border-left: 4px solid #0f172a; margin-bottom: 12px; height: 100%; }
</style>
""", unsafe_allow_html=True)

# API 설정
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("Secrets에서 API 키를 확인해 주세요.")

# 🧼 AI 답변 보정 도구
def safe_parse_json(raw_text):
    try:
        clean_text = re.sub(r'```json\s*|```\s*', '', raw_text).strip()
        clean_text = clean_text.replace('\n', ' ').replace('\r', '')
        return json.loads(clean_text)
    except:
        return None

# ==========================================
# 🧠 AI 분석 (v1 정식 경로 강제 지정)
# ==========================================
@st.cache_data(show_spinner=False)
def analyze_news_with_ai(news_text):
    
    # 🚨 [핵심 해결책] 
    # 1. 모델 이름을 명확히 지정합니다.
    target_model = "gemini-1.5-flash"
    
    # 2. v1beta가 아닌 'v1' 정식 버전을 사용하도록 강제로 설정합니다.
    # 이 옵션이 404 에러를 막는 강력한 방어막이 됩니다.
    options = RequestOptions(api_version="v1")
    
    try:
        model = genai.GenerativeModel(model_name=target_model)
        
        prompt = f"""
        당신은 친절한 뉴스 선생님입니다. 지식이 부족한 초보자도 이해할 수 있게 비유와 예시를 들어 분석하세요.
        답변은 반드시 JSON 형식으로만 출력하세요.

        [뉴스]: {news_text[:1500]}

        [형식]:
        {{"title":"제목","summary":"비유 섞인 요약","metrics":{{"who":"주체","whom":"대상","action":"행위","impact":"파장"}},"fact_check":{{"verified":["팩트"],"logic":"분석 근거"}},"balance":{{"stated":"명분","hidden":"속마음","note":"관전포인트"}}}}
        """
        
        # request_options를 통해 v1 경로로 접속합니다.
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                response_mime_type="application/json"
            ),
            request_options=options # 여기에 v1 설정 투입!
        )
        return safe_parse_json(response.text), target_model
        
    except Exception as e:
        return None, str(e)

# --- 화면 구성 ---
st.title("⚖️ NEWS DIETITIAN")
st.caption("v1 정식 경로를 통해 1.5 Flash 엔진에 직접 연결합니다.")

rss_url = "http://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=01&plink=RSSREADER"
try:
    resp = requests.get(rss_url, timeout=10)
    news = feedparser.parse(resp.content)
except:
    st.error("뉴스를 가져오지 못했습니다.")
    news = None

if news and news.entries:
    cols = st.columns(3)
    for i, entry in enumerate(news.entries[:12]):
        with cols[i % 3]:
            with st.container(border=True):
                st.markdown(f"**{entry.title}**")
                
                if st.button("✨ 쉬운 분석", key=f"v1_btn_{i}", use_container_width=True, type="primary"):
                    with st.spinner("정식 경로(v1)로 안전하게 접속 중..."):
                        res, used_model = analyze_news_with_ai(entry.description)
                        if res:
                            st.markdown("---")
                            st.markdown(f"#### {res['title']}")
                            st.info(res['summary'])
                            st.caption(f"✅ 정식 경로 연결 성공: {used_model}")
                        else:
                            st.error(f"오류: {used_model}")
                
                st.link_button("원문 보기", entry.link, use_container_width=True)