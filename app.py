import re
import requests
import streamlit as st
from bs4 import BeautifulSoup

BENCHMARK_STOCKS = [
    {"code": "005930", "name": "삼성전자"},
    {"code": "000660", "name": "SK하이닉스"},
    {"code": "005380", "name": "현대차"},
    {"code": "373220", "name": "LG에너지솔루션"},
    {"code": "105560", "name": "KB금융"},
    {"code": "000720", "name": "현대건설"},
    {"code": "034020", "name": "두산에너빌리티"},
    {"code": "196170", "name": "알테오젠"},
    {"code": "247540", "name": "에코프로비엠"},
    {"code": "240810", "name": "원익IPS"}
]

COMPANY_FILE = "krx_list.xls"
NAVER_SUMMARY_URL = "https://api.finance.naver.com/service/itemSummary.naver?itemcode={code}"
NAVER_COMP_URL = (
    "https://navercomp.wisereport.co.kr/v2/company/ajax/cF1001.aspx?"
    "cmp_cd={code}&fin_typ=4&freq_typ=Y&extY=0&extQ=0&"
    "encparam=ZVlSV1hTL1ZESGlaeUhIdXo4ZXVMQT09"
)
CHART_URL = "https://ssl.pstatic.net/imgfinance/chart/item/candle/month/{code}.png?sidcode=1588806284147"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}


def normalize(text: str) -> str:
    return re.sub(r"\s+", "", text or "").lower()


@st.cache_data(show_spinner=False)
def load_companies():
    with open(COMPANY_FILE, "rb") as f:
        html = f.read().decode("euc-kr", errors="ignore")

    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("table.bbs_tb tr")[1:]
    companies = []
    for row in rows:
        cells = row.find_all("td")
        if len(cells) >= 3:
            name = cells[0].get_text(strip=True)
            market = cells[1].get_text(strip=True)
            code = cells[2].get_text(strip=True)
            companies.append(
                {
                    "company_name": name,
                    "market": market,
                    "code": code,
                    "normalized_name": normalize(name),
                }
            )
    return companies


def search_company(query: str, companies: list):
    q = normalize(query)
    if not q:
        return None
    exact = next((c for c in companies if c["normalized_name"] == q), None)
    if exact:
        return exact
    if query.isdigit():
        exact_code = next((c for c in companies if c["code"] == query), None)
        if exact_code:
            return exact_code
    partial = next((c for c in companies if q in c["normalized_name"] or q in c["code"]), None)
    return partial


def parse_number(value: str):
    if value is None:
        return None
    text = re.sub(r"[^0-9.\-]", "", str(value))
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def format_korean_won(value):
    if value is None:
        return None
    try:
        amount = int(abs(float(value)))
    except (TypeError, ValueError):
        return None
    sign = "-" if float(value) < 0 else ""
    jo = amount // 10000
    eok = amount % 10000
    if jo > 0:
        if eok >= 1000:
            eok_formatted = f"{eok:,}"
        else:
            eok_formatted = str(eok).zfill(4)
        return f"{sign}{jo:,}조 {eok_formatted}억원"
    return f"{sign}{amount:,}억원"


def format_percent(value, digits=1):
    if value is None:
        return None
    try:
        return f"{float(value):.{digits}f}%"
    except (TypeError, ValueError):
        return None


def format_decimal(value, digits=1):
    if value is None:
        return None
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return None


def fetch_item_summary(code: str):
    url = NAVER_SUMMARY_URL.format(code=code)
    headers = {**HEADERS, "Referer": f"https://finance.naver.com/item/main.nhn?code={code}"}
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    return response.json()


def parse_navercomp_financials(html: str):
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    target = None
    for table in tables:
        if table.find(text="매출액"):
            target = table
            break
    if not target:
        return None

    rows = []
    for tr in target.find_all("tr"):
        cells = [td.get_text(strip=True).replace("\xa0", " ") for td in tr.find_all(["th", "td"])]
        if cells:
            rows.append(cells)
    if not rows:
        return None

    header = next((row for row in rows if any(re.match(r"\d{4}/\d{2}", cell) for cell in row)), None)
    if not header:
        return None
    years = [cell.strip() for cell in header[1:]]

    data = {}
    for row in rows:
        if row == header or not row[0] or re.match(r"\d{4}/\d{2}", row[0]):
            continue
        label = row[0].replace(" ", "")
        values = [parse_number(cell) for cell in row[1:1 + len(years)]]
        data[label] = values

    revenue = data.get("매출액")
    operating_profit = data.get("영업이익")
    if not revenue or not operating_profit:
        return None

    actual_indices = [i for i, year in enumerate(years) if not re.search(r"\(E\)|\bE\b", year)]
    if not actual_indices:
        return None
    last = actual_indices[-1]
    prior = actual_indices[-2] if len(actual_indices) >= 2 else max(0, last - 1)

    latest_revenue = revenue[last]
    prior_revenue = revenue[prior]
    latest_profit = operating_profit[last]
    prior_profit = operating_profit[prior]

    revenue_growth = ((latest_revenue - prior_revenue) / prior_revenue * 100) if prior_revenue and prior_revenue > 0 else None
    profit_growth = ((latest_profit - prior_profit) / prior_profit * 100) if prior_profit and prior_profit > 0 else None
    operating_margin = (latest_profit / latest_revenue * 100) if latest_revenue and latest_revenue > 0 else None

    return {
        "revenue": format_korean_won(latest_revenue),
        "operating_profit": format_korean_won(latest_profit),
        "operating_margin": format_percent(operating_margin),
        "revenue_growth": format_percent(revenue_growth),
        "profit_growth": format_percent(profit_growth),
    }


