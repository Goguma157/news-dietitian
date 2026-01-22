import streamlit as st
import feedparser
from groq import Groq
import json
import requests
import time
import re
import html
import textwrap  # <--- 이 줄을 꼭 추가해주세요! (들여쓰기 제거용)

# ==========================================
# 1. 기본 설정 및 CSS 스타일 (전문가 모드 적용)
# ==========================================
st.set_page_config(page_title="News Dietitian : Analyst Mode", page_icon="📰", layout="wide")

st.markdown("""
<style>
    /* 폰트: 제목은 권위 있는 Merriweather(명조), 본문은 가독성 좋은 Roboto(고딕) */
    @import url('https://fonts.googleapis.com/css2?family=Merriweather:ital,wght@0,300;0,400;0,700;0,900;1,300&family=Roboto:wght@300;400;500;700&display=swap');
    
    html, body, [class*="css"] { 
        font-family: 'Roboto', sans-serif !important; 
        color: #222;
        background-color: #f9f9f9; /* 눈이 편한 미색 배경 */
    }
    
    h1, h2, h3 { font-family: 'Merriweather', serif !important; color: #1a1a1a; letter-spacing: -0.5px; }

    /* --- 탭 스타일 (미니멀리즘) --- */
    .stTabs [data-baseweb="tab-list"] { gap: 20px; border-bottom: 1px solid #ddd; padding-bottom: 5px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: transparent;
        border: none;
        color: #888;
        font-weight: 500;
        font-size: 14px;
        transition: color 0.3s;
    }
    .stTabs [aria-selected="true"] {
        color: #1a1a1a;
        font-weight: 900;
        border-bottom: 3px solid #1a1a1a;
    }

    /* --- 카드 컨테이너 (기존 박스 스타일 제거) --- */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 0px; /* 각진 모서리로 전문성 강조 */
        padding: 24px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        margin-bottom: 16px;
    }

    /* --- [NEW] Compare UI: Paper Style --- */
    .compare-container {
        display: flex;
        justify-content: space-between;
        align-items: stretch;
        background-color: #fff; 
        padding: 40px;
        border: 1px solid #e0e0e0;
        gap: 40px;
        position: relative;
        margin-bottom: 30px;
    }

    .paper-card {
        flex: 1;
        background: transparent;
    }

    .news-meta {
        font-family: 'Roboto', sans-serif;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: #999;
        margin-bottom: 15px;
        font-weight: 700;
        display: flex;
        align-items: center;
    }
    
    .news-title {
        font-family: 'Merriweather', serif;
        font-size: 24px;
        font-weight: 900;
        color: #111;
        line-height: 1.4;
        margin-bottom: 25px;
        border-bottom: 3px solid #111; /* 제목 아래 굵은 선 포인트 */
        padding-bottom: 20px;
    }

    .news-summary {
        font-family: 'Merriweather', serif;
        font-size: 15px;
        line-height: 1.8;
        color: #444;
        font-weight: 300;
    }

    .stat-box {
        margin-top: 25px;
        padding-top: 15px;
        border-top: 1px solid #eee;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 12px;
        color: #666;
        font-family: 'Roboto', sans-serif;
    }

    /* --- 중앙 구분선 --- */
    .divider-vertical {
        width: 1px;
        background-color: #e0e0e0;
        position: relative;
    }
    
    .vs-badge-minimal {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background-color: #fff;
        color: #bbb;
        border: 1px solid #e0e0e0;
        padding: 6px 8px;
        font-size: 10px;
        font-weight: bold;
        letter-spacing: 1px;
        border-radius: 50%;
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    /* --- 기타 유틸리티 --- */
    .badge-source { 
        background-color: #f4f4f4; 
        color: #555; 
        padding: 4px 8px; 
        font-size: 10px; 
        font-weight: 700; 
        text-transform: uppercase; 
        border-radius: 2px; 
        margin-right: 6px; 
        border: 1px solid #ddd;
    }

    .insight-box {
        background-color: #f9f9f9;
        border-left: 3px solid #2c3e50;
        padding: 15px 20px;
        font-family: 'Merriweather', serif;
        font-size: 14px;
        line-height: 1.6;
        color: #333;
        margin-top: 15px;
    }
    
    .chat-user { text-align: right; margin: 8px 0; color: #666; font-size: 13px; font-style: italic; }
    .chat-ai { text-align: left; margin: 8px 0; font-weight: 600; color: #111; font-size: 13px; font-family: 'Merriweather', serif; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 메이저 언론사 리스트 (필터링용)
# ==========================================
MAJOR_KR = ["조선일보", "중앙일보", "동아일보", "한겨레", "경향신문", "한국일보", "매일경제", "한국경제", "KBS", "MBC", "SBS", "JTBC", "YTN", "연합뉴스"]
MAJOR_US = ["CNN", "Fox News", "New York Times", "Washington Post", "Reuters", "Associated Press", "BBC", "NBC", "CNBC", "Bloomberg", "USA Today", "Wall Street Journal"]

def is_major_media(source_name, region_code):
    target_list = MAJOR_KR if region_code == "KR" else MAJOR_US
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
        lang_instruction = "Answer strictly in Korean. Use Hangul ONLY."
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
st.sidebar.markdown("<h2 style='text-align: center; color: #2c3e50; font-family:Merriweather;'>NEWS<br>DIETITIAN</h2>", unsafe_allow_html=True)
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
st.markdown(f"<h1 style='border-bottom: 2px solid #2c3e50; padding-bottom: 15px; margin-bottom: 30px;'>{category} <span style='font-size:18px; color:#888; font-weight:400;'>| {region_code} Edition</span></h1>", unsafe_allow_html=True)

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
tab1, tab2 = st.tabs(["📰 Daily Briefing", "⚖️ Analyst Compare"])

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
                    
                    st.markdown(f"<span class='badge-source'>{source_name}</span> <span style='color:#bbb; font-size:11px;'>{entry.published[:16]}</span>", unsafe_allow_html=True)
                    st.markdown(f"<h3 style='margin-top: 10px; font-size: 20px; line-height: 1.4; margin-bottom: 20px;'>{clean_title}</h3>", unsafe_allow_html=True)
                    
                    article_id = entry.link
                    view_key = f"view_{article_id}"
                    if view_key not in st.session_state: st.session_state[view_key] = False

                    if st.session_state[view_key]:
                        btn_label = "CLOSE REPORT"
                        btn_type = "secondary"
                    else:
                        btn_label = "ANALYZE BIAS"
                        btn_type = "primary"

                    if st.button(btn_label, key=f"btn_{i}", type=btn_type, use_container_width=True):
                        st.session_state[view_key] = not st.session_state[view_key]
                        if st.session_state[view_key] and f"analysis_{article_id}" not in st.session_state:
                            with st.spinner("Processing Analyst Report..."):
                                res = analyze_news_groq(f"Title: {clean_title}\nContent: {entry.title}", region_code)
                                st.session_state[f"analysis_{article_id}"] = res
                        st.rerun()
                    
                    if st.session_state[view_key] and f"analysis_{article_id}" in st.session_state:
                        res = st.session_state[f"analysis_{article_id}"]
                        if res:
                            st.markdown("---")
                            # Keywords
                            if "keywords" in res and res["keywords"]:
                                tags_html = "".join([f"<span style='background:#f0f0f0; padding:2px 6px; font-size:11px; margin-right:4px; color:#666;'>#{tag}</span>" for tag in res["keywords"]])
                                st.markdown(f"<div style='margin-bottom:15px;'>{tags_html}</div>", unsafe_allow_html=True)

                            # Fact Score Bar
                            fact_score = res['scores'].get('fact_ratio', 50)
                            st.caption(f"FACTUALITY INDEX: {fact_score}/100")
                            st.markdown(f"""
                            <div style="width: 100%; background-color: #eee; height: 4px; margin-bottom: 15px;">
                                <div style="width: {fact_score}%; background-color: #2c3e50; height: 4px;"></div>
                            </div>
                            """, unsafe_allow_html=True)

                            sentiment_emoji = res.get("sentiment_emoji", "🧐")
                            st.markdown(f"""
                            <div class='insight-box'>
                                <b>EXECUTIVE SUMMARY {sentiment_emoji}</b><br>{res['summary']}<br><br>
                                <b>CONTEXT & BIAS</b><br>{res['balance']['hidden']}
                            </div>
                            """, unsafe_allow_html=True)

                            st.markdown("<div style='margin-top:20px; font-size:11px; font-weight:700; color:#ccc; letter-spacing:1px;'>INTERACTIVE Q&A</div>", unsafe_allow_html=True)
                            if article_id not in st.session_state.chat_history: st.session_state.chat_history[article_id] = []
                            
                            for chat in st.session_state.chat_history[article_id]:
                                role_class = "chat-user" if chat["role"] == "user" else "chat-ai"
                                st.markdown(f"<div class='{role_class}'>{chat['content']}</div>", unsafe_allow_html=True)

                            with st.form(key=f"chat_form_{i}", clear_on_submit=True):
                                c1, c2 = st.columns([4, 1])
                                uq = c1.text_input("Q", placeholder="Inquire about this article...", label_visibility="collapsed")
                                if c2.form_submit_button("ASK", use_container_width=True) and uq:
                                    st.session_state.chat_history[article_id].append({"role": "user", "content": uq})
                                    with st.spinner("Analyst is typing..."):
                                        ans = ask_ai_about_news(f"Title: {clean_title}", uq, region_code)
                                        st.session_state.chat_history[article_id].append({"role": "ai", "content": ans})
                                    st.rerun()
                    st.link_button("ORIGINAL SOURCE ↗", entry.link, use_container_width=True)

# --- TAB 2: Comparison Mode (Indentation Fix Applied) ---
with tab2:
    if region_code == "KR":
        txt = {
            "info": "💡 비교할 주제를 입력하세요. (예: 금리 인상, 선거, 부동산 정책)",
            "placeholder": "키워드 입력...",
            "search_btn": "검색 (SEARCH)",
            "compare_btn": "선택한 2개 기사 비교 분석 (RUN COMPARISON)",
            "analyzing": "심층 비교 분석 보고서를 작성 중입니다...",
            "found": "개의 관련 기사 검색됨",
            "major": "Major"
        }
    else:
        txt = {
            "info": "💡 Enter topic to compare perspectives (e.g., Fed Rates, Elections)",
            "placeholder": "Enter Keyword...",
            "search_btn": "SEARCH",
            "compare_btn": "RUN COMPARISON (Select 2)",
            "analyzing": "Generating Comparative Analyst Report...",
            "found": "articles found.",
            "major": "Major"
        }

    st.info(txt["info"])
    
    col_search, col_btn = st.columns([4, 1])
    with col_search:
        search_query = st.text_input("Search Keyword", placeholder=txt["placeholder"], label_visibility="collapsed")
    with col_btn:
        run_search = st.button(txt["search_btn"], type="primary", use_container_width=True)

    if "comparison_news" not in st.session_state: st.session_state.comparison_news = []

    if run_search and search_query:
        with st.spinner("Accessing Wire Services..."):
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
        st.write(f"Query Results: {len(st.session_state.comparison_news)} {txt['found']}")
        
        with st.form("compare_form"):
            selected_indices = []
            for idx, entry in enumerate(st.session_state.comparison_news):
                clean_title = entry.title.rsplit(' - ', 1)[0] if ' - ' in entry.title else entry.title
                source_name = entry.title.rsplit(' - ', 1)[1] if ' - ' in entry.title else "NEWS"
                
                is_major = is_major_media(source_name, region_code)
                label_prefix = "⭐ " if is_major else ""
                label = f"{label_prefix}**[{source_name}]** {clean_title}"
                
                if st.checkbox(label, key=f"chk_{idx}"): 
                    selected_indices.append(entry)
            
            st.markdown("---")
            if st.form_submit_button(txt["compare_btn"], type="primary", use_container_width=True):
                if len(selected_indices) == 2:
                    art_a, art_b = selected_indices[0], selected_indices[1]
                    
                    with st.spinner(txt["analyzing"]):
                        res = compare_news_groq(art_a.title, art_b.title, region_code)
                        if res:
                            # 1. 핵심 차이 (들여쓰기 문제 해결)
                            core_diff_safe = html.escape(res['core_difference'])
                            
                            st.markdown(textwrap.dedent(f"""
                            <div style="text-align: center; margin-bottom: 40px; padding: 20px;">
                                <div style="font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 15px; font-weight:700;">Comparative Analysis Report</div>
                                <div style="font-family: 'Merriweather', serif; font-size: 28px; font-weight: 900; color: #111; line-height:1.3;">
                                    "{core_diff_safe}"
                                </div>
                            </div>
                            """), unsafe_allow_html=True)
                            
                            # 2. Paper Style 비교 UI (들여쓰기 문제 해결)
                            score_a = res['article_a'].get('stance_score', 0)
                            score_b = res['article_b'].get('stance_score', 0)
                            
                            src_a = html.escape(art_a.title.rsplit(' - ', 1)[1]) if ' - ' in art_a.title else "Source A"
                            src_b = html.escape(art_b.title.rsplit(' - ', 1)[1]) if ' - ' in art_b.title else "Source B"
                            title_a = html.escape(art_a.title)
                            title_b = html.escape(art_b.title)
                            summary_a = html.escape(res['article_a']['summary'])
                            summary_b = html.escape(res['article_b']['summary'])
                            label_a = html.escape(res['article_a']['stance_label'])
                            label_b = html.escape(res['article_b']['stance_label'])
                            
                            # textwrap.dedent()로 HTML 앞 공백 제거 -> 코드 블록 인식 방지
                            st.markdown(textwrap.dedent(f"""
                            <div class="compare-container">
                                <div class="paper-card">
                                    <div class="news-meta">
                                        <span style="color: #2c3e50;">● ARTICLE A</span>
                                        <span style="margin: 0 10px; color: #ddd;">|</span>
                                        {src_a}
                                    </div>
                                    <div class="news-title">{title_a}</div>
                                    <div class="news-summary">
                                        {summary_a}
                                    </div>
                                    <div class="stat-box">
                                        <span>STANCE: <b>{label_a}</b></span>
                                        <span style="background: #f0f0f0; padding: 4px 8px; border-radius: 2px; font-weight:bold;">Score: {score_a}</span>
                                    </div>
                                </div>

                                <div class="divider-vertical">
                                    <div class="vs-badge-minimal">VS</div>
                                </div>

                                <div class="paper-card">
                                    <div class="news-meta">
                                        <span style="color: #c0392b;">● ARTICLE B</span>
                                        <span style="margin: 0 10px; color: #ddd;">|</span>
                                        {src_b}
                                    </div>
                                    <div class="news-title" style="border-bottom-color: #c0392b;">{title_b}</div>
                                    <div class="news-summary">
                                        {summary_b}
                                    </div>
                                    <div class="stat-box">
                                        <span>STANCE: <b>{label_b}</b></span>
                                        <span style="background: #f0f0f0; padding: 4px 8px; border-radius: 2px; font-weight:bold;">Score: {score_b}</span>
                                    </div>
                                </div>
                            </div>
                            """), unsafe_allow_html=True)

                            # 링크 버튼
                            c1, c2, c3 = st.columns([1, 0.1, 1])
                            c1.link_button(f"Read Full Article (A)", art_a.link, use_container_width=True)
                            c3.link_button(f"Read Full Article (B)", art_b.link, use_container_width=True)

                            # 3. 성향 스펙트럼 (들여쓰기 문제 해결)
                            st.markdown("<br><br>", unsafe_allow_html=True)
                            st.caption("POLITICAL COMPASS / STANCE SPECTRUM")
                            
                            pos_a = (score_a + 10) * 5 
                            pos_b = (score_b + 10) * 5
                            
                            st.markdown(textwrap.dedent(f"""
                            <div style="position: relative; height: 50px; margin-top: 20px; width: 100%;">
                                <div style="position: absolute; top: 50%; width: 100%; height: 1px; background: #bbb;"></div>
                                <div style="position: absolute; top: 35%; left: 50%; width: 1px; height: 15px; background: #999;"></div>
                                
                                <div style="position: absolute; left: {pos_a}%; top: 50%; transform: translate(-50%, -50%); transition: left 1s;">
                                    <div style="width: 14px; height: 14px; background: #2c3e50; border-radius: 50%; border: 3px solid #fff; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"></div>
                                    <div style="position: absolute; top: -25px; left: 50%; transform: translateX(-50%); font-size: 11px; font-weight: 800; color: #2c3e50;">A</div>
                                </div>
                                
                                <div style="position: absolute; left: {pos_b}%; top: 50%; transform: translate(-50%, -50%); transition: left 1s;">
                                    <div style="width: 14px; height: 14px; background: #c0392b; border-radius: 50%; border: 3px solid #fff; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"></div>
                                    <div style="position: absolute; top: -25px; left: 50%; transform: translateX(-50%); font-size: 11px; font-weight: 800; color: #c0392b;">B</div>
                                </div>
                            </div>
                            <div style="display: flex; justify-content: space-between; font-size: 10px; color: #888; font-weight:500; margin-top: 5px;">
                                <span>◀ CRITICAL / LEFT (-10)</span>
                                <span>NEUTRAL (0)</span>
                                <span>SUPPORTIVE / RIGHT (+10) ▶</span>
                            </div>
                            """), unsafe_allow_html=True)

                            # 4. Key Points
                            st.markdown("<br>", unsafe_allow_html=True)
                            st.markdown("### 📌 Analytic Notes")
                            for point in res.get("key_points", []):
                                safe_point = html.escape(point)
                                st.markdown(f"<div style='margin-bottom:8px; color:#444;'>• {safe_point}</div>", unsafe_allow_html=True)

                else:
                    st.warning("⚠️ 정확히 2개의 기사를 선택해주세요. (Please select exactly 2 articles)")