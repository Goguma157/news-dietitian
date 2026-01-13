import streamlit as st
import feedparser
import google.generativeai as genai
import json
import requests
import time
import re

# 1. 페이지 설정
st.set_page_config(page_title="News Dietitian", page_icon="⚖️", layout="wide")

# CSS 스타일 (디자인 유지)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Pretendard', sans-serif !important; color: #1a1a1a; }
    div[data-testid="stContainer"] { background-color: #ffffff; border-radius: 12px; border: 1px solid #e5e7eb; }
    .insight-card { background-color: #f8f9fa; padding: 18px; border-radius: 10px; border-left: 4px solid #0f172a; margin-bottom: 12px; height: 100%; }
    .fact-header { font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; margin-bottom: 5px; }
    .fact-content { font-size: 15px; font-weight: 600; color: #0f172a; line-height: 1.4; }
    .badge-valid { background-color: #dcfce7; color: #166534; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; margin-right: 5px; }
    h1 { font-weight: 800 !important; letter-spacing: -1px; color: #111827; }
</style>
""", unsafe_allow_html=True)

# API 설정
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("Secrets에 API Key를 넣어주세요!")

# 🔍 작동하는 모델을 직접 찾는 함수
def find_working_model():
    try:
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for m in available:
            if '1.5' in m and 'flash' in m: return m.replace('models/', '')
        for m in available:
            if 'flash' in m: return m.replace('models/', '')
        return available[0].replace('models/', '') if available else "gemini-1.5-flash"
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

# 🧼 [강력 보정] AI 답변에서 JSON만 강제로 추출하고 다듬는 도구
def safe_parse_json(raw_text):
    try:
        # 1. 마크다운 기호 제거
        clean_text = re.sub(r'```json\s*|```\s*', '', raw_text).strip()
        # 2. 줄바꿈을 공백으로 치환
        clean_text = clean_text.replace('\n', ' ').replace('\r', '')
        # 3. JSON 로드 시도
        return json.loads(clean_text)
    except:
        # 4. 만약 실패하면 텍스트 내에서 { } 구간만 찾아내서 다시 시도
        try:
            match = re.search(r'\{.*\}', clean_text)
            if match:
                return json.loads(match.group())
        except:
            return None
    return None

@st.cache_data(show_spinner=False)
def analyze_news_with_ai(news_text):
    model_name = find_working_model()
    model = genai.GenerativeModel(model_name)
    
    prompt = f"""
    당신은 뉴스 분석가입니다. 아래 뉴스를 JSON으로 분석하세요.
    중요: 답변은 반드시 JSON 형식만 출력하세요. 설명이나 다른 말은 절대 금지입니다.

    [뉴스]: {news_text[:2000]}

    [형식]:
    {{"title":"제목","summary":"요약","metrics":{{"who":"주체","whom":"대상","action":"행위","impact":"파장"}},"fact_check":{{"verified":["팩트1"],"controversial":["논란"],"logic":"근거"}},"balance":{{"stated":"명분","hidden":"의도","note":"총평"}}}}
    """
    
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.1, # 창의성을 낮춰서 문법 오류 방지
            response_mime_type="application/json" # 구글 서버에 JSON 응답 강제 설정
        )
    )
    
    return safe_parse_json(response.text)

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
                    with st.spinner("분석 중..."):
                        try:
                            start_time = time.time()
                            input_text = f"제목: {entry.title}\n내용: {entry.description}"
                            res = analyze_news_with_ai(input_text)
                            
                            if res:
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
                                st.caption(f"🤖 모델: {find_working_model()} | ⏱️ {round(time.time() - start_time, 2)}s")
                            else:
                                st.error("AI 응답 형식이 불안정합니다. 잠시 후 다시 시도해주세요.")
                            
                        except Exception as e:
                            st.error(f"예상치 못한 오류: {e}")
                
                st.link_button("Read Original", entry.link, use_container_width=True)