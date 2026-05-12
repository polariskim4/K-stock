import streamlit as st
import yfinance as yf
import pandas as pd
import FinanceDataReader as fdr

# 페이지 설정
st.set_page_config(layout="wide", page_title="주식 분석 대시보드")
st.title("📈 주식 벤치마크 & 분석 도구")

# 한글 종목명 -> 코드 변환 리스트 캐싱 (에러 방지용 예외 처리 추가)
@st.cache_data
def get_krx_list():
    try:
        df = fdr.StockListing('KRX')
        return df[['Symbol', 'Name']]
    except Exception as e:
        # 에러 발생 시 빈 데이터프레임 반환하여 앱 중단 방지
        return pd.DataFrame(columns=['Symbol', 'Name'])

krx_list = get_krx_list()

# 기본 벤치마크 (코드가 명확하므로 리스트 검색 없이 바로 사용)
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
    if not ticker_symbol: return None
    
    # 코스피(.KS)를 먼저 시도하고 데이터 없으면 코스닥(.KQ) 시도
    for suffix in [".KS", ".KQ"]:
        try:
            stock = yf.Ticker(ticker_symbol + suffix)
            info = stock.info
            if info and 'marketCap' in info:
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
                    "symbol": ticker_symbol
                }
        except:
            continue
    return None

# --- 1. 벤치마크 (자동 로드) ---
st.header("📋 주요 종목 벤치마크")

with st.spinner('벤치마크 데이터를 불러오는 중...'):
    bench_results = []
    for name, code in bench_tickers.items():
        res = get_stock_info(code)
        if res:
            res['종목명'] = name
            bench_results.append(res)

    if bench_results:
        df_bench = pd.DataFrame(bench_results).set_index('종목명')
        disp_df = pd.DataFrame(index=df_bench.index)
        disp_df['시총'] = df_bench['시총'].apply(format_currency)
        disp_df['P/E'] = df_bench['P/E'].apply(lambda x: format_number(x))
        disp_df['PEG'] = df_bench['PEG'].apply(lambda x: format_number(x))
        disp_df['매출액'] = df_bench['매출액'].apply(format_currency)
        disp_df['영업이익'] = df_bench['영업이익'].apply(format_currency)
        disp_df['마진(%)'] = df_bench['마진'].apply(lambda x: format_number(x, True))
        disp_df['매출액 성장률(%)'] = df_bench['매출액 성장률'].apply(lambda x: format_number(x, True))
        disp_df['이익 성장률(%)'] = df_bench['이익 성장률'].apply(lambda x: format_number(x, True))
        st.table(disp_df)
    else:
        st.info("벤치마크 데이터를 불러올 수 없습니다. 잠시 후 다시 시도해 주세요.")

st.write("---")

# --- 2. 개별 종목 상세 조회 ---
st.header("🔍 종목 상세 조회")
user_input = st.text_input("종목명 또는 코드 6자리를 입력하세요 (예: 삼성전자, 005930)", "삼성전자")

if user_input:
    target_code = None
    
    # 1. 입력이 숫자 6자리인 경우
    if user_input.isdigit() and len(user_input) == 6:
        target_code = user_input
    # 2. 입력이 한글 이름인 경우
    else:
        # 먼저 벤치마크에서 확인 (속도 빠름)
        if user_input in bench_tickers:
            target_code = bench_tickers[user_input]
        # 거래소 리스트에서 확인
        elif not krx_list.empty:
            match = krx_list[krx_list['Name'] == user_input]
            if not match.empty:
                target_code = match.iloc[0]['Symbol']
    
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
                st.warning(f"'{user_input}'의 상세 데이터를 가져올 수 없습니다.")
                
        with col2:
            st.subheader("🔗 네이버 증권 바로가기")
            naver_url = f"https://finance.naver.com/item/main.naver?code={target_code}"
            st.markdown(f"""
                <a href="{naver_url}" target="_blank" style="text-decoration: none;">
                    <div style="background-color: #03C75A; color: white; padding: 20px; border-radius: 12px; text-align: center; font-weight: bold; font-size: 20px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);">
                        {user_input} ({target_code}) 상세 페이지 열기 ↗
                    </div>
                </a>
            """, unsafe_allow_html=True)
    else:
        st.error(f"'{user_input}'에 해당하는 종목 코드를 찾을 수 없습니다.")
