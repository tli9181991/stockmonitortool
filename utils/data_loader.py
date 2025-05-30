import pandas as pd
import os
import yfinance as yf
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

import requests
from bs4 import BeautifulSoup as bs
import numpy as np
import sys

from ta.volatility import BollingerBands, average_true_range
from ta.momentum import RSIIndicator, WilliamsRIndicator
from ta.trend import MACD, SMAIndicator


from selenium import webdriver
from selenium.webdriver.common.by import By

import time

import warnings
warnings.filterwarnings("ignore")

NEWS_DICT = {'GC=F': {'type': 'commodities', 'key': 'gold', 'finviz': 'GLD'},
             'QQQ': {'type': 'etfs', 'key': 'powershares-qqqq', 'finviz': 'QQQ'},
             'SQQQ': {'type': 'etfs', 'key': 'ultrapro-short-qqq', 'finviz': 'SQQQ'},
             'SPY': {'type': 'etfs', 'key': 'spdr-s-p-500', 'finviz': 'SPY'},
             'DX-Y.NYB': {'type': 'indices', 'key': 'usdollar', 'finviz': 'USDU'},
             '^VIX': {'type': 'indices', 'key': 'us-spx-vix-futures', 'finviz': 'VIXY'},
             '^TNX': {'type': 'indices', 'key': '10-year-treasury-yield', 'finviz': 'TLT'},
             'DFDV': {'type': 'equities', 'key': 'janover', 'finviz': 'DFDV'},
             'NVDA': {'type': 'equities', 'key': 'nvidia-corp', 'finviz': 'NVDA'},}

def fetch_yf_stock_data(ticker, interval="15m", period="60d", auto_adjust = False):
    df = yf.download(ticker, interval=interval, period=period, auto_adjust = auto_adjust)
    df.dropna(inplace=True)
    df.columns = [col[0] for col in df.columns]
    df.index = df.index.strftime("%Y-%m-%d %H:%M:%S")
    return df[::-1]

