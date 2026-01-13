import streamlit as st
import feedparser
import google.generativeai as genai
import json
import requests
import time
import re

# 1. 페이지 설정
st.set_page_config(page_title="News Dietitian", page_icon="⚖️", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Pretendard', sans-serif !important; color: #1a1a1a; }
    .insight-card { background-color: #f8f9fa; padding: 18px; border-radius: 10px; border-left: 4px solid #0f172a; margin-bottom: 12px; height: 100%; }
</style>
""", unsafe_allow_html=True)

# 2. API 설정 (오류 방지)
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    # 공백 제거 등 안전장치
    genai.configure(api_key=api_key.strip())
except:
    st.error("Secrets에 API Key를 확인해주세요!")

# 🧼 JSON 보정 함수
def safe_parse_json(raw_text):
    try:
        clean_text = re.sub(r'```json\s*|```\s*', '', raw_text).strip()
        clean_text = clean_text.replace('\n', ' ').replace('\r', '')
        return json.loads(clean_text)
    except:
        return None

# ==========================================
# 🔍 1. 확실한 모델 이름 찾기 (여기가 핵심!)
# ==========================================
def get_verified_model_name():
    try:
        # 내 키로 조회되는 모든 모델을 가져옴
        all_models = genai.list_models()
        
        # 1순위: '1.5'와 'flash'가 들어간 모델 찾기
        for m in all_models:
            if 'generateContent' in m.supported_generation_methods:
                if '1.5' in m.name and 'flash' in m.name:
                    return m.name # (예: models/gemini-1.5-flash-001)
        
        # 2순위: 없으면 그냥 'flash' 들어간 거 아무거나
        for m in all_models:
            if 'generateContent' in m.supported_generation_methods and 'flash' in m.name:
                return m.name
                
        return "models/gemini-1.5-flash" # 비상용 기본값
    except Exception as e:
        # 목록 조회 실패 시 기본값 리턴
        return "models/gemini-1.5-flash"

# ==========================================
# 🧠 2. 찾은 모델로 분석하기
# ==========================================
@st.cache_data(show_spinner=False)
def analyze_news_final(news_text):
    # 1단계에서 찾은 '확실한 이름'을 가져옵니다.
    target_name = get_verified_model_name()
    
    model = genai.GenerativeModel(target_name)
    
    prompt = f"""
    당신은 친절한 뉴스 선생님입니다. 초보자도 이해할 수 있게 비유와 예시를 들어 설명하세요.
    반드시 JSON 형식으로만 출력하세요.

    [뉴스]: {news_text[:1500]}

    [형식]:
    {{"title":"제목","summary":"비유 요약","metrics":{{"who":"주체","whom":"대상","action":"행위","impact":"파장"}},"fact_check":{{"verified":["팩트"],"logic":"근거"}},"balance":{{"stated":"명분","hidden":"속마음","note":"팁"}}}}
    """
    
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                response_mime_type="application/json"
            )
        )
        return safe_parse_json(response.text), target_name
    except Exception as e:
        return None, str(e)

# --- 화면 구성 ---
st.title("⚖️ NEWS DIETITIAN")
st.caption("API 연결 성공! 목록에서 확인된 모델을 사용합니다.")

rss_url = "http://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=01&plink=RSSREADER"
try:
    resp = requests.get(rss_url, timeout=10)
    news = feedparser.parse(resp.content)
except:
    news = None

if news and news.entries:
    cols = st.columns(3)
    for i, entry in enumerate(news.entries[:12]):
        with cols[i % 3]:
            with st.container(border=True):
                st.markdown(f"**{entry.title}**")
                
                if st.button("✨ 분석 시작", key=f"real_final_btn_{i}", use_container_width=True, type="primary"):
                    with st.spinner("AI 연결 중..."):
                        res, model_used = analyze_news_final(entry.description)
                        
                        if res:
                            st.markdown("---")
                            st.markdown(f"#### {res['title']}")
                            st.info(res['summary'])
                            
                            m1, m2 = st.columns(2)
                            with m1: st.markdown(f"<div class='insight-card'><b>WHO:</b> {res['metrics']['who']}</div>", unsafe_allow_html=True)
                            with m2: st.markdown(f"<div class='insight-card'><b>IMPACT:</b> {res['metrics']['impact']}</div>", unsafe_allow_html=True)
                            
                            st.caption(f"✅ 사용된 모델: {model_used}")
                        else:
                            st.error(f"분석 실패: {model_used}")
                
                st.link_button("원문 보기", entry.link, use_container_width=True)