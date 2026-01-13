import streamlit as st
import feedparser
import google.generativeai as genai
import json
import requests
import time
import re

# 1. 페이지 설정
st.set_page_config(page_title="News Dietitian", page_icon="⚖️", layout="wide")

# CSS 스타일
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Pretendard', sans-serif !important; color: #1a1a1a; }
    .insight-card { background-color: #f8f9fa; padding: 18px; border-radius: 10px; border-left: 4px solid #0f172a; margin-bottom: 12px; height: 100%; }
</style>
""", unsafe_allow_html=True)

# API 설정
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("API 키를 확인해주세요.")

# 🧼 AI 답변 보정
def safe_parse_json(raw_text):
    try:
        clean_text = re.sub(r'```json\s*|```\s*', '', raw_text).strip()
        clean_text = clean_text.replace('\n', ' ').replace('\r', '')
        return json.loads(clean_text)
    except:
        return None

# ==========================================
# 🧠 AI 분석 (업데이트된 라이브러리 믿고 정석대로!)
# ==========================================
@st.cache_data(show_spinner=False)
def analyze_news_with_ai(news_text):
    # 이제 라이브러리가 업데이트되면 이 이름을 무조건 알아듣습니다.
    target_model = "gemini-1.5-flash"
    
    try:
        model = genai.GenerativeModel(target_model)
        
        prompt = f"""
        당신은 친절한 뉴스 선생님입니다. 지식이 없는 초보자도 이해할 수 있게 '쉬운 비유'와 '예시'를 들어 설명하세요.
        답변은 반드시 JSON 형식으로만 출력하세요.

        [뉴스]: {news_text[:1500]}

        [형식]:
        {{"title":"제목","summary":"비유 요약","metrics":{{"who":"주체","whom":"대상","action":"행위","impact":"파장"}},"fact_check":{{"verified":["팩트"],"logic":"근거"}},"balance":{{"stated":"명분","hidden":"속마음","note":"팁"}}}}
        """
        
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                response_mime_type="application/json"
            )
        )
        return safe_parse_json(response.text), target_model

    except Exception as e:
        return None, f"오류: {str(e)}"

# --- 화면 구성 ---
st.title("⚖️ NEWS DIETITIAN")
st.caption("최신 Gemini 엔진으로 뉴스를 소화하기 쉽게 요리합니다.")

rss_url = "http://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=01&plink=RSSREADER"
try:
    resp = requests.get(rss_url, timeout=10)
    news = feedparser.parse(resp.content)
except:
    st.error("뉴스를 가져오지 못했습니다.")
    news = None

if news and news.entries:
    cols = st.columns(3)
    for i, entry in enumerate(news.entries[:12]):
        with cols[i % 3]:
            with st.container(border=True):
                st.markdown(f"**{entry.title}**")
                
                if st.button("✨ 쉬운 분석", key=f"new_lib_btn_{i}", use_container_width=True, type="primary"):
                    with st.spinner("AI 선생님이 분석 중..."):
                        res, model_info = analyze_news_with_ai(entry.description)
                        if res:
                            st.markdown("---")
                            st.markdown(f"#### {res['title']}")
                            st.info(res['summary'])
                            st.caption(f"✅ 분석 완료 ({model_info})")
                        else:
                            st.error(f"분석 실패: {model_info}")
                
                st.link_button("원문 보기", entry.link, use_container_width=True)