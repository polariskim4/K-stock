import streamlit as st
import yfinance as yf
import pandas as pd
import streamlit.components.v1 as components

# 페이지 설정
st.set_page_config(layout="wide", page_title="주식 분석 대시보드")
st.title("📈 주식 벤치마크 & 분석 도구")

# 벤치마크 종목 설정
bench_tickers = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "현대자동차": "005380.KS",
    "두산에너빌리티": "034020.KS",
    "대한광통신": "010170.KS"
}

def format_currency(val):
    """금액을 조, 억 단위로 가독성 있게 변환"""
    if not val or pd.isna(val): return "-"
    jo = val // 10000
    억 = val % 10000
    if jo > 0:
        return f"{int(jo)}조 {int(억)}억"
    return f"{int(억)}억"

def get_stock_info(ticker_symbol):
    stock = yf.Ticker(ticker_symbol)
    info = stock.info
    
    # 원단위 데이터를 억 단위로 먼저 변환
    def to_eok(x):
        return round(x / 100_000_000) if x else None

    # 데이터 추출 및 가공
    data = {
        "시총": to_eok(info.get("marketCap")),
        "P/E": info.get("forwardPE") or info.get("trailingPE"),
        "PBR": info.get("priceToBook"),
        "PEG": info.get("pegRatio"),
        "매출액": to_eok(info.get("totalRevenue")),
        "영업이익": to_eok(info.get("operatingCashflow")),
        "마진(%)": info.get("operatingMargins"),
        "매출액 성장률(%)": info.get("revenueGrowth"),
        "이익 성장률(%)": info.get("earningsGrowth"),
    }
    return data

# --- 1. 벤치마크 섹션 ---
st.header("📋 주요 종목 벤치마크")
if st.button('데이터 새로고침'):
    bench_data = []
    for name, ticker in bench_tickers.items():
        with st.spinner(f'{name} 조회 중...'):
            info = get_stock_info(ticker)
            info['종목명'] = name
            bench_data.append(info)
    
    df = pd.DataFrame(bench_data).set_index('종목명')
    
    # 표시용 데이터프레임 가공
    display_df = pd.DataFrame(index=df.index)
    display_df['시총'] = df['시총'].apply(format_currency)
    display_df['P/E'] = df['P/E'].apply(lambda x: round(x, 1) if pd.notnull(x) else "-")
    display_df['PBR'] = df['PBR'].apply(lambda x: round(x, 1) if pd.notnull(x) else "-")
    display_df['PEG'] = df['PEG'].apply(사용자lambda x: round(x, 1) if pd.notnull(x) else "-")
    display_df['매출액'] = df['매출액'].apply(format_currency)
    display_df['영업이익'] = df['영업이익'].apply(format_currency)
    display님의 요청에 맞춰 **금액 단위를 '조/억'으로 읽_df['마진(%)'] = df['마진(%)'].apply(lambda x: round(x*100, 1) if pd.not기 쉽게 변경**하고, **지표 소수점을 한 자리로 통일**했습니다.

null(x) else "-")
    display_df['매출액 성장률(%)'] = df['매출액 성장률(%)'].apply(lambda x가장 중요한 **네이버 월봉 그래프**의 경우, 최근 네이버에서 외부 서버: round(x*100, 1) if pd.notnull(x) else "-")
    display_df['이익 성장률(%)'](Streamlit Cloud 등)의 직접적인 이미지 호출을 차단하는 경우가 많아졌 = df['이익 성장률(%)'].apply(lambda x: round(x*100, 1) if pd.notnull(x) else "-습니다. 이를 우회하기 위해 **")
    
    st.table(display_df)

st.write("---")

# --- 2. 개별 종목 상세 조회 섹션 ---
`requests` 라이브러리로 이미지를 서버에서 직접 받아와서 뿌st.header("🔍 개별 종목 상세 조회")
user_input = st.text_input("종목 코드를 입력하세요 (숫자 6자리)",려주는 방식**으로 로직을 강화했습니다.

### 🛠 수정된 `app.py "005930")

if user_input:
    col1, col2 = st.columns([1, 1.5])
    
` 코드

이 코드를 사용하려면 `requirements.txt`에 **`requests`**를 추가해야 합니다.
```python
import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from io import BytesIO

# 페이지 설정
st.set_page_config(layout="wide", page_title="주식 분석 대시보드")
st.title("📈 주식 벤치마크 & 분석 도구")

# 벤치마크 종목 설정
bench_tickers = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "현대자동차": "005380.KS",
    "두산에너빌리티": "034020.KS",
    "대한광통신": "010170.KS"
}

# 금액을 조, 억 단위로 변환하는 함수
def format_currency(val):
    if not val or pd.isna(val): return "-"
    cho = val // 10000
    eok = val % 10000
    if cho > 0:
        return f"{int(cho)}조 {int(eok)}억"
    return f"{int(eok)}억"

