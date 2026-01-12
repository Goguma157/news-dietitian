import streamlit as st
import feedparser
import google.generativeai as genai
import json
import requests

# 1. 페이지 설정 (CSS로 폰트와 여백을 좀 더 예쁘게 다듬기)
st.set_page_config(page_title="뉴스 영양사", page_icon="🥦", layout="wide")

# CSS 스타일 주입 (카드 디자인, 둥근 모서리 등)
st.markdown("""
<style>
    div[data-testid="stMetricValue"] { font-size: 1.2rem; }
    .big-font { font-size:20px !important; font-weight: bold; }
    .highlight-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# 2. 비밀 금고에서 키 꺼내서 세팅하기
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    pass 

# 3. AI 분석 함수
def analyze_news_with_ai(news_text):
    prompt = f"""
    당신은 비판적 사고를 돕는 '뉴스 분석 전문가'입니다. 
    제공된 뉴스 기사를 분석하여 아래 JSON 포맷으로 완벽하게 정리해 주세요.
    반드시 JSON 형식만 출력해야 합니다.
    
    [분석할 뉴스]: {news_text}
    
    [JSON 출력 형식]:
    {{
        "title": "기사 제목 (30자 이내)",
        "core_facts": {{
            "who": "주체 (누가)",
            "whom": "대상 (누구를)",
            "what": "행동/결과 (짧게)",
            "why": "원인/배경 (짧게)"
        }},
        "analysis": {{
            "valid_causes": ["팩트 1", "팩트 2"],
            "ref_causes": ["참고/의혹 1", "참고/의혹 2"],
            "explanation": "구분 이유"
        }},
        "terms": [
            {{ "term": "용어", "desc": "설명" }}
        ],
        "balance": {{
            "heard": "들리는 쪽 입장 요약",
            "missing": "안 들리는 쪽/부족한 점",
            "comment": "균형 잡힌 시각을 위한 한줄 평"
        }}
    }}
    """
    model = genai.GenerativeModel('gemini-flash-latest')
    response = model.generate_content(prompt)
    text = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)

# 4. 화면 구성
st.title("🥦 뉴스 영양사")
st.caption("AI가 발라낸 뉴스의 뼈와 살, 시각적으로 확인하세요.")
st.divider()

# 뉴스 가져오기
rss_url = "http://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=01&plink=RSSREADER"

try:
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(rss_url, headers=headers, timeout=5)
    if response.status_code == 200:
        news = feedparser.parse(response.content)
    else:
        news = None
except Exception as e:
    news = None

# 뉴스 카드 보여주기
if news is None or len(news.entries) == 0:
    st.warning("뉴스를 가져올 수 없습니다.")
else:
    cols = st.columns(3)
    for i in range(min(12, len(news.entries))):
        entry = news.entries[i]
        with cols[i % 3]:
            with st.container(border=True):
                st.subheader(entry.title[:30] + "...")
                st.caption(entry.published)
                st.link_button("🔗 원문 보기", entry.link)
                
                # 버튼 키 설정
                btn_key = f"ai_btn_{i}"
                
                if st.button("✨ 심층 분석", key=btn_key):
                    if "GEMINI_API_KEY" not in st.secrets:
                         st.error("AI 키가 없습니다.")
                    else:
                        with st.spinner("AI가 디자인 중..."):
                            try:
                                input_text = f"제목: {entry.title}\n내용: {entry.description}"
                                res = analyze_news_with_ai(input_text)
                                
                                # ==========================================
                                # 🎨 [디자인 개선된 분석 결과 화면]
                                # ==========================================
                                
                                st.markdown("---")
                                st.markdown(f"### 📰 {res['title']}")
                                
                                # 1. 뼈대 바르기 (4단 카드 배치)
                                st.markdown("#### 1️⃣ 핵심 팩트 4-Cut")
                                c1, c2, c3, c4 = st.columns(4)
                                with c1:
                                    st.info("**🙋‍♂️ 누가**")
                                    st.write(res['core_facts']['who'])
                                with c2:
                                    st.success("**🎯 누구를**")
                                    st.write(res['core_facts']['whom'])
                                with c3:
                                    st.warning("**📢 결과**")
                                    st.write(res['core_facts']['what'])
                                with c4:
                                    st.error("**❓ 이유**")
                                    st.write(res['core_facts']['why'])
                                
                                st.markdown("") # 여백
                                
                                # 2. 양념 걷어내기 (탭 메뉴 사용 - 깔끔하게 숨기기)
                                st.markdown("#### 2️⃣ 팩트 vs 의혹")
                                st.caption(f"💡 AI 분석: {res['analysis']['explanation']}")
                                
                                tab1, tab2 = st.tabs(["✅ 결정적 팩트 (유효타)", "⚠️ 참고/논란 (배경)"])
                                
                                with tab1:
                                    for item in res['analysis']['valid_causes']:
                                        st.success(f"📍 {item}")
                                
                                with tab2:
                                    for item in res['analysis']['ref_causes']:
                                        st.write(f"💭 {item}")

                                st.markdown("")

                                # 3. 균형 잡기 (VS 구도)
                                st.markdown("#### 3️⃣ 균형의 저울")
                                col_left, col_right = st.columns(2)
                                
                                with col_left:
                                    with st.container(border=True):
                                        st.markdown("### 📢 들리는 말")
                                        st.write(res['balance']['heard'])
                                
                                with col_right:
                                    with st.container(border=True):
                                        st.markdown("### 🔇 빠진 말")
                                        st.write(res['balance']['missing'])
                                
                                # 4. 마무리 코멘트 (강조 박스)
                                st.info(f"**🧐 News Dietitian's Pick:**\n\n{res['balance']['comment']}")
                                
                                # 용어 설명 (아코디언)
                                if res['terms']:
                                    with st.expander("🔍 어려운 용어 사전"):
                                        for term in res['terms']:
                                            st.markdown(f"**{term['term']}**: {term['desc']}")

                            except Exception as e:
                                st.error(f"분석 중 오류 발생: {e}")