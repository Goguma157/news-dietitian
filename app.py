import streamlit as st
import feedparser
import google.generativeai as genai
import json
import requests
import time

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
    st.error("API Key를 Secrets에 정확히 입력해주세요.")

# 🔍 [핵심] 사용자 계정에서 실제 작동하는 모델 이름을 찾아내는 함수
def find_working_model():
    try:
        # 사용 가능한 모델 목록을 가져옵니다.
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 1. 'gemini-1.5-flash'가 있는지 먼저 확인
        for m in available_models:
            if '1.5' in m and 'flash' in m:
                return m
        
        # 2. 없으면 'flash'라는 단어가 들어간 아무 모델이나 선택 (예: gemini-flash-latest 등)
        for m in available_models:
            if 'flash' in m:
                return m
        
        # 3. 그것도 없으면 목록의 첫 번째 모델 선택
        return available_models[0] if available_models else "gemini-pro"
    except:
        return "gemini-pro"

@st.cache_data(ttl=600, show_spinner=False)
def fetch_news_data(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=5)
        return feedparser.parse(response.content) if response.status_code == 200 else None
    except:
        return None

@st.cache_data(show_spinner=False)
def analyze_news_with_ai(news_text):
    # 💡 여기서 자동으로 찾은 모델 이름을 사용합니다!
    working_model_name = find_working_model()
    model = genai.GenerativeModel(working_model_name)
    
    prompt = f"""
    당신은 객관적이고 날카로운 '수석 뉴스 분석가'입니다. 
    뉴스를 분석하여 다음 JSON 형식으로 대답하세요. 
    답변은 명사형 문장(개조식)으로 짧고 굵게 작성하세요.

    [뉴스 내용]: {news_text[:2000]}

    [JSON 형식]:
    {{
        "title": "본질을 꿰뚫는 제목",
        "summary": "핵심 요약 (1문장)",
        "metrics": {{
            "who": "주체",
            "whom": "대상",
            "action": "핵심 행위",
            "impact": "예상 파장"
        }},
        "fact_check": {{
            "verified": ["팩트 1", "팩트 2"],
            "controversial": ["논란/배경"],
            "logic": "분석 근거"
        }},
        "balance": {{
            "stated": "표면적 명분",
            "hidden": "의도/반론",
            "note": "한 줄 평"
        }}
    }}
    """
    
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            max_output_tokens=1000,
            temperature=0.3,
            response_mime_type="application/json"
        )
    )
    return json.loads(response.text)

# 화면 구성
st.title("⚖️ NEWS DIETITIAN")
st.markdown("<div style='color: #6b7280; margin-top: -15px; margin-bottom: 30px;'>Fast & Objective News Intelligence</div>", unsafe_allow_html=True)

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

                            t1, t2 = st.tabs(["✅ Fact & Logic", "⚖️ Perspective"])
                            with t1:
                                for f in res['fact_check']['verified']:
                                    st.markdown(f"<span class='badge-valid'>팩트</span> {f}", unsafe_allow_html=True)
                                st.caption(f"근거: {res['fact_check']['logic']}")
                            with t2:
                                st.success(f"**명분:** {res['balance']['stated']}")
                                st.warning(f"**이면:** {res['balance']['hidden']}")
                            
                            st.write(f"🧐 **Editor's Note:** {res['balance']['note']}")
                            st.caption(f"⏱️ 분석 시간: {round(time.time() - start_time, 2)}초")
                            
                        except Exception as e:
                            st.error(f"분석 중 오류 발생: {e}")
                
                st.link_button("Read Full Article", entry.link, use_container_width=True)