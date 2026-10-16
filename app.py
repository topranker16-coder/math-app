import json
import re
import streamlit as st
import streamlit.components.v1 as components

# 웹 페이지 기본 설정
st.set_page_config(
    page_title="AI 대화 원클릭 PDF 변환기", page_icon="📄", layout="wide"
)

st.title("📄 AI 대화 원클릭 PDF 직접 저장기")
st.write(
    "Gemini 대화창 하단의 **[복사] 버튼**을 눌러 붙여넣으시면, 수식과 글자 배열을 완벽하게 정돈하여 **PDF 파일로 즉시 다운로드**합니다."
)

col1, col2 = st.columns(2)

with col1:
    st.subheader("📥 대화 내용 붙여넣기")
    raw_text = st.text_area(
        "복사한 대화를 붙여넣으세요:",
        height=550,
        placeholder="Gemini 답변 우측 하단의 [복사] 버튼을 누른 후 여기에 붙여넣으세요.",
    )


def preprocess_text(text):
    if not text:
        return ""
    # 백슬래시 수식을 정석 수식으로 자동 변환
    text = re.sub(r"\\\((.*?)\\\)", r"\\(\1\\)", text)
    text = re.sub(r"\\\[(.*?)\\\]", r"\\[\1\\]", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


cleaned_text = preprocess_text(raw_text)

# html2pdf 라이브러리를 활용한 PDF 직접 다운로드 템플릿
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/contrib/auto-render.min.js"
            onload="renderMathInElement(document.getElementById('pdf-area'), {{
                delimiters: [
                    {{left: '\\[', right: '\\]', display: true}},
                    {{left: '\\(', right: '\\)', display: false}},
                    {{left: '$$', right: '$$', display: true}},
                    {{left: '$', right: '$', display: false}}
                ]
            }});"></script>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <!-- 원클릭 PDF 직접 변환 라이브러리 -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>

    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
        
        body {{
            font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
            padding: 10px;
            color: #111;
        }}

        #pdf-area {{
            padding: 30px;
            background: #ffffff;
            line-height: 1.8;
            font-size: 15px;
        }}

        h1, h2, h3, h4 {{
            color: #1a202c;
            margin-top: 1.2em;
            margin-bottom: 0.5em;
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
        }}

        code {{
            background-color: #edf2f7;
            padding: 2px 5px;
            border-radius: 4px;
            font-size: 13px;
        }}

        .pdf-btn {{
            width: 100%;
            background-color: #ff4b4b;
            color: white;
            border: none;
            padding: 14px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 16px;
            cursor: pointer;
            box-shadow: 0 2px 5px rgba(0,0,0,0.15);
        }}
        .pdf-btn:hover {{
            background-color: #e03e3e;
        }}
    </style>
</head>
<body>
    <div style="margin-bottom: 15px;">
        <button class="pdf-btn" onclick="generatePDF()">📥 클릭 시 즉시 PDF 파일 다운로드 (.pdf)</button>
    </div>

    <div id="pdf-area"></div>

    <script>
        const rawMarkdown = {markdown_json};
        document.getElementById('pdf-area').innerHTML = marked.parse(rawMarkdown);

        function generatePDF() {{
            const element = document.getElementById('pdf-area');
            const opt = {{
                margin:       10,
                filename:     'AI_대화_정돈_문서.pdf',
                image:        {{ type: 'jpeg', quality: 0.98 }},
                html2canvas:  {{ scale: 2, useCORS: true }},
                jsPDF:        {{ unit: 'mm', format: 'a4', orientation: 'portrait' }}
            }};

            html2pdf().set(opt).from(element).save();
        }}
    </script>
</body>
</html>
"""

with col2:
    st.subheader("✨ 정돈된 문서 미리보기 & PDF 원클릭 저장")
    if raw_text:
        st.markdown(cleaned_text)
        st.divider()

        markdown_json_str = json.dumps(cleaned_text)
        html_code = HTML_TEMPLATE.format(markdown_json=markdown_json_str)

        components.html(html_code, height=800, scrolling=True)
    else:
        st.info(
            "왼쪽 상자에 Gemini 대화의 [복사] 버튼을 누른 텍스트를 붙여넣으시면, PDF로 바로 저장할 수 있는 버튼이 나타납니다."
        )
