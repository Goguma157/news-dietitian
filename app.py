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

# 3. 세션 상태 초기화 (챗봇 대화 기억용)
if "chat_history" not in st.session_state:
    st.session_state.chat_history = {}  # {기사URL: [대화목록]}

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
# 🧠 AI 기능 1: 뉴스 심층 분석 (게이지 데이터 추가)
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
            "fact_ratio": 0~100 사이 숫자 (팩트 비중),
            "opinion_ratio": 0~100 사이 숫자 (의견 비중, 합이 100이 되게)
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
    except Exception as e:
        return None

# ==========================================
# 🧠 AI 기능 2: Q&A 챗봇
# ==========================================
def ask_ai_about_news(news_context, user_question):
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "당신은 뉴스 기사를 읽고 사용자의 질문에 친절하게 답해주는 AI 비서입니다. 기사 내용을 바탕으로 쉽고 명쾌하게 답변하세요."},
                {"role": "user", "content": f"기사 내용: {news_context}\n\n질문: {user_question}"}
            ],
            temperature=0.5
        )
        return completion.choices[0].message.content
    except:
        return "죄송해요, 지금은 답변하기 어렵네요."

# --- 화면 구성 ---

# [기능 1] 사이드바: 카테고리 선택
st.sidebar.title("🥗 News Dietitian")
st.sidebar.markdown("뉴스를 편식하지 않고 골고루 섭취하세요!")

category = st.sidebar.radio(
    "오늘의 식단 (카테고리)",
    ("🔥 주요 뉴스", "⚖️ 정치", "💰 경제", "🌍 국제", "📱 IT/과학")
)

# RSS 주소 매핑 (SBS 뉴스 기준)
rss_feeds = {
    "🔥 주요 뉴스": "http://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=01&plink=RSSREADER",
    "⚖️ 정치": "http://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=02&plink=RSSREADER",
    "💰 경제": "http://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=03&plink=RSSREADER",
    "🌍 국제": "http://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=08&plink=RSSREADER", # 국제 섹션 ID는 다를 수 있어 일반적인거 사용
    "📱 IT/과학": "http://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=14&plink=RSSREADER"
}

# 메인 화면
st.title(f"{category} 브리핑")

try:
    resp = requests.get(rss_feeds.get(category, rss_feeds["🔥 주요 뉴스"]), timeout=5)
    news = feedparser.parse(resp.content)
except:
    st.error("뉴스를 가져오는데 실패했습니다.")
    news = None

if news and news.entries:
    # 3단 컬럼 대신 2단 컬럼으로 변경 (챗봇 공간 확보를 위해 넓게)
    cols = st.columns(2)
    
    for i, entry in enumerate(news.entries[:10]): # 10개만 로드
        with cols[i % 2]:
            with st.container(border=True):
                st.subheader(entry.title)
                st.caption(entry.published[:16])
                
                # 고유 키 생성 (URL 활용)
                article_id = entry.link
                
                # 분석 버튼
                if st.button("✨ 영양 성분 분석", key=f"btn_{i}", use_container_width=True, type="primary"):
                    with st.spinner("AI가 팩트와 의견을 분리하는 중..."):
                        res = analyze_news_groq(f"제목: {entry.title}\n내용: {entry.description}")
                        st.session_state[f"analysis_{article_id}"] = res # 결과 저장
                
                # 저장된 분석 결과가 있으면 표시
                if f"analysis_{article_id}" in st.session_state:
                    res = st.session_state[f"analysis_{article_id}"]
                    
                    if res:
                        st.markdown("---")
                        st.markdown(f"**💡 {res['title']}**")
                        st.info(res['summary'])
                        
                        # [기능 2] 시각화 게이지 (팩트 vs 의견)
                        fact_score = res['scores'].get('fact_ratio', 50)
                        st.caption(f"📊 팩트 지수: {fact_score}% / 의견 지수: {100-fact_score}%")
                        st.progress(fact_score / 100)
                        
                        # 상세 분석 카드
                        c1, c2 = st.columns(2)
                        with c1: st.markdown(f"<div class='insight-card'><b>WHO</b><br>{res['metrics']['who']}</div>", unsafe_allow_html=True)
                        with c2: st.markdown(f"<div class='insight-card'><b>IMPACT</b><br>{res['metrics']['impact']}</div>", unsafe_allow_html=True)
                        
                        with st.expander("🔍 속마음 & 관전 포인트"):
                            st.write(f"**겉 명분:** {res['balance']['stated']}")
                            st.write(f"**속마음:** {res['balance']['hidden']}")
                            st.caption(f"Tip: {res['balance']['note']}")

                        st.markdown("---")
                        
                        # [기능 3] Q&A 챗봇
                        st.markdown("##### 💬 궁금하면 물어봐!")
                        
                        # 대화 기록 초기화
                        if article_id not in st.session_state.chat_history:
                            st.session_state.chat_history[article_id] = []

                        # 이전 대화 출력
                        for chat in st.session_state.chat_history[article_id]:
                            if chat["role"] == "user":
                                st.markdown(f"<div class='user-chat'>🗣️ {chat['content']}</div>", unsafe_allow_html=True)
                            else:
                                st.markdown(f"<div class='ai-chat'>🤖 {chat['content']}</div>", unsafe_allow_html=True)

                        # 질문 입력창 (Form을 써야 엔터키 입력 시 새로고침 방지 가능)
                        with st.form(key=f"chat_form_{i}"):
                            user_q = st.text_input("예: 그래서 이게 나랑 무슨 상관이야?", label_visibility="collapsed")
                            submit_btn = st.form_submit_button("질문하기")
                            
                            if submit_btn and user_q:
                                # 사용자 질문 저장
                                st.session_state.chat_history[article_id].append({"role": "user", "content": user_q})
                                
                                # AI 답변 생성
                                with st.spinner("AI가 생각 중..."):
                                    ai_answer = ask_ai_about_news(f"제목:{entry.title}\n내용:{entry.description}\n분석:{res}", user_q)
                                    st.session_state.chat_history[article_id].append({"role": "ai", "content": ai_answer})
                                
                                st.rerun() # 답변 후 화면 갱신
                    else:
                        st.error("분석 데이터를 불러오지 못했습니다.")

                st.link_button("원문 기사 보기", entry.link, use_container_width=True)