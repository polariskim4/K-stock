import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import datetime
import plotly.graph_objects as go
import yfinance as yf

# 1. 페이지 설정
st.set_page_config(page_title="K-Stock Final Solution", layout="wide")
st.title("🚀 국내 주식 통합 분석 대시보드 (데이터 무결성 버전)")

# 2. 유틸리티 함수: 시가총액 포맷팅
def format_kr_money(val):
    try:
        val = float(val)
        if val <= 0 or pd.isna(val): return "조회 불가"
        if val >= 1_0000_0000_0000:
            return f"{val / 1_0000_0000_0000:.2f}조 원"
        return f"{val / 1_0000_0000:.0f}억 원"
    except:
        return "조회 불가"

# 3. 데이터 로드 로직
@st.cache_data(ttl=3600)
def get_krx_list():
    try:
        df = fdr.StockListing('KRX')
        # 시가총액 후보 컬럼들 모두 확인
        for col in ['MarCap', 'Amount', '시가총액', 'MarketCap']:
            if col in df.columns:
                df['Standard_MarCap'] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                break
        return df
    except:
        return pd.DataFrame()

# --- 메인 실행 로직 ---
search_name = st.text_input("종목명 입력 (예: 삼성전자):", value="삼성전자")
df_krx = get_krx_list()

if not df_krx.empty:
    try:
        # 종목명으로 코드 찾기
        target = df_krx[df_krx['Name'].str.replace(' ', '') == search_name.replace(' ', '')].iloc[0]
        s_code = target['Code']
        s_market = target['Market']
        # yfinance용 심볼 생성 (KOSPI: .KS, KOSDAQ: .KQ)
        yf_symbol = f"{s_code}.KS" if s_market == 'KOSPI' else f"{s_code}.KQ"
    except:
        st.warning(f"'{search_name}' 종목을 찾을 수 없습니다. 정확한 이름을 입력해주세요.")
        st.stop()

    # --- 데이터 2차 검증 (yfinance 활용) ---
    with st.spinner('데이터를 정밀 분석 중입니다...'):
        stock_yf = yf.Ticker(yf_symbol)
        # yfinance에서 시가총액 직접 가져오기 (FDR 실패 대비)
        yf_info = stock_yf.info
        s_marcap = yf_info.get('marketCap', target.get('Standard_MarCap', 0))

    # --- 1. 상단 요약 대시보드 ---
    st.subheader(f"📊 {search_name} 핵심 데이터 요약")
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("종목코드", s_code)
    col_b.metric("상장시장", s_market)
    col_c.metric("시가총액", format_kr_money(s_marcap))

    st.divider()

    # --- 2. 하단 상세 분석 ---
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📅 월봉 캔들 차트 (Plotly 기반)")
        # 데이터 가져오기 (yfinance가 월봉 데이터에 더 안정적임)
        df_p = stock_yf.history(period="5y", interval="1mo")
        
        if not df_p.empty:
            fig = go.Figure(data=[go.Candlestick(
                x=df_p.index,
                open=df_p['Open'], high=df_p['High'],
                low=df_p['Low'], close=df_p['Close'],
                increasing_line_color='#FF3232', # 상승 빨강
                decreasing_line_color='#3232FF'  # 하락 파랑
            )])
            fig.update_layout(
                template="plotly_dark", 
                height=500, 
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis_rangeslider_visible=False
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("차트용 시계열 데이터를 불러오지 못했습니다.")

    with col2:
        st.subheader("📌 상세 기업 정보")
        # 깔끔한 카드 형태의 정보창
        st.markdown(f"""
        <div style="background-color: #262730; padding: 20px; border-radius: 15px; border: 1px solid #444;">
            <h3 style="margin-top:0; color:#FF4B4B;">{search_name}</h3>
            <p style="font-size:14px; color:#AAA;">{yf_info.get('longBusinessSummary', '정보 없음')[:150]}...</p>
            <hr style="border:0.1px solid #555;">
            <p><b>현재가:</b> {yf_info.get('currentPrice', 0):,} 원</p>
            <p><b>52주 최고가:</b> {yf_info.get('fiftyTwoWeekHigh', 0):,} 원</p>
            <p><b>배당수익률:</b> {yf_info.get('dividendYield', 0)*100:.2f}%</p>
            <div style="margin-top:20px; padding:10px; background:#1E1E1E; border-radius:10px; text-align:center;">
                <p style="margin:0; font-size:12px; color:#AAA;">실시간 시가총액</p>
                <p style="margin:0; font-size:20px; font-weight:bold;">{format_kr_money(s_marcap)}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        st.link_button("🎯 네이버 증권에서 더 자세히 보기", f"https://finance.naver.com/item/main.naver?code={s_code}")
