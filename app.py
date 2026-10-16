import json
import re
import io
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image

# google-generativeai 라이브러리 연동
try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

# 웹 페이지 기본 설정
st.set_page_config(
    page_title="스캔북 OCR & AI 대화 정돈 변환기",
    page_icon="📚",
    layout="wide"
)

st.title("📚 스캔북 OCR & AI 대화 문서 정돈 변환기")
st.write(r"Gemini Vision AI를 연결하여 평가원/수능 특수 수식, 스캔 이미지, **PDF 파일**을 **깨짐 없이 완벽한 라텍스(\$) 수식**으로 정돈합니다.")

# 사이드바 API 키 설정
with st.sidebar:
    st.header("⚙️ Gemini AI 설정")
    api_key = st.text_input(
        "Gemini API Key 입력:",
        type="password",
        help="Google AI Studio(aistudio.google.com)에서 발급받은 무료 API 키를 입력하세요."
    )
    st.caption("💡 API 키를 입력하시면 PDF 및 수능/모의고사 특수 수식도 깨짐 없이 100% 완벽 추출됩니다.")

tab1, tab2 = st.tabs(["📋 1. 대화/텍스트 직접 붙여넣기", "🤖 2. 수학문제지/PDF/스캔북 AI OCR (Gemini Vision)"])

