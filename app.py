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
        df = fdr.StockListing('KRX')
        return df[['Symbol', 'Name']]
    except:
        # 실패 시 비상용 최소 리스트 반환
        return pd.DataFrame([
            {"Symbol": "005930", "Name": "삼성전자"},
            {"Symbol": "000660", "Name": "SK하이닉스"},
            {"Symbol": "005380", "Name": "현대자동차"}
        ])

krx_list = get_krx_list()

# 기본 벤치마크 딕셔너리
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
    cho, eok = val // 10000, val % 10000
    if cho > 0:
        return f"{cho:,.0f}조 {eok:,.0f}억" if eok > 0 else f"{cho:,.0f}조"
    return f"{eok:,.0f}억"

def format_number(val, is_percent=False):
    if val is None or pd.isna(val): return "-"
    if is_percent:
        return f"{round(val * 100, 1):,}%"
    return f"{round(val, 1):,}"

# 데이터 가져오기 (재시도 로직 추가)
@st.cache_data(ttl=3600, show_spinner=False)
def get_stock_info(ticker_symbol):
    if not ticker_symbol: return None
    
    # 코스피/코스닥 순차적 시도
    for suffix in [".KS", ".KQ"]:
        full_ticker = ticker_symbol + suffix
        try:
            stock = yf.Ticker(full_ticker)
            # info 로딩 시 타임아웃 대비 재시도 (최대 2회)
            for _ in range(2):
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
                time.sleep(0.5) # 짧은 대기 후 재시도
        except:
            continue
    return None

# --- 1. 벤치마크 (자동 로드) ---
st.header("📋 주요 종목 벤치마크")

# 벤치마크는 캐싱된 데이터를 사용하여 속도 우선
bench_results = []
for name, code in bench_tickers.items():
    res = get_stock_info(code)
    if res:
        res['종목명'] = name
        bench_results.append(res)

if bench_results:
    df_bench = pd.DataFrame(bench_results).set_index('종목명')
    disp_df = pd.DataFrame(index=df_bench.index)
    for col, func in [('시총', format_currency), ('P/E', format_number), ('PEG', format_number), 
                      ('매출액', format_currency), ('영업이익', format_currency)]:
        disp_df[col] = df_bench[col.split('(')[0]].apply(func)
    
    disp_df['마진(%)'] = df_bench['마진'].apply(lambda x: format_number(x, True))
    disp_df['매출액 성장률(%)'] = df_bench['매출액 성장률'].apply(lambda x: format_number(x, True))
    disp_df['이익 성장률(%)'] = df_bench['이익 성장률'].apply(lambda x: format_number(x, True))
    st.table(disp_df)
else:
    st.warning("현재 야후 파이낸스 서버 연결이 원활하지 않습니다. 아래 상세 조회의 '네이버 증권 바로가기'를 이용해 주세요.")

st.write("---")

# --- 2. 개별 종목 상세 조회 ---
st.header("🔍 종목 상세 조회")
user_input = st.text_input("종목명 또는 코드 6자리를 입력하세요", "삼성전자")

if user_input:
    target_code = None
    # 코드 매칭 로직
    if user_input.isdigit() and len(user_input) == 6:
        target_code = user_input
    else:
        if user_input in bench_tickers:
            target_code = bench_tickers[user_input]
        else:
            match = krx_list[krx_list['Name'] == user_input]
            if not match.empty:
                target_code = match.iloc[0]['Symbol']

    if target_code:
        col1, col2 = st.columns([1, 1])
        # 상세 데이터 로딩
        with st.spinner(f"'{user_input}' 데이터를 가져오고 있습니다..."):
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
                st.error("야후 서버에서 데이터를 가져올 수 없습니다. 아래 초록색 버튼을 눌러 네이버 증권에서 확인해 보세요.")
                
        with col2:
            st.subheader("🔗 네이버 증권 바로가기")
            naver_url = f"https://finance.naver.com/item/main.naver?code={target_code}"
            st.markdown(f"""
                <a href="{naver_url}" target="_blank" style="text-decoration: none;">
                    <div style="background-color: #03C75A; color: white; padding: 25px; border-radius: 12px; text-align: center; font-weight: bold; font-size: 20px; border: 2px solid #02a84c;">
                        {user_input} ({target_code})<br>실시간 차트 및 투자 정보 보기 ↗
                    </div>
                </a>
            """, unsafe_allow_html=True)
    else:
        st.error(f"'{user_input}' 종목을 찾을 수 없습니다. 정확한 이름을 입력해 주세요.")
