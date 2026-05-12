import streamlit as st
import yfinance as yf
import pandas as pd
import FinanceDataReader as fdr
import time

# 페이지 설정
st.set_page_config(layout="wide", page_title="주식 분석 대시보드")
st.title("📈 주식 벤치마크 & 분석 도구")

# 한글 종목명 -> 코드 변환 리스트 캐싱
@st.cache_data(show_spinner=False)
def get_krx_list():
    try:
        # KRX 전체 종목(코스피/코스닥/코넥스 포함) 리스트를 가져옴
        df = fdr.StockListing('KRX')
        return df[['Symbol', 'Name']]
    except:
        return pd.DataFrame([
            {"Symbol": "005930", "Name": "삼성전자"},
            {"Symbol": "000660", "Name": "SK하이닉스"},
            {"Symbol": "005380", "Name": "현대자동차"}
        ])

krx_list = get_krx_list()

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

# 데이터 가져오기 (코스피/코스닥 이중 검색 로직)
@st.cache_data(ttl=3600, show_spinner=False)
def get_stock_info(ticker_symbol):
    if not ticker_symbol: return None
    
    # 1. 코스피(.KS)로 먼저 시도
    # 2. 실패하거나 데이터가 부족하면 코스닥(.KQ)으로 재시도
    for suffix in [".KS", ".KQ"]:
        full_ticker = ticker_symbol + suffix
        try:
            stock = yf.Ticker(full_ticker)
            # 서버 응답 대기를 위한 루프
            for _ in range(2):
                info = stock.info
                # 필수 데이터인 marketCap이 있는지 확인
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
                time.sleep(0.3)
        except:
            continue
    return None

# --- 1. 벤치마크 (자동 로드) ---
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
    disp_df['시총'] = df_bench['시총'].apply(format_currency)
    disp_df['P/E'] = df_bench['P/E'].apply(lambda x: format_number(x))
    disp_df['PEG'] = df_bench['PEG'].apply(lambda x: format_number(x))
    disp_df['매출액'] = df_bench['매출액'].apply(format_currency)
    disp_df['영업이익'] = df_bench['영업이익'].apply(format_currency)
    disp_df['마진(%)'] = df_bench['마진'].apply(lambda x: format_number(x, True))
    disp_df['매출액 성장률(%)'] = df_bench['매출액 성장률'].apply(lambda x: format_number(x, True))
    disp_df['이익 성장률(%)'] = df_bench['이익 성장률'].apply(lambda x: format_number(x, True))
    
    st.dataframe(
        disp_df,
        column_config={col: st.column_config.Column(alignment="right") for col in disp_df.columns},
        use_container_width=True
    )

st.write("---")

# --- 2. 개별 종목 상세 조회 ---
st.header("🔍 종목 상세 조회")
user_input = st.text_input("종목명 또는 코드 6자리를 입력하세요", "오이솔루션")

if user_input:
    target_code = None
    # 1. 입력값이 숫자인지 확인
    if user_input.isdigit() and len(user_input) == 6:
        target_code = user_input
    else:
        # 2. 한글 이름으로 전체 KRX 리스트에서 코드 검색
        match = krx_list[krx_list['Name'] == user_input]
        if not match.empty:
            target_code = match.iloc[0]['Symbol']
    
    if target_code:
        col1, col2 = st.columns([1, 1])
        with st.spinner(f"'{user_input}' 정보를 가져오는 중입니다..."):
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
                detail_df = pd.Series(detail_data).to_frame(name="수치")
                st.dataframe(
                    detail_df,
                    column_config={"수치": st.column_config.Column(alignment="right")},
                    use_container_width=True
                )
            else:
                st.error("데이터 로딩 실패. 코스피/코스닥 종목이 맞는지 확인해 주세요.")
                
        with col2:
            st.subheader("🔗 네이버 증권 바로가기")
            naver_url = f"https://finance.naver.com/item/main.naver?code={target_code}"
            st.markdown(f"""
                <a href="{naver_url}" target="_blank" style="text-decoration: none;">
                    <div style="background-color: #03C75A; color: white; padding: 25px; border-radius: 12px; text-align: center; font-weight: bold; font-size: 20px;">
                        {user_input} ({target_code}) 상세 페이지 열기 ↗
                    </div>
                </a>
            """, unsafe_allow_html=True)
