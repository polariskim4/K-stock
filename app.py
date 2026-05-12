import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import datetime
import plotly.graph_objects as go

# 1. 페이지 설정
st.set_page_config(page_title="K-Stock Pro Dashboard", layout="wide")

st.title("📈 국내 주식 데이터 대시보드 (안정화 버전)")

# 2. KRX 리스트 로드 및 컬럼명 보정
@st.cache_data(ttl=3600)
def get_robust_krx_list():
    try:
        df = fdr.StockListing('KRX')
        # 시가총액 관련 컬럼 후보군 (라이브러리 버전에 따라 다름)
        marcap_candidates = ['MarCap', 'Amount', '시가총액', 'Stocks', 'MarketCap']
        
        # 실제 데이터프레임에 존재하는 컬럼 찾기
        for col in marcap_candidates:
            if col in df.columns:
                df['Standard_MarCap'] = df[col]
                break
        
        # 시가총액 데이터가 여전히 없거나 0인 경우를 대비해 보조 수단 마련
        if 'Standard_MarCap' not in df.columns:
            df['Standard_MarCap'] = 0
            
        return df
    except Exception as e:
        st.error(f"데이터 로드 중 오류 발생: {e}")
        return pd.DataFrame()

def format_ko_money(val):
    if pd.isna(val) or val == 0: return "조회 불가"
    # 보통 KRX 데이터는 '원' 단위이므로 10^12(조), 10^8(억)으로 나눕니다.
    if val >= 1_0000_0000_0000:
        return f"{val / 1_0000_0000_0000:.2f}조"
    return f"{val / 1_0000_0000:.1f}억"

# --- 메인 로직 ---
search_name = st.text_input("종목명을 정확히 입력하세요 (예: 삼성전자):", value="삼성전자")
df_krx = get_robust_krx_list()

if not df_krx.empty:
    try:
        # 검색 필터링 (정확한 매칭)
        target = df_krx[df_krx['Name'] == search_name].iloc[0]
        s_code = target['Code']
        # 시가총액 데이터를 직접 추출 시도
        raw_marcap = target['Standard_MarCap']
    except Exception:
        st.error("입력하신 종목을 KRX 상장 목록에서 찾을 수 없습니다.")
        st.stop()

    # --- 1. 상단 핵심 지표 표 (시가총액 확인용) ---
    st.header(f"📊 {search_name} ({s_code}) 핵심 정보")
    
    # 벤치마크 그룹 설정
    bench_codes = ['005930', '000660', '005380', '035420', '035720']
    if s_code not in bench_codes: bench_codes.append(s_code)
    
    summary_df = df_krx[df_krx['Code'].isin(bench_codes)].copy()
    summary_df['시가총액(표시)'] = summary_df['Standard_MarCap'].apply(format_ko_money)
    
    display_cols = ['Name', 'Code', '시가총액(표시)', 'Market']
    st.dataframe(summary_df[display_cols].sort_values(by='Name'), use_container_width=True, hide_index=True)

    st.divider()

    # --- 2. 상세 분석 (차트 & 정보 카드) ---
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📅 실시간 월봉 캔들 차트 (5년 데이터)")
        # 주가 데이터 수집
        end_d = datetime.datetime.now()
        start_d = end_d - datetime.timedelta(days=1825)
        df_p = fdr.DataReader(s_code, start_d, end_d)
        
        if not df_p.empty:
            # 월봉 리샘플링 (시, 고, 저, 종)
            df_m = df_p.resample('M').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last'})
            
            fig = go.Figure(data=[go.Candlestick(
                x=df_m.index,
                open=df_m['Open'],
                high=df_m['High'],
                low=df_m['Low'],
                close=df_m['Close'],
                increasing_line_color='#FF3232', # 상승 (강렬한 빨강)
                decreasing_line_color='#3232FF'  # 하락 (강렬한 파랑)
            )])
            fig.update_layout(
                height=550,
                xaxis_rangeslider_visible=False,
                template="plotly_dark",
                margin=dict(l=20, r=20, t=20, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("데이터 소스로부터 주가 정보를 가져오지 못했습니다.")

    with col2:
        st.subheader("📋 기업 요약")
        # 요약 정보 카드
        st.markdown(f"""
        <div style="background-color: #262730; padding: 25px; border-radius: 15px; border: 1px solid #444;">
            <p style="font-size: 16px; margin-bottom: 5px;">현재 분석 종목</p>
            <h2 style="margin-top: 0; color: #FF4B4B;">{search_name}</h2>
            <hr style="border: 0.5px solid #555;">
            <p style="font-size: 18px;"><b>시가총액:</b> <span style="color: #FFBC00;">{format_ko_money(raw_marcap)}</span></p>
            <p style="font-size: 18px;"><b>종목코드:</b> {s_code}</p>
            <p style="font-size: 18px;"><b>상장시장:</b> {target['Market']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        st.link_button("🌐 네이버 증권 상세 정보 바로가기", f"https://finance.naver.com/item/main.naver?code={s_code}")

else:
    st.error("KRX 종목 정보를 불러올 수 없습니다. 인터넷 연결이나 라이브러리 설정을 확인하세요.")
