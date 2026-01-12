import streamlit as st
import feedparser
import google.generativeai as genai
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
    div[data-testid="stContainer"] { background-color: #ffffff; border-radius: 12px; border: 1px solid #e5e7eb; }
    .insight-card { background-color: #f8f9fa; padding: 18px; border-radius: 10px; border-left: 4px solid #0f172a; margin-bottom: 12px; height: 100%; }
    .fact-header { font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; margin-bottom: 5px; }
    .fact-content { font-size: 15px; font-weight: 600; color: #0f172a; line-height: 1.4; }
    .badge-valid { background-color: #dcfce7; color: #166534; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; margin-right: 5px; }
</style>
""", unsafe_allow_html=True)

try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("Secrets에 API Key를 넣어주세요!")

# 작동 모델 찾기 로직
def find_working_model():
    try:
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for m in available:
            if '1.5' in m and 'flash' in m: return m
        return available[0] if available else "gemini-1.5-flash"
    except:
        return "gemini-1.5-flash"

@st.cache_data(ttl=600, show_spinner=False)
def fetch_news_data(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=5)
        return feedparser.parse(response.content) if response.status_code == 200 else None
    except:
        return None

# 🧼 [보강] AI 답변 청소기: 따옴표와 줄바꿈 문제를 강제로 해결
def force_clean_json(text):
    # 1. 마크다운 태그 제거
    text = re.sub(r'```json\s*|```\s*', '', text).strip()
    # 2. 제어 문자(줄바꿈 등) 제거
    text = text.replace('\n', ' ').replace('\r', '')
    return text

@st.cache_data(show_spinner=False)
def analyze_news_with_ai(news_text):
    model_name = find_working_model()
    model = genai.GenerativeModel(model_name)
    
    # 💡 AI에게 아주 엄격하게 명령 (줄바꿈 금지 등)
    prompt = f"""
    당신은 전문 뉴스 분석가입니다. 아래 뉴스를 JSON으로 분석하세요.
    중요: 모든 결과값에는 절대 줄바꿈(\n)을 넣지 말고 한 줄로 작성하세요. 
    값 내부에 큰따옴표가 필요하면 작은따옴표로 대체하세요.

    [뉴스]: {news_text[:2000]}

    [형식]:
    {{"title":"제목","summary":"요약","metrics":{{"who":"주체","whom":"대상","action":"행위","impact":"파장"}},"fact_check":{{"verified":["팩트1"],"controversial":["논란"],"logic":"근거"}},"balance":{{"stated":"명분","hidden":"의도","note":"총평"}}}}
    """
    
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.1, # 창의성을 최소화하여 에러 방지
            response_mime_type="application/json"
        )
    )
    
    # 🧼 한 번 더 닦아내고 읽기
    cleaned = force_clean_json(response.text)
    return json.loads(cleaned)

# --- 화면 구성 ---
st.title("⚖️ NEWS DIETITIAN")

rss_url = "http://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=01&plink=RSSREADER"
news = fetch_news_data(rss_url)

if news and len(news.entries) > 0:
    cols = st.columns(3)
    for i in range(min(12, len(news.entries))):
        entry = news.entries[i]
        with cols[i % 3]:
            with st.container(border=True):
                st.caption(f"{entry.published[:16]}")
                st.markdown(f"**{entry.title}**")
                
                if st.button("✨ Deep Analysis", key=f"btn_{i}", use_container_width=True, type="primary"):
                    with st.spinner("AI 분석 중..."):
                        try:
                            start_time = time.time()
                            input_text = f"제목: {entry.title}\n내용: {entry.description}"
                            res = analyze_news_with_ai(input_text)
                            
                            st.markdown("---")
                            st.markdown(f"#### {res['title']}")
                            st.info(res['summary'])
                            
                            m1, m2 = st.columns(2)
                            with m1:
                                st.markdown(f"<div class='insight-card'><div class='fact-header'>WHO</div><div class='fact-content'>{res['metrics']['who']}</div></div>", unsafe_allow_html=True)
                                st.markdown(f"<div class='insight-card'><div class='fact-header'>ACTION</div><div class='fact-content'>{res['metrics']['action']}</div></div>", unsafe_allow_html=True)
                            with m2:
                                st.markdown(f"<div class='insight-card'><div class='fact-header'>WHOM</div><div class='fact-content'>{res['metrics']['whom']}</div></div>", unsafe_allow_html=True)
                                st.markdown(f"<div class='insight-card'><div class='fact-header'>IMPACT</div><div class='fact-content'>{res['metrics']['impact']}</div></div>", unsafe_allow_html=True)

                            t1, t2 = st.tabs(["✅ Fact", "⚖️ Balance"])
                            with t1:
                                for f in res['fact_check']['verified']:
                                    st.markdown(f"<span class='badge-valid'>팩트</span> {f}", unsafe_allow_html=True)
                                st.caption(f"근거: {res['fact_check']['logic']}")
                            with t2:
                                st.success(f"**명분:** {res['balance']['stated']}")
                                st.warning(f"**이면:** {res['balance']['hidden']}")
                            
                            st.write(f"🧐 **Point:** {res['balance']['note']}")
                            st.caption(f"⏱️ {round(time.time() - start_time, 2)}s")
                            
                        except Exception:
                            # 🛡️ 최후의 보루: 에러가 나면 한 번 더 시도하게 유도
                            st.error("데이터가 꼬였습니다. 버튼을 다시 한 번만 눌러주세요!")
                
                st.link_button("Read Original", entry.link, use_container_width=True)