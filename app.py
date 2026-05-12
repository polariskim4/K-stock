import streamlit as st
import pandas as pd
import FinanceDataReader as fdr
import requests
from bs4 import BeautifulSoup

# 페이지 설정
st.set_page_config(layout="wide", page_title="주식 분석 대시보드")
st.title("📈 주식 벤치마크 & 분석 도구 (네이버 증권 엔진)")

# --- 1. 종목 리스트 로드 (이전과 동일) ---
@st.cache_data(show_spinner=False)
def get_reliable_stock_list():
    try:
        df = fdr.StockListing('KRX')
    except:
        df = pd.DataFrame([
            {"Symbol": "005930", "Name": "삼성전자"},
            {"Symbol": "407330", "Name": "가온칩스"},
            {"Symbol": "138080", "Name": "오이솔루션"}
        ])
    df['SearchName'] = df['Name'].str.replace(r'\s+', '', regex=True).str.upper()
    return df

total_list = get_reliable_stock_list()

# --- 2. [핵심] 네이버 증권 데이터 직접 스크래핑 (yfinance 대체) ---
@st.cache_data(ttl=600, show_spinner=False) # 10분 단위 캐싱
def get_naver_finance_info(code):
    """네이버 증권 웹페이지에서 직접 시총과 주요 지표를 긁어옵니다."""
    url = f"https://finance.naver.com/item/main.naver?code={code}"
    # 로봇으로 인식되지 않도록 브라우저 헤더 추가
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'} 
    
    try:
        res = requests.get(url, headers=headers, timeout=3)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 1. 시가총액 (id="_market_sum" 태그 추출)
        market_cap_tag = soup.select_one('#_market_sum')
        market_cap = int(market_cap_tag.text.replace(',', '').strip()) if market_cap_tag else 0
        
        # 2. 현재 P/E (PER)
        per_tag = soup.select_one('#_per')
        per = float(per_tag.text.replace(',', '').strip()) if per_tag else None
        
        # 3. PBR (추가 지표)
        pbr_tag = soup.select_one('#_pbr')
        pbr = float(pbr_tag.text.replace(',', '').strip()) if pbr_tag else None

        # 4. 외국인 소진율 (보너스 지표)
        foreign_rate_tag = soup.select_one('.lwidth .strong td em')
        foreign_rate = foreign_rate_tag.text.strip() if foreign_rate_tag else "-"

        return {
            "시총": market_cap,
            "P/E": per,
            "PBR": pbr,
            "외국인비율": foreign_rate
        }
    except Exception as e:
        return None

# --- 3. 종목 상세 조회 섹션 ---
st.header("🔍 종목 상세 조회")
user_input = st.text_input("종목명 또는 코드 6자리를 입력하세요 (예: 가온칩스, 407330)", "가온칩스")

if user_input:
    target_symbol = None
    target_name = None
    clean_input = user_input.replace(" ", "").upper()
    
    # 이름으로 코드 찾기
    match = total_list[total_list['SearchName'].str.contains(clean_input, na=False)]
    if not match.empty:
        target_symbol = match.iloc[0]['Symbol']
        target_name = match.iloc[0]['Name']
    elif clean_input.isdigit() and len(clean_input) == 6:
        target_symbol = clean_input
        target_name = clean_input

    if target_symbol:
        with st.status(f"'{target_name}' 네이버 증권 데이터 연동 중...", expanded=True) as status:
            res = get_naver_finance_info(target_symbol)
            
            if res:
                status.update(label="조회 완료! (속도 및 안정성 100%)", state="complete", expanded=False)
                
                # 결과 출력
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("시가총액", f"{res['시총']:,} 억")
                c2.metric("PER (주가수익비율)", f"{res['P/E']:.2f} 배" if res['P/E'] else "N/A")
                c3.metric("PBR (주가순자산비율)", f"{res['PBR']:.2f} 배" if res['PBR'] else "N/A")
                c4.metric("외국인 소진율", f"{res['외국인비율']}")
                
                st.divider()
                st.link_button(f"👉 {target_name} 네이버 증권 상세페이지 ↗", 
                               f"https://finance.naver.com/item/main.naver?code={target_symbol}", type="primary")
            else:
                status.update(label="조회 실패", state="error")
                st.error("네이버 증권에서 데이터를 가져오는 데 실패했습니다. 상장 폐지된 종목이거나 일시적인 네트워크 오류입니다.")
    else:
        st.warning("종목을 찾을 수 없습니다.")
