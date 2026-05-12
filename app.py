import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import datetime
import plotly.graph_objects as go

# 페이지 설정
st.set_page_config(page_title="K-Stock Pro Dashboard", layout="wide")

# 1. 시가총액 및 기초 데이터 로드 (컬럼명 오류 방지)
@st.cache_data(ttl=3600)
def get_krx_list():
    try:
        df = fdr.StockListing('KRX')
        # 시가총액 컬럼명 표준화 (MarCap, Amount, 시가총액 등 대응)
        possible_cols = ['MarCap', 'Amount', '시가총액', 'Stocks']
        for col in possible_cols:
            if col in df.columns:
                df['Standard_MarCap'] = df[col]
                break
        return df
    except:
        return pd.DataFrame()

def format_ko_money(val):
    if pd.isna(val) or val == 0: return "데이터 없음"
    if val >= 1_0000_0000_0000: return f"{val / 1_0000_0000_0000:.1f}조"
    return f"{val / 1_0000_0000:.1f}억"

# --- 메인 로직 ---
st.title("📈 국내 주식 실시간 분석 대시보드")

search_name = st.text_input("종목명을 입력하세요:", value="삼성전자")
df_krx = get_krx_list()

if not df_krx.empty:
    try:
        target = df_krx[df_krx['Name'] == search_name].iloc[0]
        s_code = target['Code']
        s_marcap = target.get('Standard_MarCap', 0)
    except:
        st.error("종목명을 정확히 입력해주세요.")
        st.stop()

    # --- 1. 상단 핵심 지표 표 ---
    st.header(f"📊 {search_name} ({s_code}) 및 주요 종목 비교")
    bench_codes = ['005930', '000660', '005380', '035420', '035720']
    if s_code not in bench_codes: bench_codes.append(s_code)
    
    summary_df = df_krx[df_krx['Code'].isin(bench_codes)].copy()
    summary_df['시가총액'] = summary_df['Standard_MarCap'].apply(format_ko_money)
    
    # 출력용 정렬 및 가공
    display_df = summary_df[['Name', 'Code', '시가총액', 'Market']].sort_values(by='Name')
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.divider()

    # --- 2. 상세 분석 (차트 & 정보) ---
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📅 실시간 월봉 캔들 차트")
        # 데이터 수집 (최근 5년치)
        df_p = fdr.DataReader(s_code, datetime.datetime.now() - datetime.timedelta(days=1825))
        
        if not df_p.empty:
            # 월 단위 리샘플링 (시가, 고가, 저가, 종가 추출)
            df_m = df_p.resample('M').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last'})
            
            # Plotly를 이용한 캔들스틱 차트 생성
            fig = go.Figure(data=[go.Candlestick(
                x=df_m.index,
                open=df_m['Open'],
                high=df_m['High'],
                low=df_m['Low'],
                close=df_m['Close'],
                increasing_line_color= '#FF4B4B', # 상승봉 빨간색
                decreasing_line_color= '#4B91FF'  # 하락봉 파란색
            )])
            fig.update_layout(
                height=500, 
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis_rangeslider_visible=False,
                template="plotly_dark"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("차트 데이터를 불러올 수 없습니다.")

    with col2:
        st.subheader("📋 기업 정보 요약")
        st.markdown(f"""
        <div style="background-color: #1e1e1e; padding: 20px; border-radius: 10px; border: 1px solid #333;">
            <p style="font-size: 18px;"><b>종목명:</b> {search_name}</p>
            <hr style="border: 0.5px solid #444;">
            <p style="font-size: 20px; color: #FF4B4B;"><b>시가총액:</b> {format_ko_money(s_marcap)}</p>
            <p><b>상장시장:</b> {target['Market']}</p>
            <p><b>종목코드:</b> {s_code}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 외부 연결 버튼
        st.write("")
        st.link_button("🎯 네이버 증권 상세 페이지로 이동", f"https://finance.naver.com/item/main.naver?code={s_code}")

else:
    st.error("KRX 데이터를 로드하는 데 실패했습니다.")
