import streamlit as st
import feedparser
from groq import Groq
import json
import requests
import time
import re

# 1. 페이지 설정
st.set_page_config(page_title="News Dietitian (Groq)", page_icon="⚡", layout="wide")

# CSS 스타일
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Pretendard', sans-serif !important; color: #1a1a1a; }
    div[data-testid="stContainer"] { background-color: #ffffff; border-radius: 12px; border: 1px solid #e5e7eb; }
    .insight-card { background-color: #f8f9fa; padding: 18px; border-radius: 10px; border-left: 4px solid #4f46e5; margin-bottom: 12px; height: 100%; }
    .fact-header { font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; margin-bottom: 5px; }
    .fact-content { font-size: 15px; font-weight: 600; color: #1e293b; line-height: 1.4; }
</style>
""", unsafe_allow_html=True)

# 2. Groq 클라이언트 연결
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("Secrets에 GROQ_API_KEY를 설정해주세요!")

# 🧼 JSON 세탁기
def safe_parse_json(raw_text):
    try:
        clean_text = re.sub(r'```json\s*|```\s*', '', raw_text).strip()
        clean_text = clean_text.replace('\n', ' ').replace('\r', '')
        return json.loads(clean_text)
    except:
        # 혹시 JSON 형식이 깨져서 오면 수동으로 추출 시도
        try:
            match = re.search(r'\{.*\}', clean_text)
            if match: return json.loads(match.group())
        except: return None
    return None

# ==========================================
# 🧠 AI 분석 (Groq - Llama3 사용)
# ==========================================
@st.cache_data(show_spinner=False)
def analyze_news_groq(news_text):
    
    # 초심자용 쉬운 설명 프롬프트
    system_prompt = """
    당신은 친절한 뉴스 해설가입니다. 
    해당 질문에 대한 지식이 별로 없는 초심자도 충분히 이해할 수 있도록, 
    어려운 용어 대신 '쉬운 비유'나 '구체적인 예시'를 들어 설명해주세요.
    결과는 반드시 JSON 형식으로만 출력하세요.
    """
    
    user_prompt = f"""
    [뉴스 내용]: {news_text[:2000]}

    [출력 양식]:
    {{
        "title": "호기심을 자극하는 쉬운 제목",
        "summary": "마치 친구에게 말하듯 비유를 섞은 요약 (1문장)",
        "metrics": {{
            "who": "누가 (주인공)",
            "whom": "누구에게 (영향)",
            "action": "무엇을 (핵심 행동)",
            "impact": "그래서 내 삶은 어떻게 변하나"
        }},
        "fact_check": {{
            "verified": ["확인된 팩트"],
            "logic": "해설가의 판단 근거"
        }},
        "balance": {{
            "stated": "겉으로 내세운 명분",
            "hidden": "속에 숨겨진 의도",
            "note": "이 뉴스의 관전 포인트"
        }}
    }}
    """
    
    try:
        completion = client.chat.completions.create(
            model="llama3-8b-8192", # 아주 빠르고 똑똑한 모델
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"} # JSON 강제 출력 기능
        )
        return safe_parse_json(completion.choices[0].message.content)
    except Exception as e:
        return None

# --- 화면 구성 ---
st.title("⚡ NEWS DIETITIAN (Groq)")
st.caption("Google보다 10배 빠른 Groq 엔진으로 뉴스를 분석합니다.")

rss_url = "http://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=01&plink=RSSREADER"
try:
    resp = requests.get(rss_url, timeout=5)
    news = feedparser.parse(resp.content)
except:
    st.error("뉴스를 가져올 수 없습니다.")
    news = None

if news and news.entries:
    cols = st.columns(3)
    for i, entry in enumerate(news.entries[:12]):
        with cols[i % 3]:
            with st.container(border=True):
                st.markdown(f"**{entry.title}**")
                
                if st.button("✨ 쉬운 해설 보기", key=f"groq_btn_{i}", use_container_width=True, type="primary"):
                    with st.spinner("⚡ 순식간에 분석 중..."):
                        start_time = time.time()
                        res = analyze_news_groq(f"제목: {entry.title}\n내용: {entry.description}")
                        
                        if res:
                            st.markdown("---")
                            st.markdown(f"#### {res['title']}")
                            st.info(res['summary'])
                            
                            m1, m2 = st.columns(2)
                            with m1:
                                st.markdown(f"<div class='insight-card'><div class='fact-header'>WHO</div><div class='fact-content'>{res['metrics']['who']}</div></div>", unsafe_allow_html=True)
                            with m2:
                                st.markdown(f"<div class='insight-card'><div class='fact-header'>IMPACT</div><div class='fact-content'>{res['metrics']['impact']}</div></div>", unsafe_allow_html=True)

                            with st.expander("🔍 자세히 보기 (팩트 & 속마음)"):
                                st.success(f"**명분:** {res['balance']['stated']}")
                                st.warning(f"**속마음:** {res['balance']['hidden']}")
                                st.caption(f"💡 팁: {res['balance']['note']}")
                            
                            st.caption(f"⚡ 분석 시간: {round(time.time() - start_time, 2)}초")
                        else:
                            st.error("분석 실패 (일시적 오류)")
                
                st.link_button("원문 보기", entry.link, use_container_width=True)