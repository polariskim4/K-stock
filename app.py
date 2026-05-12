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

# 금액 변환 함수 (조, 억)
def format_currency(val):
    if val is None or pd.isna(val) or val == 0: return "-"
    val = int(val)
    cho = val // 10000
    eok = val % 10000
    if cho > 0:
        return f"{cho}조 {eok}억" if eok > 0 else f"{cho}조"
    return f"{eok}억"

# 비율 변환 함수 (소수점 한 자리)
def format_ratio(val, is_percent=False):
    if val is None or pd.isna(val): return "-"
    if is_percent:
        return f"{round(val * 100, 1)}%"
    return f"{round(val, 1)}"

def get_stock_info(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        info = stock.info
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
        }
    except:
        return None

# --- 1. 벤치마크 섹션 ---
st.header("📋 주요 종목 벤치마크")
if st.button('데이터 새로고침'):
    bench_data = []
    for name, ticker in bench_tickers.items():
        res = get_stock_info(ticker)
        if res:
            res['종목명'] = name
            bench_data.append(res)
    
    if bench_data:
        df = pd.DataFrame(bench_data).set_index('종목명')
        display_df = pd.DataFrame(index=df.index)
        display_df['시총'] = df['시총'].apply(format_currency)
        display_df['P/E'] = df['P/E'].apply(lambda x: format_ratio(x))
        display_df['PEG'] = df['PEG'].apply(lambda x: format_ratio(x))
        display_df['매출액'] = df['매출액'].apply(format_currency)
        display_df['영업이익'] = df['영업이익'].apply(format_currency)
        display_df['마진(%)'] = df['마진'].apply(lambda x: format_ratio(x, True))
        display_df['매출액 성장률(%)'] = df['매출액 성장률'].apply(lambda x: format_ratio(x, True))
        display_df['이익 성장률(%)'] = df['이익 성장률'].apply(lambda x: format_ratio(x, True))
        
        st.table(display_df)

st.write("---")

# --- 2. 개별 종목 상세 조회 ---
st.header("🔍 개별 종목 상세 조회")
user_input = st.text_input("종목 코드 6자리를 입력하세요", "005930")

if user_input:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📊 핵심 지표")
        raw_detail = get_stock_info(f"{user_input}.KS") or get_stock_info(f"{user_input}.KQ")
        
        if raw_detail:
            detail_formatted = {
                "시총": format_currency(raw_detail['시총']),
                "P/E": format_ratio(raw_detail['P/E']),
                "PEG": format_ratio(raw_detail['PEG']),
                "매출액": format_currency(raw_detail['매출액']),
                "영업이익": format_currency(raw_detail['영업이익']),
                "마진(%)": format_ratio(raw_detail['마진'], True),
                "매출액 성장률(%)": format_ratio(raw_detail['매출액 성장률'], True),
                "이익 성장률(%)": format_ratio(raw_detail['이익 성장률'], True),
            }
            st.table(pd.Series(detail_formatted).to_frame(name="수치"))
        else:
            st.warning("데이터를 가져올 수 없습니다.")
            
    with col2:
        st.subheader("🔗 네이버 증권 링크")
        naver_url = f"https://finance.naver.com/item/main.naver?code={user_input}"
        
        st.write("이미지 차트 대신 안전한 공식 사이트 링크를 제공합니다.")
        # 버튼 스타일의 링크 생성
        st.markdown(f"""
            <a href="{naver_url}" target="_blank" style="text-decoration: none;">
                <div style="background-color: #03C75A; color: white; padding: 15px; border-radius: 8px; text-align: center; font-weight: bold; font-size: 18px;">
                    네이버 증권에서 월봉 차트 보기 ↗
                </div>
            </a>
        """, unsafe_allow_html=True)
        st.info("위 버튼을 클릭하면 새 창에서 해당 종목의 상세 차트 페이지가 열립니다.")
