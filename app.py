import json
import re
import streamlit as st
import streamlit.components.v1 as components

# 웹 페이지 기본 설정
st.set_page_config(
    page_title="AI 대화 내용 자동 정돈 & PDF 저장기",
    page_icon="📝",
    layout="wide",
)

st.title("📝 AI 대화 내용 깔끔 정돈 & PDF 문서 변환기")
st.write(
    "Gemini나 ChatGPT에서 복사한 대화 텍스트를 붙여넣으시면, 줄바꿈·제목·수식·목록을 자동으로 보기 좋게 정돈하여 PDF로 내보낼 수 있습니다."
)

col1, col2 = st.columns(2)

with col1:
    st.subheader("📥 복사한 대화 내용 붙여넣기")
    raw_text = st.text_area(
        "복사한 대화 텍스트를 여기에 붙여넣으세요:",
        height=540,
        placeholder="""예시:
[질문] 지니야, 피타고라스 정리에 대해 설명해줘.

[답변]
피타고라스 정리는 직각삼각형에서 빗변의 길이 \\(c\\)와 나머지 두 변 \\(a, b\\) 사이의 관계식입니다.

\\[a^2 + b^2 = c^2\\]""",
    )


def preprocess_chat_text(text):
    if not text:
        return ""

    # 1. 수식 기호 표준화 (백슬래시 수식을 달러 수식으로 자동 변환)
    text = re.sub(r"\\\((.*?)\\\)", r"\\(\1\\)", text)
    text = re.sub(r"\\\[(.*?)\\\]", r"\\[\1\\]", text)

    # 2. 불필요하게 어긋난 과도한 줄바꿈 정돈
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 3. 목록 기호 간격 일치화
    text = re.sub(r"^\s*[-*•]\s*", "- ", text, flags=re.MULTILINE)

    return text


cleaned_text = preprocess_chat_text(raw_text)

# 고품질 한글 문서 디자인 & PDF 출력용 HTML/CSS 템플릿
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>정돈된 AI 대화 문서</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/contrib/auto-render.min.js"
            onload="renderMathInElement(document.body, {{
                delimiters: [
                    {{left: '\\[', right: '\\]', display: true}},
                    {{left: '\\(', right: '\\)', display: false}},
                    {{left: '\\[', right: '\\]', display: true}},
                    {{left: '\\(', right: '\\)', display: false}}
                ]
            }});"></script>

    <!-- 마크다운 파서 -->
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>

    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
        
        body {{
            font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
            padding: 40px;
            max-width: 850px;
            margin: 0 auto;
            line-height: 1.8;
            color: #222222;
            background-color: #ffffff;
        }}

        h1, h2, h3, h4 {{
            color: #1a202c;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
            font-weight: 700;
        }}

        h1 {{ font-size: 24px; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px; }}
        h2 {{ font-size: 20px; border-bottom: 1px solid #edf2f7; padding-bottom: 6px; }}
        h3 {{ font-size: 17px; }}

        p {{
            margin-bottom: 1em;
            word-break: keep-all;
        }}

        ul, ol {{
            padding-left: 24px;
            margin-bottom: 1em;
        }}

        li {{
            margin-bottom: 0.4em;
        }}

        blockquote {{
            border-left: 4px solid #3182ce;
            background-color: #ebf8ff;
            margin: 1.2em 0;
            padding: 12px 18px;
            border-radius: 0 6px 6px 0;
        }}

        code {{
            background-color: #f7fafc;
            border: 1px solid #e2e8f0;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Consolas', monospace;
            font-size: 14px;
            color: #c53030;
        }}

        pre {{
            background-color: #2d3748;
            color: #f7fafc;
            padding: 16px;
            border-radius: 8px;
            overflow-x: auto;
            line-height: 1.5;
        }}

        pre code {{
            background-color: transparent;
            border: none;
            color: inherit;
            padding: 0;
        }}

        .katex-display {{
            margin: 1.2em 0 !important;
            padding: 8px 0;
        }}

        @media print {{
            body {{
                padding: 15mm;
                max-width: 100%;
            }}
            button {{ display: none !important; }}
        }}
    </style>
</head>
<body>
    <div id="content"></div>

    <script>
        const rawMarkdown = {markdown_json};
        document.getElementById('content').innerHTML = marked.parse(rawMarkdown);
    </script>
</body>
</html>
"""

with col2:
    st.subheader("✨ 정돈된 문서 미리보기 & 저장")
    if raw_text:
        # 1. 화면 내 정돈된 마크다운 실시간 미리보기
        st.markdown(cleaned_text)
        st.divider()

        # 2. 고품질 PDF 인쇄용 HTML 파싱
        markdown_json_str = json.dumps(cleaned_text)
        html_code = HTML_TEMPLATE.format(markdown_json=markdown_json_str)

        st.write("##### 📥 문서 저장 옵션")

        # PDF 다운로드/인쇄 버튼
        components.html(
            f"""
            <script>
            function downloadPDF() {{
                var printWindow = window.open('', '', 'height=800,width=950');
                printWindow.document.write(`{html_code}`);
                printWindow.document.close();
                setTimeout(function() {{
                    printWindow.print();
                }}, 600);
            }}
            </script>
            <button onclick="downloadPDF()" style="
                width: 100%;
                background-color: #2b6cb0;
                color: white;
                border: none;
                padding: 14px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 16px;
                cursor: pointer;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                📄 깨끗한 PDF 파일로 내보내기 / 인쇄
            </button>
            """,
            height=68,
        )

        # HTML 문서 다운로드 버튼
        st.download_button(
            label="💾 정돈된 HTML 문서로 저장하기",
            data=html_code,
            file_name="formatted_chat_document.html",
            mime="text/html",
            use_container_width=True,
        )
    else:
        st.info(
            "왼쪽 상자에 복사한 대화 텍스트를 붙여넣으시면, 자동으로 일정한 간격과 예쁜 정렬이 맞춰진 문서가 생성됩니다."
        )
