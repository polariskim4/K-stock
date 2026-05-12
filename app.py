import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import datetime
import plotly.graph_objects as go
import yfinance as yf

# 1. 페이지 설정
st.set_page_config(page_title="K-Stock Ultimate Dashboard", layout="wide")
st.title("🚀 국내 주식 통합 분석 대시보드 (최종 안정화 버전)")

# 2. 시가총액 데이터를 확실하게 가져오는 함수
@st.cache_data(ttl=3600)
def get_verified_krx_data():
    try:
        df = fdr.StockListing('KRX')
        
        # 시가총액일 가능성이 높은 컬럼들 후보
        candidates = ['MarCap', 'Amount', '시가총액', 'Stocks', 'MarketCap']
        found_col = None
        
        for col in candidates:
            if col in df.columns:
                # 데이터가 실제로 숫자인지 확인
                if pd.to_numeric(df[col], errors='coerce').sum() > 0:
                    found_col = col
                    break
        
        if found_col:
            df['Standard_MarCap'] = pd.to_numeric(df[found_col], errors='coerce').fillna(0)
        else:
            # 컬럼을 못 찾은 경우, 시가 * 상장주식수 직접 계산 시도 (필요시)
            df['Standard_MarCap'] = 0
            
        return df
    except:
        return pd.DataFrame()

def format_kr_money(val):
    if pd.isna(val) or val <= 0: return "조회 불가"
    if val >= 1_0000_0000_0000:
        return f"{val / 1_0000_0000_0000:.2f}조 원"
    return f"{val / 1_0000_0000:.0f}억 원"

# --- 메인 로직 ---
search_name = st.text_input("종목명 입력 (정확히 입력해주세요):", value="삼성전자")
df_krx = get_verified_krx_data()

if not df_krx.empty:
    try:
        # 종목 검색
        target = df_krx[df_krx['Name'] == search_name].iloc[0]
        s_code = target['Code']
        s_marcap = target['Standard_MarCap']
    except:
        st.warning(f"'{search_name}' 종목을 목록에서 찾을 수 없습니다.")
        st.stop()

    # --- 1. 상단 비교 표 ---
    st.subheader("📊 주요 종목 시가총액 비교")
    bench_codes = ['005930', '000660', '005380', '035420', '035720']
    if s_code not in bench_codes: bench_codes.append(s_code)
    
    summary_df = df_krx[df_krx['Code'].isin(bench_codes)].copy()
    summary_df['시가총액'] = summary_df['Standard_MarCap'].apply(format_kr_money)
    
    st.dataframe(summary_df[['Name', 'Code', '시가총액', 'Market']], use_container_width=True, hide_index=True)

    st.divider()

    # --- 2. 하단 상세 분석 (차트 및 카드) ---
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📈 월봉 캔들 차트 (실시간 데이터)")
        
        # 차트 데이터 가져오기 (FinanceDataReader 실패 시 yfinance 백업)
        df_p = fdr.DataReader(s_code, datetime.datetime.now() - datetime.timedelta(days=1825))
        
        if df_p.empty:
            # yfinance로 시도 (KOSPI는 .KS, KOSDAQ은 .KQ)
            suffix = ".KS" if target['Market'] == 'KOSPI' else ".KQ"
            yf_ticker = s_code + suffix
            df_p = yf.download(yf_ticker, period="5y", interval="1mo")

        if not df_p.empty:
            # 인덱스가 Datetime인지 확인 후 월봉 리샘플링
            df_p.index = pd.to_datetime(df_p.index)
            df_m = df_p.resample('M').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last'})
            
            fig = go.Figure(data=[go.Candlestick(
                x=df_m.index,
                open=df_m['Open'], high=df_m['High'],
                low=df_m['Low'], close=df_m['Close'],
                increasing_line_color='#d62728', decreasing_line_color='#1f77b4'
            )])
            fig.update_layout(template="plotly_dark", height=500, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("차트 데이터를 불러오는 데 실패했습니다.")

    with col2:
        st.subheader("📌 기업 요약 정보")
        st.markdown(f"""
        <div style="background-color: #262730; padding: 25px; border-radius: 15px; border: 2px solid #444;">
            <p style="font-size: 14px; color: #aaa;">Company Name</p>
            <h2 style="margin-top: -10px; color: white;">{search_name}</h2>
            <hr style="border: 0.1px solid #555;">
            <p style="font-size: 16px;"><b>시장:</b> {target['Market']}</p>
            <p style="font-size: 16px;"><b>종목코드:</b> {s_code}</p>
            <p style="font-size: 20px; color: #f04b4b; margin-top: 20px;"><b>시가총액</b></p>
            <p style="font-size: 24px; font-weight: bold;">{format_kr_money(s_marcap)}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.link_button("네이버 증권 상세페이지", f"https://finance.naver.com/item/main.naver?code={s_code}")
