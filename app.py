import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import datetime

# 페이지 설정
st.set_page_config(page_title="K-Stock Dashboard", layout="wide")

# 1. 시가총액 데이터 보정 함수
def get_clean_marcap():
    try:
        # KRX 전체 종목 리스트 로드
        df = fdr.StockListing('KRX')
        # 시가총액 컬럼명이 'MarCap' 또는 'Stocks' 기반으로 계산될 수 있음
        # 최신 버전에서는 'MarCap'을 우선 사용하되 없으면 0 처리
        if 'MarCap' not in df.columns:
            # 컬럼명이 다른 경우를 대비한 방어 코드
            col_name = [c for c in df.columns if '시가총액' in c or 'MarCap' in c]
            if col_name:
                df['MarCap'] = df[col_name[0]]
            else:
                df['MarCap'] = 0
        return df[['Code', 'Name', 'MarCap', 'Market']]
    except:
        return pd.DataFrame()

# 2. 금액 포맷팅 (조/억 단위)
def format_money(val):
    if not val or pd.isna(val) or val == 0: return "데이터 없음"
    if val >= 1_0000_0000_0000:
        return f"{val / 1_0000_0000_0000:.1f}조"
    return f"{val / 1_0000_0000:.1f}억"

# --- 메인 로직 ---
st.title("🇰🇷 국내 주식 벤치마크 및 상세 분석")

# 검색창
search_name = st.text_input("종목명을 입력하세요 (예: 삼성전자):", value="삼성전자")

# 데이터 가져오기
df_krx = get_clean_marcap()

if not df_krx.empty:
    # 검색 종목 정보 추출
    try:
        target_row = df_krx[df_krx['Name'] == search_name].iloc[0]
        s_code = target_row['Code']
    except IndexError:
        st.error("종목명을 찾을 수 없습니다.")
        st.stop()

    # 상단 요약 지표 (시가총액 데이터 표시 확인)
    st.header(f"📊 {search_name} ({s_code}) 핵심 지표")
    
    # 벤치마크 리스트 생성
    bench_codes = ['005930', '000660', '005380', '035420', '035720']
    if s_code not in bench_codes: bench_codes.append(s_code)
    
    summary_df = df_krx[df_krx['Code'].isin(bench_codes)].copy()
    summary_df['시가총액'] = summary_df['MarCap'].apply(format_money)
    
    st.dataframe(summary_df[['Name', 'Code', '시가총액', 'Market']], use_container_width=True, hide_index=True)

    st.divider()

    # 상세 분석 섹션
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("주가 추이 (월봉 차트)")
        # 방법 1: 네이버 증권 모바일용 차트 URL (더 안정적임)
        chart_url = f"https://ssl.pstatic.net/imgstock/chart/item/area/monthly/{s_code}.png"
        
        # 방법 2: 엑박 방지를 위한 HTML 렌더링 (Streamlit image 함수 대신 사용 가능)
        st.markdown(f'<img src="{chart_url}" style="width:100%;">', unsafe_allow_html=True)
        st.caption("제공: 네이버 증권")

    with col2:
        st.subheader("기업 요약")
        st.info(f"**현재 종목:** {search_name}\n\n**시가총액:** {format_money(target_row['MarCap'])}\n\n**상장시장:** {target_row['Market']}")
