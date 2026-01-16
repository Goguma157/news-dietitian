import streamlit as st
import feedparser
from groq import Groq
import json
import requests
import time
import re

# 1. 페이지 설정 (아이콘 변경)
st.set_page_config(page_title="News Dietitian Premium", page_icon="💎", layout="wide")

# ==========================================
# 🎨 [핵심] 고급스러운 UI 디자인 (CSS)
# ==========================================
st.markdown("""
<style>
    /* 폰트: 프리텐다드 적용 (가독성 최고) */
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] { 
        font-family: 'Pretendard', sans-serif !important; 
        color: #1f2937;
        background-color: #f3f4f6; /* 아주 연한 회색 배경 */
    }

    /* 메인 타이틀 스타일 */
    h1 {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
        letter-spacing: -1px;
    }

    /* 뉴스 카드 디자인 (그림자 + 둥근 모서리) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: white;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        border: 1px solid #f3f4f6;
        padding: 20px;
        transition: transform 0.2s ease-in-out;
    }
    
    /* 카드 호버 효과 (마우스 올리면 살짝 뜸) */
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    }

    /* 버튼 스타일 (그라데이션) */
    .stButton > button {
        background: linear-gradient(to right, #2563eb, #1d4ed8);
        color: white;
        border-radius: 12px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        background: linear-gradient(to right, #1d4ed8, #1e40af);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
        transform: scale(1.02);
    }

    /* 분석 결과 박스 */
    .insight-card { 
        background-color: #f8fafc; 
        padding: 16px; 
        border-radius: 12px; 
        border-left: 4px solid #3b82f6; 
        margin-bottom: 12px; 
    }
    
    /* 팩트/임팩트 헤더 */
    .fact-header { 
        font-size: 11px; 
        font-weight: 700; 
        color: #64748b; 
        text-transform: uppercase; 
        letter-spacing: 0.05em;
        margin-bottom: 4px; 
    }
    
    /* 채팅창 디자인 (아이메시지 스타일) */
    .user-chat { 
        background-color: #3b82f6; 
        color: white; 
        padding: 10px 16px; 
        border-radius: 18px 18px 0 18px; 
        margin-bottom: 8px; 
        text-align: right; 
        box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
        max-width: 85%;
        margin-left: auto;
    }
    .ai-chat { 
        background-color: #e2e8f0; 
        color: #1e293b; 
        padding: 10px 16px; 
        border-radius: 18px 18px 18px 0; 
        margin-bottom: 8px; 
        text-align: left; 
        max-width: 85%;
    }

    /* 사이드바 스타일 */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e5e7eb;
    }
</style>
""", unsafe_allow_html=True)

# 2. Groq 연결
try:
    api_key = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=api_key)
except Exception as e:
    st.error(f"⚠️ API 키 설정 오류: {e}")
    st.stop()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = {}

# 🧼 JSON 세탁기
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
# 🧠 AI 기능
# ==========================================
@st.cache_data(show_spinner=False)
def analyze_news_groq(news_text):
    system_prompt = "당신은 세련되고 명쾌한 뉴스 큐레이터입니다. 초심자도 이해하기 쉬운 비유로 설명하고, JSON으로 출력하세요."
    
    user_prompt = f"""
    [뉴스]: {news_text[:2000]}
    
    [형식]:
    {{
        "title": "호기심을 자극하는 제목",
        "summary": "핵심을 찌르는 쉬운 요약",
        "metrics": {{
            "who": "주인공",
            "whom": "영향받는 대상",
            "action": "핵심 사건",
            "impact": "나에게 미치는 영향"
        }},
        "scores": {{
            "fact_ratio": 0~100 숫자,
            "opinion_ratio": 0~100 숫자
        }},
        "balance": {{
            "stated": "표면적 명분",
            "hidden": "숨겨진 의도",
            "note": "인사이트"
        }}
    }}
    """
    
    try:
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
    except:
        return None

def ask_ai_about_news(news_context, user_question):
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "당신은 위트 있고 똑똑한 뉴스 비서입니다."},
                {"role": "user", "content": f"기사 내용: {news_context}\n\n질문: {user_question}"}
            ],
            temperature=0.5
        )
        return completion.choices[0].message.content
    except:
        return "죄송해요, 답변이 어렵네요."

# --- 화면 구성 ---

st.sidebar.markdown("## 💎 Premium News")
st.sidebar.info("엄선된 구글 뉴스 엔진이 실시간으로 뉴스를 큐레이션합니다.")

category = st.sidebar.radio(
    "섹션 선택",
    ("🔥 주요 헤드라인", "🏛️ 정치/사회", "💼 경제/금융", "🌏 글로벌", "🧬 테크/과학")
)

rss_feeds = {
    "🔥 주요 헤드라인": "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko",
    "🏛️ 정치/사회": "https://news.google.com/rss/headlines/section/topic/POLITICS?hl=ko&gl=KR&ceid=KR:ko",
    "💼 경제/금융": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=ko&gl=KR&ceid=KR:ko",
    "🌏 글로벌": "https://news.google.com/rss/headlines/section/topic/WORLD?hl=ko&gl=KR&ceid=KR:ko",
    "🧬 테크/과학": "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=ko&gl=KR&ceid=KR:ko"
}

