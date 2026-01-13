import streamlit as st
import feedparser
import google.generativeai as genai
import json
import requests
import time
import re

# 1. 페이지 설정
st.set_page_config(page_title="News Dietitian", page_icon="⚖️", layout="wide")

# CSS 스타일 (가독성 유지)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Pretendard', sans-serif !important; color: #1a1a1a; }
    .insight-card { background-color: #f8f9fa; padding: 18px; border-radius: 10px; border-left: 4px solid #0f172a; margin-bottom: 12px; height: 100%; }
</style>
""", unsafe_allow_html=True)

# API 설정
try:
    # 🚨 가장 중요한 부분: 라이브러리가 엉뚱한 길로 가지 않도록 키를 다시 세팅합니다.
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("Secrets에서 API 키를 확인해 주세요.")

# 🧼 AI 답변 보정 도구
def safe_parse_json(raw_text):
    try:
        clean_text = re.sub(r'```json\s*|```\s*', '', raw_text).strip()
        clean_text = clean_text.replace('\n', ' ').replace('\r', '')
        return json.loads(clean_text)
    except:
        return None

# ==========================================
# 🧠 AI 분석 (직설적인 모델 호출 방식)
# ==========================================
@st.cache_data(show_spinner=False)
def analyze_news_with_ai(news_text):
    
    # 🚨 [해결책] 시스템이 헷갈리지 않게 'models/'를 붙인 풀네임을 직접 적어줍니다.
    # 아까 테스트에서 확인하신 그 이름을 그대로 사용하는 방식입니다.
    model_full_name = "models/gemini-1.5-flash"
    
    try:
        model = genai.GenerativeModel(model_name=model_full_name)
        
        prompt = f"""
        당신은 친절한 뉴스 해설가입니다. 지식이 부족한 초보자도 이해할 수 있게 비유와 예시를 들어 분석하세요.
        답변은 반드시 JSON 형식으로만 출력하세요.

        [뉴스]: {news_text[:1500]}

        [형식]:
        {{"title":"제목","summary":"비유 섞인 요약","metrics":{{"who":"주체","whom":"대상","action":"행위","impact":"파장"}},"fact_check":{{"verified":["팩트"],"logic":"분석 근거"}},"balance":{{"stated":"명분","hidden":"속마음","note":"관전포인트"}}}}
        """
        
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                response_mime_type="application/json"
            )
        )
        return safe_parse_json(response.text), model_full_name
        
    except Exception as e:
        # 만약 그래도 안 된다면, 이름 끝에 '-latest'를 붙여서 한 번 더 시도합니다.
        try:
            retry_name = "models/gemini-1.5-flash-latest"
            model = genai.GenerativeModel(model_name=retry_name)
            response = model.generate_content(prompt)
            return safe_parse_json(response.text), retry_name
        except:
            return None, str(e)

# --- 화면 구성 ---
st.title("⚖️ NEWS DIETITIAN")
st.caption("정상 계정의 1.5 Flash 엔진으로 직접 연결을 시도합니다.")

rss_url = "http://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=01&plink=RSSREADER"
resp = requests.get(rss_url)
news = feedparser.parse(resp.content)

if news.entries:
    cols = st.columns(3)
    for i, entry in enumerate(news.entries[:12]):
        with cols[i % 3]:
            with st.container(border=True):
                st.markdown(f"**{entry.title}**")
                
                if st.button("✨ 쉬운 분석", key=f"direct_btn_{i}", use_container_width=True, type="primary"):
                    with st.spinner("AI가 정상 경로로 접속 중..."):
                        res, used_path = analyze_news_with_ai(entry.description)
                        if res:
                            st.markdown("---")
                            st.markdown(f"#### {res['title']}")
                            st.info(res['summary'])
                            st.caption(f"✅ 경로 확인됨: {used_path}")
                        else:
                            st.error(f"정상 계정임에도 경로를 찾지 못했습니다: {used_path}")
                
                st.link_button("원문 보기", entry.link, use_container_width=True)