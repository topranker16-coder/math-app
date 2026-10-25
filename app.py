import streamlit as st

st.title("🧮 나만의 수학 문제 & LaTeX 관리기")

# 사용자 입력창
problem_title = st.text_input("문제 제목", "2026학년도 고난도 수학 연습")
problem_content = st.text_area("문제 LaTeX 내용 입력", "$f(x) = x^2 - 4x + 4$ 일 때, $f(2)$의 값을 구하시오.")

if st.button("미리보기 및 생성"):
    st.subheader("📌 미리보기")
    st.write(f"**[{problem_title}]**")
    st.latex(problem_content)

    st.success("깃허브와 연동된 나만의 전용 웹 앱에서 정상적으로 작동 중입니다!")
