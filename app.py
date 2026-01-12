import streamlit as st
import feedparser
import google.generativeai as genai
import json

# 1. 페이지 설정
st.set_page_config(page_title="뉴스 영양사", page_icon="🥦", layout="wide")

# 2. 비밀 금고에서 키 꺼내서 세팅하기
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("비밀 열쇠(API Key)가 설정되지 않았습니다. Streamlit Secrets를 확인해주세요!")

# 3. AI 분석 함수 (우리의 핵심 기술!)
def analyze_news_with_ai(news_text):
    # 우리가 만들었던 '깐깐한 프롬프트'
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
    
    # Gemini 모델(Flash 버전이 빠르고 무료임)에게 일을 시킵니다
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
    
    # 결과에서 JSON 부분만 발라내기 (가끔 ```json 같은걸 붙여서 줌)
    text = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)

# 4. 화면 구성
st.title("🥦 뉴스 영양사: AI 에디션")
st.write("버튼을 누르면 AI가 기사의 영양 성분을 분석해줍니다.")
st.divider()

# 뉴스 가져오기
rss_url = "[http://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=01&plink=RSSREADER](http://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=01&plink=RSSREADER)"
news = feedparser.parse(rss_url)

if len(news.entries) == 0:
    st.error("뉴스를 가져올 수 없습니다.")
else:
    cols = st.columns(3)
    for i in range(min(12, len(news.entries))):
        entry = news.entries[i]
        with cols[i % 3]:
            with st.container(border=True):
                st.subheader(entry.title[:30] + "...")
                st.caption(entry.published)
                
                # 원문 링크
                st.link_button("🔗 기사 원문", entry.link)
                
                # ★ 여기가 핵심: AI 분석 버튼
                # 버튼마다 고유한 키(key)를 줘야 에러가 안 남
                if st.button("✨ 영양 성분 분석", key=f"ai_btn_{i}"):
                    with st.spinner("AI가 분석 중입니다..."):
                        try:
                            # 제목과 RSS 요약 내용을 합쳐서 AI에게 보냄
                            input_text = f"제목: {entry.title}\n내용: {entry.description}"
                            result = analyze_news_with_ai(input_text)
                            
                            # 분석 결과 보여주기
                            st.success("✅ 분석 완료!")
                            st.markdown(f"**📌 요약:** {result['summary']}")
                            st.markdown(f"**😡 감정 단어:** {result['bias']}")
                            st.info(f"**🕵️ 체크 포인트:** {result['fact_check']}")
                            
                        except Exception as e:
                            st.error(f"분석 실패: {e}")