# 텍스트 전처리 및 정돈 함수
def preprocess_text(text):
    if not text:
        return ""
    # \\( \\) 및 \\[ \\] 형태를 \$ \$ 및 \\[ \\] 로 통일하여 처리 안정성 향상
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

            // 1. 디스플레이 수식 (\\[ ... \\]) 보호 및 미리 KaTeX 렌더링
            let protectedText = markdownText.replace(/\\$\\$([\\s\\S]+?)\\$\\$/g, (match, math) => {{
                try {{
                    const html = katex.renderToString(math.trim(), {{ displayMode: true, throwOnError: false }});
                    mathBlocks.push(html);
                    return `\\n\\n___MATH_BLOCK_${{mathBlocks.length - 1}}___\\n\\n`;
                }} catch (e) {{
                    return match;
                }}
            }});

            // 2. 인라인 수식 (\\( ... \\)) 보호 및 미리 KaTeX 렌더링
            protectedText = protectedText.replace(/\\$([^\\$\\n]+?)\\$/g, (match, math) => {{
                try {{
                    const html = katex.renderToString(math.trim(), {{ displayMode: false, throwOnError: false }});
                    mathBlocks.push(html);
                    return `___MATH_INLINE_${{mathBlocks.length - 1}}___`;
                }} catch (e) {{
                    return match;
                }}
            }});

            // 3. 마크다운 파싱 (수식이 이미 보호되었으므로 _, ^, \\ 등이 절대 깨지지 않음)
            let htmlContent = marked.parse(protectedText);

            // 4. 렌더링된 KaTeX HTML 복원
            mathBlocks.forEach((renderedHtml, index) => {{
                const blockPlaceholder = `<p>___MATH_BLOCK_${{index}}___</p>`;
                if (htmlContent.includes(blockPlaceholder)) {{
                    htmlContent = htmlContent.replace(blockPlaceholder, `<div class="katex-display">${{renderedHtml}}</div>`);
                }} else {{
                    htmlContent = htmlContent.replace(`___MATH_BLOCK_${{index}}___`, `<div class="katex-display">${{renderedHtml}}</div>`);
                }}
                htmlContent = htmlContent.replace(`___MATH_INLINE_${{index}}___`, renderedHtml);
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

# Gemini AI로 이미지/PDF 처리하는 함수
def extract_with_gemini_vision(uploaded_file, api_key):
    if not HAS_GENAI:
        return "오류: google-generativeai 라이브러리가 설치되지 않았습니다. requirements.txt를 확인해 주세요."
    if not api_key:
        return "⚠️ 왼쪽 사이드바에 Gemini API Key를 입력하셔야 진행할 수 있습니다!"
    
    try:
        genai.configure(api_key=api_key)
        
        # 1. API 키로 사용 가능한 모델 목록을 동적으로 가져옵니다.
        candidate_models = []
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    if 'flash' in m.name:
                        candidate_models.insert(0, m.name)
                    else:
                        candidate_models.append(m.name)
        except Exception:
            pass
            
        # 예비 모델 이름 지정
        fallback_models = [
            'models/gemini-1.5-flash-latest',
            'models/gemini-1.5-flash',
            'models/gemini-2.0-flash-exp',
            'gemini-1.5-flash',
            'gemini-1.5-pro'
        ]
        
        for fb in fallback_models:
            if fb not in candidate_models:
                candidate_models.append(fb)

        file_bytes = uploaded_file.getvalue()
        file_type = uploaded_file.name.split(".")[-1].lower()
        
        if file_type == "pdf":
            content_part = {
                "mime_type": "application/pdf",
                "data": file_bytes
            }
        else:
            mime_map = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}
            content_part = {
                "mime_type": mime_map.get(file_type, "image/jpeg"),
                "data": file_bytes
            }

        prompt = (
            "이 파일(이미지 또는 PDF 문서)에 포함된 모든 글자와 수학 문제, 수식을 정확하게 읽어서 마크다운 형태로 추출해 줘.\n"
            "규칙:\n"
            "1. 모든 수학 기호, 분수, 루트, 지수, 변수 등은 LaTeX 수식 태그인 `$수식$` (문장 속 수식) 또는 `$$수식$$` (독립 수식) 형태로 정확하게 변환해 줘.\n"
            "2. 보기 선택지(①, ②, ③, ④, ⑤ 등)의 수식이나 숫자도 `$1$`, `$2$` 처럼 `$수식$` 태그로 일관되게 감싸 줘.\n"
            "3. 문단 번호(1., 2. 등)나 문제는 정갈하게 줄바꿈하여 가독성 높게 배치해 줘.\n"
            "4. 불필요한 서문이나 인사말 없이 오직 추출 및 정돈된 마크다운 내용만 출력해 줘."
        )

        last_error = None
        for m_name in candidate_models:
            try:
                model = genai.GenerativeModel(m_name)
                response = model.generate_content([prompt, content_part])
                return response.text
            except Exception as e:
                last_error = e
                continue
                
        return f"Gemini Vision 처리 중 오류 발생: {last_error}"
    except Exception as e:
        return f"Gemini Vision 처리 중 오류 발생: {e}"

# --- 탭 2: AI Vision OCR (PDF & 이미지 지원) ---
with tab2:
    st.subheader("🤖 Gemini Vision AI로 수학 문제지 PDF/이미지 깨짐 없이 추출하기")
    
    if not api_key:
        st.warning("👈 왼쪽 사이드바에서 **Gemini API Key**를 입력해 주세요! (무료 발급: aistudio.google.com)")

    uploaded_file = st.file_uploader(
        "스캔한 책/수학 문제지 파일(PDF, PNG, JPG)을 선택하세요:",
        type=["pdf", "png", "jpg", "jpeg"]
    )

    if uploaded_file is not None:
        st.info(f"📄 업로드된 파일: **{uploaded_file.name}**")
        
        if st.button("🚀 Gemini Vision AI로 PDF/이미지 글자 및 수식 추출하기"):
            with st.spinner("✨ Gemini AI가 PDF/이미지의 글자와 수식을 읽어내고 있습니다..."):
                extracted_result = extract_with_gemini_vision(uploaded_file, api_key)
                st.session_state["extracted_ocr"] = extracted_result

        if "extracted_ocr" in st.session_state and st.session_state["extracted_ocr"]:
            st.divider()
            st.success("🎉 AI 추출 완료! 추출된 마크다운 원본과 정돈 미리보기를 확인해 보세요.")
            
            col_ocr1, col_ocr2 = st.columns(2)
            with col_ocr1:
                st.write("##### ✏️ AI 추출 마크다운 (편집 가능)")
                edited_ocr = st.text_area(
                    "추출된 텍스트:",
                    value=st.session_state["extracted_ocr"],
                    height=500
                )
                if st.button("📋 이 텍스트를 1번 탭(PDF 저장 영역)으로 보낼까요?"):
                    st.session_state["input_text"] = edited_ocr
                    st.toast("1번 탭으로 정돈된 텍스트가 전달되었습니다!")

            with col_ocr2:
                st.write("##### ✨ 정돈된 문서 미리보기")
                cleaned_ocr = preprocess_text(edited_ocr)
                markdown_json_str = json.dumps(cleaned_ocr)
                html_code = HTML_TEMPLATE.format(markdown_json=markdown_json_str)
                components.html(html_code, height=520, scrolling=True)
