import streamlit as st
import yfinance as yf
import pandas as pd
import FinanceDataReader as fdr
import time

# 페이지 설정
st.set_page_config(layout="wide", page_title="주식 분석 대시보드")
st.title("📈 주식 벤치마크 & 분석 도구")

# --- 종목 리스트 로드 (필터링 강화) ---
@st.cache_data(show_spinner=False)
def get_reliable_stock_list():
    try:
        # 코스피와 코스닥을 명시적으로 합쳐서 리스트 누락 방지
        ks = fdr.StockListing('KOSPI')
        kq = fdr.StockListing('KOSDAQ')
        df = pd.concat([ks, kq], ignore_index=True)
    except:
        try:
            df = fdr.StockListing('KRX')
        except:
            return pd.DataFrame([{"Symbol": "010170", "Name": "대한광통신", "SearchName": "대한광통신"}])

    # 검색용 전처리: 모든 공백을 제거하고 대문자로 통일
    df['SearchName'] = df['Name'].str.replace(r'\s+', '', regex=True).str.upper()
    return df[['Symbol', 'Name', 'SearchName']]

total_list = get_reliable_stock_list()

# --- 데이터 포맷팅 함수 ---
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

# --- 1. 벤치마크 섹션 (상단 표) ---
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
    
    st.dataframe(disp_df, column_config={col: st.column_config.Column(alignment="right") for col in disp_df.columns}, use_container_width=True)

st.write("---")

# --- 2. 종목 상세 조회 (검색 로직 수정됨) ---
st.header("🔍 종목 상세 조회")
user_input = st.text_input("종목명 또는 코드 6자리를 입력하세요", "대한광통신")

if user_input:
    target_code = None
    # 1. 입력값에서 공백 제거 후 대문자로 변환 (검색용)
    clean_input = user_input.replace(" ", "").upper()
    
    # 2. 숫자인 경우 바로 코드 사용
    if clean_input.isdigit() and len(clean_input) == 6:
        target_code = clean_input
    # 3. 문자인 경우 SearchName 컬럼에서 비교 (공백 무시 매칭)
    else:
        match = total_list[total_list['SearchName'] == clean_input]
        if not match.empty:
            target_code = match.iloc[0]['Symbol']
        else:
            # 부분 일치 검색 (이름의 일부만 입력해도 찾을 수 있게 백업)
            partial_match = total_list[total_list['SearchName'].str.contains(clean_input)]
            if not partial_match.empty:
                target_code = partial_match.iloc[0]['Symbol']
    
    if target_code:
        col1, col2 = st.columns([1, 1])
        with st.spinner(f"'{user_input}'의 데이터를 불러오는 중..."):
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
                st.dataframe(pd.Series(detail_data).to_frame(name="수치"), 
                             column_config={"수치": st.column_config.Column(alignment="right")}, 
                             use_container_width=True)
            else:
                st.error("데이터 로드 실패.")
                
        with col2:
            st.subheader("🔗 네이버 증권 바로가기")
            st.markdown(f"""
                <a href="https://finance.naver.com/item/main.naver?code={target_code}" target="_blank" style="text-decoration: none;">
                    <div style="background-color: #03C75A; color: white; padding: 25px; border-radius: 12px; text-align: center; font-weight: bold; font-size: 20px;">
                        {user_input} ({target_code}) 상세 정보 ↗
                    </div>
                </a>
            """, unsafe_allow_html=True)
    else:
        st.error(f"'{user_input}' 종목을 찾을 수 없습니다. 이름을 다시 확인해 주세요.")
