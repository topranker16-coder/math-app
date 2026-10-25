import io
import json
import re
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image

# 로컬 PDF 및 OCR 라이브러리 연동
try:
    from pypdf import PdfReader
    import pytesseract
    from pdf2image import convert_from_bytes
    HAS_LOCAL_OCR = True
except ImportError:
    HAS_LOCAL_OCR = False

# 윈도우 환경인 경우 Tesseract 경로 설정 (필요시 경로 수정)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# 웹 페이지 기본 설정
st.set_page_config(
    page_title="완전 로컬 수학 수식 OCR & PDF 변환기",
    page_icon="📚",
    layout="wide"
)

st.title("📚 완전 로컬 수학 수식 OCR & PDF 변환기 (API 키 없음)")
st.write(r"외부 API 연결 없이, 내 컴퓨터의 OCR 엔진을 이용해 **스캔된 수학 문제지(PDF/이미지)**를 읽고 깨짐 없는 **KaTeX 수식 문서**로 정돈합니다.")

tab1, tab2 = st.tabs(["📋 1. 텍스트 직접 입력 및 정돈", "🤖 2. 로컬 Vision OCR (스캔 PDF/이미지 처리)"])

# 텍스트 전처리 및 정돈 함수
def preprocess_text(text):
    if not text:
        return ""
    text = re.sub(r'\\\((.*?)\\\)', r'\\(\1\\)', text)
    text = re.sub(r'\\\[(.*?)\\\]', r'\\[\1\\]', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text

# HTML/CSS + KaTeX 렌더링 템플릿
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
</html>"""

# 세션 상태 초기화
if "input_text" not in st.session_state:
    st.session_state["input_text"] = ""

# --- 탭 1: 직접 입력 및 실시간 정돈 ---
with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📥 텍스트 / 수식 직접 입력")
        pasted_text = st.text_area(
            "마크다운 및 LaTeX 수식($...$)을 포함한 텍스트를 입력하세요:",
            value=st.session_state["input_text"],
            height=550,
            placeholder="예시:\n2차 방정식의 근의 공식:\n$x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$"
        )
        st.session_state["input_text"] = pasted_text

    with col2:
        st.subheader("✨ 수식 렌더링 미리보기 & PDF 저장")
        if st.session_state["input_text"]:
            cleaned = preprocess_text(st.session_state["input_text"])
            markdown_json_str = json.dumps(cleaned)
            html_code = HTML_TEMPLATE.format(markdown_json=markdown_json_str)
            components.html(html_code, height=650, scrolling=True)
        else:
            st.info("왼쪽에 텍스트나 수식을 입력하시면 KaTeX로 깔끔하게 렌더링된 미리보기와 PDF 저장 버튼이 나타납니다.")

# --- 탭 2: 로컬 Vision OCR (스캔 PDF 및 이미지 처리) ---
with tab2:
    st.subheader("🤖 로컬 OCR 엔진으로 스캔 PDF / 이미지 글자 추출")
    st.caption("💡 Tesseract OCR을 이용하여 이미지 기반 문서나 스캔본의 텍스트를 컴퓨터 안에서 직접 읽어냅니다.")

    if not HAS_LOCAL_OCR:
        st.error("⚠️ 필수 라이브러리가 없습니다. 터미널에 `pip install pypdf pytesseract pdf2image pillow`를 실행해 주세요.")

    uploaded_file = st.file_uploader("스캔된 PDF 또는 이미지(PNG, JPG) 파일을 선택하세요:", type=["pdf", "png", "jpg", "jpeg"])

    if uploaded_file is not None and HAS_LOCAL_OCR:
        file_name = uploaded_file.name
        file_ext = file_name.split(".")[-1].lower()
        st.info(f"📄 업로드된 파일: **{file_name}**")
        
        if st.button("🚀 로컬 OCR 추출 시작하기"):
            with st.spinner("🔍 로컬 OCR 엔진이 문서를 분석하고 있습니다 (잠시만 기다려주세요)..."):
                try:
                    extracted_text = ""
                    if file_ext == "pdf":
                        # PDF를 이미지로 변환 후 OCR 수행
                        images = convert_from_bytes(uploaded_file.getvalue())
                        for i, img in enumerate(images):
                            # 한국어 + 영어 인식 설정 (kor+eng)
                            text = pytesseract.image_to_string(img, lang='kor+eng')
                            extracted_text += f"\n\n--- [Page {i+1}] ---\n\n" + text
                    else:
                        # 일반 이미지 파일 처리
                        img = Image.open(uploaded_file)
                        text = pytesseract.image_to_string(img, lang='kor+eng')
                        extracted_text = text
                    
                    st.session_state["extracted_ocr"] = extracted_text
                except Exception as e:
                    st.error(f"OCR 처리 중 오류 발생: 라이브러리 및 Tesseract 설치 상태를 확인해주세요. 상세 내용: {e}")

        if "extracted_ocr" in st.session_state and st.session_state["extracted_ocr"]:
            st.divider()
            st.success("🎉 로컬 OCR 추출 완료!")
            
            col_ocr1, col_ocr2 = st.columns(2)
            with col_ocr1:
                st.write("##### ✏️ 추출된 텍스트 편집")
                edited_ocr_text = st.text_area(
                    "내용 수정:",
                    value=st.session_state["extracted_ocr"],
                    height=500
                )
                if st.button("📋 1번 탭(정돈/PDF 출력 영역)으로 보내기", key="send_to_tab1_ocr"):
                    st.session_state["input_text"] = edited_ocr_text
                    st.toast("1번 탭으로 전송되었습니다!")

            with col_ocr2:
                st.write("##### ✨ 미리보기")
                cleaned_ocr = preprocess_text(edited_ocr_text)
                markdown_json_str = json.dumps(cleaned_ocr)
                html_code = HTML_TEMPLATE.format(markdown_json=markdown_json_str)
                components.html(html_code, height=520, scrolling=True)
