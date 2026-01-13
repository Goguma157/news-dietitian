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
# 🧠 AI 분석 (무차별 대입 접속)
# ==========================================
@st.cache_data(show_spinner=False)
def analyze_news_brute_force(news_text):
    api_key = st.secrets["GEMINI_API_KEY"]
    
    # 🚨 [전략] 별명이 안 되면 본명으로, 본명이 안 되면 옛날 이름으로 다 찔러봅니다.
    candidate_urls = [
        # 1. 가장 최신 (002) - 주민등록번호
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-002:generateContent?key={api_key}",
        # 2. 구형 안정화 (001) - 주민등록번호
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-001:generateContent?key={api_key}",
        # 3. 최신 별명 (latest)
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}",
        # 4. 기본 별명 (여기서 404가 났었음)
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}",
        # 5. 정 안되면 Pro 버전이라도
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={api_key}",
    ]
    
    headers = {'Content-Type': 'application/json'}
    
    prompt_text = f"""
    당신은 친절한 뉴스 선생님입니다. 지식이 없는 초보자도 이해할 수 있게 '쉬운 비유'와 '예시'를 들어 설명하세요.
    답변은 반드시 JSON 형식으로만 출력하세요.

    [뉴스]: {news_text[:1500]}

    [형식]:
    {{"title":"제목","summary":"비유 요약","metrics":{{"who":"주체","whom":"대상","action":"행위","impact":"파장"}},"fact_check":{{"verified":["팩트"],"logic":"근거"}},"balance":{{"stated":"명분","hidden":"속마음","note":"팁"}}}}
    """
    
    data = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "generationConfig": {"temperature": 0.3, "responseMimeType": "application/json"}
    }

    last_error = ""
    
    # 🔁 반복문으로 뚫릴 때까지 시도
    for url in candidate_urls:
        try:
            # 모델 이름만 추출 (디버깅용)
            model_name = url.split("models/")[1].split(":")[0]
            
            response = requests.post(url, headers=headers, json=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                text_content = result['candidates'][0]['content']['parts'][0]['text']
                return safe_parse_json(text_content), f"성공! ({model_name})"
            else:
                last_error = f"{model_name} -> {response.status_code}"
                continue # 실패하면 다음 URL로 넘어감
                
        except Exception as e:
            last_error = str(e)
            continue

    return None, f"모든 경로 실패. 마지막 에러: {last_error}"

# --- 화면 구성 ---
st.title("⚖️ NEWS DIETITIAN")
st.caption("가능한 모든 모델 주소를 순차적으로 시도합니다.")

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
                
                if st.button("✨ 분석", key=f"nuke_btn_{i}", use_container_width=True, type="primary"):
                    with st.spinner("접속 가능한 모델을 찾는 중..."):
                        res, msg = analyze_news_brute_force(entry.description)
                        if res:
                            st.markdown("---")
                            st.markdown(f"#### {res['title']}")
                            st.info(res['summary'])
                            st.caption(f"✅ {msg}")
                        else:
                            st.error(f"❌ {msg}")
                
                st.link_button("원문", entry.link, use_container_width=True)