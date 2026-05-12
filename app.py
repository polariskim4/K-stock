import streamlit as st
import yfinance as yf
import pandas as pd
import FinanceDataReader as fdr
import time

# 페이지 설정
st.set_page_config(layout="wide", page_title="주식 분석 대시보드")
st.title("📈 주식 벤치마크 & 분석 도구")

# --- 종목 리스트 로드 로직 (코스닥 검색 실패 방지용) ---
@st.cache_data(show_spinner=False)
def get_reliable_stock_list():
    """코스피와 코스닥 리스트를 각각 명시적으로 가져와 검색 정확도를 높입니다."""
    try:
        # 1. 코스피와 코스닥을 따로 불러와 병합 (가장 확실한 방법)
        ks = fdr.StockListing('KOSPI')
        kq = fdr.StockListing('KOSDAQ')
        df = pd.concat([ks, kq], ignore_index=True)
    except:
        try:
            # 2. 실패 시 통합 KRX 리스트 호출
            df = fdr.StockListing('KRX')
        except:
            # 3. 모든 API 호출 실패 시 비상용 리스트 (삼성전자 등)
            return pd.DataFrame([{"Symbol": "005930", "Name": "삼성전자", "SearchName": "삼성전자"}])

    # 검색 시 오차를 줄이기 위해 모든 공백 제거 및 대문자화
    df['SearchName'] = df['Name'].str.replace(r'\s+', '', regex=True).str.upper()
    return df[['Symbol', 'Name', 'SearchName']]

# 통합 종목 리스트 생성
total_list = get_reliable_stock_list()

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

@st.cache_data(ttl=3600, show_spinner=False)
def get_stock_info(ticker_symbol):
    """야후 파이낸스에서 코스피/코스닥 데이터를 순차 검색합니다."""
    if not ticker_symbol: return None
    
    for suffix in [".KS", ".KQ"]:
        try:
            stock = yf.Ticker(ticker_symbol + suffix)
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
        except: continue
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
    # 우측 정렬을 위해 모든 데이터를 문자열 포맷으로 변경
    disp_df['시총'] = df_bench['시총'].apply(format_currency)
    disp_df['P/E'] = df_bench['P/E'].apply(lambda x: format_number(x))
    disp_df['PEG'] = df_bench['PEG'].apply(lambda x: format_number(x))
    disp_df['매출액'] = df_bench['매출액'].apply(format_currency)
    disp_df['영업이익'] = df_bench['영업이익'].apply(format_currency)
    disp_df['마진(%)'] = df_bench['마진'].apply(lambda x: format_number(x, True))
    disp_df['매출액 성장률(%)'] = df_bench['매출액 성장률'].apply(lambda x: format_number(x, True))
    disp_df['이익 성장률(%)'] = df_bench['이익 성장률'].apply(lambda x: format_number(x, True))
    
    st.dataframe(disp_df, column_config={col: st.column_config.Column(alignment="right") for col in disp_df.columns}, use_container_width=True)

st.write("---")

# --- 2. 종목 상세 조회 (오이솔루션 등 코스닥 종목 해결) ---
st.header("🔍 종목 상세 조회")
user_input = st.text_input("종목명 또는 코드 6자리를 입력하세요", "오이솔루션")

if user_input:
    target_code = None
    # 검색어에서 공백 제거 후 비교
    clean_input = user_input.replace(" ", "").upper()
    
    if clean_input.isdigit() and len(clean_input) == 6:
        target_code = clean_input
    else:
        # SearchName 컬럼을 사용하여 정확한 이름 매칭 시도
        match = total_list[total_list['SearchName'] == clean_input]
        if not match.empty:
            target_code = match.iloc[0]['Symbol']
    
    if target_code:
        col1, col2 = st.columns([1, 1])
        with st.spinner(f"'{user_input}'의 데이터를 가져오고 있습니다..."):
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
                # 상세 지표도 우측 정렬 적용
                st.dataframe(pd.Series(detail_data).to_frame(name="수치"), 
                             column_config={"수치": st.column_config.Column(alignment="right")}, 
                             use_container_width=True)
            else:
                st.error("데이터 로드 실패. 야후 파이낸스에서 정보를 불러올 수 없습니다.")
                
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
        st.error(f"'{user_input}' 종목을 거래소 리스트에서 찾을 수 없습니다. 이름을 정확히 입력했는지 확인해 주세요.")
