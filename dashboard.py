import streamlit as st
import requests, redis
import config, json
from iex import IEXStock
from helpers import format_number
from datetime import datetime, timedelta

symbol = st.sidebar.text_input("Symbol", value='MSFT')

stock = IEXStock(config.IEX_TOKEN, symbol)

client = redis.Redis(host="localhost", port=6379)

screen = st.sidebar.selectbox("View", ('Overview', 'Fundamentals', 'News', 'Ownership', 'Technicals'), index=1)

st.title(screen)

if screen == 'Overview':
    logo_cache_key = f"{symbol}_logo"
    cached_logo = client.get(logo_cache_key)

    if cached_logo is not None:
        print("found logo in cache")
        logo = json.loads(cached_logo)
    else:
        print("getting logo from api, and then storing it in cache")
        logo = stock.get_logo()
        client.set(logo_cache_key, json.dumps(logo))
        client.expire(logo_cache_key, timedelta(hours=24))
    
    company_cache_key = f"{symbol}_company"
    cached_company_info = client.get(company_cache_key)

    if cached_company_info is not None:
        print("found company news in cache")
        company = json.loads(cached_company_info)
    else:
        print("getting company from api, and then storing it in cache")
        company = stock.get_company_info()
        client.set(company_cache_key, json.dumps(company))
        client.expire(company_cache_key, timedelta(hours=24))

    col1, col2 = st.beta_columns([1, 4])

    with col1:
        st.image(logo['url'])

    with col2:
        st.subheader(company['companyName'])
        st.write(company['industry'])
        st.subheader('Description')
        st.write(company['description'])
        st.subheader('CEO')
        st.write(company['CEO'])


if screen == 'News':
    news_cache_key = f"{symbol}_news"

    news = client.get(news_cache_key)

    if news is not None:
        news = json.loads(news)
    else:
        news = stock.get_company_news()
        client.set(news_cache_key, json.dumps(news))

    for article in news:
        st.subheader(article['headline'])
        dt = datetime.utcfromtimestamp(article['datetime']/1000).isoformat()
        st.write(f"Posted by {article['source']} at {dt}")
        st.write(article['url'])
        st.write(article['summary'])
        st.image(article['image'])


if screen == 'Fundamentals':
    stats_cache_key = f"{symbol}_stats"
    stats = client.get(stats_cache_key)
    
    if stats is None:
        stats = stock.get_stats()
        client.set(stats_cache_key, json.dumps(stats))
    else:
        stats = json.loads(stats)

    st.header('Ratios')

    col1, col2 = st.beta_columns(2)

    with col1:
        st.subheader('P/E')
        st.write(stats['peRatio'])
        st.subheader('Forward P/E')
        st.write(stats['forwardPERatio'])
        st.subheader('PEG Ratio')
        st.write(stats['pegRatio'])
        st.subheader('Price to Sales')
        st.write(stats['priceToSales'])
        st.subheader('Price to Book')
        st.write(stats['priceToBook'])
    with col2:
        st.subheader('Revenue')
        st.write(format_number(stats['revenue']))
        st.subheader('Cash')
        st.write(format_number(stats['totalCash']))
        st.subheader('Debt')
        st.write(format_number(stats['currentDebt']))
        st.subheader('200 Day Moving Average')
        st.write(stats['day200MovingAvg'])
        st.subheader('50 Day Moving Average')
        st.write(stats['day50MovingAvg'])

    fundamentals_cache_key = f"{symbol}_fundamentals"
    fundamentals = client.get(fundamentals_cache_key)

    if fundamentals is None:
        fundamentals = stock.get_fundamentals('quarterly')
        client.set(fundamentals_cache_key, json.dumps(fundamentals))
    else:
        fundamentals = json.loads(fundamentals)

    for quarter in fundamentals:
        st.header(f"Q{quarter['fiscalQuarter']} {quarter['fiscalYear']}")
        st.subheader('Filing Date')
        st.write(quarter['filingDate'])
        st.subheader('Revenue')
        st.write(format_number(quarter['revenue']))
        st.subheader('Net Income')
        st.write(format_number(quarter['incomeNet']))

    st.header("Dividends")

    dividends_cache_key = f"{symbol}_dividends"
    dividends = client.get(dividends_cache_key)

    if dividends is None:
        dividends = stock.get_dividends()
        client.set(dividends_cache_key, json.dumps(dividends))
    else:
        dividends = json.loads(dividends)

    for dividend in dividends:
        st.write(dividend['paymentDate'])
        st.write(dividend['amount'])

if screen == 'Ownership':
    st.subheader("Institutional Ownership")

    institutional_ownership_cache_key = f"{symbol}_institutional"
    institutional_ownership = client.get(institutional_ownership_cache_key)

    if institutional_ownership is None:
        institutional_ownership = stock.get_institutional_ownership()
        client.set(institutional_ownership_cache_key, json.dumps(institutional_ownership))
    else:
        print("getting inst ownership from cache")
        institutional_ownership = json.loads(institutional_ownership)

    for institution in institutional_ownership:
        st.write(institution['date'])
        st.write(institution['entityProperName'])
        st.write(institution['reportedHolding'])

    st.subheader("Insider Transactions")

    insider_transactions_cache_key = f"{symbol}_insider_transactions"

    insider_transactions = client.get(insider_transactions_cache_key)
    if insider_transactions is None:
        insider_transactions = stock.get_insider_transactions()
        client.set(insider_transactions_cache_key, json.dumps(insider_transactions))
    else:
        print("getting insider transactions from cache")
        insider_transactions = json.loads(insider_transactions)
    
    for transaction in insider_transactions:
        st.write(transaction['filingDate'])
        st.write(transaction['fullName'])
        st.write(transaction['transactionShares'])
        st.write(transaction['transactionPrice'])
