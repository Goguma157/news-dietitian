import streamlit as st
import feedparser
from groq import Groq
import json
import requests
import time
import re

# 1. 페이지 설정
st.set_page_config(page_title="News Dietitian : Fact Checker", page_icon="⚖️", layout="wide")

# ==========================================
# 🎨 AllSides 스타일: 전문적이고 신뢰감 있는 CSS
# ==========================================
st.markdown("""
<style>
    /* 폰트: 제목은 권위 있는 Serif(명조), 본문은 깔끔한 Sans-serif(고딕) */
    @import url('https://fonts.googleapis.com/css2?family=Merriweather:wght@300;400;700;900&family=Roboto:wght@300;400;500;700&display=swap');
    
    html, body, [class*="css"] { 
        font-family: 'Roboto', sans-serif !important; 
        color: #333333;
        background-color: #fcfcfc;
    }
    
    h1, h2, h3 {
        font-family: 'Merriweather', serif !important;
        font-weight: 900;
        color: #2c3e50;
    }

    /* 사이드바 스타일 (신문 1면 사이드바 느낌) */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e0e0e0;
    }

    /* 뉴스 카드 컨테이너 (각진 모서리, 미니멀한 그림자) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 4px; /* 둥근 느낌 제거 */
        padding: 24px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        transition: all 0.2s;
        margin-bottom: 16px;
    }
    
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: #b0b0b0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.08);
    }

    /* 버튼 스타일 (언론사 구독 버튼 느낌) */
    .stButton > button {
        background-color: #ffffff;
        color: #2c3e50;
        border: 1px solid #2c3e50;
        border-radius: 2px;
        font-weight: 600;
        font-family: 'Roboto', sans-serif;
        text-transform: uppercase;
        font-size: 12px;
        padding: 0.4rem 1rem;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background-color: #2c3e50;
        color: #ffffff;
        border-color: #2c3e50;
    }

    /* 커스텀 배지 스타일 */
    .badge-fact { background-color: #27ae60; color: white; padding: 4px 8px; font-size: 10px; font-weight: 800; text-transform: uppercase; border-radius: 2px; letter-spacing: 0.05em; }
    .badge-mixed { background-color: #f39c12; color: white; padding: 4px 8px; font-size: 10px; font-weight: 800; text-transform: uppercase; border-radius: 2px; letter-spacing: 0.05em; }
    .badge-opinion { background-color: #c0392b; color: white; padding: 4px 8px; font-size: 10px; font-weight: 800; text-transform: uppercase; border-radius: 2px; letter-spacing: 0.05em; }
    .badge-source { background-color: #ecf0f1; color: #7f8c8d; padding: 4px 8px; font-size: 10px; font-weight: 700; text-transform: uppercase; border-radius: 2px; margin-right: 6px; }

    /* 분석 결과 박스 (신문 사설 느낌) */
    .insight-box {
        background-color: #f9f9f9;
        border-left: 4px solid #34495e;
        padding: 15px 20px;
        font-family: 'Merriweather', serif;
        font-size: 14px;
        line-height: 1.6;
        color: #2c3e50;
        margin-top: 15px;
    }

    /* 채팅 스타일 */
    .chat-user { text-align: right; margin: 8px 0; color: #555; font-size: 13px; font-style: italic; }
    .chat-ai { text-align: left; margin: 8px 0; font-weight: 600; color: #2c3e50; font-size: 13px; }
    
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
# 🧠 AI 분석
# ==========================================
@st.cache_data(show_spinner=False)
def analyze_news_groq(news_text):
    # AllSides 스타일의 전문적인 분석 요청
    system_prompt = "You are a professional news analyst like AllSides. Analyze the bias, factuality, and context strictly. Output JSON."
    
    user_prompt = f"""
    [Article]: {news_text[:2500]}
    
    [Output Format (JSON Only)]:
    {{
        "title": "Unbiased Headline",
        "summary": "Neutral summary (1-2 sentences)",
        "metrics": {{
            "who": "Key Actor",
            "impact": "Core Impact"
        }},
        "scores": {{
            "fact_ratio": Number (0-100),
            "opinion_ratio": Number (0-100)
        }},
        "balance": {{
            "stated": "Explicit Claim",
            "hidden": "Implicit Bias/Context",
            "rating": "FACT" or "MIXED" or "OPINION"
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
            temperature=0.1, # 사실 기반 분석을 위해 온도를 낮춤
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
                {"role": "system", "content": "You are a neutral news assistant."},
                {"role": "user", "content": f"Context: {news_context}\n\nQuestion: {user_question}"}
            ],
            temperature=0.5
        )
        return completion.choices[0].message.content
    except:
        return "Analysis unavailable."

# --- 화면 구성 ---

st.sidebar.markdown("<h2 style='text-align: center; color: #2c3e50;'>NEWS<br>DIETITIAN</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.caption("CURATED FEEDS")

category = st.sidebar.radio(
    "TOPICS",
    ("HEADLINES", "POLITICS", "BUSINESS", "WORLD", "TECH")
)

rss_feeds = {
    "HEADLINES": "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko",
    "POLITICS": "https://news.google.com/rss/headlines/section/topic/POLITICS?hl=ko&gl=KR&ceid=KR:ko",
    "BUSINESS": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=ko&gl=KR&ceid=KR:ko",
    "WORLD": "https://news.google.com/rss/headlines/section/topic/WORLD?hl=ko&gl=KR&ceid=KR:ko",
    "TECH": "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=ko&gl=KR&ceid=KR:ko"
}

# 메인 헤더 (신문 타이틀 느낌)
st.markdown(f"<h1 style='border-bottom: 2px solid #2c3e50; padding-bottom: 10px;'>{category}</h1>", unsafe_allow_html=True)

try:
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(rss_feeds.get(category), headers=headers, timeout=5)
    news = feedparser.parse(resp.content)
except:
    st.error("Feed Unavailable")
    news = None

if news and news.entries:
    cols = st.columns(2)
    
    for i, entry in enumerate(news.entries[:10]):
        with cols[i % 2]:
            with st.container(border=True):
                # 뉴스 메타 정보
                if ' - ' in entry.title:
                    clean_title = entry.title.rsplit(' - ', 1)[0]
                    source_name = entry.title.rsplit(' - ', 1)[1]
                else:
                    clean_title = entry.title
                    source_name = "NEWS"
                
                # 상단 배지 (출처)
                st.markdown(f"<span class='badge-source'>{source_name}</span> <span style='color:#999; font-size:11px;'>{entry.published[5:16]}</span>", unsafe_allow_html=True)
                
                # 제목 (Serif 폰트 적용)
                st.markdown(f"<h3 style='margin-top: 8px; font-size: 20px; line-height: 1.4; margin-bottom: 15px;'>{clean_title}</h3>", unsafe_allow_html=True)
                
                article_id = entry.link
                
                # 분석 버튼
                if st.button("ANALYZE BIAS", key=f"btn_{i}", use_container_width=True):
                    with st.spinner("Analyzing content..."):
                        res = analyze_news_groq(f"Title: {clean_title}\nContent: {entry.title}")
                        st.session_state[f"analysis_{article_id}"] = res
                
                if f"analysis_{article_id}" in st.session_state:
                    res = st.session_state[f"analysis_{article_id}"]
                    
                    if res:
                        # 등급 배지 결정 (AllSides 스타일)
                        fact_score = res['scores'].get('fact_ratio', 50)
                        if fact_score >= 80:
                            badge_html = "<span class='badge-fact'>FACT-BASED</span>"
                            bar_color = "#27ae60"
                        elif fact_score >= 50:
                            badge_html = "<span class='badge-mixed'>MIXED</span>"
                            bar_color = "#f39c12"
                        else:
                            badge_html = "<span class='badge-opinion'>OPINION</span>"
                            bar_color = "#c0392b"

                        st.markdown(f"<div style='margin-top: 15px; margin-bottom: 5px;'>{badge_html}</div>", unsafe_allow_html=True)
                        
                        # 팩트 게이지 바 (AllSides의 Meter 느낌)
                        st.markdown(f"""
                        <div style="width: 100%; background-color: #eee; height: 6px; border-radius: 3px; margin-bottom: 15px;">
                            <div style="width: {fact_score}%; background-color: {bar_color}; height: 6px; border-radius: 3px;"></div>
                        </div>
                        """, unsafe_allow_html=True)

                        # 분석 내용 박스
                        st.markdown(f"""
                        <div class='insight-box'>
                            <b>SUMMARY</b><br>{res['summary']}<br><br>
                            <b>IMPLICIT BIAS</b><br>{res['balance']['hidden']}
                        </div>
                        """, unsafe_allow_html=True)

                        # Q&A 섹션 (간소화)
                        st.markdown("<div style='margin-top:20px; font-size:12px; font-weight:700; color:#95a5a6;'>ASK THE ANALYST</div>", unsafe_allow_html=True)
                        
                        if article_id not in st.session_state.chat_history:
                            st.session_state.chat_history[article_id] = []

                        for chat in st.session_state.chat_history[article_id]:
                            role_class = "chat-user" if chat["role"] == "user" else "chat-ai"
                            st.markdown(f"<div class='{role_class}'>{chat['content']}</div>", unsafe_allow_html=True)

                        with st.form(key=f"chat_form_{i}", clear_on_submit=True):
                            col_input, col_btn = st.columns([4, 1])
                            with col_input:
                                user_q = st.text_input("Question", placeholder="Ask about context...", label_visibility="collapsed")
                            with col_btn:
                                submit_btn = st.form_submit_button("Ask", use_container_width=True)
                            
                            if submit_btn and user_q:
                                st.session_state.chat_history[article_id].append({"role": "user", "content": user_q})
                                with st.spinner("..."):
                                    ai_answer = ask_ai_about_news(f"Title: {clean_title}", user_q)
                                    st.session_state.chat_history[article_id].append({"role": "ai", "content": ai_answer})
                                st.rerun()

                st.link_button("READ FULL ARTICLE", entry.link, use_container_width=True)