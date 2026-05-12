import streamlit as st
import yfinance as yf
import pandas as pd

# 페이지 설정
st.set_page_config(layout="wide", page_title="주식 분석 대시보드")
st.title("📈 주식 벤치마크 & 분석 도구")

# 1. 벤치마크 종목 설정
bench_tickers = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "현대자동차": "005380.KS",
    "두산에너빌리티": "034020.KS",
    "대한광통신": "010170.KQ"
}

# 금액 변환 함수 (조, 억 단위 + 콤마)
def format_currency(val):
    if val is None or pd.isna(val) or val == 0: return "-"
    val = int(val)
    cho = val // 10000
    eok = val % 10000
    if cho > 0:
        return f"{cho:,.0f}조 {eok:,.0f}억" if eok > 0 else f"{cho:,.0f}조"
    return f"{eok:,.0f}억"

# 비율 및 일반 숫자 변환 함수 (콤마 + 소수점 한 자리)
def format_number(val, is_percent=False):
    if val is None or pd.isna(val): return "-"
    if is_percent:
        return f"{round(val * 100, 1):,}%"
    return f"{round(val, 1):,}"

@st.cache_data(ttl=3600) # 한 시간 동안 데이터 캐싱하여 속도 향상
def get_stock_info(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        info = stock.info
        if not info or 'marketCap' not in info: return None
        
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
            "symbol": info.get("symbol")
        }
    except:
        return None

# --- SECTION 1: 주요 종목 벤치마크 (자동 로드) ---
st.header("📋 주요 종목 벤치마크")

bench_list = []
for name, ticker in bench_tickers.items():
    res = get_stock_info(ticker)
    if res:
        res['종목명'] = name
        bench_list.append(res)

if bench_list:
    df = pd.DataFrame(bench_list).set_index('종목명')
    disp_df = pd.DataFrame(index=df.index)
    disp_df['시총'] = df['시총'].apply(format_currency)
    disp_df['P/E'] = df['P/E'].apply(lambda x: format_number(x))
    disp_df['PEG'] = df['PEG'].apply(lambda x: format_number(x))
    disp_df['매출액'] = df['매출액'].apply(format_currency)
    disp_df['영업이익'] = df['영업이익'].apply(format_currency)
    disp_df['마진(%)'] = df['마진'].apply(lambda x: format_number(x, True))
    disp_df['매출액 성장률(%)'] = df['매출액 성장률'].apply(lambda x: format_number(x, True))
    disp_df['이익 성장률(%)'] = df['이익 성장률'].apply(lambda x: format_number(x, True))
    
    st.table(disp_df)

st.write("---")

# --- SECTION 2: 개별 종목 상세 조회 (이름/코드 겸용) ---
st.header("🔍 종목 상세 조회")
user_input = st.text_input("종목명 또는 코드 6자리를 입력하세요", "삼성전자")

# 한글 이름을 코드로 변환하기 위한 매핑 (벤치마크 외 종목 검색 지원용)
def get_ticker_from_input(input_val):
    # 이미 코드 형식인 경우 (.KS/.KQ 제외하고 6자리 숫자만)
    if input_val.isdigit() and len(input_val) == 6:
        return input_val
    # 벤치마크 이름인 경우
    if input_val in bench_tickers:
        return bench_tickers[input_val].split('.')[0]
    # 기타 한글 이름인 경우 (yfinance 검색 시도 - 정확도가 떨어질 수 있음)
    try:
        search = yf.Search(input_val, max_results=1).stocks
        if search:
            return search[0]['symbol'].split('.')[0]
    except:
        return None
    return input_val

target_code = get_ticker_from_input(user_input)

if target_code:
    col1, col2 = st.columns([1, 1])
    
    # 데이터 가져오기 (코스피 우선 시도 후 코스닥 시도)
    raw_detail = get_stock_info(f"{target_code}.KS") or get_stock_info(f"{target_code}.KQ")
    
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
            st.warning("데이터를 가져올 수 없습니다. 종목명이나 코드를 확인해 주세요.")
            
    with col2:
        st.subheader("🔗 네이버 증권 상세 페이지")
        naver_url = f"https://finance.naver.com/item/main.naver?code={target_code}"
        
        st.write(f"**{user_input}**의 실시간 차트와 투자 정보를 보시려면 아래 버튼을 클릭하세요.")
        st.markdown(f"""
            <a href="{naver_url}" target="_blank" style="text-decoration: none;">
                <div style="background-color: #03C75A; color: white; padding: 20px; border-radius: 12px; text-align: center; font-weight: bold; font-size: 20px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);">
                    N Pay 증권 상세 페이지 열기 ↗
                </div>
            </a>
        """, unsafe_allow_html=True)
        st.info("클릭 시 'image_8d7660.png'와 같은 상세 분석 페이지로 연결됩니다.")
