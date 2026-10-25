import io
import json
import re
import streamlit as st
import streamlit.components.v1 as components

# python-docx 라이브러리 체크
try:
    import docx
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

# 웹 페이지 기본 설정
st.set_page_config(
    page_title="수학 수식 문서 정돈 & PDF 변환기",
    page_icon="📚",
    layout="wide"
)

st.title("📚 수학 수식 문서 정돈 & PDF 변환기")
st.write(r"워드(.docx) 파일을 업로드하거나 텍스트를 붙여넣어 수식($...$)을 깔끔하게 정돈하고 PDF로 출력합니다.")

# 텍스트 전처리 및 정돈 함수
def preprocess_text(text):
    if not text:
        return ""
    text = re.sub(r'\\\((.*?)\\\)', r'\\(\1\\)', text)
    text = re.sub(r'\\\[(.*?)\\\]', r'\\[\1\\]', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text

# HTML/CSS + KaTeX 렌더링 템플릿 (PDF 저장 기능 포함)
HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>정돈된 문서</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
    <script src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
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

        .katex-display {{
            margin: 0.8em 0;
            overflow-x: auto;
            overflow-y: hidden;
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
        <button class="pdf-btn" onclick="window.print()">📄 정돈된 문서 PDF로 저장하기</button>
    </div>
    <div id="content"></div>

    <script>
        const rawMarkdown = {markdown_json};

        function renderMarkdownWithMath(markdownText) {{
            if (!markdownText) return '';
            
            const mathBlocks = [];

            let protectedText = markdownText.replace(/\\$\\$([\\s\\S]+?)\\$\\$/g, (match, math) => {{
                try {{
                    const html = katex.renderToString(math.trim(), {{ displayMode: true, throwOnError: false }});
                    mathBlocks.push({{ type: 'block', html: html }});
                    return `\\n\\nKATEXBLOCKPH${{mathBlocks.length - 1}}ENDPH\\n\\n`;
                }} catch (e) {{
                    return match;
                }}
            }});

            protectedText = protectedText.replace(/\\$([^\\$\\n]+?)\\$/g, (match, math) => {{
                try {{
                    const html = katex.renderToString(math.trim(), {{ displayMode: false, throwOnError: false }});
                    mathBlocks.push({{ type: 'inline', html: html }});
                    return `KATEXINLINEPH${{mathBlocks.length - 1}}ENDPH`;
                }} catch (e) {{
                    return match;
                }}
            }});

            let htmlContent = marked.parse(protectedText);

            mathBlocks.forEach((item, index) => {{
                if (item.type === 'block') {{
                    const blockP = `<p>KATEXBLOCKPH${{index}}ENDPH</p>`;
                    if (htmlContent.includes(blockP)) {{
                        htmlContent = htmlContent.replace(blockP, `<div class="katex-display">${{item.html}}</div>`);
                    }} else {{
                        htmlContent = htmlContent.replace(`KATEXBLOCKPH${{index}}ENDPH`, `<div class="katex-display">${{item.html}}</div>`);
                    }}
                }} else {{
                    htmlContent = htmlContent.replace(`KATEXINLINEPH${{index}}ENDPH`, item.html);
                }}
            }});

            return htmlContent;
        }}

        document.getElementById('content').innerHTML = renderMarkdownWithMath(rawMarkdown);
    </script>
</body>
</html>
"""

# 세션 상태 초기화
if "input_text" not in st.session_state:
    st.session_state["input_text"] = ""

# 화면 구성 (좌우 2단 분할)
col1, col2 = st.columns(2)

with col1:
    st.subheader("📥 워드(.docx) 파일 업로드")
    
    if not HAS_DOCX:
        st.error("⚠️ `python-docx` 라이브러리가 없습니다. 터미널에 `pip install python-docx`를 입력해 주세요.")

    uploaded_docx = st.file_uploader("수학 문제지 워드 파일을 선택하세요:", type=["docx"])
    
    if uploaded_docx is not None and HAS_DOCX:
        try:
            doc = docx.Document(uploaded_docx)
            extracted_docx_text = "\n".join([para.text for para in doc.paragraphs])
            st.session_state["input_text"] = extracted_docx_text
            st.success("🎉 워드 파일 내용을 성공적으로 불러왔습니다!")
        except Exception as e:
            st.error(f"워드 파일 읽기 오류: {e}")

    pasted_text = st.text_area(
        "불러온 내용 수정 및 직접 편집:",
        value=st.session_state["input_text"],
        height=500,
        placeholder="워드 파일을 올리면 여기에 텍스트가 자동으로 채워집니다."
    )
    st.session_state["input_text"] = pasted_text

with col2:
    st.subheader("✨ 수식 미리보기 및 PDF 저장")
    if st.session_state["input_text"]:
        cleaned = preprocess_text(st.session_state["input_text"])
        markdown_json_str = json.dumps(cleaned)
        html_code = HTML_TEMPLATE.format(markdown_json=markdown_json_str)
        components.html(html_code, height=650, scrolling=True)
    else:
        st.info("왼쪽 칸에 워드 파일을 업로드하시면, 오른쪽에 수식이 예쁘게 정돈된 미리보기와 PDF 저장 버튼이 나타납니다.")
