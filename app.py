import streamlit as st
import yfinance as yf
import pandas as pd
import FinanceDataReader as fdr

# 페이지 설정
st.set_page_config(layout="wide", page_title="주식 분석 대시보드")
st.title("📈 주식 벤치마크 & 분석 도구")

# 한글 종목명 -> 코드 변환을 위한 한국 거래소 종목 리스트 캐싱
@st.cache_data
def get_krx_list():
    df = fdr.StockListing('KRX')
    return df[['Symbol', 'Name']]

krx_list = get_krx_list()

# 벤치마크 설정
bench_tickers = {
    "삼성전자": "005930",
    "SK하이닉스": "000660",
    "현대자동차": "005380",
    "두산에너빌리티": "034020",
    "대한광통신": "010170"
}

def format_currency(val):
    if val is None or pd.isna(val) or val == 0: return "-"
    val = int(val)
    cho = val // 10000
    eok = val % 10000
    if cho > 0:
        return f"{cho:,.0f}조 {eok:,.0f}억" if eok > 0 else f"{cho:,.0f}조"
    return f"{eok:,.0f}억"

def format_number(val, is_percent=False):
    if val is None or pd.isna(val): return "-"
    if is_percent:
        return f"{round(val * 100, 1):,}%"
    return f"{round(val, 1):,}"

@st.cache_data(ttl=3600)
def get_stock_info(ticker_symbol):
    # .KS 또는 .KQ가 없으면 붙여줌
    if not (ticker_symbol.endswith(".KS") or ticker_symbol.endswith(".KQ")):
        # 거래소 리스트에서 코스피/코스닥 구분 (간이)
        full_ticker = f"{ticker_symbol}.KS"
    else:
        full_ticker = ticker_symbol
        
    try:
        stock = yf.Ticker(full_ticker)
        info = stock.info
        if not info or 'marketCap' not in info:
            # 코스피로 안되면 코스닥 시도
            stock = yf.Ticker(f"{ticker_symbol}.KQ")
            info = stock.info
        
        to_eok = lambda x: round(x / 100_000_000) if x else None
        return {
            "시총": to_eok(info.get("marketCap")),
            "P/E": info.get("forwardPE") or info.get("trailingPE"),
            "PEG": info.get("pegRatio"),
            "매출액": to_eok(info.get("totalRevenue")),
            "영업이익": to_eok(info.get("operatingCashflow")),
            "마진": info.get("operatingMargins"),
            "매출액 성장률": info.get("revenueGrowth"),
            "이익 성장률": info.get("earningsGrowth"),
            "symbol": ticker_symbol.split('.')[0]
        }
    except:
        return None

# --- 1. 벤치마크 (자동 로드) ---
st.header("📋 주요 종목 벤치마크")

with st.spinner('데이터를 불러오는 중입니다...'):
    bench_list = []
    for name, code in bench_tickers.items():
        res = get_stock_info(code)
        if res:
            res['종목명'] = name
            bench_list.append(res)

    if bench_list:
        df = pd.DataFrame(bench_list).set_index('종목명')
        disp_df = pd.DataFrame(index=df.index)
        disp_df['시총'] = df['시총'].apply(format_currency)
        disp_df['P/E'] = df['P/E'].apply(lambda x: format_number(x))
        disp_df['PEG'] = df['PEG'].apply(lambda x: format_number(x))
        disp_df['매출액'] = df['매출액'].apply(format_currency)
        disp_df['영업이익'] = df['영업이익'].apply(format_currency)
        disp_df['마진(%)'] = df['마진'].apply(lambda x: format_number(x, True))
        disp_df['매출액 성장률(%)'] = df['매출액 성장률'].apply(lambda x: format_number(x, True))
        disp_df['이익 성장률(%)'] = df['이익 성장률'].apply(lambda x: format_number(x, True))
        st.table(disp_df)

st.write("---")

# --- 2. 개별 종목 상세 조회 ---
st.header("🔍 종목 상세 조회")
user_input = st.text_input("종목명 또는 코드 6자리를 입력하세요", "삼성전자")

if user_input:
    # 1. 입력값이 숫자인지 이름인지 확인하여 코드로 변환
    if user_input.isdigit():
        target_code = user_input
    else:
        # 한글 이름으로 코드 찾기
        match = krx_list[krx_list['Name'] == user_input]
        if not match.empty:
            target_code = match.iloc[0]['Symbol']
        else:
            target_code = None
            st.error(f"'{user_input}' 종목을 찾을 수 없습니다.")

    if target_code:
        col1, col2 = st.columns([1, 1])
        raw_detail = get_stock_info(target_code)
        
        with col1:
            st.subheader("📊 핵심 지표")
            if raw_detail:
                detail_formatted = {
                    "시총": format_currency(raw_detail['시총']),
                    "P/E": format_number(raw_detail['P/E']),
                    "PEG": format_number(raw_detail['PEG']),
                    "매출액": format_currency(raw_detail['매출액']),
                    "영업이익": format_currency(raw_detail['영업이익']),
                    "마진(%)": format_number(raw_detail['마진'], True),
                    "매출액 성장률(%)": format_number(raw_detail['매출액 성장률'], True),
                    "이익 성장률(%)": format_number(raw_detail['이익 성장률'], True),
                }
                st.table(pd.Series(detail_formatted).to_frame(name="수치"))
            else:
                st.warning("데이터 로딩 실패")
                
        with col2:
            st.subheader("🔗 네이버 증권 바로가기")
            naver_url = f"https://finance.naver.com/item/main.naver?code={target_code}"
            st.markdown(f"""
                <a href="{naver_url}" target="_blank" style="text-decoration: none;">
                    <div style="background-color: #03C75A; color: white; padding: 20px; border-radius: 12px; text-align: center; font-weight: bold; font-size: 20px;">
                        {user_input} ({target_code}) 상세 페이지 열기 ↗
                    </div>
                </a>
            """, unsafe_allow_html=True)
