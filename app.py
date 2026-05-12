import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import datetime

# 페이지 설정
st.set_page_config(page_title="K-Stock Dashboard", layout="wide")

st.title("🇰🇷 국내 주식 벤치마크 및 상세 분석 대시보드")

# 벤치마크 기본 종목
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
            
            # 주가 데이터 (52주 고점 계산용)
            df_p = fdr.DataReader(code, datetime.datetime.now() - datetime.timedelta(days=365))
            curr_p = df_p['Close'].iloc[-1]
            high_52 = df_p['High'].max()
            perf = (curr_p / high_52 - 1) * 100

            results.append({
                "종목명": name,
                "Ticker": code,
                "MarCap_Raw": mkt_cap,
                "시가총액": format_ko_money(mkt_cap),
                "현재가": f"{int(curr_p):,}원",
                "52주 고점 대비": f"{perf:+.1f}%",
                "시장": row['Market']
            })
        except:
            continue
    
    return pd.DataFrame(results)

# --- 종목 검색 및 데이터 로드 ---
search_input = st.text_input("종목명 또는 코드를 입력하세요:", value="삼성전자")

with st.spinner('데이터를 분석 중...'):
    df_all = fdr.StockListing('KRX')
    try:
        if search_input.isdigit():
            s_code = search_input
            s_name = df_all[df_all['Code'] == s_code].iloc[0]['Name']
        else:
            s_name = search_input
            s_code = df_all[df_all['Name'] == s_name].iloc[0]['Code']
    except:
        s_code, s_name = "005930", "삼성전자"

    current_list = DEFAULT_TICKERS.copy()
    current_list[s_code] = s_name
    df_final = get_k_stock_data(current_list)
    
    # 정렬 에러 방지를 위해 컬럼 존재 확인 후 정렬
    if not df_final.empty and 'MarCap_Raw' in df_final.columns:
        df_final = df_final.sort_values(by="MarCap_Raw", ascending=False)

# --- 1. 비교 분석 표 ---
st.header("📊 핵심 지표 비교")
def highlight_search(s):
    return ['background-color: #262730; color: #ff4b4b; font-weight: bold'] * len(s) if s.Ticker == s_code else [''] * len(s)

# 불필요한 원본 데이터 컬럼 제외 후 출력
display_df = df_final.drop(columns=['MarCap_Raw']) if 'MarCap_Raw' in df_final.columns else df_final
st.dataframe(display_df.style.apply(highlight_search, axis=1), use_container_width=True, hide_index=True)

st.divider()

# --- 2. Finviz 스타일 상세 분석 ---
if s_code:
    st.header(f"🔍 {s_name} ({s_code}) 상세 분석")
    col_chart, col_stat = st.columns([1.8, 1])
    
    with col_chart:
        st.subheader("주가 추이 (월봉)")
        chart_url = f"https://ssl.pstatic.net/imgstock/chart/item/area/monthly/{s_code}.png"
        st.image(chart_url, use_container_width=True, caption="제공: 네이버 증권")
        
    with col_stat:
        st.subheader("Key Statistics")
        try:
            data = df_final[df_final['Ticker'] == s_code].iloc[0]
            st.markdown(f"""
            <div style="background-color: #161618; padding: 20px; border-radius: 10px; border: 1px solid #333; line-height: 2.2;">
                <table style="width: 100%; color: white;">
                    <tr style="border-bottom: 1px solid #444;"><td><b>Ticker</b></td><td style="text-align: right; color: #ff4b4b;">{s_code}</td></tr>
                    <tr style="border-bottom: 1px solid #444;"><td><b>시가총액</b></td><td style="text-align: right;">{data['시가총액']}</td></tr>
                    <tr style="border-bottom: 1px solid #444;"><td><b>현재가</b></td><td style="text-align: right;">{data['현재가']}</td></tr>
                    <tr style="border-bottom: 1px solid #444;"><td><b>52주 고점 대비</b></td><td style="text-align: right; color: {'#ff4b4b' if '+' in data['52주 고점 대비'] else '#4b91ff'};">{data['52주 고점 대비']}</td></tr>
                    <tr><td><b>상장시장</b></td><td style="text-align: right;">{data['시장']}</td></tr>
                </table>
            </div>
            """, unsafe_allow_html=True)
            
            # 네이버 증권 링크
            naver_url = f"https://finance.naver.com/item/main.naver?code={s_code}"
            st.markdown(f'<br><a href="{naver_url}" target="_blank"><button style="width: 100%; padding: 12px; background-color: #03c75a; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold;">네이버 증권에서 재무표 확인</button></a>', unsafe_allow_html=True)
        except:
            st.error("상세 데이터를 불러올 수 없습니다.")
