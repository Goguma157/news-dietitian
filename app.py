import streamlit as st

# 1. 재료 준비 (아까 AI가 만들어준 JSON 데이터를 변수에 담습니다)
# 실제 앱에서는 이 부분이 AI에게 실시간으로 받아오는 코드로 바뀝니다.
news_analysis = {
  "summary": "더불어민주당 윤리심판원이 여러 비위 의혹을 받는 김병기 의원을 당에서 제명하기로 12일 결정했습니다. 3년이 지나 징계할 수 없는 옛날 의혹들 대신, 작년에 발생한 기업 접대(호텔 숙박권, 식사) 사건을 주된 제명 사유로 삼았습니다.",
  "facts": [
    {
      "fact": "더불어민주당 윤리심판원은 김병기 의원에 대해 제명 처분을 의결함",
      "evidence": "더불어민주당 윤리심판원은 12일... 제명을 의결했다."
    },
    {
      "fact": "징계 시효(3년)가 지난 사안은 처벌 근거가 아닌 참고용으로만 활용됨",
      "evidence": "징계 시효가 완성된 부분은 징계 양정에 참고가 된다는 것이 대법원 판례이고"
    }
  ],
  "bias_check": {
    "missing_viewpoints": "김병기 의원이 혐의를 인정했는지 부인했는지에 대한 구체적인 해명이나 반박 내용은 기사에 전혀 포함되지 않음."
  },
  "verification_needed": "‘고가 식사’라고 언급되었으나 구체적인 금액이 명시되지 않아 검증이 필요함."
}

# 2. 간판 달기 (제목)
st.set_page_config(page_title="뉴스 영양사", page_icon="🥦")
st.title("🥦 뉴스 영양사")
st.subheader("복잡한 정치 뉴스, 뼈와 살을 발라드립니다.")
st.divider() # 구분선

# 3. 메인 요리: 3줄 요약 (초록색 박스로 깔끔하게)
st.header("1. 3줄 핵심 요약")
st.success(news_analysis["summary"])

# 4. 반찬: 팩트 체크 (눌러서 펼쳐보는 기능)
st.header("2. 팩트와 증거 확인")
st.info("아래 항목을 누르면 기사 원문의 '증거 문장'이 나옵니다.")

for item in news_analysis["facts"]:
    # 접었다 폈다 할 수 있는 확장 박스(Expander)를 만듭니다
    with st.expander(f"✅ {item['fact']}"):
        st.write(f"🕵️ **증거:** \"{item['evidence']}\"")

# 5. 후식: 편향성 경고 (노란색/빨간색 경고 박스)
st.header("3. 영양 성분표 (주의사항)")

col1, col2 = st.columns(2) # 화면을 반으로 나눕니다

with col1:
    st.warning("🔇 **빠진 목소리**")
    st.write(news_analysis["bias_check"]["missing_viewpoints"])

with col2:
    st.error("🤔 **검증 필요**")
    st.write(news_analysis["verification_needed"])