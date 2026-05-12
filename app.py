import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import datetime

# 페이지 설정
st.set_page_config(page_title="K-Stock Dashboard", layout="wide")
st.title("🇰🇷 국내 주식 벤치마크 및 상세 분석 대시보드")

# 1. 시가총액 포맷팅 함수 (조/억 단위 변환)
def format_ko_money(num):
    if pd.isna(num) or num == 0: return "데이터 없음"
    if num >= 1_0000_0000_0000:
        return f"{num / 1_0000_0000_0000:.1f}조"
    return f"{num / 1_0000_0000:.1f}억"

# 2. 데이터 로드 함수 (캐싱 적용으로 속도 향상)
@st.cache_data(ttl=3600)
def get_stock_data(ticker_dict):
    try:
        # KRX 상장사 전체 리스트 로드 (시가총액 정보 포함)
        df_krx = fdr.StockListing('KRX')
    except Exception as e:
        st.error(f"상장사 목록을 가져오지 못했습니다: {e}")
        return pd.DataFrame()

    results = []
    for code, name in ticker_dict.items():
        try:
            # 기본 정보 추출
            stock_info = df_krx[df_krx['Code'] == code].iloc[0]
            mkt_cap = stock_info.get('MarCap', 0) # 시가총액 데이터 추출
            
            # 주가 데이터 로드 (최근 1년)
            df_price = fdr.DataReader(code, datetime.datetime.now() - datetime.timedelta(days=365))
            if df_price.empty: continue
            
            curr_p = df_price['Close'].iloc[-1]
            high_52 = df_price['High'].max()
            perf = (curr_p / high_52 - 1) * 100

            results.append({
                "종목명": name,
                "Ticker": code,
                "MarCap_Raw": mkt_cap,
                "시가총액": format_ko_money(mkt_cap),
                "현재가": f"{int(curr_p):,}원",
                "52주 고점 대비": f"{perf:+.1f}%",
                "상장시장": stock_info.get('Market', 'KRX')
            })
        except:
            continue
    return pd.DataFrame(results)

# --- 메인 검색부 ---
search_input = st.text_input("분석할 종목명 또는 코드를 입력하세요:", value="삼성전자")

# 종목 코드 찾기
df_krx_all = fdr.StockListing('KRX')
try:
    if search_input.isdigit():
        s_code = search_input
        s_name = df_krx_all[df_krx_all['Code'] == s_code].iloc[0]['Name']
    else:
        s_name = search_input
        s_code = df_krx_all[df_krx_all['Name'] == s_name].iloc[0]['Code']
except:
    st.error("종목을 찾을 수 없습니다. 기본값인 삼성전자로 표시합니다.")
    s_code, s_name = "005930", "삼성전자"

# 데이터 통합
bench_list = {'005930':'삼성전자', '000660':'SK하이닉스', '005380':'현대차', '035420':'NAVER', '035720':'카카오'}
bench_list[s_code] = s_name
df_final = get_stock_data(bench_list)

# --- 1. 비교 분석 표 ---
st.header("📊 국내 주요 종목 비교")
if not df_final.empty:
    df_display = df_final.sort_values(by="MarCap_Raw", ascending=False).drop(columns=['MarCap_Raw'])
    
    # 검색한 종목 하이라이트
    def highlight_target(row):
        return ['background-color: #262730; color: #ff4b4b; font-weight: bold'] * len(row) if row.Ticker == s_code else [''] * len(row)
    
    st.dataframe(df_display.style.apply(highlight_target, axis=1), use_container_width=True, hide_index=True)

st.divider()

# --- 2. 상세 분석 ---
st.header(f"🔍 {s_name} ({s_code}) 상세 분석")
col_chart, col_stat = st.columns([1.5, 1])

with col_chart:
    st.subheader("주가 추이 (월봉 차트)")
    # 네이버 차트 URL 최적화 (캐시 방지 파라미터 추가)
    now_ts = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    chart_url = f"https://ssl.pstatic.net/imgstock/chart/item/area/monthly/{s_code}.png?sid={now_ts}"
    
    # 엑박 방지를 위해 캡션과 함께 출력
    st.image(chart_url, use_container_width=True, caption=f"제공: 네이버 증권 (기준: {datetime.datetime.now().strftime('%Y-%m-%d')})")

with col_stat:
    st.subheader("Key Statistics")
    try:
        target_info = df_final[df_final['Ticker'] == s_code].iloc[0]
        st.markdown(f"""
        <div style="background-color: #111; padding: 15px; border-radius: 10px; border: 1px solid #333;">
            <p style="margin: 5px 0;"><b>종목명:</b> {s_name}</p>
            <p style="margin: 5px 0;"><b>시가총액:</b> {target_info['시가총액']}</p>
            <p style="margin: 5px 0;"><b>현재가:</b> {target_info['현재가']}</p>
            <p style="margin: 5px 0;"><b>52주 고점 대비:</b> <span style="color:#ff4b4b;">{target_info['52주 고점 대비']}</span></p>
            <p style="margin: 5px 0;"><b>시장:</b> {target_info['상장시장']}</p>
        </div>
        """, unsafe_allow_html=True)
    except:
        st.warning("상세 지표를 불러오는데 실패했습니다.")
