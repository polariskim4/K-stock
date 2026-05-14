import streamlit as st
from pykrx import stock
import OpenDartReader  # pip install opendartreader
import pandas as pd
from datetime import datetime

st.set_page_config(layout="wide", page_title="DART 공식 데이터 분석기")

# --- 1. 설정: 발급받은 DART API 키 입력 ---
DART_API_KEY = "762f5a76c8e917dec5e3cb6a552c33cd39505cc3" # 여기에 발급받은 키를 넣으세요
dart = OpenDartReader(DART_API_KEY)

# --- 2. 데이터 추출 함수 ---
def get_official_data(ticker, name):
    try:
        # A. pykrx를 이용한 실시간급 시총 및 PER 조회 (image_e8208a.png 참고)
        today = datetime.now().strftime("%Y%m%d")
        df_fund = stock.get_market_fundamental(today, today, ticker)
        df_price = stock.get_market_cap(today, today, ticker)
        
        # B. DART를 이용한 공식 재무제표 조회 (image_e81d9e.png 참고)
        # 2023년 연간 보고서 기준 매출액, 영업이익 추출
        df_fn = dart.finstate(ticker, 2023) 
        # 재무제표 결과 중 '매출액'과 '영업이익' 행만 필터링
        revenue = df_fn[df_fn['account_nm'] == '매출액']['thstrm_amount'].values[0]
        op_profit = df_fn[df_fn['account_nm'] == '영업이익']['thstrm_amount'].values[0]

        return {
            "시총": df_price['시가총액'].values[0] // 100_000_000,
            "PER": df_fund['PER'].values[0],
            "PBR": df_fund['PBR'].values[0],
            "매출액": int(revenue) // 100_000_000,
            "영업이익": int(op_profit) // 100_000_000
        }
    except Exception as e:
        st.error(f"데이터 추출 중 오류 발생: {e}")
        return None

# --- 3. UI 화면 구성 ---
st.title("🏛️ 금감원 DART 공식 데이터 기반 분석")
target_name = st.text_input("분석할 종목명을 입력하세요", "가온칩스")

# 종목명으로 티커 변환 (pykrx 기능)
# 가장 안전하게 최근 영업일 데이터를 가져오도록 날짜를 명시합니다.
from datetime import datetime, timedelta

# 오늘 날짜를 가져오되, 안전하게 어제 날짜로 설정 (주말/휴일 대비)
target_date = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
ticker = stock.get_market_ticker_list(date=target_date, market="ALL")
name_to_ticker = {stock.get_market_ticker_name(t): t for t in ticker}

if target_name in name_to_ticker:
    code = name_to_ticker[target_name]
    
    with st.spinner('DART 공시 시스템 접속 중...'):
        data = get_official_data(code, target_name)
    
    if data:
        st.success(f"'{target_name}' 데이터 연동 성공!")
        col1, col2, col3 = st.columns(3)
        col1.metric("공식 시가총액", f"{data['시총']:,} 억")
        col2.metric("23년 매출액 (DART)", f"{data['매출액']:,} 억")
        col3.metric("23년 영업이익 (DART)", f"{data['영업이익']:,} 억")
        
        col4, col5 = st.columns(2)
        col4.metric("PER (현재)", f"{data['PER']:.2f} 배")
        col5.metric("PBR (현재)", f"{data['PBR']:.2f} 배")
else:
    st.warning("상장된 종목명을 정확히 입력해주세요.")
