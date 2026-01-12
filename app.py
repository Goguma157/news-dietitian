import streamlit as st
import feedparser
import google.generativeai as genai
import json
import requests

# 1. 페이지 설정
st.set_page_config(page_title="News Dietitian", page_icon="📰", layout="wide")

# ==========================================
# 🎨 [디자인 업그레이드] CSS 커스텀 스타일
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
    
    /* [수정됨] 분석 결과 박스 스타일: 너비 문제 해결 */
    .insight-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #0f172a; 
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        height: 100%; /* 높이 맞춤 */
        word-break: keep-all; /* [중요] 한국어 단어 중간에 줄바꿈 방지 */
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
        line-height: 1.5; /* 줄 간격 확보 */
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

def analyze_news_with_ai(news_text):
    prompt = f"""
    당신은 냉철한 데이터 기반의 '수석 뉴스 분석가'입니다.
    제공된 뉴스를 분석하여, 감정을 배제하고 구조화된 JSON 데이터로 출력하세요.
    
    [뉴스 데이터]: {news_text}
    
    [JSON 출력 형식]:
    {{
        "title": "핵심을 찌르는 제목 (30자 내외)",
        "summary": "전체 내용을 관통하는 1문장 요약 (Executive Summary)",
        "metrics": {{
            "who": "주체 (핵심 인물/기관)",
            "whom": "대상",
            "action": "핵심 행위",
            "impact": "영향/결과"
        }},
        "fact_check": {{
            "verified": ["확인된 팩트 1", "확인된 팩트 2"],
            "controversial": ["논란/의혹/참고 1", "논란/의혹 2"],
            "logic": "위와 같이 구분한 논리적 근거 (1문장)"
        }},
        "balance_sheet": {{
            "side_a": "주요 발언/입장 (A측)",
            "side_b": "반론/침묵/누락된 입장 (B측)",
            "editor_note": "객관적 시각을 위한 제언"
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

try:
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(rss_url, headers=headers, timeout=5)
    if response.status_code == 200:
        news = feedparser.parse(response.content)
    else:
        news = None
except:
    news = None

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
                        with st.spinner("Analyzing data structure..."):
                            try:
                                input_text = f"제목: {entry.title}\n내용: {entry.description}"
                                res = analyze_news_with_ai(input_text)
                                
                                st.markdown("---")
                                st.markdown(f"### {res['title']}")
                                st.markdown(f"<div style='background-color: #f3f4f6; padding: 15px; border-radius: 8px; font-style: italic; color: #4b5563; margin-bottom: 20px;'>“{res['summary']}”</div>", unsafe_allow_html=True)
                                
                                # ==========================================
                                # [수정됨] 2x2 그리드 레이아웃 (가로 확보)
                                # ==========================================
                                st.markdown("<div class='fact-header'>KEY ENTITIES & IMPACT</div>", unsafe_allow_html=True)
                                
                                # 첫 번째 줄: WHO / WHOM
                                row1_col1, row1_col2 = st.columns(2)
                                with row1_col1:
                                    st.markdown(f"<div class='insight-card'><div class='fact-header'>WHO</div><div class='fact-content'>{res['metrics']['who']}</div></div>", unsafe_allow_html=True)
                                with row1_col2:
                                    st.markdown(f"<div class='insight-card'><div class='fact-header'>WHOM</div><div class='fact-content'>{res['metrics']['whom']}</div></div>", unsafe_allow_html=True)
                                
                                # 두 번째 줄: ACTION / IMPACT
                                row2_col1, row2_col2 = st.columns(2)
                                with row2_col1:
                                    st.markdown(f"<div class='insight-card'><div class='fact-header'>ACTION</div><div class='fact-content'>{res['metrics']['action']}</div></div>", unsafe_allow_html=True)
                                with row2_col2:
                                    st.markdown(f"<div class='insight-card'><div class='fact-header'>IMPACT</div><div class='fact-content'>{res['metrics']['impact']}</div></div>", unsafe_allow_html=True)

                                st.markdown("<div class='fact-header' style='margin-top: 20px;'>FACT CHECK & CONTEXT</div>", unsafe_allow_html=True)
                                st.caption(f"Logic: {res['fact_check']['logic']}")
                                
                                tab_a, tab_b = st.tabs(["VERIFIED FACTS", "CONTROVERSY / CONTEXT"])
                                with tab_a:
                                    for item in res['fact_check']['verified']:
                                        st.markdown(f"<div style='margin-bottom: 8px;'><span class='badge-valid'>FACT</span> {item}</div>", unsafe_allow_html=True)
                                with tab_b:
                                    for item in res['fact_check']['controversial']:
                                        st.markdown(f"<div style='margin-bottom: 8px;'><span class='badge-ref'>REF</span> {item}</div>", unsafe_allow_html=True)

                                st.markdown("<div class='fact-header' style='margin-top: 20px;'>VIEWPOINT BALANCE</div>", unsafe_allow_html=True)
                                col_l, col_r = st.columns(2)
                                with col_l:
                                    st.markdown(f"""
                                    <div style='border: 1px solid #e5e7eb; padding: 15px; border-radius: 8px;'>
                                        <strong style='color: #059669;'>📢 STATED</strong><br><br>{res['balance_sheet']['side_a']}
                                    </div>
                                    """, unsafe_allow_html=True)
                                with col_r:
                                    st.markdown(f"""
                                    <div style='border: 1px solid #e5e7eb; padding: 15px; border-radius: 8px; background-color: #fef2f2;'>
                                        <strong style='color: #dc2626;'>🔇 UNSTATED / MISSING</strong><br><br>{res['balance_sheet']['side_b']}
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                st.markdown(f"""
                                <div style='margin-top: 15px; font-size: 13px; color: #6b7280; text-align: right;'>
                                    <strong>Editor's Note:</strong> {res['balance_sheet']['editor_note']}
                                </div>
                                """, unsafe_allow_html=True)

                            except Exception as e:
                                st.error(f"Analysis Failed: {e}")