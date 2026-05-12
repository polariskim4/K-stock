import streamlit as st
import yfinance as yf
import pandas as pd
import FinanceDataReader as fdr
import time

# 페이지 설정
st.set_page_config(layout="wide", page_title="주식 분석 대시보드")
st.title("📈 주식 벤치마크 & 분석 도구")

# --- 종목 리스트 로드 로직 개선 ---
@st.cache_data(show_spinner=False)
def get_total_list():
    try:
        # KOSPI와 KOSDAQ을 각각 불러와 명시적으로 합침
        df_ks = fdr.StockListing('KOSPI')
        df_kq = fdr.StockListing('KOSDAQ')
        df = pd.concat([df_ks, df_kq], ignore_index=True)
        
        # 검색용 전처리: 이름에서 공백 제거
        df['Name_Clean'] = df['Name'].str.replace(" ", "")
        return df[['Symbol', 'Name', 'Name_Clean']]
    except:
        # 비상용 기본 리스트
        return pd.DataFrame([
            {"Symbol": "005930", "Name": "삼성전자", "Name_Clean": "삼성전자"},
            {"Symbol": "000660", "Name": "SK하이닉스", "Name_Clean": "SK하이닉스"}
        ])

total_list = get_total_list()

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
    
    # 코스피(.KS)와 코스닥(.KQ) 둘 다 시도
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

# --- 1. 벤치마크 ---
st.header("📋 주요 종목 벤치마크")
# 생략된 벤치마크 로직 (이전과 동일)

# --- 2. 종목 상세 조회 (오이솔루션/가온칩스 해결) ---
st.header("🔍 종목 상세 조회")
user_input = st.text_input("종목명 또는 코드 6자리를 입력하세요", "오이솔루션")

if user_input:
    target_code = None
    clean_input = user_input.replace(" ", "") # 입력값 공백 제거
    
    if clean_input.isdigit() and len(clean_input) == 6:
        target_code = clean_input
    else:
        # 공백을 제거한 이름으로 매칭 시도
        match = total_list[total_list['Name_Clean'] == clean_input]
        if not match.empty:
            target_code = match.iloc[0]['Symbol']
    
    if target_code:
        col1, col2 = st.columns([1, 1])
        with st.spinner(f"'{user_input}' 정보를 가져오고 있습니다..."):
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
                # 우측 정렬 적용
                st.dataframe(pd.Series(detail_data).to_frame(name="수치"), 
                             column_config={"수치": st.column_config.Column(alignment="right")}, 
                             use_container_width=True)
            else:
                st.error("데이터 로드 실패. 야후 서버 연결을 확인해 주세요.")
                
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
