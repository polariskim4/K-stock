import streamlit as st
import yfinance as yf
import pandas as pd
import FinanceDataReader as fdr

# 페이지 설정
st.set_page_config(layout="wide", page_title="주식 분석 대시보드")
st.title("📈 주식 벤치마크 & 분석 도구")

# --- 종목 리스트 로드 (코스닥 검색 강화) ---
@st.cache_data(show_spinner=False)
def get_reliable_stock_list():
    df_final = pd.DataFrame()
    # 명시적으로 KOSPI, KOSDAQ을 각각 가져와서 합칩니다.
    for market in ['KOSPI', 'KOSDAQ', 'KONEX']:
        try:
            temp = fdr.StockListing(market)
            df_final = pd.concat([df_final, temp], ignore_index=True)
        except:
            continue
    
    # 만약 위 과정이 모두 실패했다면 KRX 통합 리스트 시도
    if df_final.empty:
        try:
            df_final = fdr.StockListing('KRX')
        except:
            # 최종 비상용 데이터 (주요 코스닥 종목 추가)
            df_final = pd.DataFrame([
                {"Symbol": "005930", "Name": "삼성전자"},
                {"Symbol": "196170", "Name": "알테오젠"},
                {"Symbol": "247540", "Name": "에코프로비엠"},
                {"Symbol": "074430", "Name": "오이솔루션"}
            ])

    if not df_final.empty:
        df_final['SearchName'] = df_final['Name'].str.replace(r'\s+', '', regex=True).str.upper()
    return df_final

total_list = get_reliable_stock_list()

# --- 포맷팅 함수들 ---
def format_currency(val):
    if val is None or pd.isna(val) or val == 0: return "-"
    val = int(val)
    cho, eok = val // 10000, val % 10000
    if cho > 0: return f"{cho:,.0f}조 {str(eok).zfill(4)}억"
    return f"{eok:,.0f}억"

def format_number(val, is_percent=False):
    if val is None or pd.isna(val): return "-"
    if is_percent: return f"{round(val * 100, 1):,}%"
    return f"{round(val, 1):,}"

@st.cache_data(ttl=3600, show_spinner=False)
def get_stock_info(ticker_symbol):
    if not ticker_symbol: return None
    # 코스피(.KS), 코스닥(.KQ) 모두 확인
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

# --- 1. 벤치마크 섹션 (기존과 동일) ---
st.header("📋 주요 종목 벤치마크 (시총순 정렬)")
bench_tickers = {
    "삼성전자": "005930", "SK하이닉스": "000660", "현대자동차": "005380",
    "LG에너지솔루션": "373220", "HD현대중공업": "329180", "KB금융": "105560",
    "삼성바이오로직스": "207940", "NAVER": "035420", "SK이노베이션": "096770",
    "두산에너빌리티": "034020", "알테오젠": "196170", "에코프로비엠": "247540", "리노공업": "058470"
}

bench_results = []
for name, code in bench_tickers.items():
    res = get_stock_info(code)
    if res:
        res['종목명'] = name
        bench_results.append(res)

if bench_results:
    df_bench = pd.DataFrame(bench_results).sort_values(by="시총", ascending=False).set_index('종목명')
    disp_df = pd.DataFrame(index=df_bench.index)
    disp_df['시총'] = df_bench['시총'].apply(format_currency)
    disp_df['매출액'] = df_bench['매출액'].apply(format_currency)
    disp_df['영업이익'] = df_bench['영업이익'].apply(format_currency)
    disp_df['P/E'] = df_bench['P/E'].apply(lambda x: format_number(x))
    disp_df['PEG'] = df_bench['PEG'].apply(lambda x: format_number(x))
    disp_df['마진(%)'] = df_bench['마진'].apply(lambda x: format_number(x, True))
    disp_df['매출액 성장률(%)'] = df_bench['매출액 성장률'].apply(lambda x: format_number(x, True))
    disp_df['이익 성장률(%)'] = df_bench['이익 성장률'].apply(lambda x: format_number(x, True))
    st.dataframe(disp_df, use_container_width=True)

st.write("---")

# --- 2. 종목 상세 조회 (코스닥 검색 개선) ---
st.header("🔍 종목 상세 조회")
user_input = st.text_input("종목명 또는 코드 6자리를 입력하세요", "오이솔루션")

if user_input:
    target_code = None
    clean_input = user_input.replace(" ", "").upper()
    
    # 1. 숫자인 경우
    if clean_input.isdigit() and len(clean_input) == 6:
        target_code = clean_input
    # 2. 한글명 검색
    elif not total_list.empty:
        match = total_list[total_list['SearchName'] == clean_input]
        if not match.empty:
            target_code = match.iloc[0]['Symbol']
        else:
            # 부분 일치 검색 시도 (예: '오이'만 쳐도 나오게)
            partial = total_list[total_list['SearchName'].str.contains(clean_input)]
            if not partial.empty:
                target_code = partial.iloc[0]['Symbol']
    
    if target_code:
        raw_detail = get_stock_info(target_code)
        if raw_detail:
            col1, col2 = st.columns([1, 1])
            with col1:
                st.subheader(f"📊 {user_input} 핵심 지표")
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
                st.dataframe(pd.Series(detail_data).to_frame(name="수치"), use_container_width=True)
            with col2:
                st.subheader("🔗 링크")
                st.link_button(f"{user_input} 네이버 증권 ↗", f"https://finance.naver.com/item/main.naver?code={target_code}")
        else:
            st.error("데이터를 찾을 수 없습니다. 종목 코드가 맞는지 확인해 주세요.")
    else:
        st.error(f"'{user_input}'을(를) 종목 리스트에서 찾을 수 없습니다.")
