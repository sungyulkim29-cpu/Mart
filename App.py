import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="마트 3D 탈출 게임", layout="wide")

st.title("🛒 마트 3D 탈출 게임")
st.caption("패스워드 순서: ○ (파랑) -> □ (빨강) -> ♤ (노랑) -> ♧ (초록)")

# html 파일 읽기
try:
    with open("index.html", "r", encoding="utf-8") as f:
        html_code = f.read()
    
    # 3D Canvas 렌더링
    components.html(html_code, height=700)
except FileNotFoundError:
    st.error("index.html 파일을 찾을 수 없습니다. 동일한 경로에 위치시켜 주세요.")
