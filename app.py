import streamlit as st
import feedparser
import google.generativeai as genai
import json
import requests

# 1. 페이지 설정
st.set_page_config(page_title="뉴스 영양사", page_icon="🥦", layout="wide")

# 2. 비밀 금고에서 키 꺼내서 세팅하기
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    pass 

# 3. AI 분석 함수 (프롬프트가 대폭 업그레이드 되었습니다!)
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
            "what": "행동/결과 (어떻게 했다)",
            "why": "핵심 원인 (왜)"
        }},
        "analysis": {{
            "valid_causes": ["직접적인 처벌/사건의 원인이 된 팩트 1", "팩트 2"],
            "ref_causes": ["참고는 되었으나 결정적이지 않거나 시효가 지난 의혹 1", "의혹 2"],
            "explanation": "위 두 가지를 구분한 이유 설명 (한 문장)"
        }},
        "terms": [
            {{
                "term": "어려운 용어 또는 핵심 개념 (예: 징계 시효)",
                "desc": "초등학생도 이해할 수 있는 쉬운 설명"
            }}
        ],
        "balance": {{
            "heard": "기사에서 주로 목소리가 실린 쪽의 입장 요약",
            "missing": "기사에서 구체적인 해명이나 입장이 부족한 쪽의 지적",
            "comment": "균형 잡힌 시각을 위한 조언"
        }}
    }}
    """
    
    # 모델: gemini-flash-latest 사용
    model = genai.GenerativeModel('gemini-flash-latest')
    
    response = model.generate_content(prompt)
    text = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)

# 4. 화면 구성
st.title("🥦 뉴스 영양사: 심층 분석판")
st.write("뉴스의 뼈와 살을 발라내어, 진짜 정보를 떠먹여 드립니다.")
st.divider()

# 뉴스 가져오기 (SBS 정치)
rss_url = "http://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=01&plink=RSSREADER"

try:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(rss_url, headers=headers, timeout=5)
    
    if response.status_code == 200:
        news = feedparser.parse(response.content)
    else:
        st.error(f"뉴스 접속 거부됨: {response.status_code}")
        news = None
except Exception as e:
    st.error(f"접속 에러: {e}")
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
                
                # 심층 분석 버튼
                if st.button("✨ 영양 성분 심층 분석", key=f"ai_btn_{i}"):
                    if "GEMINI_API_KEY" not in st.secrets:
                         st.error("AI 키가 설정되지 않았습니다.")
                    else:
                        with st.spinner("AI가 기사를 해체하고 분석 중입니다... (약 5초 소요)"):
                            try:
                                # 제목과 내용을 합쳐서 보냄
                                input_text = f"제목: {entry.title}\n내용: {entry.description}"
                                res = analyze_news_with_ai(input_text)
                                
                                # --- [분석 결과 화면 디자인] ---
                                st.success("✅ 분석 완료! 아래 내용을 확인하세요.")
                                
                                # 1. 뼈대 바르기
                                st.markdown("### 1. 🍖 뼈대 바르기 (핵심 팩트)")
                                st.markdown(f"""
                                - **누가:** {res['core_facts']['who']}
                                - **누구를:** {res['core_facts']['whom']}
                                - **결과:** {res['core_facts']['what']}
                                - **이유:** {res['core_facts']['why']}
                                """)
                                st.divider()
                                
                                # 2. 양념 걷어내기
                                st.markdown("### 2. 🧂 양념 걷어내기 (팩트 vs 참고)")
                                st.info(f"💡 {res['analysis']['explanation']}")
                                
                                st.markdown("**✅ 결정적 사유 (유효타)**")
                                for item in res['analysis']['valid_causes']:
                                    st.write(f"- {item}")
                                    
                                st.markdown("**⚠️ 참고용 사유 (논란/시효만료)**")
                                for item in res['analysis']['ref_causes']:
                                    st.caption(f"- {item}") # 회색 글씨로 약하게 표시
                                st.divider()
                                
                                # 3. 돋보기 (용어 설명)
                                st.markdown("### 3. 🔍 돋보기 (용어 해설)")
                                for term in res['terms']:
                                    with st.expander(f"❓ '{term['term']}' 뜻이 뭐예요?"):
                                        st.write(term['desc'])
                                
                                # 4. 균형 잡기
                                st.divider()
                                st.markdown("### 4. ⚖️ 균형 잡기 (목소리 확인)")
                                col_heard, col_miss = st.columns(2)
                                with col_heard:
                                    st.success("📢 들리는 목소리")
                                    st.write(res['balance']['heard'])
                                with col_miss:
                                    st.error("🔇 안 들리는 목소리")
                                    st.write(res['balance']['missing'])
                                
                                st.warning(f"💡 코멘트: {res['balance']['comment']}")

                            except Exception as e:
                                st.error(f"분석 중 오류 발생: {e}")
                                st.error("기사 내용이 너무 짧거나 AI가 응답을 생성하지 못했습니다.")