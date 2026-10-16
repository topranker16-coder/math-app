import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="LaTeX 수식 정돈 & PDF 생성기", page_icon="📐", layout="wide")

st.title("📐 LaTeX 수식 자동 정돈 & PDF 내보내기 앱")
st.write("Gemini 대화에서 복사한 텍스트를 붙여넣으시면, 정석 수식으로 정돈되고 PDF로 바로 다운로드할 수 있습니다.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📥 원본 텍스트 입력")
    user_input = st.text_area(
        "텍스트를 입력하세요:",
        height=480,
        placeholder=r"""예시:
이차방정식 \\(ax^2 + bx + c = 0\\)의 근의 공식은 다음과 같습니다.

\\[x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}\\]""",
    )

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/contrib/auto-render.min.js"
            onload="renderMathInElement(document.body, {{delimiters: [{{left: '\\[', right: '\\]', display: true}}, {{left: '\\(', right: '\\)', display: false}}]}});"></script>
    <style>
        body {{
            font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
            padding: 25px;
            font-size: 16px;
            line-height: 1.8;
            color: #111;
        }}
    </style>
</head>
<body>
    <div id="content">
        {content}
    </div>
</body>
</html>
"""

with col2:
    st.subheader("✨ 수식 미리보기 & PDF 다운로드")
    if user_input:
        st.markdown(user_input)
        st.divider()

        formatted_html = user_input.replace("\n", "<br>")
        html_code = HTML_TEMPLATE.format(content=formatted_html)

        st.write("##### 📥 다운로드 옵션")

        components.html(
            f"""
            <script>
            function downloadPDF() {{
                var printWindow = window.open('', '', 'height=700,width=900');
                printWindow.document.write(`{html_code}`);
                printWindow.document.close();
                setTimeout(function() {{
                    printWindow.print();
                }}, 500);
            }}
            </script>
            <button onclick="downloadPDF()" style="
                width: 100%;
                background-color: #ff4b4b;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 16px;
                cursor: pointer;">
                📄 PDF 파일로 다운로드 / 인쇄하기
            </button>
            """,
            height=65,
        )

        st.download_button(
            label="💾 웹 문서 파일(.html)로 소장하기",
            data=html_code,
            file_name="math_document.html",
            mime="text/html",
            use_container_width=True,
        )
    else:
        st.info("왼쪽에 텍스트를 입력하면 수식 변환 미리보기와 PDF 다운로드 버튼이 활성화됩니다.")