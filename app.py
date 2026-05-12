import streamlit as st
import yfinance as yf
import pandas as pd

# 페이지 설정
st.set_page_config(layout="wide", page_title="주식 분석 대시보드")
st.title("📈 주식 벤치마크 & 분석 도구")

# 1. 벤치마크 종목 리스트 (삼성전자, SK하이닉스, 현대차, 두산에너빌리티, 대한광통신)
# 한국 종목은 뒤에 .KS(코스피) 또는 .KQ(코스닥)을 붙여야 합니다.
bench_tickers = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "현대자동차": "005380.KS",
    "두산에너빌리티": "034020.KS",
    "대한광통신": "010170.KS"
}

def get_stock_info(ticker_symbol):
    stock = yf.Ticker(ticker_symbol)
    info = stock.info
    
    # 데이터 추출 (일부 항목은 API 제공 상황에 따라 None일 수 있음)
    data = {
        "시총(억)": round(info.get("marketCap", 0) / 100000000) if info.get("marketCap") else "N/A",
        "P/E": info.get("forwardPE", "N/A"),
        "PBR": info.get("priceToBook", "N/A"),
        "PEG": info.get("pegRatio", "N/A"),
        "매출액": info.get("totalRevenue", "N/A"),
        "영업이익": info.get("operatingCashflow", "N/A"), # yfinance에서 영업이익은 info 항목별 확인 필요
        "마진(%)": round(info.get("operatingMargins", 0) * 100, 2) if info.get("operatingMargins") else "N/A",
        "매출액 성장률(%)": round(info.get("revenueGrowth", 0) * 100, 2) if info.get("revenueGrowth") else "N/A",
        "이익 성장률(%)": round(info.get("earningsGrowth", 0) * 100, 2) if info.get("earningsGrowth") else "N/A",
    }
    return data

# --- 2. 벤치마크 섹션 ---
st.header("📋 주요 종목 벤치마크")
if st.button('데이터 불러오기'):
    bench_data = []
    for name, ticker in bench_tickers.items():
        info = get_stock_info(ticker)
        info['종목명'] = name
        bench_data.append(info)
    
    df_bench = pd.DataFrame(bench_data).set_index('종목명')
    st.table(df_bench)

st.write("---")

# --- 3. 종목 티커 입력 섹션 ---
st.header("🔍 개별 종목 상세 조회")
user_input = st.text_input("종목 코드를 입력하세요 (예: 005930)", "005930")

if user_input:
    # 한국 종목 형식으로 변환
    formatted_ticker = f"{user_input}.KS"
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("기본 지표")
        try:
            detail_info = get_stock_info(formatted_ticker)
            st.json(detail_info)
        except:
            st.error("데이터를 불러올 수 없습니다. 티커를 확인하세요.")
            
    with col2:
        st.subheader("네이버 증권 월봉 차트")
        # 네이버 금융 차트 이미지 URL (월봉: month)
        chart_url = f"https://ssl.pstatic.net/imgstock/chart3/mobile/candle/month/{user_input}.png"
        st.image(chart_url, use_column_width=True)
