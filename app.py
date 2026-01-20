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
# 🎨 UI Style
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

    /* 탭 스타일 */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #fff;
        border-radius: 4px;
        color: #555;
        font-weight: 600;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .stTabs [aria-selected="true"] {
        background-color: #2c3e50;
        color: #fff;
    }

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
    .label-container:hover { transform: translateY(-2px); }
    .fact-based { background-color: #27ae60; } 
    .mixed { background-color: #f39c12; }      
    .opinion { background-color: #c0392b; }    

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

    /* 해시태그 스타일 */
    .hashtag {
        background-color: #f0f2f6;
        color: #555;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
        margin-right: 4px;
        display: inline-block;
    }
    
    /* 비교 모드 스타일 */
    .vs-badge {
        background-color: #2c3e50;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 12px;
    }

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
# 🧠 AI Logic (단일 분석 & 비교 분석)
# ==========================================
@st.cache_data(show_spinner=False)
def analyze_news_groq(news_text, region_code):
    
    if region_code == "US":
        lang_instruction = "Answer strictly in English."
    else:
        lang_instruction = "Answer strictly in Korean. Use Hangul ONLY. Do NOT use Chinese characters (Hanja)."
    
    system_prompt = f"""
    You are a professional news analyst. 
    Analyze the bias, factuality, context, and sentiment strictly. 
    {lang_instruction}
    Output JSON format ONLY.
    """
    
    user_prompt = f"""
    [Article]: {news_text[:2500]}
    
    [Output Format (JSON Only)]:
    {{
        "title": "Unbiased Headline",
        "summary": "Neutral summary (1-2 sentences)",
        "keywords": ["tag1", "tag2", "tag3"], 
        "sentiment_emoji": "🔥" or "😐" or "🧊", 
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

# 🌟 [NEW] 비교 분석 함수
@st.cache_data(show_spinner=False)
def compare_news_groq(text_a, text_b, region_code):
    if region_code == "US":
        lang_instruction = "Answer strictly in English."
    else:
        lang_instruction = "Answer strictly in Korean. Use Hangul ONLY. Do NOT use Chinese characters (Hanja)."

    system_prompt = f"""
    You are an unbiased news comparator.
    Compare two articles on the same topic and identify the differences in perspective, tone, and framing.
    {lang_instruction}
    Output JSON format ONLY.
    """

    user_prompt = f"""
    [Article A]: {text_a[:2000]}
    [Article B]: {text_b[:2000]}

    [Output Format (JSON Only)]:
    {{
        "core_difference": "Summarize the main conflict or difference in viewpoint (3 bullet points max).",
        "article_a": {{
            "stance": "Brief stance description",
            "tone": "Tone keyword (e.g., Critical, Supportive)"
        }},
        "article_b": {{
            "stance": "Brief stance description",
            "tone": "Tone keyword"
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

region = st.sidebar.selectbox("REGION / EDITION", ("🇰🇷 Korea (KR)", "🇺🇸 USA (US)"), index=1)
st.sidebar.caption("CURATED FEEDS")

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
st.markdown(f"<h1 style='border-bottom: 2px solid #2c3e50; padding-bottom: 10px;'>{category} <span style='font-size:18px; color:#666;'>({region_code})</span></h1>", unsafe_allow_html=True)

# RSS Fetch
try:
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(rss_categories.get(category), headers=headers, timeout=5)
    news = feedparser.parse(resp.content)
except:
    st.error("Feed Unavailable")
    news = None

# ------------------------------------------------------------------
# 🌟 [NEW] 탭(Tab) 구조: 기존 피드 vs 비교 모드
# ------------------------------------------------------------------
tab1, tab2 = st.tabs(["📰 Daily Feed", "⚖️ Comparison Mode"])

# ==========================================
# 탭 1: 기존 데일리 피드 (기존 기능 모두 포함)
# ==========================================
with tab1:
    if news and news.entries:
        cols = st.columns(2)
        
        for i, entry in enumerate(news.entries[:10]):
            with cols[i % 2]:
                with st.container(border=True):
                    if ' - ' in entry.title:
                        clean_title = entry.title.rsplit(' - ', 1)[0]
                        source_name = entry.title.rsplit(' - ', 1)[1]
                    else:
                        clean_title = entry.title
                        source_name = "NEWS"
                    
                    st.markdown(f"<span class='badge-source'>{source_name}</span> <span style='color:#999; font-size:11px;'>{entry.published[:16]}</span>", unsafe_allow_html=True)
                    st.markdown(f"<h3 style='margin-top: 8px; font-size: 20px; line-height: 1.4; margin-bottom: 15px;'>{clean_title}</h3>", unsafe_allow_html=True)
                    
                    article_id = entry.link
                    
                    # --- 토글 로직 ---
                    view_key = f"view_{article_id}"
                    if view_key not in st.session_state:
                        st.session_state[view_key] = False

                    if st.session_state[view_key]:
                        btn_label = "CLOSE ✕"
                        btn_type = "secondary"
                    else:
                        btn_label = "ANALYZE BIAS"
                        btn_type = "primary"

                    if st.button(btn_label, key=f"btn_{i}", type=btn_type, use_container_width=True):
                        st.session_state[view_key] = not st.session_state[view_key]
                        if st.session_state[view_key] and f"analysis_{article_id}" not in st.session_state:
                            with st.spinner("Analyzing..."):
                                res = analyze_news_groq(f"Title: {clean_title}\nContent: {entry.title}", region_code)
                                st.session_state[f"analysis_{article_id}"] = res
                        st.rerun()
                    
                    if st.session_state[view_key] and f"analysis_{article_id}" in st.session_state:
                        res = st.session_state[f"analysis_{article_id}"]
                        
                        if res:
                            st.markdown("---")
                            
                            # 키워드 태그
                            if "keywords" in res and res["keywords"]:
                                tags_html = ""
                                for tag in res["keywords"]:
                                    tags_html += f"<span class='hashtag'>#{tag}</span>"
                                st.markdown(f"<div style='margin-bottom:10px;'>{tags_html}</div>", unsafe_allow_html=True)

                            fact_score = res['scores'].get('fact_ratio', 50)
                            
                            if fact_score >= 80:
                                badge_class = "fact-based"
                                label_text = "FACT-BASED"
                                tooltip_desc = "작성자의 의견을 배제하고,<br>검증된 사실과 데이터만 담았습니다." if region_code == "KR" else "Strictly based on facts and data,<br>without personal opinion."
                                bar_color = "#27ae60"
                            elif fact_score >= 50:
                                badge_class = "mixed"
                                label_text = "MIXED"
                                tooltip_desc = "사실적인 정보에 작성자의<br>개인적인 해석이나 견해가 섞여 있습니다." if region_code == "KR" else "Factual information mixed with<br>personal interpretation or opinion."
                                bar_color = "#f39c12"
                            else:
                                badge_class = "opinion"
                                label_text = "OPINION"
                                tooltip_desc = "작성자의 주관적인 주장이나<br>감정적 호소가 주를 이룹니다." if region_code == "KR" else "Primarily consists of subjective arguments<br>or emotional appeals."
                                bar_color = "#c0392b"
                            
                            badge_html = f"""
                            <div style='margin-top: 5px; margin-bottom: 5px;'>
                                <span class='label-container {badge_class}'>
                                    {label_text}
                                    <span class='tooltip-text'>{tooltip_desc}</span>
                                </span>
                            </div>
                            """
                            st.markdown(badge_html, unsafe_allow_html=True)
                            
                            st.markdown(f"""
                            <div style="width: 100%; background-color: #eee; height: 6px; border-radius: 3px; margin-bottom: 15px;">
                                <div style="width: {fact_score}%; background-color: {bar_color}; height: 6px; border-radius: 3px;"></div>
                            </div>
                            """, unsafe_allow_html=True)

                            sentiment_emoji = res.get("sentiment_emoji", "🧐")
                            
                            st.markdown(f"""
                            <div class='insight-box'>
                                <b>SUMMARY {sentiment_emoji}</b><br>{res['summary']}<br><br>
                                <b>CONTEXT & BIAS</b><br>{res['balance']['hidden']}
                            </div>
                            """, unsafe_allow_html=True)

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

# ==========================================
# 탭 2: ⚖️ 비교 분석 모드 (Comparison Mode)
# ==========================================
with tab2:
    st.info("💡 비교하고 싶은 키워드를 입력하고, 기사 2개를 선택해보세요. (예: 의대, 금리, AI)")
    
    # 1. 키워드 검색
    search_query = st.text_input("Search Keyword", placeholder="Type keyword to filter articles...", label_visibility="collapsed")
    
    # 기사 필터링
    filtered_entries = []
    if news and news.entries:
        if search_query:
            filtered_entries = [e for e in news.entries if search_query.lower() in e.title.lower()]
        else:
            filtered_entries = news.entries[:20] # 검색어 없으면 최신 20개 표시

    # 2. 체크박스로 기사 선택
    if filtered_entries:
        st.write(f"Found {len(filtered_entries)} articles:")
        selected_articles = []
        
        # 기사 목록 출력 및 선택
        for entry in filtered_entries:
            # 기사 제목 옆에 체크박스
            if st.checkbox(f"{entry.title}", key=f"chk_{entry.link}"):
                selected_articles.append(entry)
        
        # 3. 비교 실행 버튼
        st.markdown("---")
        if len(selected_articles) == 2:
            if st.button("⚖️ COMPARE SELECTED (2)", type="primary", use_container_width=True):
                art_a = selected_articles[0]
                art_b = selected_articles[1]
                
                with st.spinner("Analyzing differences..."):
                    comp_res = compare_news_groq(art_a.title, art_b.title, region_code)
                    
                    if comp_res:
                        # 결과 화면
                        st.subheader("🔍 Perspective Analysis")
                        
                        # 3줄 요약 박스
                        st.markdown(f"""
                        <div class='insight-box' style='border-left: 4px solid #8e44ad; background-color: #f4ecf7;'>
                            <b>⚖️ CORE DIFFERENCE (핵심 차이점)</b><br>
                            {comp_res['core_difference']}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # 좌우 대결 구도
                        col_a, col_b = st.columns(2)
                        
                        with col_a:
                            st.markdown(f"<div class='vs-badge'>ARTICLE A</div>", unsafe_allow_html=True)
                            st.markdown(f"**{art_a.title}**")
                            st.markdown(f"Start Point: **{comp_res['article_a']['stance']}**")
                            st.caption(f"Tone: {comp_res['article_a']['tone']}")
                            st.link_button("Read A", art_a.link, use_container_width=True)

                        with col_b:
                            st.markdown(f"<div class='vs-badge' style='background-color:#7f8c8d;'>ARTICLE B</div>", unsafe_allow_html=True)
                            st.markdown(f"**{art_b.title}**")
                            st.markdown(f"Start Point: **{comp_res['article_b']['stance']}**")
                            st.caption(f"Tone: {comp_res['article_b']['tone']}")
                            st.link_button("Read B", art_b.link, use_container_width=True)
                            
        elif len(selected_articles) > 2:
            st.warning("⚠️ Please select only 2 articles to compare.")
        elif len(selected_articles) == 1:
            st.info("👇 Please select one more article.")
        else:
            st.write("👆 Select 2 articles to compare perspectives.")
            
    else:
        st.write("No articles found based on your keyword.")