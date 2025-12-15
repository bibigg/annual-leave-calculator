import streamlit as st
import pandas as pd
from datetime import date, datetime
import io
from fpdf import FPDF
import os


# ---------------------------------------------------
# 날짜 차이 계산 (개월 수)
# ---------------------------------------------------
def months_between(start_date, end_date):
    return (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)


# ---------------------------------------------------
# B방식(입사일 기준) – 전체 연차 계산
# ---------------------------------------------------
def calc_leave_join(start_date, end_date):
    m = months_between(start_date, end_date)

    # 1년 미만 월차: 11개 (입사 후 매월 1개, 최대 11)
    if m < 12:
        return m

    # 1년차: 11개월치 월차
    total = 11

    # 2년차부터: 15 → 16 → 17 … 매년 1개 증가
    years_after_1 = (m // 12) - 1
    base = 15
    for i in range(years_after_1):
        total += base + i

    return total


# ---------------------------------------------------
# A방식(회계연도 기준) – 회계연도 연차 계산
# ---------------------------------------------------
def calc_leave_fiscal(start_date, end_date):
    fiscal_year_start = date(end_date.year, 1, 1)

    if start_date > fiscal_year_start:
        months = months_between(start_date, end_date)
        if months < 12:
            return months
        return 11
    else:
        return 15


# ---------------------------------------------------
# PDF 생성 함수
# ---------------------------------------------------
def download_pdf(df_summary):

    class PDF(FPDF):
        pass

    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # 폰트 경로 자동 탐지
    font_path = os.path.join(os.path.dirname(__file__), "fonts", "NanumGothic-Regular.ttf")

    pdf.add_font("Nanum", "", font_path, uni=True)
    pdf.set_font("Nanum", "", 14)

    pdf.cell(0, 10, "연차 계산 결과", ln=True)

    for i, row in df_summary.iterrows():
        pdf.cell(0, 10, f"{row['구분']}: {row['값']}", ln=True)

    return pdf.output(dest='S').encode("latin-1")


# ---------------------------------------------------
# UI 구성
# ---------------------------------------------------
st.set_page_config(page_title="연차 자동 계산기", layout="centered")


# 타이틀
st.markdown("<h1 style='text-align:center;'>📘 연차 자동 계산기</h1>", unsafe_allow_html=True)


# 입력
st.subheader("입사일을 선택하세요")
join_date = st.date_input("입사일", date(2021, 1, 1))

st.subheader("퇴직일 (없으면 오늘 기준 계산)")
input_end_date = st.date_input("퇴직일", value=None)

end_date = input_end_date if input_end_date else date.today()


# 버튼
if st.button("연차 계산하기"):
    leave_join = calc_leave_join(join_date, end_date)
    leave_fiscal = calc_leave_fiscal(join_date, end_date)

    df = pd.DataFrame({
        "구분": ["입사일 기준 연차 합계", "회계연도 기준 연차 합계"],
        "값": [leave_join, leave_fiscal]
    })

    st.subheader("요약")

    st.table(df)

    # Excel 다운로드
    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False)
    st.download_button(
        label="📥 엑셀 파일 다운로드",
        data=excel_buffer.getvalue(),
        file_name="annual_leave.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # PDF 다운로드
    pdf_file = download_pdf(df)
    st.download_button(
        label="📄 PDF 다운로드",
        data=pdf_file,
        file_name="annual_leave.pdf",
        mime="application/pdf"
    )

    st.success("연차 계산이 완료되었습니다! 😊")
