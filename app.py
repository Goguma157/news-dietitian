import streamlit as st
import feedparser
import google.generativeai as genai
import json
import requests
import time

# 1. 페이지 설정
st.set_page_config(page_title="News Dietitian", page_icon="⚖️", layout="wide")

# CSS 스타일
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Pretendard', sans-serif !important; color: #1a1a1a; }
    div[data-testid="stContainer"] { background-color: #ffffff; border-radius: 12px; border: 1px solid #e5e7eb; }
    .insight-card { background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #0f172a; height: 100%; word-break: keep-all; }
    .fact-header { font-size: 12px; font-weight: 700; color: #64748b; margin-bottom: 5px; }
    .fact-content { font-size: 16px; font-weight: 600; color: #0f172a; line-height: 1.4; }
    .badge-valid { background-color: #dcfce7; color: #166534; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: 600; margin-right: 5px; }
    .badge-ref { background-color: #f1f5f9; color: #475569; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: 500; margin-right: 5px; }
</style>
""", unsafe_allow_html=True)

try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    pass 

@st.cache_data(ttl=600, show_spinner=False)
def fetch_news_data(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=3)
        return feedparser.parse(response.content) if response.status_code == 200 else None
    except:
        return None

# 🛡️ 최적화된 분석 함수
@st.cache_data(show_spinner=False)
def analyze_news_with_ai(news_text):
    prompt = f"""
    당신은 '수석 정치 평론가'입니다. 제공된 뉴스를 분석하여 JSON으로 출력하세요.
    이면의 의도나 맥락을 날카롭게 짚어내되, 문장은 '개조식'으로 간결하게 작성하세요.
    
    [뉴스]: {news_text[:2500]} 
    
    [JSON 형식] (반드시 이 형식을 지키세요):
    {{
        "title": "본질을 꿰뚫는 제목 (25자 내)",
        "summary": "핵심 요약 (1문장)",
        "metrics": {{
            "who": "주체",
            "whom": "대상",
            "action": "핵심 행위",
            "impact": "파장/의미"
        }},
        "fact_check": {{
            "verified": ["확인된 팩트1", "팩트2"],
            "controversial": ["논란/맥락"],
            "logic": "판단 근거 (1문장)"
        }},
        "balance_sheet": {{
            "side_a": "명분 (A측)",
            "side_b": "의도/반론 (B측)",
            "editor_note": "관전 포인트 (1문장)"
        }}
    }}
    """
    
    max_retries = 2
    last_error = ""
    
    for attempt in range(max_retries):
        try:
            # 💡 [핵심 변경] 아까 성공했던 'gemini-flash-latest'로 복귀!
            # 사용자님 목록에 확실히 존재하고, 작동이 확인된 모델입니다.
            model = genai.GenerativeModel('gemini-flash-latest')
            
            response = model.generate_content(
                prompt, 
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=1500,
                    temperature=0.3,
                    response_mime_type="application/json"
                )
            )
            return json.loads(response.text)
            
        except Exception as e:
            last_error = str(e)
            continue
            
    return {
        "title": "분석 일시 오류",
        "summary": "AI 연결 상태가 좋지 않아 분석 정보를 가져오지 못했습니다.",
        "metrics": {"who": "-", "whom": "-", "action": "-", "impact": "-"},
        "fact_check": {"verified": [], "controversial": [], "logic": "데이터 파싱 실패"},
        "balance_sheet": {"side_a": "-", "side_b": "-", "editor_note": f"Error: {last_error}"}
    }

st.title("⚖️ News Dietitian (Pro)")
st.markdown("<div style='color: #6b7280; margin-top: -15px; margin-bottom: 30px; font-size: 18px;'>Deep Insight, Fast Delivery</div>", unsafe_allow_html=True)

rss_url = "http://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=01&plink=RSSREADER"
news = fetch_news_data(rss_url)

if news and len(news.entries) > 0:
    cols = st.columns(3)
    for i in range(min(12, len(news.entries))):
        entry = news.entries[i]
        with cols[i % 3]:
            with st.container(border=True):
                st.markdown(f"<div style='font-size: 11px; color: #999;'>{entry.published[:16]}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size: 15px; font-weight: 700; height: 45px; overflow: hidden; margin-bottom:10px;'>{entry.title}</div>", unsafe_allow_html=True)
                
                if st.button("⚖️ 심층 분석", key=f"btn_{i}", use_container_width=True, type="primary"):
                    if "GEMINI_API_KEY" not in st.secrets:
                         st.error("Key Error")
                    else:
                        bar = st.progress(10, text="📡 데이터 수집 중...")
                        try:
                            start_time = time.time()
                            
                            input_text = f"{entry.title}\n{entry.description}"
                            time.sleep(0.1) 
                            bar.progress(40, text="🧠 AI가 맥락을 분석 중...")
                            
                            res = analyze_news_with_ai(input_text)
                            
                            bar.progress(100, text="✨ 리포트 생성 완료!")
                            time.sleep(0.2)
                            bar.empty()
                            
                            # --- 결과 표시 ---
                            st.markdown("---")
                            st.markdown(f"### {res['title']}")
                            st.markdown(f"<div style='background-color: #f3f4f6; padding: 15px; border-radius: 8px; font-style: italic; color: #4b5563; margin-bottom: 20px;'>“{res['summary']}”</div>", unsafe_allow_html=True)
                            
                            st.markdown("<div class='fact-header'>ANALYSIS MATRIX</div>", unsafe_allow_html=True)
                            r1c1, r1c2 = st.columns(2)
                            with r1c1: st.markdown(f"<div class='insight-card'><div class='fact-header'>WHO (주체)</div><div class='fact-content'>{res['metrics']['who']}</div></div>", unsafe_allow_html=True)
                            with r1c2: st.markdown(f"<div class='insight-card'><div class='fact-header'>WHOM (대상)</div><div class='fact-content'>{res['metrics']['whom']}</div></div>", unsafe_allow_html=True)
                            
                            r2c1, r2c2 = st.columns(2)
                            with r2c1: st.markdown(f"<div class='insight-card' style='margin-top:10px'><div class='fact-header'>KEY ACTION</div><div class='fact-content'>{res['metrics']['action']}</div></div>", unsafe_allow_html=True)
                            with r2c2: st.markdown(f"<div class='insight-card' style='margin-top:10px'><div class='fact-header'>IMPACT / INSIGHT</div><div class='fact-content'>{res['metrics']['impact']}</div></div>", unsafe_allow_html=True)

                            st.markdown("", unsafe_allow_html=True)
                            st.markdown("<div class='fact-header' style='margin-top: 20px;'>FACT CHECK & LOGIC</div>", unsafe_allow_html=True)
                            st.caption(f"💡 판단 근거: {res['fact_check']['logic']}")
                            
                            t1, t2 = st.tabs(["✅ 검증된 팩트", "🔍 맥락/논란"])
                            with t1:
                                for f in res['fact_check']['verified']: st.markdown(f"<span class='badge-valid'>FACT</span> {f}", unsafe_allow_html=True)
                            with t2:
                                for c in res['fact_check']['controversial']: st.markdown(f"<span class='badge-ref'>CTX</span> {c}", unsafe_allow_html=True)
                            
                            st.markdown("<div class='fact-header' style='margin-top: 20px;'>PERSPECTIVE</div>", unsafe_allow_html=True)
                            c1, c2 = st.columns(2)
                            with c1:
                                st.markdown(f"""<div style='border:1px solid #e5e7eb; padding:15px; border-radius:8px;'><strong style='color:#059669'>🗣 명분/주장</strong><br>{res['balance_sheet']['side_a']}</div>""", unsafe_allow_html=True)
                            with c2:
                                st.markdown(f"""<div style='border:1px solid #e5e7eb; padding:15px; border-radius:8px; background:#fef2f2'><strong style='color:#dc2626'>🕵️ 의도/이면</strong><br>{res['balance_sheet']['side_b']}</div>""", unsafe_allow_html=True)
                            
                            st.info(f"🧐 **Editor's Insight:** {res['balance_sheet']['editor_note']}")
                            
                            end_time = time.time()
                            st.caption(f"⏱️ 분석 소요 시간: {round(end_time - start_time, 2)}초")

                        except Exception as e:
                            st.error(f"Error: {e}")