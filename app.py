import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
from fpdf import FPDF

st.set_page_config(page_title="연차 자동 계산기", layout="wide")

# 스타일 (B버전 깔끔 UI)
st.markdown("""
    <style>
        .result-box {
            padding: 20px;
            border-radius: 12px;
            background-color: #1e1e1e;
            border: 1px solid #333;
            margin-top: 20px;
        }
        .section-title {
            font-size: 20px;
            margin-top: 15px;
            margin-bottom: 8px;
            font-weight: 600;
        }
    </style>
""", unsafe_allow_html=True)


# ------------------------------------
# 연차 계산 함수
# ------------------------------------
def calculate_leave(start_date, end_date):
    months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)

    data = []
    fiscal_data = []

    # 입사일 기준 발생일자(매년)
    for i in range(1, 6):
        year = start_date.year + (i - 1)
        date = datetime(year, start_date.month, start_date.day)
        amount = 11 + (i - 1) if i > 1 else 11
        data.append([f"{i}년차", date.strftime("%Y-%m-%d"), amount])

    df_in = pd.DataFrame(data, columns=["근속년수", "발생일자", "발생 연차"])

    # 회계연도 기준 발생일자(매년 1월)
    for i in range(1, 6):
        fiscal_date = datetime(start_date.year + (i - 1), 1, 1)
        amount_f = 11 + (i - 1)
        fiscal_data.append([f"{i}년차", fiscal_date.strftime("%Y-%m-%d"), amount_f])

    df_fiscal = pd.DataFrame(fiscal_data, columns=["근속년수", "발생일자", "발생 연차"])

    total_in = df_in["발생 연차"].sum()
    total_fiscal = df_fiscal["발생 연차"].sum()

    summary = pd.DataFrame({
        "구분": ["입사일 기준 연차 합계", "회계연도 기준 연차 합계"],
        "값": [total_in, total_fiscal]
    })

    return months, df_in, df_fiscal, summary


# ------------------------------------
# 엑셀 다운로드
# ------------------------------------
def download_excel(df1, df2, df3):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df1.to_excel(writer, sheet_name='입사일 기준', index=False)
        df2.to_excel(writer, sheet_name='회계연도 기준', index=False)
        df3.to_excel(writer, sheet_name='요약', index=False)
    return buffer.getvalue()


# ------------------------------------
# PDF 다운로드 (전체 테이블 A버전)
# ------------------------------------
def download_pdf(df1, df2, df3):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font('Nanum', '', 'fonts/NanumGothic.ttf', uni=True)
    pdf.set_font('Nanum', size=12)

    pdf.cell(0, 10, "연차 계산 결과", ln=True)

    def add_table(df, title):
        pdf.ln(5)
        pdf.set_font('Nanum', size=11)
        pdf.cell(0, 8, title, ln=True)
        pdf.set_font('Nanum', size=9)

        col_width = 45
        for col in df.columns:
            pdf.cell(col_width, 8, col, border=1)
        pdf.ln()

        for row in df.itertuples(index=False):
            for cell in row:
                pdf.cell(col_width, 8, str(cell), border=1)
            pdf.ln()

    add_table(df1, "[입사일 기준]")
    add_table(df2, "[회계연도 기준]")
    add_table(df3, "[요약]")

    return pdf.output(dest='S').encode('latin-1')


# ------------------------------------
# UI 시작
# ------------------------------------
st.title("💼 연차 자동 계산기")

start = st.date_input("입사일을 선택하세요", value=datetime(2021, 1, 1))
end = st.date_input("퇴직일 (없으면 오늘 기준 계산)", value=datetime.today())

if st.button("연차 계산하기"):
    months, df_in, df_fiscal, df_summary = calculate_leave(start, end)

    st.success("연차 계산이 완료되었습니다 😄")

    st.markdown('<div class="result-box">', unsafe_allow_html=True)

    # 근속개월
    st.markdown('<div class="section-title">근속 개월</div>', unsafe_allow_html=True)
    st.metric(label="총 근속개월", value=f"{months}개월")

    # 입사일 기준
    st.markdown('<div class="section-title">입사일 기준 연차</div>', unsafe_allow_html=True)
    st.dataframe(df_in, use_container_width=True)

    # 회계연도 기준
    st.markdown('<div class="section-title">회계연도 기준 연차</div>', unsafe_allow_html=True)
    st.dataframe(df_fiscal, use_container_width=True)

    # 요약
    st.markdown('<div class="section-title">요약</div>', unsafe_allow_html=True)
    st.dataframe(df_summary, use_container_width=True)

    # 다운로드 버튼
    excel_file = download_excel(df_in, df_fiscal, df_summary)
    pdf_file = download_pdf(df_in, df_fiscal, df_summary)

    st.download_button(
        label="📥 엑셀 파일 다운로드",
        data=excel_file,
        file_name="연차계산.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.download_button(
        label="📄 PDF 다운로드",
        data=pdf_file,
        file_name="연차계산.pdf",
        mime="application/pdf"
    )

    st.markdown('</div>', unsafe_allow_html=True)
