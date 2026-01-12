import streamlit as st
import feedparser

# 1. 페이지 설정 (탭 이름과 아이콘)
st.set_page_config(
    page_title="실시간 정치 뉴스",
    page_icon="📡"
)

# 2. 제목과 설명
st.title("📡 실시간 정치 뉴스 모음")
st.write("지금 정치권에서 무슨 일이 일어나고 있는지 실시간으로 확인하세요.")
st.divider()

# 3. 사이드바 (꾸미기용)
with st.sidebar:
    st.header("정보")
    st.info("이 사이트는 SBS 뉴스 RSS 데이터를 실시간으로 가져와서 보여줍니다.")

# 4. 뉴스 데이터 가져오기 (SBS 정치)
rss_url = "http://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=01&plink=RSSREADER"

# 로딩 중일 때 돌아가는 아이콘 보여주기
with st.spinner("최신 뉴스를 배달받고 있습니다..."):
    news = feedparser.parse(rss_url)

# 5. 뉴스 카드 만들기
if len(news.entries) == 0:
    st.error("뉴스를 가져올 수 없습니다. 잠시 후 다시 시도해주세요.")
else:
    # 최신 뉴스 10개 보여주기
    for i in range(min(10, len(news.entries))):
        entry = news.entries[i]
        
        # 카드를 박스 형태로 예쁘게 묶기 (Container)
        with st.container(border=True):
            # 뉴스 제목 (클릭하면 이동하는 링크 포함)
            st.subheader(f"{i+1}. {entry.title}")
            
            # 날짜 표시
            st.caption(f"발행일: {entry.published}")
            
            # 요약 내용 (description) - RSS가 제공하는 짧은 설명
            st.write(entry.description)
            
            # 버튼
            st.link_button("기사 전문 읽기 👉", entry.link)