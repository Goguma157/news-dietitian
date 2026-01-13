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
    div[data-testid="stContainer"] { background-color: #ffffff; border-radius: 12px; border: 1px solid #e5e7eb; }
    .insight-card { background-color: #f8f9fa; padding: 18px; border-radius: 10px; border-left: 4px solid #0f172a; margin-bottom: 12px; height: 100%; }
    .fact-header { font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; margin-bottom: 5px; }
    .fact-content { font-size: 15px; font-weight: 600; color: #0f172a; line-height: 1.4; }
    .badge-valid { background-color: #dcfce7; color: #166534; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; margin-right: 5px; }
    h1 { font-weight: 800 !important; letter-spacing: -1px; color: #111827; }
</style>
""", unsafe_allow_html=True)

# API 설정
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("Secrets에 API Key를 넣어주세요!")

# 🔍 [핵심 수정] 사용자님 목록에 있는 'Lite' 모델을 최우선으로 낚아채는 함수
def find_working_model():
    try:
        # 사용자님 계정의 모델 목록 조회
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 1순위: '2.0' 버전이면서 'lite'인 것 (가장 가볍고 횟수 제한 적음)
        for m in available:
            if '2.0' in m and 'lite' in m: return m.replace('models/', '')
            
        # 2순위: '2.5' 버전이면서 'lite'인 것
        for m in available:
            if '2.5' in m and 'lite' in m: return m.replace('models/', '')

        # 3순위: 그냥 'lite' 들어간 아무거나
        for m in available:
            if 'lite' in m: return m.replace('models/', '')
            
        # 4순위: 정 없으면 목록의 첫 번째 (2.5-flash 등)
        return available[0].replace('models/', '') if available else "gemini-2.0-flash-lite"
    except:
        return "gemini-2.0-flash-lite"

@st.cache_data(ttl=600, show_spinner=False)
def fetch_news_data(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=5)
        return feedparser.parse(response.content) if response.status_code == 200 else None
    except:
        return None

# 🧼 AI 답변 보정 도구
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
# 🧠 AI 분석 (초심자용 쉬운 설명 모드)
# ==========================================
@st.cache_data(show_spinner=False)
def analyze_news_with_ai(news_text):
    # 여기서 'Lite' 모델을 자동으로 찾아옵니다!
    model_name = find_working_model()
    model = genai.GenerativeModel(model_name)
    
    prompt = f"""
    당신은 친절한 뉴스 선생님입니다. 
    해당 질문에 대한 지식이 전혀 없는 초심자도 이해할 수 있도록, 쉬운 '비유'나 '예시'를 꼭 들어서 설명해주세요.
    답변은 JSON 형식으로 하되, 줄바꿈이나 특수기호 오류가 없도록 주의하세요.

    [뉴스]: {news_text[:2000]}

    [형식]:
    {{
        "title": "호기심을 자극하는 쉬운 제목",
        "summary": "일상 생활에 비유한 핵심 요약 (1문장)",
        "metrics": {{
            "who": "누가 (주인공)",
            "whom": "누구에게 (영향받는 사람)",
            "action": "무엇을 했나 (핵심 행동)",
            "impact": "그래서 내 삶은 어떻게 변하나"
        }},
        "fact_check": {{
            "verified": ["확인된 사실 1", "사실 2"],
            "controversial": ["알고 보면 복잡한 속사정"],
            "logic": "선생님의 판단 근거"
        }},
        "balance": {{
            "stated": "겉으로 하는 말 (명분)",
            "hidden": "속마음 (의도)",
            "note": "이 뉴스의 한 줄 관전 포인트"
        }}
    }}
    """
    
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.2,
            response_mime_type="application/json"
        )
    )
    return safe_parse_json(response.text)

# --- 화면 구성 ---
st.title("⚖️ NEWS DIETITIAN")
st.markdown("<div style='color: #6b7280; margin-top: -15px; margin-bottom: 30px;'>Powered by Gemini 2.0 Lite</div>", unsafe_allow_html=True)

rss_url = "http://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=01&plink=RSSREADER"
news = fetch_news_data(rss_url)

if news and len(news.entries) > 0:
    cols = st.columns(3)
    for i in range(min(12, len(news.entries))):
        entry = news.entries[i]
        with cols[i % 3]:
            with st.container(border=True):
                st.caption(f"{entry.published[:16]}")
                st.markdown(f"**{entry.title}**")
                
                # key를 변경하여 캐시 초기화
                if st.button("✨ 쉬운 분석 보기", key=f"lite_btn_{i}", use_container_width=True, type="primary"):
                    with st.spinner("AI 선생님이 내용을 쉽게 풀이 중..."):
                        try:
                            start_time = time.time()
                            input_text = f"제목: {entry.title}\n내용: {entry.description}"
                            res = analyze_news_with_ai(input_text)
                            
                            if res:
                                st.markdown("---")
                                st.markdown(f"#### {res['title']}")
                                st.info(res['summary'])
                                
                                m1, m2 = st.columns(2)
                                with m1:
                                    st.markdown(f"<div class='insight-card'><div class='fact-header'>WHO</div><div class='fact-content'>{res['metrics']['who']}</div></div>", unsafe_allow_html=True)
                                    st.markdown(f"<div class='insight-card'><div class='fact-header'>ACTION</div><div class='fact-content'>{res['metrics']['action']}</div></div>", unsafe_allow_html=True)
                                with m2:
                                    st.markdown(f"<div class='insight-card'><div class='fact-header'>WHOM</div><div class='fact-content'>{res['metrics']['whom']}</div></div>", unsafe_allow_html=True)
                                    st.markdown(f"<div class='insight-card'><div class='fact-header'>IMPACT</div><div class='fact-content'>{res['metrics']['impact']}</div></div>", unsafe_allow_html=True)

                                t1, t2 = st.tabs(["✅ 팩트 체크", "⚖️ 속마음 읽기"])
                                with t1:
                                    for f in res['fact_check']['verified']:
                                        st.markdown(f"<span class='badge-valid'>팩트</span> {f}", unsafe_allow_html=True)
                                    st.caption(f"근거: {res['fact_check']['logic']}")
                                with t2:
                                    st.success(f"**명분:** {res['balance']['stated']}")
                                    st.warning(f"**속마음:** {res['balance']['hidden']}")
                                
                                st.write(f"🧐 **Point:** {res['balance']['note']}")
                                st.caption(f"🤖 모델: {find_working_model()} | ⏱️ {round(time.time() - start_time, 2)}s")
                            else:
                                st.error("분석 내용을 불러오지 못했습니다. 다시 시도해주세요.")
                        except Exception as e:
                            st.error(f"오류: {e}")
                
                st.link_button("기사 원문 보기", entry.link, use_container_width=True)