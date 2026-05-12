import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import datetime

# 1. 페이지 기본 설정
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
    # KRX 전체 종목 정보 로드
    try:
        df_krx = fdr.StockListing('KRX')
    except:
        return pd.DataFrame()

    results = []
    for code, name in ticker_dict.items():
        try:
            # 1. 기본 마켓 정보
            row = df_krx[df_krx['Code'] == code].iloc[0]
            mkt_cap = row['MarCap'] if 'MarCap' in row else 0
            
            # 2. 주가 데이터 (안정성을 위해 최근 2년치 로드)
            end_date = datetime.datetime.now()
            start_date = end_date - datetime.timedelta(days=730)
            df_p = fdr.DataReader(code, start_date, end_date)
            
            if df_p.empty: continue
            
            curr_p = df_p['Close'].iloc[-1]
            high_52 = df_p['High'].rolling(window=250, min_periods=1).max().iloc[-1]
            perf = (curr_p / high_52 - 1) * 100

            results.append({
                "종목명": name,
                "Ticker": code,
                "MarCap_Raw": mkt_cap,
                "시가총액": format_ko_money(mkt_cap),
                "현재가": f"{int(curr_p):,}원",
                "52주 고점 대비": f"{perf:+.1f}%",
                "상장시장": row['Market'] if 'Market' in row else "KRX"
            })
        except Exception as e:
            continue
    
    return pd.DataFrame(results)

# --- 메인 검색 및 데이터 처리 ---
search_input = st.text_input("종목명 또는 6자리 코드를 입력하세요:", value="삼성전자")

with st.spinner('데이터를 실시간으로 불러오는 중...'):
    df_all_list = fdr.StockListing('KRX')
    try:
        if search_input.isdigit():
            s_code = search_input
            s_name = df_all_list[df_all_list['Code'] == s_code].iloc[0]['Name']
        else:
            s_name = search_input
            s_code = df_all_list[df_all_list['Name'] == s_name].iloc[0]['Code']
    except:
        st.error("입력하신 종목 정보를 찾을 수 없습니다.")
        s_code, s_name = "005930", "삼성전자"

    # 데이터 통합 및 정렬
    current_list = DEFAULT_TICKERS.copy()
    current_list[s_code] = s_name
    df_final = get_k_stock_data(current_list)

# --- 1. 비교 분석 표 (Empty 에러 방지) ---
st.header("📊 핵심 지표 비교")
if not df_final.empty:
    df_sorted = df_final.sort_values(by="MarCap_Raw", ascending=False)
    
    def highlight_row(s):
        return ['background-color: #262730; color: #ff4b4b; font-weight: bold'] * len(s) if s.Ticker == s_code else [''] * len(s)
    
    # 출력용 데이터프레임 (정렬용 Raw 데이터는 숨김)
    show_df = df_sorted.drop(columns=['MarCap_Raw'])
    st.dataframe(show_df.style.apply(highlight_row, axis=1), use_container_width=True, hide_index=True)
else:
    st.warning("데이터를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.")

st.divider()

# --- 2. 상세 분석 (에러 방지 레이아웃) ---
if not df_final.empty and s_code:
    st.header(f"🔍 {s_name} ({s_code}) 상세 분석")
    col_chart, col_stat = st.columns([1.5, 1])
    
    with col_chart:
        st.subheader("주가 추이 (월봉 차트)")
        # 네이버 금융 차트 이미지 (엑박 방지를 위한 파라미터 최적화)
        chart_url = f"https://ssl.pstatic.net/imgstock/chart/item/area/monthly/{s_code}.png?sid={datetime.datetime.now().strftime('%H%M%S')}"
        st.image(chart_url, use_container_width=True)
        st.caption("제공: 네이버 증권")
        
    with col_stat:
        st.subheader("Key Statistics")
        try:
            # 안전하게 데이터 추출
            target_row = df_final[df_final['Ticker'] == s_code].iloc[0]
            st.markdown(f"""
            <div style="background-color: #161618; padding: 20px; border-radius: 10px; border: 1px solid #333; line-height: 2.2;">
                <table style="width: 100%; color: white;">
                    <tr style="border-bottom: 1px solid #444;"><td><b>Ticker</b></td><td style="text-align: right; color: #ff4b4b;">{s_code}</td></tr>
                    <tr style="border-bottom: 1px solid #444;"><td><b>시가총액</b></td><td style="text-align: right;">{target_row['시가총액']}</td></tr>
                    <tr style="border-bottom: 1px solid #444;"><td><b>현재가</b></td><td style="text-align: right;">{target_row['현재가']}</td></tr>
                    <tr style="border-bottom: 1px solid #444;"><td><b>52주 고점 대비</b></td><td style="text-align: right; color: {'#ff4b4b' if '+' in target_row['52주 고점 대비'] else '#4b91ff'};">
                        {target_row['52주 고점 대비']}
                    </td></tr>
                    <tr><td><b>상장시장</b></td><td style="text-align: right;">{target_row['상장시장']}</td></tr>
                </table>
            </div>
            """, unsafe_allow_html=True)
            
            naver_link = f"https://finance.naver.com/item/main.naver?code={s_code}"
            st.markdown(f'<br><a href="{naver_link}" target="_blank"><button style="width: 100%; padding: 12px; background-color: #03c75a; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold;">네이버 증권 상세 재무 정보</button></a>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"상세 데이터를 불러올 수 없습니다. ({e})")
