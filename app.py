import streamlit as st
import feedparser
from groq import Groq
import json
import requests
import time
import re

# 1. 페이지 설정
st.set_page_config(page_title="News Dietitian (Groq)", page_icon="⚡", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Pretendard', sans-serif !important; color: #1a1a1a; }
    .insight-card { background-color: #f8f9fa; padding: 18px; border-radius: 10px; border-left: 4px solid #4f46e5; margin-bottom: 12px; height: 100%; }
    .fact-header { font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; margin-bottom: 5px; }
    .fact-content { font-size: 15px; font-weight: 600; color: #1e293b; line-height: 1.4; }
</style>
""", unsafe_allow_html=True)

# 2. Groq 연결
try:
    api_key = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=api_key)
except Exception as e:
    st.error(f"⚠️ API 키 설정 오류: {e}")
    st.stop()

def safe_parse_json(raw_text):
    try:
        clean_text = re.sub(r'```json\s*|```\s*', '', raw_text).strip()
        clean_text = clean_text.replace('\n', ' ').replace('\r', '')
        return json.loads(clean_text)
    except:
        try:
            match = re.search(r'\{.*\}', clean_text)
            if match: return json.loads(match.group())
        except: return None
    return None

# ==========================================
# 🧠 AI 분석 (최신 모델 Llama 3.3 적용)
# ==========================================
@st.cache_data(show_spinner=False)
def analyze_news_groq(news_text):
    system_prompt = """
    당신은 친절한 뉴스 해설가입니다. 초심자도 이해할 수 있게 비유와 예시를 들어 설명하세요.
    결과는 반드시 JSON 형식으로만 출력하세요.
    """
    
    user_prompt = f"""
    [뉴스]: {news_text[:2000]}
    
    [형식]:
    {{
        "title": "호기심을 자극하는 쉬운 제목",
        "summary": "비유를 섞은 쉬운 요약",
        "metrics": {{
            "who": "주체",
            "whom": "대상",
            "action": "핵심 행위",
            "impact": "나에게 미치는 영향"
        }},
        "fact_check": {{
            "verified": ["확인된 팩트"],
            "logic": "판단 근거"
        }},
        "balance": {{
            "stated": "겉으로 내세운 명분",
            "hidden": "속에 숨겨진 의도",
            "note": "관전 포인트"
        }}
    }}
    """
    
    try:
        # 🚨 [수정 완료] 은퇴한 모델 대신 최신 'Llama 3.3' 모델을 사용합니다.
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        return safe_parse_json(completion.choices[0].message.content)
        
    except Exception as e:
        st.error(f"분석 중 에러: {e}")
        return None

# --- 화면 구성 ---
st.title("⚡ NEWS DIETITIAN (Llama 3.3)")
st.caption("최신 Llama 3.3 엔진으로 뉴스를 쉽고 빠르게 요리합니다.")

rss_url = "http://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=01&plink=RSSREADER"
try:
    resp = requests.get(rss_url, timeout=5)
    news = feedparser.parse(resp.content)
except:
    news = None

if news and news.entries:
    cols = st.columns(3)
    for i, entry in enumerate(news.entries[:12]):
        with cols[i % 3]:
            with st.container(border=True):
                st.markdown(f"**{entry.title}**")
                
                if st.button("✨ 쉬운 해설 보기", key=f"llama33_btn_{i}", use_container_width=True, type="primary"):
                    with st.spinner("⚡ 최신 AI가 분석 중..."):
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
                        else:
                            st.error("분석 데이터를 가져오지 못했습니다.")
                
                st.link_button("원문 보기", entry.link, use_container_width=True)