def fetch_navercomp_financials(code: str):
    url = NAVER_COMP_URL.format(code=code)
    headers = {**HEADERS, "Referer": f"https://navercomp.wisereport.co.kr/v2/company/c1010001.aspx?cmp_cd={code}"}
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    return parse_navercomp_financials(response.text)


def get_stock_metrics(code: str):
    summary = fetch_item_summary(code)
    financials = fetch_navercomp_financials(code)

    market_sum = summary.get("marketSum")
    market_cap_value = float(market_sum) / 1000 if market_sum is not None else None

    return {
        "market_cap": format_korean_won(market_cap_value),
        "market_cap_value": market_cap_value,
        "per": format_decimal(summary.get("per"), 1),
        "pbr": format_decimal(summary.get("pbr"), 1),
        "revenue": financials.get("revenue") if financials else "정보 없음",
        "operating_profit": financials.get("operating_profit") if financials else "정보 없음",
        "operating_margin": financials.get("operating_margin") if financials else "정보 없음",
        "revenue_growth": financials.get("revenue_growth") if financials else "정보 없음",
        "profit_growth": financials.get("profit_growth") if financials else "정보 없음",
        "naver_link": f"https://finance.naver.com/item/main.nhn?code={code}",
    }


def render_metrics(stock, metrics):
    st.subheader(f"{stock['company_name']} ({stock['code']})")
    st.markdown(f"**시장:** {stock['market']} | [네이버 금융 링크]({metrics['naver_link']})")
    cols = st.columns(2)
    cols[0].metric("시가총액", metrics["market_cap"] or "정보 없음")
    cols[0].metric("PER", metrics["per"] or "정보 없음")
    cols[0].metric("PBR", metrics["pbr"] or "정보 없음")
    cols[1].metric("매출액", metrics["revenue"])
    cols[1].metric("영업이익", metrics["operating_profit"])
    cols[1].metric("영업이익률", metrics["operating_margin"])
    st.write("---")
    st.markdown("**성장률**")
    cols = st.columns(2)
    cols[0].write(f"- 매출성장률: {metrics['revenue_growth']}")
    cols[1].write(f"- 이익성장률: {metrics['profit_growth']}")
    st.image(CHART_URL.format(code=stock["code"]), caption="네이버 월간 캔들 차트", use_column_width=True)


def render_benchmarks(search_stock, companies):
    benchmark_data = []
    for stock in BENCHMARK_STOCKS:
        try:
            metrics = get_stock_metrics(stock["code"])
            benchmark_data.append(
                {
                    "종목": stock["name"],
                    "시가총액": metrics["market_cap"],
                    "PER": metrics["per"],
                    "PBR": metrics["pbr"],
                    "매출액": metrics["revenue"],
                }
            )
        except Exception:
            benchmark_data.append(
                {
                    "종목": stock["name"],
                    "시가총액": "조회 실패",
                    "PER": "-",
                    "PBR": "-",
                    "매출액": "-",
                }
            )

    benchmark_data.sort(key=lambda item: parse_number(item["시장총액"] if item["시가총액"] != "조회 실패" else "0"), reverse=True)
    st.subheader("벤치마크 비교")
    st.table(benchmark_data)


def main():
    st.set_page_config(page_title="한국 주식 재무 정보 조회", layout="wide")
    st.title("한국 주식 재무 정보 조회")
    st.write("KRX 한글 종목명을 입력하면 Naver 금융 데이터를 기반으로 주요 재무 정보를 표시합니다.")

    companies = load_companies()
    query = st.text_input("종목명 또는 종목코드 입력", value="삼성전자")

    if st.button("조회") or query:
        stock = search_company(query, companies)
        if not stock:
            st.error("검색어와 일치하는 종목을 찾을 수 없습니다. 정확한 한글 종목명을 입력해 주세요.")
            return

        with st.spinner("데이터를 불러오는 중입니다..."):
            try:
                metrics = get_stock_metrics(stock["code"])
                render_metrics(stock, metrics)
            except Exception as ex:
                st.error(f"데이터 조회 중 오류가 발생했습니다: {ex}")
                return

            st.markdown("---")
            st.subheader("벤치마크 종목")
            try:
                benchmark_rows = []
                for bench in BENCHMARK_STOCKS:
                    if bench["code"] == stock["code"]:
                        continue
                    bench_metrics = get_stock_metrics(bench["code"])
                    benchmark_rows.append(
                        {
                            "종목": bench["name"],
                            "시가총액": bench_metrics["market_cap"],
                            "PER": bench_metrics["per"],
                            "PBR": bench_metrics["pbr"],
                        }
                    )
                benchmark_rows.append({
                    "종목": f"{stock['company_name']} (검색)",
                    "시가총액": metrics["market_cap"],
                    "PER": metrics["per"],
                    "PBR": metrics["pbr"],
                })
                st.table(benchmark_rows)
            except Exception as ex:
                st.error(f"벤치마크 데이터를 불러오는 중 오류가 발생했습니다: {ex}")


if __name__ == "__main__":
    main()
