import streamlit as st
import feedparser
import time

# 1. 페이지 설정 (넓은 화면 모드 사용)
st.set_page_config(
    page_title="뉴스 영양사",
    page_icon="🥦",
    layout="wide"  # <--- 화면을 넓게 써서 가로로 배치하기 위함
)

st.title("🥦 뉴스 영양사: 오늘의 정치")
st.write("실시간으로 업데이트되는 정치 뉴스를 한눈에 확인하세요.")
st.divider()

# 2. 뉴스 데이터 가져오기 (SBS 정치)
rss_url = "http://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=01&plink=RSSREADER"
news = feedparser.parse(rss_url)

# 3. 가로 배치를 위한 그리드 설정
if len(news.entries) == 0:
    st.error("뉴스를 가져올 수 없습니다.")
else:
    # 3개의 기둥(Column)을 만듭니다.
    cols = st.columns(3) 
    
    # 뉴스 12개만 가져와서 배치해봅시다
    for i in range(min(12, len(news.entries))):
        entry = news.entries[i]
        
        # 0, 1, 2번 기둥에 번갈아가며 담기 (나머지 연산 %)
        with cols[i % 3]:
            # 카드 디자인 (컨테이너)
            with st.container(border=True):
                # 제목 (높이를 맞추기 위해 일정 길이로 자름)
                safe_title = entry.title[:30] + "..." if len(entry.title) > 30 else entry.title
                st.subheader(safe_title)
                
                # 날짜
                st.caption(entry.published)
                
                # 버튼 그룹
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    st.link_button("🔗 원문", entry.link)
                with col_btn2:
                    # 이 버튼을 누르면 AI 분석이 시작됨
                    analyze_btn = st.button("✨ 분석", key=f"btn_{i}")
                
                # 분석 버튼을 눌렀을 때 보여줄 내용
                if analyze_btn:
                    with st.spinner("AI가 기사를 씹고 뜯고 맛보는 중..."):
                        time.sleep(1.5) # (분석하는 척 연출)
                        
                        # --- [여기에 아까 그 프롬프트가 들어갑니다] ---
                        # 지금은 API 키가 없어서 가짜 결과를 보여줍니다.
                        st.success("✅ 3줄 요약 완료!")
                        st.markdown(f"""
                        **1. 팩트:** {entry.title} 관련 보도임.
                        **2. 분석:** 아직 'AI 뇌(API Key)'가 연결되지 않았습니다.
                        **3. 알림:** 다음 단계에서 키를 연결하면 진짜 분석이 나옵니다!
                        """)
                        st.info("💡 꿀팁: 기사 원문의 감정적 표현을 걸러냈습니다.")