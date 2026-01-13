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

# 2. API 설정
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key.strip())
except:
    st.error("Secrets 확인 필요")

# 🧼 JSON 세탁기
def safe_parse_json(raw_text):
    try:
        clean_text = re.sub(r'```json\s*|```\s*', '', raw_text).strip()
        clean_text = clean_text.replace('\n', ' ').replace('\r', '')
        return json.loads(clean_text)
    except:
        return None

# ==========================================
# 🧠 AI 분석 (이름표 떼고 알맹이만 던지기)
# ==========================================
@st.cache_data(show_spinner=False)
def analyze_news_stripped(news_text):
    
    # 🚨 [전략 수정] 'models/' 접두사를 절대 붙이지 않습니다.
    # 구글 서버가 버전에 따라 접두사를 싫어하는 경우가 있습니다.
    candidates = [
        "gemini-1.5-flash",          # 1순위: 가장 깔끔한 이름
        "gemini-1.5-flash-latest",   # 2순위: 최신 별명
        "gemini-1.5-flash-001",      # 3순위: 구형 고정 버전
        "gemini-1.5-flash-002",      # 4순위: 신형 고정 버전
        "gemini-pro"                 # 5순위: 최후의 보루 (1.0)
    ]
    
    prompt = f"""
    당신은 친절한 뉴스 선생님입니다. 초보자도 이해할 수 있게 비유와 예시를 들어 설명하세요.
    반드시 JSON 형식으로만 출력하세요.

    [뉴스]: {news_text[:1500]}

    [형식]:
    {{"title":"제목","summary":"비유 요약","metrics":{{"who":"주체","whom":"대상","action":"행위","impact":"파장"}},"fact_check":{{"verified":["팩트"],"logic":"근거"}},"balance":{{"stated":"명분","hidden":"속마음","note":"팁"}}}}
    """

    last_error = ""
    
    # 후보군을 순서대로 대입
    for name in candidates:
        try:
            # 여기서 name은 'models/'가 없는 순수 이름입니다.
            model = genai.GenerativeModel(name)
            
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    response_mime_type="application/json"
                )
            )
            # 성공하면 바로 리턴
            return safe_parse_json(response.text), name
            
        except Exception as e:
            last_error = str(e)
            continue # 실패하면 다음 후보로

    return None, f"모든 모델 실패. (마지막 에러: {last_error})"

# --- 화면 구성 ---
st.title("⚖️ NEWS DIETITIAN")
st.caption("접두사 없는 순수 모델명으로 접속을 시도합니다.")

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
                
                if st.button("✨ 분석 시작", key=f"strip_btn_{i}", use_container_width=True, type="primary"):
                    with st.spinner("알맹이 이름으로 접속 시도..."):
                        res, used_name = analyze_news_stripped(entry.description)
                        
                        if res:
                            st.markdown("---")
                            st.markdown(f"#### {res['title']}")
                            st.info(res['summary'])
                            st.caption(f"✅ 접속 성공: {used_name}")
                        else:
                            st.error(f"❌ 실패: {used_name}")
                
                st.link_button("원문", entry.link, use_container_width=True)