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
    st.error("Secrets에서 API 키를 확인해 주세요.")

# 🔍 [핵심] 내 계정에서 실제로 쓸 수 있는 모델의 정확한 풀네임을 찾는 함수
def get_exact_model_name():
    try:
        # 사용 가능한 모든 모델을 가져옵니다.
        for m in genai.list_models():
            # 이름에 '1.5'와 'flash'가 들어있는 녀석을 찾습니다.
            if '1.5' in m.name and 'flash' in m.name and 'generateContent' in m.supported_generation_methods:
                return m.name  # 예: 'models/gemini-1.5-flash' 또는 'models/gemini-1.5-flash-latest'
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
# 🧠 AI 분석 (자동 조준 로직 적용)
# ==========================================
@st.cache_data(show_spinner=False)
def analyze_news_with_ai(news_text):
    # 실시간으로 사용자님 계정에 맞는 정확한 이름을 가져옵니다.
    working_name = get_exact_model_name()
    model = genai.GenerativeModel(working_name)
    
    # 초심자 배려 프롬프트
    prompt = f"""
    당신은 친절한 뉴스 해설가입니다. 지식이 부족한 사람도 이해할 수 있게 비유와 예시를 들어 분석하세요.
    모든 답변은 반드시 JSON 형식으로만 출력하세요.

    [뉴스]: {news_text[:1500]}

    [형식]:
    {{"title":"제목","summary":"비유 섞인 요약","metrics":{{"who":"주체","whom":"대상","action":"행위","impact":"파장"}},"fact_check":{{"verified":["팩트"],"logic":"분석 근거"}},"balance":{{"stated":"명분","hidden":"속마음","note":"관전포인트"}}}}
    """
    
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
                
                if st.button("✨ 쉬운 분석", key=f"final_btn_{i}", use_container_width=True, type="primary"):
                    with st.spinner("가장 정확한 모델 주소를 찾는 중..."):
                        res, model_info = analyze_news_with_ai(entry.description)
                        if res:
                            st.markdown("---")
                            st.markdown(f"#### {res['title']}")
                            st.info(res['summary'])
                            
                            m1, m2 = st.columns(2)
                            with m1:
                                st.markdown(f"<div class='insight-card'><div class='fact-header'>WHO</div><div class='fact-content'>{res['metrics']['who']}</div></div>", unsafe_allow_html=True)
                            with m2:
                                st.markdown(f"<div class='insight-card'><div class='fact-header'>IMPACT</div><div class='fact-content'>{res['metrics']['impact']}</div></div>", unsafe_allow_html=True)
                            
                            st.caption(f"🤖 연결 성공: {model_info} | ⏱️ {round(time.time(), 2)}")
                        else:
                            st.error(f"오류: {model_info}")
                
                st.link_button("원문 보기", entry.link, use_container_width=True)