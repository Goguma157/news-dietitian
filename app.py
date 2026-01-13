import streamlit as st
import feedparser
import google.generativeai as genai
import json
import requests
import time
import re

# 1. 페이지 설정
st.set_page_config(page_title="News Dietitian", page_icon="⚖️", layout="wide")

# ==========================================
# 🎨 전문적이면서도 친근한 디자인 (CSS)
# ==========================================
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
    st.error("Secrets에 API Key를 확인해주세요!")

# 🔍 [핵심 수정] 1.5 Flash를 최우선으로 찾아 횟수 제한을 해결하는 함수
def find_working_model():
    try:
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # 1순위: 무조건 1.5 Flash를 먼저 찾습니다 (하루 1,500회 무료 버전)
        for m in available:
            if '1.5' in m and 'flash' in m: return m.replace('models/', '')
        # 2순위: 1.5가 없다면 다른 Flash 모델 확인
        for m in available:
            if 'flash' in m: return m.replace('models/', '')
        return available[0].replace('models/', '') if available else "gemini-1.5-flash"
    except:
        return "gemini-1.5-flash"

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
# 🧠 AI 분석 (비유와 예시를 활용한 쉬운 설명)
# ==========================================
@st.cache_data(show_spinner=False)
def analyze_news_with_ai(news_text):
    model_name = find_working_model()
    model = genai.GenerativeModel(model_name)
    
    # 지식이 부족한 사람을 위해 비유와 예시를 들어달라는 요청 추가
    prompt = f"""
    당신은 친절한 뉴스 평론가입니다. 지식이 부족한 사람도 이해할 수 있게 비유와 구체적인 예시를 들어 분석하세요.
    모든 답변은 반드시 JSON 형식만 출력하며, 각 값 안에 줄바꿈이나 큰따옴표 사용을 금지합니다.

    [뉴스]: {news_text[:2000]}

    [형식]:
    {{
        "title": "비유를 섞은 쉬운 제목",
        "summary": "뉴스 내용을 일상적인 예시로 비유한 요약 (1문장)",
        "metrics": {{
            "who": "주체",
            "whom": "대상",
            "action": "핵심 행위",
            "impact": "이 뉴스가 우리 삶에 미칠 영향"
        }},
        "fact_check": {{
            "verified": ["확인된 팩트 1", "팩트 2"],
            "controversial": ["숨겨진 배경이나 논란"],
            "logic": "왜 이렇게 분석했는지 쉬운 설명"
        }},
        "balance": {{
            "stated": "겉으로 내세운 명분",
            "hidden": "속에 숨겨진 의도나 다른 입장",
            "note": "이 뉴스를 볼 때 놓치지 말아야 할 포인트 (친근하게)"
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
st.markdown("<div style='color: #6b7280; margin-top: -15px; margin-bottom: 30px;'>1.5 Flash 엔진으로 즐기는 무제한 뉴스 통찰</div>", unsafe_allow_html=True)

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
                
                if st.button("✨ Deep Analysis", key=f"btn_{i}", use_container_width=True, type="primary"):
                    with st.spinner("1.5 Flash 엔진 분석 중..."):
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

                                t1, t2 = st.tabs(["✅ Fact", "⚖️ Balance"])
                                with t1:
                                    for f in res['fact_check']['verified']:
                                        st.markdown(f"<span class='badge-valid'>팩트</span> {f}", unsafe_allow_html=True)
                                    st.caption(f"근거: {res['fact_check']['logic']}")
                                with t2:
                                    st.success(f"**명분:** {res['balance']['stated']}")
                                    st.warning(f"**이면:** {res['balance']['hidden']}")
                                
                                st.write(f"🧐 **Point:** {res['balance']['note']}")
                                # 🏁 사용 모델 확인 및 시간 출력
                                current_model = find_working_model()
                                st.caption(f"🤖 모델: {current_model} | ⏱️ {round(time.time() - start_time, 2)}s")
                            else:
                                st.error("분석 실패. 다시 시도해주세요!")
                        except Exception as e:
                            st.error(f"오류: {e}")
                
                st.link_button("Read Original", entry.link, use_container_width=True)