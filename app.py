import streamlit as st
import feedparser
from groq import Groq
import json
import requests
import time
import re

# ==========================================
# 1. 기본 설정 및 CSS 스타일
# ==========================================
st.set_page_config(page_title="News Dietitian : Global", page_icon="🌎", layout="wide")

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

    /* --- [VS 모드 시각화 스타일] --- */
    .vs-container {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-top: 20px;
        gap: 20px;
    }
    .vs-card {
        flex: 1;
        padding: 20px;
        border-radius: 12px;
        color: #fff;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
    .vs-card-a { background: linear-gradient(135deg, #3498db, #2980b9); } /* 파랑 (A) */
    .vs-card-b { background: linear-gradient(135deg, #e74c3c, #c0392b); } /* 빨강 (B) */
    
    .vs-title { font-size: 16px; font-weight: bold; margin-bottom: 10px; line-height: 1.4; height: 50px; overflow: hidden; }
    .vs-label { font-size: 11px; text-transform: uppercase; letter-spacing: 1px; opacity: 0.8; margin-bottom: 5px; }
    .vs-tag { 
        background-color: rgba(255,255,255,0.2); 
        padding: 4px 8px; 
        border-radius: 4px; 
        font-size: 12px; 
        font-weight: bold; 
        display: inline-block;
        margin-top: 10px;
    }
    
    .major-badge {
        background-color: #f1c40f;
        color: #333;
        font-size: 10px;
        font-weight: 800;
        padding: 2px 6px;
        border-radius: 4px;
        margin-right: 5px;
        vertical-align: middle;
    }

    /* --- [기존 라벨 스타일] --- */
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
        width: 220px;
        background-color: #2c3e50;
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 10px;
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

# ==========================================
# 2. 메이저 언론사 리스트 (필터링용)
# ==========================================
MAJOR_KR = ["조선일보", "중앙일보", "동아일보", "한겨레", "경향신문", "한국일보", "매일경제", "한국경제", "KBS", "MBC", "SBS", "JTBC", "YTN", "연합뉴스"]
MAJOR_US = ["CNN", "Fox News", "New York Times", "Washington Post", "Reuters", "Associated Press", "BBC", "NBC", "CNBC", "Bloomberg", "USA Today", "Wall Street Journal"]

def is_major_media(source_name, region_code):
    target_list = MAJOR_KR if region_code == "KR" else MAJOR_US
    # 대소문자 무시하고 포함 여부 확인
    return any(m.lower() in source_name.lower() for m in target_list)

# ==========================================
# 3. Groq 설정
# ==========================================
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
# 4. AI 분석 로직
# ==========================================
@st.cache_data(show_spinner=False)
def analyze_news_groq(news_text, region_code):
    
    if region_code == "KR":
        lang_instruction = "Answer strictly in Korean. Use Hangul ONLY. Do NOT use Chinese characters (Hanja)."
    else:
        lang_instruction = "Answer strictly in English."
    
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

# 🌟 [업데이트] AI 분석 함수 (성향 점수 요청 추가)
@st.cache_data(show_spinner=False)
def compare_news_groq(text_a, text_b, region_code):
    if region_code == "KR":
        lang_instruction = "Answer strictly in Korean. Use Hangul ONLY."
        target_lang = "Korean"
    else:
        lang_instruction = "Answer strictly in English."
        target_lang = "English"

    system_prompt = f"""
    You are an unbiased news comparator.
    Compare two articles on the same topic strictly.
    Quantify the stance on a scale from -10 to +10.
    {lang_instruction}
    Output JSON format ONLY.
    """

    user_prompt = f"""
    [Article A]: {text_a[:2000]}
    [Article B]: {text_b[:2000]}

    [Instruction]:
    Assign a 'stance_score' for each article from -10 to +10.
    - -10 = Extremely Critical / Negative / Left-leaning
    - 0 = Neutral / Balanced
    - +10 = Extremely Supportive / Positive / Right-leaning
    
    [Output Format (JSON Only)]:
    {{
        "core_difference": "One sentence summary of the main conflict in {target_lang}.",
        "key_points": ["Point 1", "Point 2", "Point 3"],
        "article_a": {{
            "stance_label": "Short keyword (e.g. Critical) in {target_lang}",
            "stance_score": Integer (-10 to 10),
            "summary": "1 sentence summary in {target_lang}"
        }},
        "article_b": {{
            "stance_label": "Short keyword in {target_lang}",
            "stance_score": Integer (-10 to 10),
            "summary": "1 sentence summary in {target_lang}"
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

# ==========================================
# 5. UI Layout
# ==========================================
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

try:
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(rss_categories.get(category), headers=headers, timeout=5)
    news = feedparser.parse(resp.content)
except:
    st.error("Feed Unavailable")
    news = None

# ==========================================
# 6. TABS (Feed / Comparison)
# ==========================================
tab1, tab2 = st.tabs(["📰 Daily Feed", "⚖️ Comparison Mode"])

# --- TAB 1: Daily Feed ---
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
                    view_key = f"view_{article_id}"
                    if view_key not in st.session_state: st.session_state[view_key] = False

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
                            if "keywords" in res and res["keywords"]:
                                tags_html = "".join([f"<span class='hashtag'>#{tag}</span>" for tag in res["keywords"]])
                                st.markdown(f"<div style='margin-bottom:10px;'>{tags_html}</div>", unsafe_allow_html=True)

                            fact_score = res['scores'].get('fact_ratio', 50)
                            if fact_score >= 80:
                                badge_class, label_text, bar_color = "fact-based", "FACT-BASED", "#27ae60"
                                tooltip_desc = "작성자의 의견을 배제하고,<br>검증된 사실과 데이터만 담았습니다." if region_code == "KR" else "Strictly based on facts and data,<br>without personal opinion."
                            elif fact_score >= 50:
                                badge_class, label_text, bar_color = "mixed", "MIXED", "#f39c12"
                                tooltip_desc = "사실적인 정보에 작성자의<br>개인적인 해석이나 견해가 섞여 있습니다." if region_code == "KR" else "Factual information mixed with<br>personal interpretation or opinion."
                            else:
                                badge_class, label_text, bar_color = "opinion", "OPINION", "#c0392b"
                                tooltip_desc = "작성자의 주관적인 주장이나<br>감정적 호소가 주를 이룹니다." if region_code == "KR" else "Primarily consists of subjective arguments<br>or emotional appeals."
                            
                            st.markdown(f"""
                            <div style='margin-top: 5px; margin-bottom: 5px;'>
                                <span class='label-container {badge_class}'>{label_text}<span class='tooltip-text'>{tooltip_desc}</span></span>
                            </div>
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
                            if article_id not in st.session_state.chat_history: st.session_state.chat_history[article_id] = []
                            
                            for chat in st.session_state.chat_history[article_id]:
                                role_class = "chat-user" if chat["role"] == "user" else "chat-ai"
                                st.markdown(f"<div class='{role_class}'>{chat['content']}</div>", unsafe_allow_html=True)

                            with st.form(key=f"chat_form_{i}", clear_on_submit=True):
                                c1, c2 = st.columns([4, 1])
                                uq = c1.text_input("Q", placeholder="Ask...", label_visibility="collapsed")
                                if c2.form_submit_button("ASK", use_container_width=True) and uq:
                                    st.session_state.chat_history[article_id].append({"role": "user", "content": uq})
                                    with st.spinner("..."):
                                        ans = ask_ai_about_news(f"Title: {clean_title}", uq, region_code)
                                        st.session_state.chat_history[article_id].append({"role": "ai", "content": ans})
                                    st.rerun()
                    st.link_button("READ FULL ARTICLE", entry.link, use_container_width=True)

# --- TAB 2: Comparison Mode (Visual Spectrum Added) ---
with tab2:
    # 스타일 추가 (스펙트럼 바 전용)
    st.markdown("""
    <style>
        .spectrum-container {
            position: relative;
            width: 100%;
            height: 60px;
            background: linear-gradient(90deg, #3498db 0%, #ecf0f1 50%, #e74c3c 100%);
            border-radius: 30px;
            margin: 20px 0 40px 0;
            box-shadow: inset 0 2px 5px rgba(0,0,0,0.1);
        }
        .center-line {
            position: absolute;
            left: 50%;
            top: 0;
            bottom: 0;
            width: 2px;
            background-color: rgba(0,0,0,0.1);
            border-right: 1px dashed #999;
        }
        .marker {
            position: absolute;
            top: 50%;
            transform: translate(-50%, -50%);
            width: 40px;
            height: 40px;
            border-radius: 50%;
            border: 3px solid white;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            font-weight: bold;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            z-index: 10;
            transition: left 0.5s ease-out;
        }
        .marker-a { background-color: #2980b9; } /* Blue for A */
        .marker-b { background-color: #c0392b; } /* Red for B */
        
        .marker-label {
            position: absolute;
            top: -25px;
            left: 50%;
            transform: translateX(-50%);
            background: #333;
            color: white;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 10px;
            white-space: nowrap;
        }
    </style>
    """, unsafe_allow_html=True)

    if region_code == "KR":
        txt = {
            "info": "💡 주제를 입력하고 검색하세요. (예: 의대 증원, 트럼프, 금리)",
            "placeholder": "관심 있는 키워드 입력...",
            "search_btn": "뉴스 검색 🔎",
            "compare_btn": "⚖️ 비교 분석 시작 (COMPARE)",
            "analyzing": "두 기사의 관점을 치열하게 분석 중입니다...",
            "core_diff": "⚔️ 핵심 대립 포인트",
            "found": "개의 기사를 찾았습니다.",
            "major": "메이저",
            "visual_title": "📊 성향 스펙트럼 (Stance Spectrum)"
        }
    else:
        txt = {
            "info": "💡 Enter topic to search & compare (e.g., Bitcoin, AI)",
            "placeholder": "Type keywords...",
            "search_btn": "Search 🔎",
            "compare_btn": "⚖️ COMPARE SELECTED (2)",
            "analyzing": "Analyzing conflict...",
            "core_diff": "⚔️ KEY CONFLICT",
            "found": "articles found.",
            "major": "MAJOR",
            "visual_title": "📊 Stance Spectrum"
        }

    st.info(txt["info"])
    
    col_search, col_btn = st.columns([4, 1])
    with col_search:
        search_query = st.text_input("Search Keyword", placeholder=txt["placeholder"], label_visibility="collapsed")
    with col_btn:
        run_search = st.button(txt["search_btn"], type="primary", use_container_width=True)

    if "comparison_news" not in st.session_state: st.session_state.comparison_news = []

    if run_search and search_query:
        with st.spinner("Searching..."):
            url = f"https://news.google.com/rss/search?q={search_query}&hl=ko&gl=KR&ceid=KR:ko" if region_code == "KR" else f"https://news.google.com/rss/search?q={search_query}&hl=en-US&gl=US&ceid=US:en"
            feed = feedparser.parse(url)
            
            all_entries = feed.entries[:20] 
            major_entries = []
            minor_entries = []
            
            for e in all_entries:
                src = e.title.rsplit(' - ', 1)[1] if ' - ' in e.title else ""
                if is_major_media(src, region_code):
                    major_entries.append(e)
                else:
                    minor_entries.append(e)
            
            st.session_state.comparison_news = major_entries + minor_entries

    if st.session_state.comparison_news:
        st.write(f"Results: {len(st.session_state.comparison_news)} {txt['found']}")
        
        with st.form("compare_form"):
            selected_indices = []
            for idx, entry in enumerate(st.session_state.comparison_news):
                clean_title = entry.title.rsplit(' - ', 1)[0] if ' - ' in entry.title else entry.title
                source_name = entry.title.rsplit(' - ', 1)[1] if ' - ' in entry.title else "NEWS"
                
                is_major = is_major_media(source_name, region_code)
                if is_major:
                    label = f"⭐ **[{source_name}]** {clean_title}"
                else:
                    label = f"[{source_name}] {clean_title}"
                
                if st.checkbox(label, key=f"chk_{idx}"): 
                    selected_indices.append(entry)
            
            st.markdown("---")
            if st.form_submit_button(txt["compare_btn"], type="primary", use_container_width=True):
                if len(selected_indices) == 2:
                    art_a, art_b = selected_indices[0], selected_indices[1]
                    
                    with st.spinner(txt["analyzing"]):
                        res = compare_news_groq(art_a.title, art_b.title, region_code)
                        if res:
                            # 1. 핵심 차이 요약
                            st.subheader(txt["core_diff"])
                            st.markdown(f"<div style='font-size:18px; font-weight:bold; margin-bottom:20px;'>{res['core_difference']}</div>", unsafe_allow_html=True)
                            
                            # 2. [NEW] 성향 스펙트럼 시각화 (Balance Scale) 
                            st.markdown(f"#### {txt['visual_title']}")
                            
                            # 점수 계산 (-10~10 -> 0~100%)
                            score_a = res['article_a'].get('stance_score', 0)
                            score_b = res['article_b'].get('stance_score', 0)
                            
                            pos_a = (score_a + 10) * 5  # 예: -10 -> 0%, 0 -> 50%, 10 -> 100%
                            pos_b = (score_b + 10) * 5
                            
                            # HTML로 저울(Bar) 그리기
                            st.markdown(f"""
                            <div class="spectrum-container">
                                <div class="center-line"></div>
                                <div class="marker marker-a" style="left: {pos_a}%;">
                                    A
                                    <div class="marker-label">Article A</div>
                                </div>
                                <div class="marker marker-b" style="left: {pos_b}%;">
                                    B
                                    <div class="marker-label">Article B</div>
                                </div>
                            </div>
                            <div style="display:flex; justify-content:space-between; font-size:12px; color:#666; margin-top:-30px; margin-bottom:30px;">
                                <span>◀ Critical / Negative</span>
                                <span>Neutral</span>
                                <span>Supportive / Positive ▶</span>
                            </div>
                            """, unsafe_allow_html=True)

                            # 3. 상세 비교 카드
                            col_a, col_b = st.columns(2)
                            
                            # Article A
                            with col_a:
                                src_a = art_a.title.rsplit(' - ', 1)[1] if ' - ' in art_a.title else "A"
                                st.markdown(f"""
                                <div class='vs-card vs-card-a'>
                                    <div class='vs-label'>ARTICLE A • {src_a}</div>
                                    <div class='vs-title'>{art_a.title}</div>
                                    <div class='vs-tag'>Stance Score: {score_a}</div>
                                    <div class='vs-tag'>{res['article_a']['stance_label']}</div>
                                    <hr style='border-color:rgba(255,255,255,0.3);'>
                                    <div style='font-size:13px; opacity:0.9;'>{res['article_a']['summary']}</div>
                                </div>
                                """, unsafe_allow_html=True)
                                st.link_button("Read A", art_a.link, use_container_width=True)
                            
                            # Article B
                            with col_b:
                                src_b = art_b.title.rsplit(' - ', 1)[1] if ' - ' in art_b.title else "B"
                                st.markdown(f"""
                                <div class='vs-card vs-card-b'>
                                    <div class='vs-label'>ARTICLE B • {src_b}</div>
                                    <div class='vs-title'>{art_b.title}</div>
                                    <div class='vs-tag'>Stance Score: {score_b}</div>
                                    <div class='vs-tag'>{res['article_b']['stance_label']}</div>
                                    <hr style='border-color:rgba(255,255,255,0.3);'>
                                    <div style='font-size:13px; opacity:0.9;'>{res['article_b']['summary']}</div>
                                </div>
                                """, unsafe_allow_html=True)
                                st.link_button("Read B", art_b.link, use_container_width=True)

                            # Key Points
                            st.markdown("### 📌 Detail Points")
                            for point in res.get("key_points", []):
                                st.info(point)

                else:
                    st.warning("⚠️ 2개의 기사를 선택해주세요. (Select exactly 2 articles)")