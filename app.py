import streamlit as st
import feedparser
from groq import Groq
import json
import requests
import time
import re

# 1. 페이지 설정
st.set_page_config(page_title="News Dietitian Pro", page_icon="🥗", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Pretendard', sans-serif !important; color: #1a1a1a; }
    .insight-card { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 4px solid #4f46e5; margin-bottom: 10px; }
    .chat-box { background-color: #eef2ff; padding: 10px; border-radius: 8px; margin-top: 10px; border: 1px solid #c7d2fe; }
    .user-chat { background-color: #ffffff; padding: 8px 12px; border-radius: 15px; border: 1px solid #e5e7eb; margin-bottom: 5px; text-align: right; }
    .ai-chat { background-color: #4f46e5; color: white; padding: 8px 12px; border-radius: 15px; margin-bottom: 5px; text-align: left; }
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
# 🧠 AI 기능 1: 뉴스 심층 분석
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
        "scores": {{
            "fact_ratio": 0~100 숫자,
            "opinion_ratio": 0~100 숫자
        }},
        "balance": {{
            "stated": "겉으로 내세운 명분",
            "hidden": "속에 숨겨진 의도",
            "note": "관전 포인트"
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

# ==========================================
# 🧠 AI 기능 2: Q&A 챗봇
# ==========================================
def ask_ai_about_news(news_context, user_question):
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "당신은 뉴스 기사를 읽고 사용자의 질문에 친절하게 답해주는 AI 비서입니다."},
                {"role": "user", "content": f"기사 내용: {news_context}\n\n질문: {user_question}"}
            ],
            temperature=0.5
        )
        return completion.choices[0].message.content
    except:
        return "죄송해요, 답변이 어렵네요."

# --- 화면 구성 ---

st.sidebar.title("🥗 News Dietitian")
st.sidebar.markdown("편식 없는 뉴스 섭취를 위해 Google News 엔진을 사용합니다.")

category = st.sidebar.radio(
    "오늘의 식단 (카테고리)",
    ("🔥 주요 뉴스", "⚖️ 정치", "💰 경제", "🌍 국제", "📱 IT/과학")
)

# RSS 주소 (구글 뉴스)
rss_feeds = {
    "🔥 주요 뉴스": "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko",
    "⚖️ 정치": "https://news.google.com/rss/headlines/section/topic/POLITICS?hl=ko&gl=KR&ceid=KR:ko",
    "💰 경제": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=ko&gl=KR&ceid=KR:ko",
    "🌍 국제": "https://news.google.com/rss/headlines/section/topic/WORLD?hl=ko&gl=KR&ceid=KR:ko",
    "📱 IT/과학": "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=ko&gl=KR&ceid=KR:ko"
}

st.title(f"{category} 브리핑")

try:
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(rss_feeds.get(category), headers=headers, timeout=5)
    news = feedparser.parse(resp.content)
except:
    st.error("뉴스를 가져오는데 실패했습니다.")
    news = None

if news and news.entries:
    cols = st.columns(2)
    
    for i, entry in enumerate(news.entries[:10]):
        with cols[i % 2]:
            with st.container(border=True):
                # 제목 정제
                if ' - ' in entry.title:
                    clean_title = entry.title.rsplit(' - ', 1)[0]
                    source_name = entry.title.rsplit(' - ', 1)[1]
                else:
                    clean_title = entry.title
                    source_name = "News"
                
                st.caption(f"{source_name} | {entry.published[:16]}")
                st.subheader(clean_title)
                
                article_id = entry.link
                
                if st.button("✨ 영양 성분 분석", key=f"btn_{i}", use_container_width=True, type="primary"):
                    with st.spinner("AI가 분석 중..."):
                        res = analyze_news_groq(f"제목: {clean_title}\n내용: {entry.title}")
                        st.session_state[f"analysis_{article_id}"] = res
                
                if f"analysis_{article_id}" in st.session_state:
                    res = st.session_state[f"analysis_{article_id}"]
                    
                    if res:
                        st.markdown("---")
                        st.info(res['summary'])
                        
                        fact_score = res['scores'].get('fact_ratio', 50)
                        st.caption(f"📊 팩트 지수: {fact_score}%")
                        st.progress(fact_score / 100)
                        
                        c1, c2 = st.columns(2)
                        with c1: st.markdown(f"<div class='insight-card'><b>WHO</b><br>{res['metrics']['who']}</div>", unsafe_allow_html=True)
                        with c2: st.markdown(f"<div class='insight-card'><b>IMPACT</b><br>{res['metrics']['impact']}</div>", unsafe_allow_html=True)
                        
                        with st.expander("🔍 속마음 & 관전 포인트"):
                            st.write(f"**명분:** {res['balance']['stated']}")
                            st.write(f"**속마음:** {res['balance']['hidden']}")
                            st.caption(f"Tip: {res['balance']['note']}")

                        st.markdown("---")
                        st.markdown("##### 💬 궁금하면 물어봐!")
                        
                        if article_id not in st.session_state.chat_history:
                            st.session_state.chat_history[article_id] = []

                        for chat in st.session_state.chat_history[article_id]:
                            if chat["role"] == "user":
                                st.markdown(f"<div class='user-chat'>🗣️ {chat['content']}</div>", unsafe_allow_html=True)
                            else:
                                st.markdown(f"<div class='ai-chat'>🤖 {chat['content']}</div>", unsafe_allow_html=True)

                        with st.form(key=f"chat_form_{i}"):
                            user_q = st.text_input("질문:", label_visibility="collapsed", placeholder="이게 무슨 뜻이야?")
                            if st.form_submit_button("전송"):
                                st.session_state.chat_history[article_id].append({"role": "user", "content": user_q})
                                with st.spinner("답변 중..."):
                                    # 에러가 났던 부분을 수정했습니다. 들여쓰기를 정확히 맞췄습니다.
                                    ai_answer = ask_ai_about_news(f"제목: {clean_title}", user_q)
                                    st.session_state.chat_history[article_id].append({"role": "ai", "content": ai_answer})
                                st.rerun()

                st.link_button("원문 기사 보기", entry.link, use_container_width=True)