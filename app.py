import streamlit as st
import streamlit.components.v1 as components
import json
import re
from PIL import Image
import pytesseract
from pypdf import PdfReader
import io

# 웹 페이지 기본 설정
st.set_page_config(
    page_title="스캔북 OCR & AI 대화 정돈 변환기",
    page_icon="📚",
    layout="wide"
)

st.title("📚 스캔북 OCR & AI 대화 문서 정돈 변환기")
st.write("스캔 이미지/PDF 파일을 올리거나 Gemini 대화 텍스트를 붙여넣으시면, **자동 OCR 추출 및 수식·문단 정돈**을 거쳐 **A4 규격 PDF 문서**로 만들어 드립니다.")

tab1, tab2 = st.tabs(["📋 1. 대화/텍스트 직접 붙여넣기", "📸 2. 스캔 이미지/PDF 업로드 (OCR)"])

# 텍스트 전처리 및 정돈 함수
def preprocess_text(text):
    if not text:
        return ""
    # 백슬래시 수식을 정석 라텍스 수식($$)으로 자동 변환
    text = re.sub(r'\\\((.*?)\\\)', r'\\(\1\\)', text)
    text = re.sub(r'\\\[(.*?)\\\]', r'\\[\1\\]', text)
    # 3줄 이상 연속된 줄바꿈을 2줄로 정리
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text

# HTML/CSS 출력 템플릿
HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>정돈된 문서</title>
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
        <button class="pdf-btn" onclick="window.print()">📄 정돈된 문서 PDF로 저장하기</button>
    </div>
    <div id="content"></div>

    <script>
        const rawMarkdown = {markdown_json};
        document.getElementById('content').innerHTML = marked.parse(rawMarkdown);
    </script>
</body>
</html>"""

# 세션 상태 초기화
if "input_text" not in st.session_state:
    st.session_state["input_text"] = ""

# --- 탭 1: 직접 붙여넣기 ---
with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📥 대화/텍스트 입력")
        pasted_text = st.text_area(
            "복사한 대화나 텍스트를 붙여넣으세요:",
            value=st.session_state["input_text"],
            height=550,
            placeholder="Gemini 답변이나 OCR로 뽑은 텍스트를 여기에 붙여넣으세요."
        )
        st.session_state["input_text"] = pasted_text

    with col2:
        st.subheader("✨ 정돈된 문서 미리보기 & PDF 저장")
        if st.session_state["input_text"]:
            cleaned = preprocess_text(st.session_state["input_text"])
            markdown_json_str = json.dumps(cleaned)
            html_code = HTML_TEMPLATE.format(markdown_json=markdown_json_str)
            components.html(html_code, height=650, scrolling=True)
        else:
            st.info("왼쪽에 텍스트를 입력하시면 정돈된 미리보기와 PDF 저장 버튼이 나타납니다.")

# --- 탭 2: 스캔 이미지/PDF OCR 추출 ---
with tab2:
    st.subheader("📸 이미지 및 PDF 스캔 파일에서 글자(OCR) 추출하기")
    uploaded_file = st.file_uploader(
        "스캔한 책 이미지(PNG, JPG) 또는 PDF 파일을 선택하세요:",
        type=["png", "jpg", "jpeg", "pdf"]
    )

    if uploaded_file is not None:
        extracted_text = ""
        file_type = uploaded_file.name.split(".")[-1].lower()

        with st.spinner("🔍 파일에서 글자 및 문장을 읽어오는 중입니다..."):
            try:
                if file_type in ["png", "jpg", "jpeg"]:
                    image = Image.open(uploaded_file)
                    st.image(image, caption="업로드한 이미지", use_container_width=True)
                    try:
                        extracted_text = pytesseract.image_to_string(image, lang="kor+eng")
                    except Exception:
                        extracted_text = pytesseract.image_to_string(image)

                elif file_type == "pdf":
                    pdf_bytes = uploaded_file.read()
                    reader = PdfReader(io.BytesIO(pdf_bytes))
                    pdf_text = []
                    for idx, page in enumerate(reader.pages):
                        text = page.extract_text()
                        if text:
                            pdf_text.append(f"--- [ {idx+1} 페이지 ] ---\n" + text)
                    extracted_text = "\n\n".join(pdf_text)

            except Exception as e:
                st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")

        if extracted_text.strip():
            st.success("🎉 글자 추출 완료! 아래 텍스트를 확인 및 편집하실 수 있습니다.")
            
            col_ocr1, col_ocr2 = st.columns(2)
            with col_ocr1:
                st.write("##### ✏️ 추출된 원본 텍스트 (편집 가능)")
                edited_ocr = st.text_area(
                    "추출된 텍스트:",
                    value=extracted_text,
                    height=450
                )
                if st.button("📋 이 텍스트로 정돈 문서 생성하기"):
                    st.session_state["input_text"] = edited_ocr
                    st.toast("1번 탭의 정돈 영역으로 텍스트가 전달되었습니다!")

            with col_ocr2:
                st.write("##### ✨ 정돈된 문서 미리보기")
                cleaned_ocr = preprocess_text(edited_ocr if 'edited_ocr' in locals() else extracted_text)
                markdown_json_str = json.dumps(cleaned_ocr)
                html_code = HTML_TEMPLATE.format(markdown_json=markdown_json_str)
                components.html(html_code, height=520, scrolling=True)
        else:
            st.warning("파일에서 텍스트를 추출하지 못했습니다. 스캔 이미지의 해상도를 확인해 주세요.")
