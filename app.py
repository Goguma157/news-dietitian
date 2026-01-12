import streamlit as st
import feedparser
import google.generativeai as genai
import json
import requests
import time

# 1. 페이지 설정
st.set_page_config(page_title="News Dietitian", page_icon="📰", layout="wide")

# ==========================================
# 🎨 CSS 스타일
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, sans-serif !important;
        color: #1a1a1a;
    }
    div[data-testid="stContainer"] {
        background-color: #ffffff;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        transition: box-shadow 0.3s ease;
    }
    .insight-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #0f172a; 
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        height: 100%;
        word-break: keep-all;
    }
    .fact-header {
        font-size: 13px;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 8px;
    }
    .fact-content {
        font-size: 17px;
        font-weight: 600;
        color: #0f172a;
        line-height: 1.5;
    }
    .badge-valid {
        background-color: #dcfce7;
        color: #166534;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
        display: inline-block;
        margin-right: 5px;
    }
    .badge-ref {
        background-color: #f1f5f9;
        color: #475569;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 500;
        display: inline-block;
        margin-right: 5px;
    }
    h1 { font-weight: 800 !important; letter-spacing: -1px; color: #111827; }
    h2, h3 { font-weight: 700 !important; color: #374151; }
</style>
""", unsafe_allow_html=True)

try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    pass 

# ==========================================
# ⚡ [속도 최적화] 캐싱 적용
# ==========================================
@st.cache_data(ttl=600, show_spinner=False)
def fetch_news_data(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            return feedparser.parse(response.content)
        else:
            return None
    except:
        return None

@st.cache_data(show_spinner=False)
def analyze_news_with_ai(news_text):
    # ⚡ [속도 핵심] 프롬프트를 줄이고, 답변을 짧게 요구함
    prompt = f"""
    당신은 '수석 뉴스 분석가'입니다. 뉴스 핵심을 JSON으로 추출하세요.
    최대한 간결하고 짧게(단답형 위주) 작성하여 응답 속도를 높이세요.
    
    [뉴스]: {news_text[:1500]} 
    (내용이 길면 앞부분 1500자만 읽고 분석하세요)
    
    [JSON 형식]:
    {{
        "title": "제목 (30자 내외)",
        "summary": "1문장 요약",
        "metrics": {{
            "who": "주체",
            "whom": "대상",
            "action": "핵심 행위 (짧게)",
            "impact": "결과 (짧게)"
        }},
        "fact_check": {{
            "verified": ["팩트 1", "팩트 2"],
            "controversial": ["참고/배경 1"],
            "logic": "구분 이유 (1문장)"
        }},
        "balance_sheet": {{
            "side_a": "A측 입장 (1문장)",
            "side_b": "B측/누락된 입장 (1문장)",
            "editor_note": "짧은 제언"
        }}
    }}
    """
    model = genai.GenerativeModel('gemini-flash-latest')
    response = model.generate_content(prompt)
    text = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)

st.title("NEWS DIETITIAN")
st.markdown("<div style='color: #6b7280; margin-top: -15px; margin-bottom: 30px; font-size: 18px;'>Objective News Analysis Dashboard</div>", unsafe_allow_html=True)

rss_url = "http://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=01&plink=RSSREADER"
news = fetch_news_data(rss_url)

if news is None or len(news.entries) == 0:
    st.error("System Error: Unable to fetch news feed.")
else:
    cols = st.columns(3)
    
    for i in range(min(12, len(news.entries))):
        entry = news.entries[i]
        with cols[i % 3]:
            with st.container(border=True):
                st.markdown(f"<div style='font-size: 12px; color: #9ca3af; margin-bottom: 5px;'>{entry.published[:16]}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size: 16px; font-weight: 700; line-height: 1.4; margin-bottom: 10px; height: 50px; overflow: hidden;'>{entry.title}</div>", unsafe_allow_html=True)
                st.link_button("Read Original Article 🔗", entry.link, use_container_width=True)
                
                if st.button("Deep Analysis ✨", key=f"btn_{i}", use_container_width=True, type="primary"):
                    if "GEMINI_API_KEY" not in st.secrets:
                         st.error("API Key Missing")
                    else:
                        # ⚡ 진행바 UI 추가
                        progress_text = "Reading News..."
                        my_bar = st.progress(0, text=progress_text)

                        try:
                            # 1. 데이터 준비 (30%)
                            time.sleep(0.1)
                            my_bar.progress(30, text="Extracting Facts...")
                            
                            input_text = f"제목: {entry.title}\n내용: {entry.description}"
                            
                            # 2. AI 분석 (캐싱됨)
                            res = analyze_news_with_ai(input_text)
                            
                            # 3. 완료 (100%)
                            my_bar.progress(100, text="Finalizing Design...")
                            time.sleep(0.2)
                            my_bar.empty() # 진행바 삭제

                            # --- 결과 화면 ---
                            st.markdown("---")
                            st.markdown(f"### {res['title']}")
                            st.markdown(f"