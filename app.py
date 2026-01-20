import streamlit as st
import feedparser
from groq import Groq
import json
import requests
import time
import re

# 1. Page Config
st.set_page_config(page_title="News Dietitian : Global", page_icon="🌎", layout="wide")

# ==========================================
# 🎨 UI Style (툴팁 기능 + 깔끔한 디자인)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Merriweather:wght@300;400;700;900&family=Roboto:wght@300;400;500;700&display=swap');
    
    html, body, [class*="css"] { 
        font-family: 'Roboto', sans-serif !important; 
        color: #333333;
        background-color: #fcfcfc;
    }
    
    h1, h2, h3 { font-family: 'Merriweather', serif !important; font-weight: 900; color: #2c3e50; }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 4px;
        padding: 24px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 16px;
    }

    /* --- [라벨 & 말풍선 스타일] --- */
    .label-container {
        position: relative;
        display: inline-block;
        padding: 5px 10px;
        border-radius: 4px;
        color: white;
        font-weight: 800;
        font-size: 11px;
        cursor: help; 
        margin-right: 5px;
        transition: transform 0.2s;
    }
    
    .label-container:hover {
        transform: translateY(-2px); 
    }

    /* 색상 정의 */
    .fact-based { background-color: #27ae60; } 
    .mixed { background-color: #f39c12; }      
    .opinion { background-color: #c0392b; }    

    /* 숨겨진 말풍선 (Tooltip) */
    .tooltip-text {
        visibility: hidden;
        width: 200px;
        background-color: #2c3e50;
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 8px 10px;
        font-size: 11px;
        font-weight: normal;
        line-height: 1.4;

        position: absolute;
        bottom: 135%; 
        left: 50%;
        transform: translateX(-50%);
        z-index: 999; 
        
        opacity: 0;
        transition: opacity 0.3s, bottom 0.3s;
        box-shadow: 0 4px 6px rgba(0,0,0,0.15);
    }

    /* 말풍선 꼬리 */
    .tooltip-text::after {
        content: "";
        position: absolute;
        top: 100%;
        left: 50%;
        margin-left: -5px;
        border-width: 5px;
        border-style: solid;
        border-color: #2c3e50 transparent transparent transparent;
    }

    .label-container:hover .tooltip-text {
        visibility: visible;
        opacity: 1;
        bottom: 125%; 
    }
    /* --- [스타일 끝] --- */

    .badge-source { background-color: #ecf0f1; color: #7f8c8d; padding: 4px 8px; font-size: 10px; font-weight: 700; text-transform: uppercase; border-radius: 2px; margin-right: 6px; }

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
    
    .chat-user { text-align: right; margin: 8px 0; color: #555; font-size: 13px; font-style: italic; }
    .chat-ai { text-align: left; margin: 8px 0; font-weight: 600; color: #2c3e50; font-size: 13px; }
</style>
""", unsafe_allow_html=True)

# 2. Groq Setup
try:
    api_key = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=api_key)
except Exception as e:
    st.error(f"⚠️ API Key Error: {e}")
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
# 🧠 AI Logic (Language Adaptive & No Hanja)
# ==========================================
@st.cache_data(show_spinner=False)
def analyze_news_groq(news_text, region_code):
    
    # 🚨 언어 설정: 한자 사용 금지(No Hanja) 규칙 추가됨!
    if region_code == "US":
        lang_instruction = "Answer strictly in English."
    else:
        # 여기에 'Hangul ONLY' 조건을 강력하게 추가했습니다.
        lang_instruction = "Answer strictly in Korean. Use Hangul ONLY. Do NOT use Chinese characters (Hanja) or Mixed script."
    
    system_prompt = f"""
    You are a professional news analyst like AllSides. 
    Analyze the bias, factuality, and context strictly. 
    {lang_instruction}
    Output JSON format ONLY.
    """
    
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
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        return safe_parse_json(completion.choices[0].message.content)
    except:
        return None

def ask_ai_about_news(news_context, user_question, region_code):
    # 챗봇도 뉴스 언어에 맞춰서 대답
    lang_instruction = "Answer in English." if region_code == "US" else "Answer in Korean (Hangul only)."
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": f"You are a neutral news assistant. {lang_instruction}"},
                {"role": "user", "content": f"Context: {news_context}\n\nQuestion: {user_question}"}
            ],
            temperature=0.5
        )
        return completion.choices[0].message.content
    except:
        return "Sorry, I cannot answer right now."

# --- UI Layout ---

st.sidebar.markdown("<h2 style='text-align: center; color: #2c3e50;'>NEWS<br>DIETITIAN</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")

# 🌍 Region Selector
region = st.sidebar.selectbox(
    "REGION / EDITION",
    ("🇰🇷 Korea (KR)", "🇺🇸 USA (US)"),
    index=1 
)

st.sidebar.caption("CURATED FEEDS")

# RSS Feeds Mapping
if "Korea" in region:
    region_code = "KR"
    rss_categories = {
        "HEADLINES": "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko",
        "POLITICS": "https://news.google.com/rss/headlines/section/topic/POLITICS?hl=ko&gl=KR&ceid=KR:ko",
        "BUSINESS": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=ko&gl=KR&ceid=KR:ko",
        "WORLD": "https://news.google.com/rss/headlines/section/topic/WORLD?hl=ko&gl=KR&ceid=KR:ko",
        "TECH": "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=ko&gl=KR&ceid=KR:ko"
    }
else:
    region_code = "US"
    rss_categories = {
        "HEADLINES": "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
        "POLITICS": "https://news.google.com/rss/headlines/section/topic/POLITICS?hl=en-US&gl=US&ceid=US:en",
        "BUSINESS": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-US&gl=US&ceid=US:en",
        "WORLD": "https://news.google.com/rss/headlines/section/topic/WORLD?hl=en-US&gl=US&ceid=US:en",
        "TECH": "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-US&gl=US&ceid=US:en"
    }

category = st.sidebar.radio("TOPICS", list(rss_categories.keys()))

# Main Header
st.markdown(f"<h1 style='border-bottom: 2px solid #2c3e50; padding-bottom: 10px;'>{category} <span style='font-size:18px; color:#666;'>({region_code})</span></h1>", unsafe_allow_html=True)

try:
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(rss_categories.get(category), headers=headers, timeout=5)
    news = feedparser.parse(resp.content)
except:
    st.error("Feed Unavailable")
    news = None

if news and news.entries:
    cols = st.columns(2)
    
    for i, entry in enumerate(news.entries[:10]):
        with cols[i % 2]:
            with st.container(border=True):
                # Title Cleanup
                if ' - ' in entry.title:
                    clean_title = entry.title.rsplit(' - ', 1)[0]
                    source_name = entry.title.rsplit(' - ', 1)[1]
                else:
                    clean_title = entry.title
                    source_name = "NEWS"
                
                # Top Badge
                st.markdown(f"<span class='badge-source'>{source_name}</span> <span style='color:#999; font-size:11px;'>{entry.published[:16]}</span>", unsafe_allow_html=True)
                
                # Title
                st.markdown(f"<h3 style='margin-top: 8px; font-size: 20px; line-height: 1.4; margin-bottom: 15px;'>{clean_title}</h3>", unsafe_allow_html=True)
                
                article_id = entry.link
                
                # Analyze Button
                if st.button("ANALYZE BIAS", key=f"btn_{i}", use_container_width=True):
                    with st.spinner("Analyzing..."):
                        res = analyze_news_groq(f"Title: {clean_title}\nContent: {entry.title}", region_code)
                        st.session_state[f"analysis_{article_id}"] = res
                
                if f"analysis_{article_id}" in st.session_state:
                    res = st.session_state[f"analysis_{article_id}"]
                    
                    if res:
                        fact_score = res['scores'].get('fact_ratio', 50)
                        
                        # ==========================================
                        # 🏷️ 툴팁이 적용된 라벨 생성 (No Hanja는 위에서 처리됨)
                        # ==========================================
                        if fact_score >= 80:
                            # 1. Fact-based
                            badge_class = "fact-based"
                            label_text = "FACT-BASED"
                            tooltip_desc = "작성자의 의견을 배제하고,<br>검증된 사실과 데이터만 담았습니다." if region_code == "KR" else "Strictly based on facts and data,<br>without personal opinion."
                            bar_color = "#27ae60"

                        elif fact_score >= 50:
                            # 2. Mixed
                            badge_class = "mixed"
                            label_text = "MIXED"
                            tooltip_desc = "사실적인 정보에 작성자의<br>개인적인 해석이나 견해가 섞여 있습니다." if region_code == "KR" else "Factual information mixed with<br>personal interpretation or opinion."
                            bar_color = "#f39c12"

                        else:
                            # 3. Opinion
                            badge_class = "opinion"
                            label_text = "OPINION"
                            tooltip_desc = "작성자의 주관적인 주장이나<br>감정적 호소가 주를 이룹니다." if region_code == "KR" else "Primarily consists of subjective arguments<br>or emotional appeals."
                            bar_color = "#c0392b"
                        
                        # HTML 조립
                        badge_html = f"""
                        <div style='margin-top: 15px; margin-bottom: 5px;'>
                            <span class='label-container {badge_class}'>
                                {label_text}
                                <span class='tooltip-text'>{tooltip_desc}</span>
                            </span>
                        </div>
                        """

                        st.markdown(badge_html, unsafe_allow_html=True)
                        
                        # Fact Gauge
                        st.markdown(f"""
                        <div style="width: 100%; background-color: #eee; height: 6px; border-radius: 3px; margin-bottom: 15px;">
                            <div style="width: {fact_score}%; background-color: {bar_color}; height: 6px; border-radius: 3px;"></div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Analysis Box
                        st.markdown(f"""
                        <div class='insight-box'>
                            <b>SUMMARY</b><br>{res['summary']}<br><br>
                            <b>CONTEXT & BIAS</b><br>{res['balance']['hidden']}
                        </div>
                        """, unsafe_allow_html=True)

                        # Q&A Section
                        st.markdown("<div style='margin-top:20px; font-size:12px; font-weight:700; color:#95a5a6;'>ASK THE ANALYST</div>", unsafe_allow_html=True)
                        
                        if article_id not in st.session_state.chat_history:
                            st.session_state.chat_history[article_id] = []

                        for chat in st.session_state.chat_history[article_id]:
                            role_class = "chat-user" if chat["role"] == "user" else "chat-ai"
                            st.markdown(f"<div class='{role_class}'>{chat['content']}</div>", unsafe_allow_html=True)

                        with st.form(key=f"chat_form_{i}", clear_on_submit=True):
                            col_input, col_btn = st.columns([4, 1])
                            with col_input:
                                user_q = st.text_input("Question", placeholder="Ask about this article...", label_visibility="collapsed")
                            with col_btn:
                                submit_btn = st.form_submit_button("ASK", use_container_width=True)
                            
                            if submit_btn and user_q:
                                st.session_state.chat_history[article_id].append({"role": "user", "content": user_q})
                                with st.spinner("Thinking..."):
                                    ai_answer = ask_ai_about_news(f"Title: {clean_title}", user_q, region_code)
                                    st.session_state.chat_history[article_id].append({"role": "ai", "content": ai_answer})
                                st.rerun()

                st.link_button("READ FULL ARTICLE", entry.link, use_container_width=True)