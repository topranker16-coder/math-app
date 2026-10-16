import json
import re
import streamlit as st
import streamlit.components.v1 as components

# 웹 페이지 기본 설정
st.set_page_config(
    page_title="AI 대화 깔끔 문서 & PDF 변환기",
    page_icon="📄",
    layout="wide"
)

st.title("📄 AI 대화 자동 정돈 & PDF 저장기")
st.write("Gemini 대화창 하단의 **[복사] 버튼**을 눌러 붙여넣으시면, 수식과 글자 배열을 완벽하게 정돈하여 **PDF 파일로 저장**할 수 있습니다.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📥 대화 내용 붙여넣기")
    raw_text = st.text_area(
        "복사한 대화를 붙여넣으세요:",
        height=550,
        placeholder="Gemini 답변 우측 하단의 [복사] 버튼을 누른 후 여기에 붙여넣으세요."
    )

def preprocess_text(text):
    if not text:
        return ""
    # 백슬래시 수식을 정석 수식으로 자동 변환
    text = re.sub(r'\\\((.*?)\\\)', r'\\(\1\\)', text)
    text = re.sub(r'\\\[(.*?)\\\]', r'\\[\1\\]', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text

cleaned_text = preprocess_text(raw_text)

# 안전하고 깨끗한 PDF 출력을 위한 HTML/CSS 템플릿
HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>AI 대화 정돈 문서</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/contrib/auto-render.min.js"
            onload="renderMathInElement(document.getElementById('content'), {{
                delimiters: [
                    {{left: '\\[', right: '\\]', display: true}},
                    {{left: '\\(', right: '\\)', display: false}},
                    {{left: '$$', right: '$$', display: true}},
                    {{left: '$', right: '$', display: false}}
                ]
            }});"></script>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>

    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
        
        body {{
            font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
            padding: 20px;
            color: #111111;
            line-height: 1.8;
            font-size: 15px;
            background-color: #ffffff;
        }}

        .no-print {{
            margin-bottom: 20px;
            position: sticky;
            top: 0;
            background-color: #ffffff;
            padding-bottom: 10px;
            z-index: 100;
        }}

        .pdf-btn {{
            width: 100%;
            background-color: #2b6cb0;
            color: white;
            border: none;
            padding: 14px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 16px;
            cursor: pointer;
            box-shadow: 0 2px 5px rgba(0,0,0,0.15);
            transition: background-color 0.2s;
        }}

        .pdf-btn:hover {{
            background-color: #2c5282;
        }}

        h1, h2, h3, h4 {{
            color: #1a202c;
            margin-top: 1.2em;
            margin-bottom: 0.5em;
            font-weight: 700;
        }}
        h1 {{ font-size: 22px; border-bottom: 2px solid #cbd5e0; padding-bottom: 6px; }}
        h2 {{ font-size: 18px; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; }}
        h3 {{ font-size: 16px; }}

        p {{ margin-bottom: 0.8em; word-break: keep-all; }}
        ul, ol {{ padding-left: 20px; margin-bottom: 0.8em; }}
        li {{ margin-bottom: 0.3em; }}

        blockquote {{
            border-left: 4px solid #3182ce;
            background-color: #f7fafc;
            margin: 1em 0;
            padding: 10px 15px;
            border-radius: 0 4px 4px 0;
        }}

        code {{
            background-color: #edf2f7;
            padding: 2px 5px;
            border-radius: 4px;
            font-size: 13px;
            color: #c53030;
        }}

        pre {{
            background-color: #2d3748;
            color: #f7fafc;
            padding: 15px;
            border-radius: 6px;
            overflow-x: auto;
        }}

        pre code {{
            background-color: transparent;
            color: inherit;
            padding: 0;
        }}

        @media print {{
            .no-print {{ display: none !important; }}
            body {{
                padding: 0;
                margin: 0;
                background-color: #ffffff;
            }}
        }}
    </style>
</head>
<body>
    <div class="no-print">
        <button class="pdf-btn" onclick="window.print()">📄 PDF 문서로 저장하기</button>
    </div>
    <div id="content"></div>

    <script>
        const rawMarkdown = {markdown_json};
        document.getElementById('content').innerHTML = marked.parse(rawMarkdown);
    </script>
</body>
</html>"""

with col2:
    st.subheader("✨ 정돈된 문서 미리보기 & PDF 저장")
    if raw_text:
        # 정돈된 HTML 렌더링
        markdown_json_str = json.dumps(cleaned_text)
        html_code = HTML_TEMPLATE.format(markdown_json=markdown_json_str)

        # PDF 버튼이 포함된 미리보기 영역
        components.html(html_code, height=650, scrolling=True)
    else:
        st.info("왼쪽 상자에 Gemini 대화의 [복사] 버튼을 누른 텍스트를 붙여넣으시면, 정돈된 문서 미리보기와 PDF 저장 버튼이 나타납니다.")
