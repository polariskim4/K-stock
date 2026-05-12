import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import datetime
import plotly.graph_objects as go
import yfinance as yf

# 1. 페이지 설정
st.set_page_config(page_title="K-Stock Ultimate Dashboard", layout="wide")
st.title("🚀 국내 주식 통합 분석 대시보드 (최종 안정화 버전)")

# 2. 시가총액 및 기초 데이터 로드 (매우 강력한 로직)
@st.cache_data(ttl=3600)
def get_verified_krx_data():
    try:
        df = fdr.StockListing('KRX')
        
        # [해결책 1] 시가총액 컬럼 찾기 (모든 가능성 확인)
        marcap_col = None
        for col in ['MarCap', 'Amount', '시가총액', 'Stocks', 'MarketCap']:
            if col in df.columns:
                # 해당 컬럼이 숫자형인지 확인
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                if df[col].sum() > 0:
                    marcap_col = col
                    break
        
        if marcap_col:
            df['Standard_MarCap'] = df[marcap_col]
        else:
            # 컬럼을 정말 못 찾겠으면 0으로 초기화
            df['Standard_MarCap'] = 0
            
        return df
    except:
        return pd.DataFrame()

def format_kr_money(val):
    if pd.isna(val) or val <= 0: return "데이터 확인 불가"
    # KRX 시가총액 데이터는 보통 '원' 단위입니다.
    if val >= 1_0000_0000_0000:
        return f"{val / 1_0000_0000_0000:.2f}조 원"
    return f"{val / 1_0000_0000:.0f}억 원"

# --- 메인 로직 ---
search_name = st.text_input("종목명 입력 (정확히 입력해주세요):", value="삼성전자")
df_krx = get_verified_krx_data()

if not df_krx.empty:
    try:
        # 종목 검색 (대소문자 및 공백 제거 후 검색)
        target = df_krx[df_krx['Name'].str.replace(' ', '') == search_name.replace(' ', '')].iloc[0]
        s_code = target['Code']
        s_marcap = target['Standard_MarCap']
        s_market = target['Market']
    except:
        st.warning(f"'{search_name}' 종목을 목록에서 찾을 수 없습니다.")
        st.stop()

    # --- 1. 상단 비교 표 ---
    st.subheader("📊 주요 종목 시가총액 비교")
    bench_codes = ['005930', '000660', '005380', '035420', '035720']
    if s_code not in bench_codes: bench_codes.append(s_code)
    
    summary_df = df_krx[df_krx['Code'].isin(bench_codes)].copy()
    summary_df['시가총액_포맷'] = summary_df['Standard_MarCap'].apply(format_kr_money)
    
    st.dataframe(summary_df[['Name', 'Code', '시가총액_포맷', 'Market']].sort_values(by='Name'), 
                 use_container_width=True, hide_index=True)

    st.divider()

    # --- 2. 하단 상세 분석 ---
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📅 월봉 캔들 차트 (실시간 데이터)")
        
        # [해결책 2] 이중 데이터 소스 (FDR 실패 시 yfinance 사용)
        df_p = fdr.DataReader(s_code, datetime.datetime.now() - datetime.timedelta(days=1825))
        
        if df_p.empty or len(df_p) < 10:
            suffix = ".KS" if s_market == 'KOSPI' else ".KQ"
            df_p = yf.download(s_code + suffix, period="5y", interval="1mo", progress=False)

        if not df_p.empty:
            # 월봉 리샘플링 및 차트 생성
            df_p.index = pd.to_datetime(df_p.index)
            df_m = df_p.resample('M').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last'})
            
            fig = go.Figure(data=[go.Candlestick(
                x=df_m.index, open=df_m['Open'], high=df_m['High'],
                low=df_m['Low'], close=df_m['Close'],
                increasing_line_color='#FF3232', decreasing_line_color='#3232FF'
            )])
            fig.update_layout(template="plotly_dark", height=500, margin=dict(l=10, r=10, t=10, b=10),
                              xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("차트 데이터를 불러올 수 없습니다. Ticker를 확인해주세요.")

    with col2:
        st.subheader("📌 기업 요약 정보")
        # 시가총액을 아주 크게 강조
        st.markdown(f"""
        <div style="background-color: #1E1E1E; padding: 25px; border-radius: 15px; border: 2px solid #FF4B4B; text-align: center;">
            <p style="font-size: 16px; color: #AAA; margin-bottom: 0;">현재 분석 종목</p>
            <h1 style="margin-top: 0; color: white; border-bottom: 1px solid #444; padding-bottom: 10px;">{search_name}</h1>
            <p style="font-size: 18px; margin-top: 15px;"><b>시장:</b> {s_market} ({s_code})</p>
            <div style="margin-top: 25px; background: #2D2D2D; padding: 15px; border-radius: 10px;">
                <p style="font-size: 16px; color: #FF4B4B; margin-bottom: 5px;"><b>현시점 시가총액</b></p>
                <p style="font-size: 26px; font-weight: bold; color: #FFFFFF;">{format_kr_money(s_marcap)}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        st.link_button("🌐 네이버 증권에서 더 자세히 보기", f"https://finance.naver.com/item/main.naver?code={s_code}")

else:
    st.error("KRX 데이터를 로드하지 못했습니다. 라이브러리 설정을 확인해주세요.")
