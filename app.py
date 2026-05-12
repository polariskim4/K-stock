import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from io import BytesIO

# 페이지 설정
st.set_page_config(layout="wide", page_title="주식 분석 대시보드")
st.title("📈 주식 벤치마크 & 분석 도구")

# 벤치마크 종목 설정
bench_tickers = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "현대자동차": "005380.KS",
    "두산에너빌리티": "034020.KS",
    "대한광통신": "010170.KS"
}

# 금액을 조, 억 단위로 변환하는 함수
def format_currency(val):
    if val is None or pd.isna(val): return "-"
    val = int(val)
    cho = val // 10000
    eok = val % 10000
    if cho > 0:
        return f"{cho}조 {eok}억" if eok > 0 else f"{cho}조"
    return f"{eok}억"

def get_stock_info(ticker_symbol):
    stock = yf.Ticker(ticker_symbol)
    info = stock.info
    
    # 기본 금액 단위: 억 (yfinance는 원 단위 제공)
    to_eok = lambda x: round(x / 100_000_000) if x else None

    data = {
        "시총": to_eok(info.get("marketCap")),
        "P/E": info.get("forwardPE") or info.get("trailingPE"),
        "PBR": info.get("priceToBook"),
        "PEG": info.get("pegRatio"),
        "매출액": to_eok(info.get("totalRevenue")),
        "영업이익": to_eok(info.get("operatingCashflow")), # 현금흐름으로 대체 혹은 None
        "마진(%)": info.get("operatingMargins"),
        "매출액 성장률(%)": info.get("revenueGrowth"),
        "이익 성장률(%)": info.get("earningsGrowth"),
    }
    return data

# --- 1. 벤치마크 섹션 ---
st.header("📋 주요 종목 벤치마크")
if st.button('데이터 새로고침'):
    bench_data = []
    for name, ticker in bench_tickers.items():
        try:
            info = get_stock_info(ticker)
            info['종목명'] = name
            bench_data.append(info)
        except:
            continue
    
    if bench_data:
        df = pd.DataFrame(bench_data).set_index('종목명')
        
        # 데이터 가공 및 소수점 한 자리 통일
        display_df = pd.DataFrame(index=df.index)
        display_df['시총'] = df['시총'].apply(format_currency)
        display_df['P/E'] = df['P/E'].apply(lambda x: f"{round(x, 1)}" if pd.notnull(x) else "-")
        display_df['PBR'] = df['PBR'].apply(lambda x: f"{round(x, 1)}" if pd.notnull(x) else "-")
        display_df['PEG'] = df['PEG'].apply(lambda x: f"{round(x, 1)}" if pd.notnull(x) else "-")
        display_df['매출액'] = df['매출액'].apply(format_currency)
        display_df['영업이익'] = df['영업이익'].apply(format_currency)
        display_df['마진(%)'] = df['마진(%)'].apply(lambda x: f"{round(x*100, 1)}%" if pd.notnull(x) else "-")
        display_df['매출액 성장률(%)'] = df['매출액 성장률(%)'].apply(lambda x: f"{round(x*100, 1)}%" if pd.notnull(x) else "-")
        display_df['이익 성장률(%)'] = df['이익 성장률(%)'].apply(lambda x: f"{round(x*100, 1)}%" if pd.notnull(x) else "-")
        
        st.table(display_df)

st.write("---")

# --- 2. 개별 종목 상세 조회 섹션 ---
st.header("🔍 개별 종목 상세 조회")
user_input = st.text_input("종목 코드를 입력하세요", "005930")

if user_input:
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.subheader("📊 핵심 지표")
        try:
            raw_detail = get_stock_info(f"{user_input}.KS")
            detail = {
                "시총": format_currency(raw_detail['시총']),
                "P/E": round(raw_detail['P/E'], 1) if raw_detail['P/E'] else "-",
                "PBR": round(raw_detail['PBR'], 1) if raw_detail['PBR'] else "-",
                "PEG": round(raw_detail['PEG'], 1) if raw_detail['PEG'] else "-",
                "매출액": format_currency(raw_detail['매출액']),
                "영업이익": format_currency(raw_detail['영업이익']),
                "마진(%)": f"{round(raw_detail['마진(%)']*100, 1)}%" if raw_detail['마진(%)'] else "-",
                "매출액 성장률(%)": f"{round(raw_detail['매출액 성장률(%)']*100, 1)}%" if raw_detail['매출액 성장률(%)'] else "-",
                "이익 성장률(%)": f"{round(raw_detail['이익 성장률(%)']*100, 1)}%" if raw_detail['이익 성장률(%)'] else "-",
            }
            st.table(pd.Series(detail).to_frame(name="수치"))
        except:
            st.error("데이터를 가져올 수 없습니다. 코스피 종목이 맞는지 확인하세요.")
            
    with col2:
        st.subheader("📅 네이버 월봉 차트")
        chart_url = f"https://ssl.pstatic.net/imgstock/chart3/mobile/candle/month/{user_input}.png"
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        try:
            response = requests.get(chart_url, headers=headers)
            if response.status_code == 200:
                st.image(BytesIO(response.content), use_container_width=True)
            else:
                st.warning("네이버 차트를 불러올 수 없습니다.")
        except:
            st.error("차트 로딩 중 오류 발생")