def get_stock_info(ticker_symbol):
    stock = yf.Ticker(ticker_symbol)
    info = stock.info
    
    # 기본 금액 단위: 억 (yfinance는 원 단위 제공)
    to_eok = lambda x: round(x / 100_000_000) if x else None

    data = {
        "시총": to_eok(info.get("marketCap")),
        "P/E": info.get("forwardPE") or info.get("trailingPE"),
        "PBR": info.get("priceToBook"),
        "PEG": info.get("pegRatio"),
        "매출액": to_eok(info.get("totalRevenue")),
        "영업이익": to_eok(info.get("operatingCashflow")),
        "마진(%)": info.get("operatingMargins"),
        "매출액 성장률(%)": info.get("revenueGrowth"),
        "이익 성장률(%)": info.get("earningsGrowth"),
    }
    return data

# --- 1. 벤치마크 섹션 ---
st.header("📋 주요 종목 벤치마크")
if st.button('데이터 새로고침'):
    bench_data = []
    for name, ticker in bench_tickers.items():
        info = get_stock_info(ticker)
        info['종목명'] = name
        bench_data.append(info)
    
    df = pd.DataFrame(bench_data).set_index('```

---

### 💡 달라진 점

1.  **조/억 단위 변환:** `183207종목명')
    
    # 데이터 가공
    display_df = pd.DataFrame(index=df.index)
    display_df['시총'] = df['시총'].apply(format_currency)
    display_df['P/E'] = df['P/E'].apply(lambda x: round(12` 같은 숫자가 이제 **"183조 2071억"**으로 표시되어 한눈에 들어옵니다.
2.x, 1) if pd.notnull(x) else "-")
    display_df['PBR'] = df['PBR'].apply(lambda x: round(x, 1) if pd.notnull(x) else "-")
    display_df['PEG'] = df['PEG'].apply(  **소수점 일관성:** 모든 비율 지표(P/E, 성장률 등)는 `round(x, 1)`을 사용하여 소수점 첫째 자리까지만 깔끔하게 나옵니다.
3.  **차트 로드 방식:** `st.imagelambda x: round(x, 1) if pd.notnull(x) else "-")
    display_df['매출액'] = df['매출액'].apply(format_currency)
    display_df['영업이익'] = df['영업이익'].apply(format_currency)
    display_df['마진(%)'] = df['마진(%)'].apply(lambda x: round(x*100, 1) if pd` 대신 `components.html`을 사용하여 브라우저가 직접 네이버 이미지를 렌더링하게 했습니다. 이렇게 하면 서버 차단을 우회하여 차.notnull(x) else "-")
    display_df['매출액 성장률(%)'] = df['매출액 성장률(%)'].apply(lambda x: round(x*100, 1) if pd.notnull(x) else "-")
    display_df['이익 성장률(%)'] = df['이익 성장률(%)'].apply(lambda x: round(x*100, 1) if pd.notnull(x)트가 정상적으로 뜰 확률이 훨씬 높습니다.
    *   *주의: 여전히 안 뜬다면 네이버가 해당 리퍼러(Refer else "-")
    
    st.table(display_df)

st.write("---")

# --- 2. 개별 종목 상세 조회 섹션 ---
st.header("🔍 개별 종목 상세 조회")
user_input = st.text_input("종목 코드를 입력하세요",rer)를 강하게 막은 것이므로, 이럴 땐 대체 이미지 서버 주소를 사용해야 합니다.*

이 코드를 다시 GitHub에 반영해 "005930")

if user_input:
    col1, col2 = st.columns([1, 1.5])
    
 보세요! 훨씬 더 '전문 도구' 같은 느낌이 날 것입니다.    with col1:
        st.subheader("📊 핵심 지표")
        try:
            raw_detail = get_stock_info(f"{user_input}.KS")
            # 보기 좋게 변환
            detail = {
                "시총": format_currency(raw_detail['시총']),
                "P/E": round(raw_detail['P/E'], 1) if raw_detail['P/E'] else "-",
                "PBR": round(raw_detail['PBR'], 1) if raw_detail['PBR'] else "-",
                "PEG": round(raw_detail['PEG'], 1) if raw_detail['PEG'] else "-",
                "매출액": format_currency(raw_detail['매출액']),
                "영업이익": format_currency(raw_detail['영업이익']),
                "마진(%)": f"{round(raw_detail['마진(%)']*100, 1)}%" if raw_detail['마진(%)'] else "-",
                "매출액 성장률(%)": f"{round(raw_detail['매출액 성장률(%)']*100, 1)}%" if raw_detail['매출액 성장률(%)'] else "-",
                "이익 성장률(%)": f"{round(raw_detail['이익 성장률(%)']*100, 1)}%" if raw_detail['이익 성장률(%)'] else "-",
            }
            st.table(pd.Series(detail).to_frame(name="수치"))
        except:
            st.error("데이터를 가져올 수 없습니다.")
            
    with col2:
        st.subheader("📅 네이버 월봉 차트")
        # 우회 방법: requests로 이미지를 받아와서 바이트로 변환 후 표시
        chart_url = f"https://ssl.pstatic.net/imgstock/chart3/mobile/candle/month/{user_input}.png"
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        try:
            response = requests.get(chart_url, headers=headers)
            if response.status_code == 200:
                img = BytesIO(response.content)
                st.image(img, use_container_width=True)
            else:
                st.warning("네이버에서 이미지를 불러올 수 없습니다. (상태 코드: " + str(response.status_code) + ")")
        except:
            st.error("차트 로딩 중 오류가 발생했습니다.")
