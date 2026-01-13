import streamlit as st
import feedparser
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
    div[data-testid="stContainer"] { background-color: #ffffff; border-radius: 12px; border: 1px solid #e5e7eb; }
    .insight-card { background-color: #f8f9fa; padding: 18px; border-radius: 10px; border-left: 4px solid #0f172a; margin-bottom: 12px; height: 100%; }
</style>
""", unsafe_allow_html=True)

# 🧼 JSON 정리 함수
def safe_parse_json(raw_text):
    try:
        clean_text = re.sub(r'```json\s*|```\s*', '', raw_text).strip()
        clean_text = clean_text.replace('\n', ' ').replace('\r', '')
        return json.loads(clean_text)
    except:
        return None

# ==========================================
# 🧠 AI 분석 (라이브러리 없이 직접 통신)
# ==========================================
@st.cache_data(show_spinner=False)
def analyze_news_direct(news_text):
    api_key = st.secrets["GEMINI_API_KEY"]
    
    # 🚨 [핵심] 라이브러리 대신 직접 URL로 접속합니다. 
    # v1beta 버전을 사용하되, 모델명은 확실한 1.5-flash를 씁니다.
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    
    prompt_text = f"""
    당신은 친절한 뉴스 선생님입니다. 지식이 없는 초보자도 이해할 수 있게 '쉬운 비유'와 '예시'를 들어 설명하세요.
    답변은 반드시 JSON 형식으로만 출력하세요.

    [뉴스]: {news_text[:1500]}

    [형식]:
    {{"title":"제목","summary":"비유 요약","metrics":{{"who":"주체","whom":"대상","action":"행위","impact":"파장"}},"fact_check":{{"verified":["팩트"],"logic":"근거"}},"balance":{{"stated":"명분","hidden":"속마음","note":"팁"}}}}
    """
    
    data = {
        "contents": [{
            "parts": [{"text": prompt_text}]
        }],
        "generationConfig": {
            "temperature": 0.3,
            "responseMimeType": "application/json"
        }
    }

    try:
        # requests로 직접 쏘기 때문에 라이브러리 버전 문제에서 자유롭습니다.
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            # 구글이 주는 쌩 데이터에서 텍스트만 발라내기
            text_content = result['candidates'][0]['content']['parts'][0]['text']
            return safe_parse_json(text_content), "Direct REST API"
        else:
            return None, f"HTTP Error {response.status_code}: {response.text}"
            
    except Exception as e:
        return None, f"통신 오류: {str(e)}"

# --- 화면 구성 ---
st.title("⚖️ NEWS DIETITIAN")
st.caption("라이브러리 없이 구글 서버와 직접 통신합니다.")

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
                
                if st.button("✨ 분석", key=f"rest_btn_{i}", use_container_width=True, type="primary"):
                    with st.spinner("구글 본사로 직접 연결 중..."):
                        res, method = analyze_news_direct(entry.description)
                        if res:
                            st.markdown("---")
                            st.markdown(f"#### {res['title']}")
                            st.info(res['summary'])
                            st.caption(f"✅ 연결 방식: {method}")
                        else:
                            st.error(f"실패: {method}")
                
                st.link_button("원문", entry.link, use_container_width=True)