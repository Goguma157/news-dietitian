import streamlit as st
import feedparser
import google.generativeai as genai
import json
import requests
import time
import re

# 1. 페이지 설정
st.set_page_config(page_title="News Dietitian", page_icon="⚖️", layout="wide")

# CSS 스타일 (가독성 높은 디자인)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Pretendard', sans-serif !important; color: #1a1a1a; }
    .insight-card { background-color: #f8f9fa; padding: 18px; border-radius: 10px; border-left: 4px solid #0f172a; margin-bottom: 12px; height: 100%; }
    .fact-header { font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; margin-bottom: 5px; }
    .fact-content { font-size: 15px; font-weight: 600; color: #0f172a; line-height: 1.4; }
    .badge-valid { background-color: #dcfce7; color: #166534; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; margin-right: 5px; }
</style>
""", unsafe_allow_html=True)

# API 설정 (새 계정의 키를 Secrets에 넣으셨다고 가정합니다)
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("새 계정의 API Key를 설정해주세요!")

# 🧼 AI 답변 보정 도구
def safe_parse_json(raw_text):
    try:
        clean_text = re.sub(r'```json\s*|```\s*', '', raw_text).strip()
        clean_text = clean_text.replace('\n', ' ').replace('\r', '')
        return json.loads(clean_text)
    except:
        return None

# ==========================================
# 🧠 AI 분석 (1.5 Flash - 초심자 배려 모드)
# ==========================================
@st.cache_data(show_spinner=False)
def analyze_news_with_ai(news_text):
    # 이제 목록에 있는 1.5 Flash를 당당하게 사용합니다!
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    prompt = f"""
    당신은 친절한 뉴스 선생님입니다. 이 뉴스를 잘 모르는 초보자도 바로 이해할 수 있게 '비유'나 '일상적인 예시'를 들어 설명하세요.
    모든 답변은 반드시 JSON 형식으로만 출력하세요.

    [뉴스 내용]: {news_text[:2000]}

    [출력 양식]:
    {{
        "title": "한눈에 쏙 들어오는 쉬운 제목",
        "summary": "일상생활에 비유한 요약 (1문장)",
        "metrics": {{
            "who": "주인공",
            "whom": "영향을 받는 대상",
            "action": "어떤 일이 일어났나",
            "impact": "우리에게 생길 변화"
        }},
        "fact_check": {{
            "verified": ["확인된 핵심 사실"],
            "logic": "왜 이렇게 생각했는지 설명"
        }},
        "balance": {{
            "stated": "겉으로 보이는 이유",
            "hidden": "진짜 속마음이나 배경",
            "note": "이 뉴스를 볼 때 놓치지 말 것"
        }}
    }}
    """
    
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                response_mime_type="application/json"
            )
        )
        return safe_parse_json(response.text)
    except Exception as e:
        st.error(f"분석 중 오류 발생: {e}")
        return None

# --- 뉴스 가져오기 및 화면 구성 ---
st.title("⚖️ NEWS DIETITIAN")
st.markdown("<p style='color: gray;'>정상 계정(Gemini 1.5 Flash)으로 작동 중입니다.</p>", unsafe_allow_html=True)

rss_url = "http://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=01&plink=RSSREADER"
try:
    resp = requests.get(rss_url, timeout=10)
    news = feedparser.parse(resp.content)
except:
    st.error("뉴스를 불러올 수 없습니다.")
    news = None

if news and news.entries:
    cols = st.columns(3)
    for i, entry in enumerate(news.entries[:12]):
        with cols[i % 3]:
            with st.container(border=True):
                st.caption(entry.published[:16])
                st.markdown(f"**{entry.title}**")
                
                if st.button("✨ 쉬운 분석", key=f"btn_{i}", use_container_width=True, type="primary"):
                    with st.spinner("선생님이 비유를 생각 중..."):
                        res = analyze_news_with_ai(f"제목: {entry.title}\n내용: {entry.description}")
                        if res:
                            st.markdown("---")
                            st.markdown(f"#### {res['title']}")
                            st.info(res['summary'])
                            
                            m1, m2 = st.columns(2)
                            with m1:
                                st.markdown(f"<div class='insight-card'><div class='fact-header'>WHO</div><div class='fact-content'>{res['metrics']['who']}</div></div>", unsafe_allow_html=True)
                            with m2:
                                st.markdown(f"<div class='insight-card'><div class='fact-header'>IMPACT</div><div class='fact-content'>{res['metrics']['impact']}</div></div>", unsafe_allow_html=True)
                            
                            with st.expander("⚖️ 깊이 있는 분석 보기"):
                                st.success(f"**명분:** {res['balance']['stated']}")
                                st.warning(f"**속마음:** {res['balance']['hidden']}")
                                st.write(f"💡 **팁:** {res['balance']['note']}")
                        else:
                            st.error("분석 실패. 다시 시도해 주세요.")
                
                st.link_button("기사 원문", entry.link, use_container_width=True)