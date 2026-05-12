import streamlit as st
import yfinance as yf
import pandas as pd
import FinanceDataReader as fdr
import time

# 페이지 설정
st.set_page_config(layout="wide", page_title="주식 분석 대시보드")
st.title("📈 주식 벤치마크 & 분석 도구")

# --- 종목 리스트 통합 로드 ---
@st.cache_data(show_spinner=False)
def get_integrated_stock_list():
    try:
        # 코스피, 코스닥 종목을 각각 명시적으로 가져와서 합칩니다.
        df_kospi = fdr.StockListing('KOSPI')
        df_kosdaq = fdr.StockListing('KOSDAQ')
        combined = pd.concat([df_kospi, df_kosdaq], ignore_index=True)
        return combined[['Symbol', 'Name']]
    except Exception as e:
        # 만약 에러가 나면 KRX 전체 리스트를 시도합니다.
        try:
            return fdr.StockListing('KRX')[['Symbol', 'Name']]
        except:
            return pd.DataFrame([{"Symbol": "005930", "Name": "삼성전자"}])

# 전역 변수로 종목 리스트 로드
total_stock_list = get_integrated_stock_list()

def format_currency(val):
    if val is None or pd.isna(val) or val == 0: return "-"
    val = int(val)
    cho, eok = val // 10000, val % 10000
    if cho > 0:
        return f"{cho:,.0f}조 {eok:,.0f}억" if eok > 0 else f"{cho:,.0f}조"
    return f"{eok:,.0f}억"

def format_number(val, is_percent=False):
    if val is None or pd.isna(val): return "-"
    if is_percent:
        return f"{round(val * 100, 1):,}%"
    return f"{round(val, 1):,}"

# --- 데이터 추출 로직 개선 ---
@st.cache_data(ttl=3600, show_spinner=False)
def get_stock_info(ticker_symbol):
    if not ticker_symbol: return None
    
    # 코스피(.KS)와 코스닥(.KQ)을 모두 시도합니다.
    suffixes = [".KS", ".KQ"]
    
    for suffix in suffixes:
        full_ticker = ticker_symbol + suffix
        try:
            stock = yf.Ticker(full_ticker)
            # info 데이터를 가져올 때까지 약간의 대기 시간을 줍니다.
            info = stock.info
            if info and info.get('marketCap'):
                to_eok = lambda x: round(x / 100_000_000) if x else None
                return {
                    "시총": to_eok(info.get("marketCap")),
                    "P/E": info.get("forwardPE") or info.get("trailingPE"),
                    "PEG": info.get("pegRatio"),
                    "매출액": to_eok(info.get("totalRevenue")),
                    "영업이익": to_eok(info.get("operatingCashflow")),
                    "마진": info.get("operatingMargins"),
                    "매출액 성장률": info.get("revenueGrowth"),
                    "이익 성장률": info.get("earningsGrowth")
                }
        except:
            continue
    return None

# --- 1. 벤치마크 ---
st.header("📋 주요 종목 벤치마크")
bench_tickers = {"삼성전자": "005930", "SK하이닉스": "000660", "현대자동차": "005380", "두산에너빌리티": "034020", "대한광통신": "010170"}
bench_results = []

for name, code in bench_tickers.items():
    res = get_stock_info(code)
    if res:
        res['종목명'] = name
        bench_results.append(res)

if bench_results:
    df_bench = pd.DataFrame(bench_results).set_index('종목명')
    disp_df = pd.DataFrame(index=df_bench.index)
    cols_to_format = ['시총', 'P/E', 'PEG', '매출액', '영업이익']
    for c in cols_to_format:
        if c in ['시총', '매출액', '영업이익']:
            disp_df[c] = df_bench[c].apply(format_currency)
        else:
            disp_df[c] = df_bench[c].apply(format_number)
    
    disp_df['마진(%)'] = df_bench['마진'].apply(lambda x: format_number(x, True))
    disp_df['매출액 성장률(%)'] = df_bench['매출액 성장률'].apply(lambda x: format_number(x, True))
    disp_df['이익 성장률(%)'] = df_bench['이익 성장률'].apply(lambda x: format_number(x, True))
    
    st.dataframe(disp_df, column_config={col: st.column_config.Column(alignment="right") for col in disp_df.columns}, use_container_width=True)

st.write("---")

# --- 2. 종목 상세 조회 (가온칩스 등 코스닥 종목 대응) ---
st.header("🔍 종목 상세 조회")
user_input = st.text_input("종목명 또는 코드 6자리를 입력하세요", "가온칩스")

if user_input:
    target_code = None
    if user_input.isdigit() and len(user_input) == 6:
        target_code = user_input
    else:
        # 통합 리스트에서 검색 (대소문자 무관하게 처리)
        match = total_stock_list[total_stock_list['Name'].str.upper() == user_input.upper()]
        if not match.empty:
            target_code = match.iloc[0]['Symbol']
    
    if target_code:
        col1, col2 = st.columns([1, 1])
        with st.spinner(f"'{user_input}'의 데이터를 야후에서 가져오는 중..."):
            raw_detail = get_stock_info(target_code)
        
        with col1:
            st.subheader("📊 핵심 지표")
            if raw_detail:
                detail_data = {
                    "시총": format_currency(raw_detail['시총']),
                    "P/E": format_number(raw_detail['P/E']),
                    "PEG": format_number(raw_detail['PEG']),
                    "매출액": format_currency(raw_detail['매출액']),
                    "영업이익": format_currency(raw_detail['영업이익']),
                    "마진(%)": format_number(raw_detail['마진'], True),
                    "매출액 성장률(%)": format_number(raw_detail['매출액 성장률'], True),
                    "이익 성장률(%)": format_number(raw_detail['이익 성장률'], True),
                }
                st.dataframe(pd.Series(detail_data).to_frame(name="수치"), column_config={"수치": st.column_config.Column(alignment="right")}, use_container_width=True)
            else:
                st.error("데이터 로드 실패. 야후 파이낸스에 해당 코드가 없거나 일시적 오류입니다.")
                
        with col2:
            st.subheader("🔗 네이버 증권 바로가기")
            st.markdown(f"""
                <a href="https://finance.naver.com/item/main.naver?code={target_code}" target="_blank" style="text-decoration: none;">
                    <div style="background-color: #03C75A; color: white; padding: 25px; border-radius: 12px; text-align: center; font-weight: bold; font-size: 20px;">
                        {user_input} ({target_code}) 상세 페이지 열기 ↗
                    </div>
                </a>
            """, unsafe_allow_html=True)
    else:
        st.error(f"'{user_input}' 종목을 찾을 수 없습니다. 정확한 이름을 입력해 주세요.")