st.markdown(f"<h1>{category}</h1>", unsafe_allow_html=True)
st.caption("AI가 복잡한 뉴스를 영양가 있게 소화시켜 드립니다.")

try:
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(rss_feeds.get(category), headers=headers, timeout=5)
    news = feedparser.parse(resp.content)
except:
    st.error("뉴스 피드를 연결할 수 없습니다.")
    news = None

if news and news.entries:
    cols = st.columns(2)
    
    for i, entry in enumerate(news.entries[:10]):
        with cols[i % 2]:
            # 카드형 디자인 적용 (st.container 활용)
            with st.container(border=True):
                # 제목 및 출처 정리
                if ' - ' in entry.title:
                    clean_title = entry.title.rsplit(' - ', 1)[0]
                    source_name = entry.title.rsplit(' - ', 1)[1]
                else:
                    clean_title = entry.title
                    source_name = "News"
                
                # 상단 메타 정보 (뱃지 스타일)
                st.markdown(
                    f"""<div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;'>
                        <span style='background:#eff6ff; color:#2563eb; padding:2px 8px; border-radius:6px; font-size:12px; font-weight:600;'>{source_name}</span>
                        <span style='color:#94a3b8; font-size:12px;'>{entry.published[5:16]}</span>
                    </div>""", 
                    unsafe_allow_html=True
                )
                
                st.markdown(f"<h3 style='margin-top:0; font-size:18px; line-height:1.4;'>{clean_title}</h3>", unsafe_allow_html=True)
                
                article_id = entry.link
                
                # 버튼 (전체 너비)
                if st.button("✨ AI 심층 분석", key=f"btn_{i}", use_container_width=True):
                    with st.spinner("💎 프리미엄 인사이트 추출 중..."):
                        res = analyze_news_groq(f"제목: {clean_title}\n내용: {entry.title}")
                        st.session_state[f"analysis_{article_id}"] = res
                
                # 분석 결과 표시
                if f"analysis_{article_id}" in st.session_state:
                    res = st.session_state[f"analysis_{article_id}"]
                    
                    if res:
                        st.markdown("<hr style='margin: 15px 0; border-color: #f1f5f9;'>", unsafe_allow_html=True)
                        st.markdown(f"**💡 {res['title']}**")
                        st.success(res['summary'])
                        
                        # 게이지 바
                        fact_score = res['scores'].get('fact_ratio', 50)
                        st.caption(f"📊 팩트 지수: {fact_score}%")
                        st.progress(fact_score / 100)
                        
                        # 2열 정보 카드
                        c1, c2 = st.columns(2)
                        with c1: st.markdown(f"<div class='insight-card'><div class='fact-header'>WHO (주인공)</div><div class='fact-content'>{res['metrics']['who']}</div></div>", unsafe_allow_html=True)
                        with c2: st.markdown(f"<div class='insight-card'><div class='fact-header'>IMPACT (나의 삶)</div><div class='fact-content'>{res['metrics']['impact']}</div></div>", unsafe_allow_html=True)
                        
                        # 아코디언 스타일
                        with st.expander("🔍 숨겨진 의도와 맥락 더보기"):
                            st.markdown(f"**🗣️ 명분:** {res['balance']['stated']}")
                            st.markdown(f"**🕵️ 속마음:** {res['balance']['hidden']}")
                            st.info(f"💡 Insight: {res['balance']['note']}")

                        st.markdown("---")
                        
                        # 채팅 UI
                        st.markdown("##### 💬 AI 에디터와 대화하기")
                        
                        if article_id not in st.session_state.chat_history:
                            st.session_state.chat_history[article_id] = []

                        # 대화 내용 렌더링
                        for chat in st.session_state.chat_history[article_id]:
                            if chat["role"] == "user":
                                st.markdown(f"<div class='user-chat'>{chat['content']}</div>", unsafe_allow_html=True)
                            else:
                                st.markdown(f"<div class='ai-chat'>{chat['content']}</div>", unsafe_allow_html=True)

                        # 입력창
                        with st.form(key=f"chat_form_{i}", clear_on_submit=True):
                            col_input, col_btn = st.columns([4, 1])
                            with col_input:
                                user_q = st.text_input("질문", placeholder="이 뉴스, 호재인가요?", label_visibility="collapsed")
                            with col_btn:
                                submit_btn = st.form_submit_button("전송", use_container_width=True)
                            
                            if submit_btn and user_q:
                                st.session_state.chat_history[article_id].append({"role": "user", "content": user_q})
                                with st.spinner("작성 중..."):
                                    ai_answer = ask_ai_about_news(f"제목: {clean_title}", user_q)
                                    st.session_state.chat_history[article_id].append({"role": "ai", "content": ai_answer})
                                st.rerun()

                st.link_button("기사 원문 읽기", entry.link, use_container_width=True)