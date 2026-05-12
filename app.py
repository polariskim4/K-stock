import streamlit as st
import yfinance as yf
import pandas as pd
import FinanceDataReader as fdr

# 페이지 설정
st.set_page_config(layout="wide", page_title="주식 분석 대시보드")
st.title("📈 주식 벤치마크 & 분석 도구")

# --- 1. 종목 리스트 로드 (완전 자동화 및 예외 처리) ---
@st.cache_data(show_spinner=False)
def get_reliable_stock_list():
    """KRX 전체 종목을 가져오되 실패 시 캐시된 데이터를 최대한 활용"""
    try:
        # 코스피, 코스닥, 코넥스를 한 번에 가장 확실히 가져오는 방법
        df = fdr.StockListing('KRX')
        if df.empty:
            raise ValueError("Data is empty")
    except:
        # API 호출 실패 시 최소한의 정확한 매핑 데이터 (수정 완료)
        df = pd.DataFrame([
            {"Symbol": "005930", "Name": "삼성전자"},
            {"Symbol": "196170", "Name": "알테오젠"},
            {"Symbol": "407330", "Name": "가온칩스"},      # 코드 수정
            {"Symbol": "138080", "Name": "오이솔루션"},    # 코드 수정 (아미노로직스 074430과 분리)
            {"Symbol": "074430", "Name": "아미노로직스"}
        ])
    
    # 검색용 컬럼 정리
    df['SearchName'] = df['Name'].str.replace(r'\s+', '', regex=True).str.upper()
    return df[['Symbol', 'Name', 'SearchName']]

total_list = get_reliable_stock_list()

# --- 2. 데이터 포맷팅 함수 ---
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

# --- 3. 야후 파이낸스 데이터 추출 ---
@st.cache_data(ttl=3600, show_spinner=False)
def get_stock_info(ticker_symbol):
    if not ticker_symbol: return None
    # 코스피(.KS)와 코스닥(.KQ)을 순차적으로 확인
    for suffix in [".KS", ".KQ"]:
        try:
            stock = yf.Ticker(ticker_symbol + suffix)
            info = stock.info
            # 시가총액 정보가 있는지로 유효성 확인
            if info and info.get('marketCap'):
                to_eok = lambda x: round(x / 100_000_000) if x else None
                return {
                    "Symbol": ticker_symbol,
                    "시총": to_eok(info.get("marketCap")),
                    "P/E": info.get("forwardPE") or info.get("trailingPE"),
                    "매출액": to_eok(info.get("totalRevenue")),
                    "영업이익": to_eok(info.get("operatingCashflow")),
                    "마진": info.get("operatingMargins"),
                    "매출액 성장률": info.get("revenueGrowth"),
                }
        except: continue
    return None

# --- 4. 종목 상세 조회 섹션 (가장 많이 개선된 부분) ---
st.header("🔍 종목 상세 조회")
user_input = st.text_input("종목명 또는 코드 6자리를 입력하세요", "가온칩스")

if user_input:
    target_symbol = None
    target_name = None
    clean_input = user_input.replace(" ", "").upper()
    
    # [검색 로직 1] 6자리 숫자인 경우 직접 코드 지정
    if clean_input.isdigit() and len(clean_input) == 6:
        target_symbol = clean_input
        target_name = clean_input
    # [검색 로직 2] 이름 검색 (부분 일치 허용)
    else:
        # 정확히 일치하는 것 먼저 검색
        exact_match = total_list[total_list['SearchName'] == clean_input]
        if not exact_match.empty:
            target_symbol = exact_match.iloc[0]['Symbol']
            target_name = exact_match.iloc[0]['Name']
        else:
            # 부분 일치 검색
            partial_match = total_list[total_list['SearchName'].str.contains(clean_input, na=False)]
            if not partial_match.empty:
                target_symbol = partial_match.iloc[0]['Symbol']
                target_name = partial_match.iloc[0]['Name']

    if target_symbol:
        with st.spinner(f"'{target_name}' 데이터를 가져오는 중..."):
            raw_detail = get_stock_info(target_symbol)
            
            if raw_detail:
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.subheader(f"📊 {target_name} ({target_symbol})")
                    metrics = {
                        "시가총액": format_currency(raw_detail['시총']),
                        "현재 P/E": format_number(raw_detail['P/E']),
                        "연간 매출액": format_currency(raw_detail['매출액']),
                        "영업현금흐름": format_currency(raw_detail['영업이익']),
                        "영업이익률": format_number(raw_detail['마진'], True),
                        "매출액 성장률": format_number(raw_detail['매출액 성장률'], True),
                    }
                    st.table(pd.Series(metrics).to_frame(name="수치"))
                
                with col2:
                    st.subheader("🔗 외부 링크")
                    # 네이버 증권 링크 (코드가 정확하므로 이제 아미노로직스가 뜨지 않습니다)
                    st.link_button(f"🚀 {target_name} 네이버 증권 바로가기", 
                                   f"https://finance.naver.com/item/main.naver?code={target_symbol}")
            else:
                st.error("야후 파이낸스에서 종목 정보를 찾을 수 없습니다. (상장 폐지 또는 코드 오류)")
    else:
        st.error(f"'{user_input}'에 해당하는 종목을 찾을 수 없습니다. 정확한 명칭을 입력해주세요.")
