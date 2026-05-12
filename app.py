import streamlit as st
import yfinance as yf
import pandas as pd

# 페이지 설정
st.set_page_config(layout="wide", page_title="주식 분석 대시보드")
st.title("📈 주식 벤치마크 & 분석 도구")

# 벤치마크 종목 설정
bench_tickers = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "현대자동차": "005380.KS",
    "두산에너빌리티": "034020.KS"
}

def format_number(val):
    if isinstance(val, (int, float)):
        return f"{val:,.0f}" if val > 100 else f"{val:,.2f}"
    return val

def get_stock_info(ticker_symbol):
    stock = yf.Ticker(ticker_symbol)
    info = stock.info
    
    # 억 단위 환산 함수
    to_eok = lambda x: round(x / 100_000_000) if x else None

    data = {
        "시총(억)": to_eok(info.get("marketCap")),
        "P/E": info.get("forwardPE") or info.get("trailingPE"),
        "PBR": info.get("priceToBook"),
        "PEG": info.get("pegRatio"),
        "매출액(억)": to_eok(info.get("totalRevenue")),
        "영업이익(억)": to_eok(info.get("operatingCashflow")), # 간이 영업이익 대용
        "마진(%)": round(info.get("operatingMargins", 0) * 100, 2) if info.get("operatingMargins") else None,
        "매출액 성장률(%)": round(info.get("revenueGrowth", 0) * 100, 2) if info.get("revenueGrowth") else None,
        "이익 성장률(%)": round(info.get("earningsGrowth", 0) * 100, 2) if info.get("earningsGrowth") else None,
    }
    return data

# --- 1. 벤치마크 섹션 ---
st.header("📋 주요 종목 벤치마크")
if st.button('데이터 새로고침'):
    bench_data = []
    for name, ticker in bench_tickers.items():
        with st.spinner(f'{name} 데이터를 가져오는 중...'):
            info = get_stock_info(ticker)
            info['종목명'] = name
            bench_data.append(info)
    
    df_bench = pd.DataFrame(bench_data).set_index('종목명')
    # N/A 처리 및 포맷팅
    st.dataframe(df_bench.style.highlight_max(axis=0, color='#e6f3ff').format(precision=2, na_rep='-'), use_container_width=True)

st.write("---")

# --- 2. 개별 종목 상세 조회 섹션 ---
st.header("🔍 개별 종목 상세 조회")
user_input = st.text_input("종목 코드를 입력하세요 (숫자 6자리)", "005930")

if user_input:
    # 코스피/코스닥 구분 로직 (간단히 .KS 적용 후 에러 시 처리)
    target_ticker = f"{user_input}.KS"
    
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.subheader("📊 핵심 지표")
        try:
            detail = get_stock_info(target_ticker)
            # 깔끔한 출력을 위해 DataFrame으로 변환
            df_detail = pd.Series(detail).to_frame(name="수치")
            st.table(df_detail)
        except Exception as e:
            st.error("데이터를 불러올 수 없습니다. 코드를 확인하세요.")
            
    with col2:
        st.subheader("📅 네이버 월봉 차트")
        # 최신 네이버 이미지 서버 주소
        chart_url = f"https://ssl.pstatic.net/imgstock/chart3/mobile/candle/month/{user_input}.png?{pd.Timestamp.now().timestamp()}"
        st.image(chart_url, caption=f"종목코드 {user_input} 월봉 데이터", use_container_width=True)
