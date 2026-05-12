import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import datetime

# 페이지 설정
st.set_page_config(page_title="K-Stock Dashboard", layout="wide")

st.title("🇰🇷 국내 주식 벤치마크 및 상세 분석 대시보드")

# 벤치마크 대상 (기본 리스트)
DEFAULT_TICKERS = {
    '005930': '삼성전자', '000660': 'SK하이닉스', '005380': '현대차', 
    '035420': 'NAVER', '035720': '카카오', '068270': '셀트리온', 
    '005490': 'POSCO홀딩스', '247540': '에코프로비엠'
}

def format_ko_money(num):
    if pd.isna(num) or num == 0: return "N/A"
    if num >= 1_0000_0000_0000: return f"{num / 1_0000_0000_0000:.1f}조"
    return f"{num / 1_0000_0000:.1f}억"

@st.cache_data(ttl=3600)
def get_k_stock_data(ticker_dict):
    df_krx = fdr.StockListing('KRX')
    results = []
    
    for code, name in ticker_dict.items():
        try:
            # 기본 마켓 정보 추출
            row = df_krx[df_krx['Code'] == code].iloc[0]
            mkt_cap = row['MarCap']
            
            # 주가 데이터 (최근 1년 전고점 계산용)
            end_date = datetime.datetime.now()
            start_date = end_date - datetime.timedelta(days=365)
            df_price = fdr.DataReader(code, start_date, end_date)
            
            curr_p = df_price['Close'].iloc[-1]
            high_52 = df_price['High'].max()
            perf = (curr_p / high_52 - 1) * 100

            results.append({
                "종목명": name,
                "Ticker": code,
                "MarCap_Raw": mkt_cap,
                "시총": format_ko_money(mkt_cap),
                "현재가": f"{int(curr_p):,}원",
                "전고점 대비": f"{perf:+.1f}%",
                "시장": row['Market']
            })
        except:
            continue
    
    return pd.DataFrame(results).sort_values(by="MarCap_Raw", ascending=False)

# --- 메인 검색 로직 ---
search_input = st.text_input("종목명 또는 6자리 코드를 입력하세요:", value="삼성전자")

with st.spinner('데이터를 불러오는 중...'):
    df_krx_all = fdr.StockListing('KRX')
    try:
        if search_input.isdigit():
            s_code = search_input
            s_name = df_krx_all[df_krx_all['Code'] == s_code].iloc[0]['Name']
        else:
            s_name = search_input
            s_code = df_krx_all[df_krx_all['Name'] == s_name].iloc[0]['Code']
    except:
        st.warning("종목을 찾을 수 없습니다. 기본값으로 표시합니다.")
        s_code, s_name = "005930", "삼성전자"

    # 데이터 통합
    current_list = DEFAULT_TICKERS.copy()
    current_list[s_code] = s_name
    df_final = get_k_stock_data(current_list)

# --- 1. 비교 분석 표 ---
st.header("📊 주요 종목 비교")
def highlight_row(s):
    return ['background-color: #262730; color: #ff4b4b; font-weight: bold'] * len(s) if s.Ticker == s_code else [''] * len(s)

st.dataframe(df_final.style.apply(highlight_row, axis=1), use_container_width=True, hide_index=True)

st.divider()

# --- 2. 상세 분석 (에러 방지 레이아웃) ---
if s_code:
    st.header(f"🔍 {s_name} ({s_code}) 상세 지표")
    col_left, col_right = st.columns([1.5, 1])
    
    with col_left:
        st.subheader("주가 추이 (월봉)")
        c_url = f"https://ssl.pstatic.net/imgstock/chart/item/area/monthly/{s_code}.png"
        st.image(c_url, use_container_width=True, caption="제공: 네이버 증권")
        
    with col_right:
        st.subheader("Key Statistics")
        try:
            # KeyError 방지를 위한 필터링 추출
            row_data = df_final[df_final['Ticker'] == s_code].iloc[0]
            st.markdown(f"""
            <div style="background-color: #161618; padding: 20px; border-radius: 10px; border: 1px solid #333; line-height: 2.5;">
                <table style="width: 100%; color: white; border-collapse: collapse;">
                    <tr style="border-bottom: 1px solid #444;"><td>종목명</td><td style="text-align: right; color: #ff4b4b;"><b>{s_name}</b></td></tr>
                    <tr style="border-bottom: 1px solid #444;"><td>시가총액</td><td style="text-align: right;">{row_data['시총']}</td></tr>
                    <tr style="border-bottom: 1px solid #444;"><td>현재가</td><td style="text-align: right;">{row_data['현재가']}</td></tr>
                    <tr style="border-bottom: 1px solid #444;"><td>1년 전고점 대비</td><td style="text-align: right; color: {'#ff4b4b' if '+' in row_data['전고점 대비'] else '#4b91ff'};">{row_data['전고점 대비']}</td></tr>
                    <tr><td>상장시장</td><td style="text-align: right;">{row_data['시장']}</td></tr>
                </table>
            </div>
            """, unsafe_allow_html=True)
            
            n_url = f"https://finance.naver.com/item/main.naver?code={s_code}"
            st.markdown(f'<br><a href="{n_url}" target="_blank"><button style="width: 100%; padding: 12px; background-color: #03c75a; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold;">네이버 증권 상세 재무제표 보기</button></a>', unsafe_allow_html=True)
        except Exception as e:
            st.error("상세 정보를 표시하는 중 오류가 발생했습니다.")