def fetch_yf_stock_data_scrap(ticker):
    url = f"https://finance.yahoo.com/quote/{ticker}/"
    print(f"url: {url}")

    t_content = requests.get(url, headers = {"User-Agent":  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'})
    content_bs = bs(t_content.content, 'html')
    
    price = content_bs.find('span', {'data-testid': 'qsp-price'}).text.replace(' ', '')
    if price == None:
        price = pd.nan
    else:
        price = float(price.replace(',', ''))
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    
    df_price = pd.DataFrame([{'Datetime': now, 'price': price}])
    return df_price

def sracp_daily_yf_data(ticker):
    pass

def fetch_cur_price(ticker):
    t_dict = NEWS_DICT[ticker]
    url = f"https://www.investing.com/{t_dict['type']}/{t_dict['key']}-news/"
    
    t_content = requests.get(url, headers = {"User-Agent":  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'})
    content_bs = bs(t_content.content, 'html')
    
    price = content_bs.find('div', {'data-test': 'instrument-price-last'}).text
    price = float(price.replace(',', ''))

    return price
    
def get_investing_news_content(link):
    driver = webdriver.Chrome()
    driver.minimize_window()
    driver.get(link)
    
    last_height = driver.execute_script('return document.body.scrollHeight')
    max_sroll = 20
    n_srcoll = 0
    article = ''
    
    while n_srcoll < max_sroll:
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        time.sleep(5)
    
        new_height = driver.execute_script('return document.body.scrollHeight')
        if new_height == last_height:
            break
        else:
            # driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
            last_height = new_height
            n_srcoll += 1
    full_page = bs(driver.page_source, 'html')
    p_contents = full_page.find('div', {'id': 'article', 'class': 'article_container'})
    if p_contents is not None:
        article_content = [p_content.text for p_content in p_contents.find_all('p')]

        for content in article_content:
            article += content + ' '
    driver.close()

    return article

def fetch_yfinance_news_data(ticker, end_datetime = None, max_sroll = 20):
    link = f"https://finance.yahoo.com/quote/{ticker}/news/"
    driver = webdriver.Chrome()
    driver.minimize_window()

    driver.get(link)
    sys.stdout.flush()
    print_str = "\rLoading..."
    sys.stdout.write(print_str)
        
    n_srcoll = 0
    
    END_FATCH = False
    
    if end_datetime != None:
        end_datetime = datetime.strptime(end_datetime.strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")
    
    last_height = driver.execute_script('return document.body.scrollHeight')
    driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
    while (END_FATCH == False and n_srcoll < max_sroll):
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        time.sleep(10)
        
        sys.stdout.flush()
        print_str = f"\rScrolling {n_srcoll}..."
        sys.stdout.write(print_str)
        
        new_height = driver.execute_script('return document.body.scrollHeight')
        
        full_page = bs(driver.page_source, 'html')
        
        last_link = full_page.find_all('li', {'class': 'stream-item story-item yf-1drgw5l'})[-1].find('a').get('href')
        
        content = requests.get(last_link, headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.3"})
        content_bs = bs(content.content, 'html')

        date_time = content_bs.find('time', {'class': 'byline-attr-meta-time'}).text

        weekday, mon_date, year, news_time = date_time.split(',')
        month = mon_date.split(' ')[1]
        day = mon_date.split(' ')[2]
        year = year.replace(' ', '')
        news_date = year + "-" + month + "-" + day

        last_news_datetime = pd.to_datetime(news_date + news_time)
        
        if end_datetime != None:
            delta_s = (last_news_datetime - end_datetime).total_seconds()
            if delta_s < 0:
                END_FATCH = True
                break
                
        if new_height == last_height:
            break
        else:
            # driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
            last_height = new_height
            n_srcoll += 1
                
                
    full_page = bs(driver.page_source, 'html')
    
    sys.stdout.flush()
    print_str = "\rNews Collecting..."
    sys.stdout.write(print_str)

    headlines = [soup.text for soup in full_page.find_all('h3', {'class': 'clamp yf-1y7058a'})]
    descriptions = [soup.text for soup in full_page.find_all('p', {'class': 'clamp yf-1y7058a'})]
    sources = [soup.text.split(' • ')[0] for soup in full_page.find_all('div', {'class': 'publishing yf-1weyqlp'})]

    news_links = [li_soup.find('a').get('href') for li_soup in full_page.find_all('li', {'class': 'stream-item story-item yf-1drgw5l'})]
    
    news_data = []
    for headline, description, source, news_link in zip(headlines, descriptions, sources, news_links):
            
        content = requests.get(news_link, headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.3"})
        content_bs = bs(content.content, 'html')
    
        date_time = content_bs.find('time', {'class': 'byline-attr-meta-time'}).text
        weekday, mon_date, year, news_time = date_time.split(',')
        month = mon_date.split(' ')[1]
        day = mon_date.split(' ')[2]
        year = year.replace(' ', '')
        news_date = year + "-" + month + "-" + day
        news_datetime = pd.to_datetime(news_date + news_time)

        if end_datetime != None:
            delta_s = (news_datetime - end_datetime).total_seconds()
            if delta_s <= 0:
                break
        
        news_data.append({
                'Datetime': news_datetime,
                'headline': headline,
                'source': source,
                'description': description,
                'link': news_link
            })
        
    df_news = pd.DataFrame(news_data)
    if len(df_news) > 0:
        print(f"\nNews collected from {news_data[0]['Datetime']} to {news_data[-1]['Datetime']}")    
    else:
        print("No News updated")
    
    driver.close()
    
    return df_news

def fetch_investing_news_data(ticker, end_datetime = None, max_page = 50):
    news_data = []
    page_id = 1
    
    t_dict = NEWS_DICT[ticker]
    END_FATCH = False
    
    if end_datetime == None:
        now = datetime.now()
        end_datetime = now - timedelta(days= 5)
        
    # print(f"url: https://www.investing.com/{t_dict['type']}/{t_dict['key']}-news/")
    url = f"https://www.investing.com/{t_dict['type']}/{t_dict['key']}-news/"
    t_content = requests.get(url, headers = {"User-Agent":  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'})
    content_bs = bs(t_content.content, 'html')
    page_list = content_bs.find_all('div', {'class': 'flex items-center gap-2'})
    if len(page_list) == 0:
        driver = webdriver.Chrome()
        driver.minimize_window()
        driver.get(url)
        time.sleep(5)
        content_bs = bs(driver.page_source, 'html')
        page_list = content_bs.find_all('div', {'class': 'flex items-center gap-2'})
        driver.close()
    for page_list in content_bs.find_all('div', {'class': 'flex items-center gap-2'}):
        if page_list.find('a') != None:
            max_page = min(int(page_list.find_all('a')[-1].text), max_page)    

    while (page_id < max_page and END_FATCH == False):
        url = f"https://www.investing.com/{t_dict['type']}/{t_dict['key']}-news/{page_id}"
        
        sys.stdout.flush()
        print_str = f"\rCollecting page {page_id} {url}"
        sys.stdout.write(print_str)

        t_content = requests.get(url, headers = {"User-Agent":  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'})
        content_bs = bs(t_content.content, 'html')
        news_list= content_bs.find('ul', {'data-test': 'news-list'})
        
        if news_list == None:
            driver = webdriver.Chrome()
            driver.minimize_window()
            driver.get(url)
            time.sleep(5)
            full_page = bs(driver.page_source, 'html')
            news_list= full_page.find('ul', {'data-test': 'news-list'})
            driver.close()
        
        for news_blk in news_list.find_all('li'):
            if news_blk.find('a', {"data-test": "article-title-link"}) is None:
                continue
        
            headline = news_blk.find('a', {"data-test": "article-title-link"}).text
            source = news_blk.find('span', {"data-test": "news-provider-name"}).text
            date_time = news_blk.find('time', {"data-test": "article-publish-date"}).get("datetime")
            date_time = date_time.replace('/', '-')
            date_time = pd.to_datetime(date_time)
            link = news_blk.find('a', {"data-test": "article-title-link"}).get("href")
            
            if end_datetime is not None:
                delta_s = (date_time - end_datetime).total_seconds()
                if delta_s < 0:
                    END_FATCH = True
                    break

            news_data.append({
                'Datetime': date_time,
                'headline': headline,
                'source': source,
                'link': link
            })
        page_id += 1
        
    df_news = pd.DataFrame(news_data)
    if len(df_news) > 0:
        print(f"\nNews collected from {news_data[0]['Datetime']} to {news_data[-1]['Datetime']}")    
    else:
        print("No News updated")
    return df_news

def fetch_finviz_news_data(ticker):
    t_dict = NEWS_DICT[ticker]
    finviz_ticker = t_dict['finviz']
    
    headlines = []
    news_dict = []
    date = datetime.now().strftime('%b-%d-%y')
    
    url = f"https://finviz.com/quote.ashx?t={finviz_ticker}"
    
    content = requests.get(url, headers = {"User-Agent":  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'})
    content_bs = bs(content.content, 'html')
    news_table = content_bs.find('table', {'id': 'news-table'})
    
    for new_items in news_table.find_all('tr'):
        if len(new_items.find_all('a')) > 0:
            link = new_items.find('a').get("href")
            headline = new_items.find('a').text
            
            if link[:4] != 'http':
                link = 'https://finviz.com' + link
            date_time = ''
            for item in new_items.find('td', {'align': 'right'}).text.replace('\r\n', '').split(' '):
                if item != '\r\n' and item != '':
                    date_time += item + ' '
                    
            date_time = date_time[:-1]
            if len(date_time.split(' ')) == 1:
                time = date_time.split(' ')[0]
            else:
                date, time = date_time.split(' ')
                
            if headline not in headlines:
                news_dict.append({'date': date, 'time': time, 'headline': headline, 'link': link})
                headlines.append(headline)
    df_new = pd.DataFrame(news_dict)
    df_new['date'] = np.where(df_new['date'] == 'Today', datetime.now().strftime('%b-%d-%y'), df_new['date'])
    df_new['Datetime'] = pd.to_datetime(df_new['date'] + ' ' + df_new['time'])
    
    return df_new[['Datetime', 'headline', 'link']]
    

def update_news_data(df_old, ticker, source = 'investing'):
    if type(df_old['datetime'].iloc[0]) == type('str'):
        end_datetime = pd.to_datetime(df_old['Datetime'].iloc[0])
    else:
        end_datetime = df_old['Datetime'].iloc[0]

    if source == 'investing':
        df_new = fetch_investing_news_data(ticker, end_datetime = end_datetime)
    elif source == 'yfinance':
        df_new = fetch_yfinance_news_data(ticker, end_datetime = end_datetime)
    else:
        raise RuntimeError(f"Source not found: {source}")
        
    if len(df_new) > 0:
        df_merge = pd.concat([df_new, df_old], ignore_index=True)
        return df_merge
    else:
        return df_old.copy()

def add_technical_indicator(df_stock):
    df = df_stock.copy()
    
    # BollingerBands
    bb = BollingerBands(df['Close'], window = 20, window_dev = 2)
    df['bb_bbm'] = bb.bollinger_mavg()
    df['bb_bbh'] = bb.bollinger_hband()
    df['bb_bbl'] = bb.bollinger_lband()
    
    df['bb_bbhi'] = bb.bollinger_hband_indicator() # close price > hight band
    df['bb_bbli'] = bb.bollinger_lband_indicator() # close price < lower band
    
    def get_bb_signal(df):
        if df['bb_bbhi'] == 1:
            return 1
        elif df['bb_bbli'] == 1:
            return -1
        else:
            return 0
    df['bb_signal'] = df.apply(get_bb_signal, axis = 1)
    
    # rsi
    rsi = RSIIndicator(df["Close"], window=20)
    df['rsi'] = rsi.rsi()
    
    # macd
    macd = MACD(df['Close'], window_slow=26, window_fast=12, window_sign=9)
    df['MACD'] = macd.macd()
    df['MACD_signal'] = macd.macd_signal()
    df['MACD_diff'] = macd.macd_diff()
    
    def get_sign(x):
      if x > 0:
        return 1
      else:
        return -1
    
    df['MACDD_sign'] = df['MACD_diff'].apply(get_sign)
    df['MACDD_sign_shift'] = df['MACDD_sign'].shift()
    
    def get_macdd_signal(df):
      prev_sign = df['MACDD_sign_shift']
      cur_sign = df['MACDD_sign']
      change_sign = prev_sign * cur_sign
      if change_sign == 1:
        return 0
      elif prev_sign < 0:
        return 1
      else:
        return -1
    
    df['MACDD_sign_signal'] = df.apply(get_macdd_signal, axis = 1)
    
    # Williams R Indicator
    williamR = WilliamsRIndicator(df['High'], df["Low"], df["Close"], lbp=14)
    df['WilliamsR'] = williamR.williams_r()
    
    def get_williamRSignal(x):
        if x > -20:
            return 1
        elif x < -80:
            return -1
        else:
            return 0
    df['WilliamsR_signal'] = df['WilliamsR'].apply(get_williamRSignal)
    
    sma10 =  SMAIndicator(df["Close"], window=10)
    sma20 =  SMAIndicator(df["Close"], window=20)
    sma50 =  SMAIndicator(df["Close"], window=50)
    sma200 =  SMAIndicator(df["Close"], window=200)    
    
    df['sma10'] = sma10.sma_indicator()
    df['sma20'] = sma20.sma_indicator()
    df['sma50'] = sma50.sma_indicator()
    df['sma200'] = sma200.sma_indicator()
    
    def get_sma_signal(df):
        if df['sma50'] > df['sma200']:
            return 1
        if df['sma50'] < df['sma200']:
            return -1
        
        return 0

    df['sma_signal'] = df.apply(get_sma_signal, axis = 1)
    
    # ATR
    df['ATR10'] = average_true_range(
                                high=df['High'], 
                                low=df['Low'], 
                                close=df['Close'], 
                                window=10
                            )
    
    df['ATR20'] = average_true_range(
                                high=df['High'], 
                                low=df['Low'], 
                                close=df['Close'], 
                                window=20
                            )
    
    rsi_indicator = RSIIndicator(close=df['Close'], window=14)
    df['RSI'] = rsi_indicator.rsi()
    
    return df