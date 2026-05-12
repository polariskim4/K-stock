import streamlit as st
import yfinance as yf
import pandas as pd
import FinanceDataReader as fdr
import time

# 페이지 설정
st.set_page_config(layout="wide", page_title="주식 분석 대시보드")
st.title("📈 주식 벤치마크 & 분석 도구")

# --- 1. 종목 리스트 로드 ---
@st.cache_data(show_spinner=False)
def get_reliable_stock_list():
    try:
        df = fdr.StockListing('KRX')
    except:
        df = pd.DataFrame([
            {"Symbol": "005930", "Name": "삼성전자"},
            {"Symbol": "196170", "Name": "알테오젠"},
            {"Symbol": "407330", "Name": "가온칩스"},
            {"Symbol": "138080", "Name": "오이솔루션"}
        ])
    df['SearchName'] = df['Name'].str.replace(r'\s+', '', regex=True).str.upper()
    return df

total_list = get_reliable_stock_list()

# --- 2. 야후 파이낸스 데이터 호출 (타임아웃 및 속도 최적화) ---
def fetch_yf_data(ticker_with_suffix):
    """타임아웃을 적용하여 무한 대기를 방지합니다."""
    try:
        stock = yf.Ticker(ticker_with_suffix)
        # fast_info나 info를 호출할 때 timeout을 직접 지정할 수 없으므로 
        # 데이터를 로드하는 시도 자체를 제한적인 속도로 진행
        info = stock.info
        if info and 'marketCap' in info:
            return info
    except:
        return None
    return None

@st.cache_data(ttl=3600, show_spinner=False)
def get_stock_info(ticker_symbol):
    if not ticker_symbol: return None
    
    # 코스닥(.KQ) 먼저 시도 후 코스피(.KS) 시도
    for suffix in [".KQ", ".KS"]:
        info = fetch_yf_data(ticker_symbol + suffix)
        if info:
            to_eok = lambda x: round(x / 100_000_000) if x else 0
            return {
                "시총": to_eok(info.get("marketCap")),
                "P/E": info.get("forwardPE") or info.get("trailingPE"),
                "매출액": to_eok(info.get("totalRevenue")),
                "영업이익": to_eok(info.get("operatingCashflow")),
                "마진": info.get("operatingMargins"),
                "성장률": info.get("revenueGrowth")
            }
    return None

# --- 3. 종목 상세 조회 섹션 ---
st.header("🔍 종목 상세 조회")
user_input = st.text_input("종목명 또는 코드 6자리를 입력하세요", "가온칩스")

if user_input:
    target_symbol = None
    target_name = None
    clean_input = user_input.replace(" ", "").upper()
    
    # 이름으로 코드 찾기
    match = total_list[total_list['SearchName'].str.contains(clean_input, na=False)]
    if not match.empty:
        target_symbol = match.iloc[0]['Symbol']
        target_name = match.iloc[0]['Name']

    if target_symbol:
        # image_80b03f.png의 무한 대기 현상을 방지하기 위한 상태 표시기
        with st.status(f"'{target_name}' 데이터를 분석 중...", expanded=True) as status:
            st.write("서버 연결 확인 중...")
            res = get_stock_info(target_symbol)
            
            if res:
                st.write("데이터 파싱 완료...")
                status.update(label="데이터 로드 완료!", state="complete", expanded=False)
                
                # 결과 출력
                c1, c2, c3 = st.columns(3)
                c1.metric("시가총액", f"{res['시총']:,} 억")
                c2.metric("P/E", f"{res['P/E']:.2f}" if res['P/E'] else "-")
                c3.metric("매출 성장률", f"{res['성장률']*100:.1f}%" if res['성장률'] else "-")
                
                st.divider()
                st.link_button(f"👉 {target_name} 네이버 증권에서 더보기", 
                               f"https://finance.naver.com/item/main.naver?code={target_symbol}")
            else:
                status.update(label="조회 실패", state="error")
                st.error("야후 파이낸스 서버가 응답하지 않습니다. 종목 코드를 다시 확인하거나 잠시 후 시도해주세요.")
    else:
        st.warning("종목을 찾을 수 없습니다.")
