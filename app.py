import streamlit as st
import feedparser
import google.generativeai as genai
import json
import requests  # <--- 새로 추가된 도구!

# 1. 페이지 설정
st.set_page_config(page_title="뉴스 영양사", page_icon="🥦", layout="wide")

# 2. 비밀 금고에서 키 꺼내서 세팅하기
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    # 키가 없을 때 안내 메시지
    pass 

# 3. AI 분석 함수
def analyze_news_with_ai(news_text):
    prompt = f"""
    당신은 뉴스 분석가입니다. 아래 뉴스 요약을 보고 다음 JSON 형식으로만 답하세요.
    다른 말은 절대 하지 말고 오직 JSON 데이터만 출력하세요.
    
    [분석할 뉴스]: {news_text}
    
    [출력 형식]:
    {{
        "summary": "초등학생도 이해하는 1줄 핵심 요약",
        "bias": "기사 제목이나 내용에서 느껴지는 감정적 단어 (없으면 '없음')",
        "fact_check": "이 기사에서 확인해야 할 핵심 숫자나 주장 1가지"
    }}
    """
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt)
    text = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)

# 4. 화면 구성
st.title("🥦 뉴스 영양사: AI 에디션")
st.write("버튼을 누르면 AI가 기사의 영양 성분을 분석해줍니다.")
st.divider()

# --- [수정된 부분] 뉴스 가져오기 (가짜 신분증 사용) ---
rss_url = "http://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=01&plink=RSSREADER"

try:
    # 가짜 신분증(User-Agent) 만들기
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    # 정중하게 요청하기
    response = requests.get(rss_url, headers=headers, timeout=5)
    
    if response.status_code == 200:
        # 성공하면 내용물(content)을 feedparser에게 넘겨줌
        news = feedparser.parse(response.content)
    else:
        st.error(f"뉴스 사이트에서 접속을 거부했습니다. 상태 코드: {response.status_code}")
        news = None
        
except Exception as e:
    st.error(f"접속 중 에러가 발생했습니다: {e}")
    news = None
# ----------------------------------------------------

# 5. 뉴스 카드 보여주기
if news is None or len(news.entries) == 0:
    st.warning("현재 뉴스를 가져올 수 없습니다. 잠시 후 다시 시도해주세요.")
else:
    cols = st.columns(3)
    for i in range(min(12, len(news.entries))):
        entry = news.entries[i]
        with cols[i % 3]:
            with st.container(border=True):
                st.subheader(entry.title[:30] + "...")
                st.caption(entry.published)
                st.link_button("🔗 기사 원문", entry.link)
                
                # AI 분석 버튼
                if st.button("✨ 영양 성분 분석", key=f"ai_btn_{i}"):
                    if "GEMINI_API_KEY" not in st.secrets:
                         st.error("AI 키가 설정되지 않아서 분석할 수 없습니다.")
                    else:
                        with st.spinner("AI가 분석 중입니다..."):
                            try:
                                input_text = f"제목: {entry.title}\n내용: {entry.description}"
                                result = analyze_news_with_ai(input_text)
                                st.success("✅ 분석 완료!")
                                st.markdown(f"**📌 요약:** {result['summary']}")
                                st.markdown(f"**😡 감정 단어:** {result['bias']}")
                                st.info(f"**🕵️ 체크 포인트:** {result['fact_check']}")
                            except Exception as e:
                                st.error(f"분석 실패: {e}")