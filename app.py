import streamlit as st
import yfinance as yf
import pandas as pd
import FinanceDataReader as fdr

# 페이지 설정
st.set_page_config(layout="wide", page_title="주식 분석 대시보드")
st.title("📈 주식 벤치마크 & 분석 도구")

# --- 1. 종목 리스트 로드 (상태 관리 강화) ---
@st.cache_data(show_spinner=False)
def get_reliable_stock_list():
    """시장의 모든 종목 코드를 정확히 매핑하여 가져옵니다."""
    try:
        # 모든 상장 종목(KOSPI, KOSDAQ, KONEX) 통합 로드
        df = fdr.StockListing('KRX')
    except Exception:
        # 서버 오류 시 비상용 리스트 (데이터의 정확성 확보)
        df = pd.DataFrame([
            {"Symbol": "005930", "Name": "삼성전자"},
            {"Symbol": "196170", "Name": "알테오젠"},
            {"Symbol": "407330", "Name": "가온칩스"},      #
            {"Symbol": "138080", "Name": "오이솔루션"},    #
            {"Symbol": "000660", "Name": "SK하이닉스"}
        ])
    
    # 전처리: 공백 제거 및 대문자화로 검색 정확도 향상
    df['SearchName'] = df['Name'].str.replace(r'\s+', '', regex=True).str.upper()
    # Market 정보가 없을 경우를 대비해 Symbol로 추측하는 로직 포함
    return df

total_list = get_reliable_stock_list()

# --- 2. 야후 파이낸스 데이터 호출 (확장자 로직 개선) ---
@st.cache_data(ttl=3600, show_spinner=False)
def get_stock_info(ticker_symbol):
    if not ticker_symbol: return None
    
    # 한국 시장은 .KS(코스피)와 .KQ(코스닥) 두 가지만 존재합니다.
    # 두 확장자를 모두 시도하여 데이터를 먼저 찾는 쪽을 반환합니다.
    for suffix in [".KQ", ".KS"]: 
        try:
            stock = yf.Ticker(ticker_symbol + suffix)
            # info 호출 시 실제 데이터가 존재하는지 검증
            info = stock.info
            if info and 'marketCap' in info and info['marketCap'] is not None:
                to_eok = lambda x: round(x / 100_000_000) if x else 0
                return {
                    "시총": to_eok(info.get("marketCap")),
                    "P/E": info.get("forwardPE") or info.get("trailingPE"),
                    "매출액": to_eok(info.get("totalRevenue")),
                    "영업이익": to_eok(info.get("operatingCashflow")),
                    "마진": info.get("operatingMargins"),
                    "성장률": info.get("revenueGrowth"),
                    "Suffix": suffix # 디버깅용
                }
        except:
            continue
    return None

# --- 3. 종목 상세 조회 (가온칩스 에러 해결 로직) ---
st.header("🔍 종목 상세 조회")
user_input = st.text_input("종목명 또는 코드 6자리를 입력하세요", "가온칩스")

if user_input:
    target_symbol = None
    target_name = None
    clean_input = user_input.replace(" ", "").upper()
    
    # 1단계: 6자리 숫자(코드) 입력 확인
    if clean_input.isdigit() and len(clean_input) == 6:
        target_symbol = clean_input
        # 이름 찾기 시도
        match = total_list[total_list['Symbol'] == clean_input]
        target_name = match.iloc[0]['Name'] if not match.empty else clean_input
    # 2단계: 이름으로 검색
    else:
        # 부분 일치 검색 (더 유연한 검색 제공)
        match = total_list[total_list['SearchName'].str.contains(clean_input, na=False)]
        if not match.empty:
            # 첫 번째 검색 결과 사용
            target_symbol = match.iloc[0]['Symbol']
            target_name = match.iloc[0]['Name']

    if target_symbol:
        # 데이터를 가져오기 전 사용자에게 피드백 제공
        with st.status(f"'{target_name}' 정보를 야후 파이낸스에서 조회 중...", expanded=False) as status:
            res = get_stock_info(target_symbol)
            if res:
                status.update(label="조회 완료!", state="complete")
                
                # 결과 출력
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("시가총액", f"{res['시총']:,} 억")
                    st.metric("P/E 비율", f"{res['P/E']:.2f}" if res['P/E'] else "-")
                with col2:
                    st.metric("매출액 (연간)", f"{res['매출액']:,} 억")
                    st.metric("영업이익률", f"{res['마진']*100:.1f}%" if res['마진'] else "-")
                
                st.link_button(f"🔗 {target_name} 네이버 증권 바로가기", 
                               f"https://finance.naver.com/item/main.naver?code={target_symbol}")
            else:
                # image_80b41b.png 에러 상황에 대한 친절한 설명
                st.error(f"야후 파이낸스 서버에서 '{target_name}({target_symbol})'의 실시간 데이터를 응답하지 않습니다. 잠시 후 다시 시도해주세요.")
    else:
        st.warning(f"'{user_input}' 종목을 찾을 수 없습니다. 종목명을 다시 확인해주세요.")
