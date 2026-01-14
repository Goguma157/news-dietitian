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
</style>
""", unsafe_allow_html=True)

# 2. Groq 연결 확인
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
        return None

# ==========================================
# 🧠 AI 분석 (에러 추적 모드)
# ==========================================
def analyze_news_groq(news_text):
    system_prompt = """
    당신은 친절한 뉴스 해설가입니다. 초심자도 이해할 수 있게 비유와 예시를 들어 설명하세요.
    결과는 반드시 JSON 형식으로만 출력하세요.
    """
    
    user_prompt = f"""
    [뉴스]: {news_text[:2000]}
    
    [형식]:
    {{"title":"제목","summary":"요약","metrics":{{"who":"주체","whom":"대상","action":"행위","impact":"파장"}},"fact_check":{{"verified":["팩트"],"logic":"근거"}},"balance":{{"stated":"명분","hidden":"속마음","note":"팁"}}}}
    """
    
    try:
        # 모델을 가장 안정적인 Llama3-70b로 변경해봅니다.
        completion = client.chat.completions.create(
            model="llama3-70b-8192", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        return safe_parse_json(completion.choices[0].message.content), "성공"
        
    except Exception as e:
        # 🚨 여기서 에러 내용을 그대로 반환합니다.
        return None, str(e)

# --- 화면 구성 ---
st.title("⚡ NEWS DIETITIAN (Groq Debug)")

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
                
                if st.button("✨ 분석 시도", key=f"debug_btn_{i}", use_container_width=True, type="primary"):
                    with st.spinner("Groq 서버에 접속 중..."):
                        res, msg = analyze_news_groq(f"제목: {entry.title}\n내용: {entry.description}")
                        
                        if res:
                            st.success("분석 성공!")
                            st.info(res['summary'])
                        else:
                            # 🚨 여기가 중요합니다! 에러 메시지를 보여줍니다.
                            st.error(f"❌ 분석 실패 원인:\n{msg}")
                            
                            # 흔한 원인에 대한 힌트 제공
                            if "401" in msg:
                                st.warning("힌트: API 키가 틀렸습니다. Secrets에 'gsk_'로 시작하는 키가 맞는지, 공백은 없는지 확인하세요.")
                            elif "Rate limit" in msg:
                                st.warning("힌트: 너무 빨리 눌렀거나, Groq 무료 사용량을 초과했습니다.")
                            elif "module" in msg:
                                st.warning("힌트: requirements.txt에 'groq'가 설치되지 않았습니다.")
                
                st.link_button("원문", entry.link, use_container_width=True)