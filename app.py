import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import datetime
import time

# 페이지 설정
st.set_page_config(page_title="K-Stock Analysis Dashboard", layout="wide")

st.title("🇰🇷 국내 주식 벤치마크 및 상세 분석 대시보드")

# 벤치마크 대상 목록 (종목코드: 종목명)
DEFAULT_TICKERS = {
    '005930': '삼성전자', '000660': 'SK하이닉스', '005380': '현대차', 
    '035420': 'NAVER', '035720': '카카오', '006840': 'AK홀딩스', 
    '068270': '셀트리온', '005490': 'POSCO홀딩스', '247540': '에코프로비엠', '086520': '에코프로'
}

def format_ko_money(num):
    if pd.isna(num) or num == 0: return "N/A"
    if num >= 1_0000_0000_0000: # 1조 이상
        return f"{num / 1_0000_0000_0000:.1f}조"
    return f"{num / 1_0000_0000:.1f}억"

@st.cache_data(ttl=3600)
def get_k_stock_data(ticker_dict):
    results = []
    # 전체 종목 리스트 (시총 정렬용)
    df_krx = fdr.StockListing('KRX')
    
    for code, name in ticker_dict.items():
        try:
            # 기본 시총 정보 추출
            target_info = df_krx[df_krx['Code'] == code].iloc[0]
            mkt_cap = target_info['MarCap']
            
            # 주가 데이터 (전고점 계산용 - 최근 1년)
            df_price = fdr.DataReader(code, datetime.datetime.now() - datetime.timedelta(days=365))
            current_price = df_price['Close'].iloc[-1]
            high_52w = df_price['High'].max()
            perf_from_high = (current_price / high_52w - 1) * 100
            
            # FinanceDataReader는 상세 재무(PEG 등)를 직접 제공하지 않으므로 
            # 네이버 증권 수치를 기본으로 가공하거나 요약 정보를 넣습니다.
            results.append({
                "종목명": name,
                "Ticker": code,
                "MarCap_Raw": mkt_cap,
                "시총": format_ko_money(mkt_cap),
                "현재가": f"{int(current_price):,}원",
                "전고점 대비": f"{perf_from_high:+.1f}%",
                "매출액(24.E)": "네이버증권 참조", # 크롤링 한계상 텍스트 대체
                "영업이익(24.E)": "네이버증권 참조",
                "시장": target_info['Market']
            })
        except:
            results.append({"종목명": name, "Ticker": code, "MarCap_Raw": 0})
    
    df = pd.DataFrame(results)
    return df.sort_values(by="MarCap_Raw", ascending=False).drop(columns=["MarCap_Raw"])

# --- 데이터 로드 ---
search_input = st.text_input("분석할 종목명 또는 코드를 입력하세요:", value="삼성전자")

with st.spinner('국내 시장 데이터를 분석 중...'):
    # 검색 로직 (이름으로 코드 찾기)
    df_all_krx = fdr.StockListing('KRX')
    try:
        if search_input.isdigit():
            search_code = search_input
            search_name = df_all_krx[df_all_krx['Code'] == search_code].iloc[0]['Name']
        else:
            search_name = search_input
            search_code = df_all_krx[df_all_krx['Name'] == search_name].iloc[0]['Code']
    except:
        search_code, search_name = "005930", "삼성전자"

    df_final = get_k_stock_data(DEFAULT_TICKERS)
    
    # 검색 종목이 벤치마크에 없으면 추가
    if search_code not in DEFAULT_TICKERS:
        df_search = get_k_stock_data({search_code: search_name})
        df_final = pd.concat([df_final, df_search], ignore_index=True)

# --- 1. 비교 분석 표 ---
st.header("📊 국내 주요 종목 비교")
def highlight_search(s):
    return ['background-color: #262730; font-weight: bold; color: #ff4b4b'] * len(s) if s.Ticker == search_code else [''] * len(s)

st.dataframe(df_final.style.apply(highlight_search, axis=1), use_container_width=True, hide_index=True)

st.divider()

# --- 2. 상세 분석 섹션 (네이버 증권 연동) ---
if search_code:
    st.header(f"🔍 {search_name} ({search_code}) 상세 분석")
    
    col_chart, col_info = st.columns([1.8, 1])
    
    with col_chart:
        st.subheader("주가 차트 (네이버 증권)")
        # 네이버 증권의 실시간 일봉/월봉 차트 이미지 활용
        chart_url = f"https://ssl.pstatic.net/imgstock/chart/item/area/monthly/{search_code}.png"
        st.image(chart_url, caption="네이버 증권 제공 월봉 차트", use_column_width=True)
        
    with col_info:
        st.subheader("Key Statistics")
        target_data = df_final[df_final['Ticker'] == search_code].iloc[0]
        
        st.markdown(f"""
        <div style="background-color: #161618; padding: 15px; border-radius: 8px; border: 1px solid #333; line-height: 2.2;">
            <table style="width: 100%; color: white;">
                <tr style="border-bottom: 1px solid #333;"><td style="color: #888;">종목명</td><td style="text-align: right; font-weight: bold; color: #ff4b4b;">{search_name}</td></tr>
                <tr style="border-bottom: 1px solid #333;"><td style="color: #888;">종목코드</td><td style="text-align: right;">{search_code}</td></tr>
                <tr style="border-bottom: 1px solid #333;"><td style="color: #888;">시가총액</td><td style="text-align: right;">{target_data['시총']}</td></tr>
                <tr style="border-bottom: 1px solid #333;"><td style="color: #888;">현재가</td><td style="text-align: right;">{target_data['현재가']}</td></tr>
                <tr style="border-bottom: 1px solid #333;"><td style="color: #888;">52주 고점 대비</td><td style="text-align: right; color: {'#ff4b4b' if '-' not in target_data['전고점 대비'] else '#0087ff'};">{target_data['전고점 대비']}</td></tr>
                <tr><td style="color: #888;">시장 구분</td><td style="text-align: right;">{target_data['시장']}</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
        
        # 네이버 증권 상세 페이지 링크 버튼
        naver_url = f"https://finance.naver.com/item/main.naver?code={search_code}"
        st.markdown(f'<br><a href="{naver_url}" target="_blank"><button style="width: 100%; padding: 10px; background-color: #03c75a; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold;">네이버 증권에서 재무제표 보기</button></a>', unsafe_allow_html=True)

    st.info("💡 국내 주식의 상세 재무(PER, EPS 전망 등)는 네이버 증권의 보안 정책상 버튼을 클릭하여 확인하는 것이 가장 정확합니다.")
