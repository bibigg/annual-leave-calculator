import streamlit as st
import pandas as pd
from datetime import date, datetime
import io

# ---------------------------------------
# 유틸 함수
# ---------------------------------------

# 두 날짜 사이 개월 수 계산
def months_between(start_date, end_date):
    return (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)

# 입사일 기준 연차 총합 계산 (51개월 → 73개 등)
def calc_total_leave_by_join(months):
    total = 0
    current = date.today().replace(day=1)

    # 1년 미만 : 월 1개씩
    if months < 12:
        return months

    # 1년차 : 11개
    total += 11

    # 2년차부터 → 근속연수 기반 계산
    year_num = 2
    remaining_years = (months // 12) - 1

    while remaining_years > 0:
        if year_num == 2:
            total += 15
        elif year_num >= 3:
            total += 16
        year_num += 1
        remaining_years -= 1

    return total

# 회계연도 기준 연차 계산
def calc_total_leave_fiscal(join_date, end_date):
    fiscal_year = join_date.year
    current_year = end_date.year
    total = 0

    while fiscal_year <= current_year:
        fy_start = date(fiscal_year, 1, 1)
        fy_end = date(fiscal_year, 12, 31)

        if fiscal_year == join_date.year:
            work_months = months_between(join_date, fy_end)
            work_months += 1 if join_date.day <= fy_end.day else 0
        elif fiscal_year == end_date.year:
            work_months = months_between(fy_start, end_date)
        else:
            work_months = 12

        if work_months < 12:
            leave = min(work_months, 11)
        else:
            if fiscal_year - join_date.year == 1:
                leave = 15
            else:
                leave = 16

        total += leave
        fiscal_year += 1

    return total

# ---------------------------------------
# UI – 모바일 최적화 CSS
# ---------------------------------------

st.markdown("""
<style>
button, input, label, select {
    font-size: 18px !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------
# UI 입력
# ---------------------------------------

st.title("📘 연차 자동 계산기")

with st.form("input_form"):
    join_date = st.date_input("입사일을 선택하세요", value=date(2021, 1, 1))
    end_date = st.date_input("퇴직일 (없으면 오늘 기준 계산)", value=date.today())

    submitted = st.form_submit_button("연차 계산하기")

# ---------------------------------------
# 계산
# ---------------------------------------

if submitted:

    # 기본 계산
    months = months_between(join_date, end_date)

    leave_join = calc_total_leave_by_join(months)
    leave_fiscal = calc_total_leave_fiscal(join_date, end_date)

    # 결과 테이블
    df = pd.DataFrame({
        "구분": ["근속개월", "입사일 기준 연차", "회계연도 기준 연차"],
        "값": [months, leave_join, leave_fiscal]
    })

    st.subheader("결과")
    st.table(df)

    # ---------------------------------------
    # 엑셀 다운로드
    # ---------------------------------------
    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False)
    st.download_button(
        label="📥 엑셀 파일 다운로드",
        data=excel_buffer.getvalue(),
        file_name="annual_leave.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # ---------------------------------------
    # PDF 다운로드 (HTML → PDF 변환 없이 텍스트 PDF)
    # ---------------------------------------
    pdf_content = f"""
연차 계산 결과

입사일: {join_date}
퇴직일: {end_date}

근속개월: {months}
입사일 기준 연차: {leave_join}
회계연도 기준 연차: {leave_fiscal}
"""

    pdf_bytes = pdf_content.encode("utf-8")

    st.download_button(
        label="📄 PDF 다운로드",
        data=pdf_bytes,
        file_name="annual_leave.pdf",
        mime="application/pdf"
    )

    st.success("연차 계산이 완료되었습니다 😊")
