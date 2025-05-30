import requests
from bs4 import BeautifulSoup as bs
import yfinance as yf
import pandas as pd
import sys
import time

from selenium import webdriver
import warnings
warnings.filterwarnings("ignore")

def fetch_yf_stock_data(ticker, interval="15m", period="60d", auto_adjust = False):
    df = yf.download(ticker, interval=interval, period=period, auto_adjust = auto_adjust)
    df.dropna(inplace=True)
    df.columns = [col[0] for col in df.columns]
    df.index = df.index.strftime("%Y-%m-%d %H:%M:%S")
    return df[::-1]

def fetch_yfinance_news_data(end_datetime = None, max_sroll = 20):
    link = "https://finance.yahoo.com/news/"
    driver = webdriver.Chrome()
    driver.minimize_window()

    driver.get(link)
    sys.stdout.flush()
    print_str = "\rLoading..."
    sys.stdout.write(print_str)
        
    n_srcoll = 0
    
    END_FATCH = False
    
    last_height = driver.execute_script('return document.body.scrollHeight')
    driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
    while (END_FATCH == False and n_srcoll < max_sroll):
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        time.sleep(10)
        
        sys.stdout.flush()
        print_str = f"\rScrolling {n_srcoll}..."
        sys.stdout.write(print_str)
        
        new_height = driver.execute_script('return document.body.scrollHeight')
        
        full_page = bs(driver.page_source, "html")
        
        last_link = full_page.find_all('li', {'class': 'stream-item story-item yf-1drgw5l'})[-1].find('a').get('href')
        
        content = requests.get(last_link, headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.3"})
        content_bs = bs(content.content, "html")
        
        if content_bs.find('time', {'class': 'byline-attr-meta-time'}) is None:
            sub_driver = webdriver.Chrome()
            sub_driver.minimize_window()
            sub_driver.get(last_link)
            time.sleep(5)
            content_bs = bs(sub_driver.page_source, 'html')
            sub_driver.close()
            
        if content_bs.find('time', {'class': 'byline-attr-meta-time'}) is None:
            continue

        date_time = content_bs.find('time', {'class': 'byline-attr-meta-time'}).get('datetime')

        news_date, news_time = date_time.split('T')
        news_time = news_time.split('.')[0]

        last_news_datetime = pd.to_datetime(news_date + " " +  news_time)
        
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
        
        # if content_bs.find('time', {'class': 'byline-attr-meta-time'}) is None:
        #     sub_driver = webdriver.Chrome()
        #     sub_driver.minimize_window()
        #     sub_driver.get(news_link)
        #     time.sleep(5)
        #     content_bs = bs(sub_driver.page_source, 'html')
        #     sub_driver.close()
            
        if content_bs.find('time', {'class': 'byline-attr-meta-time'}) is None:
            continue
    
        date_time = content_bs.find('time', {'class': 'byline-attr-meta-time'}).get('datetime')

        news_date, news_time = date_time.split('T')
        news_time = news_time.split('.')[0]

        news_datetime = pd.to_datetime(news_date + " " +  news_time)
        
        news_content = " ".join([p.text for p in content_bs.find_all('p')])

        if end_datetime != None:
            delta_s = (news_datetime - end_datetime).total_seconds()
            if delta_s <= 0:
                break
        
        news_data.append({
                'Datetime': news_datetime,
                'headline': headline,
                'source': source,
                'description': description,
                'article': news_content,
                'link': news_link
            })
        
    df_news = pd.DataFrame(news_data)
    if len(df_news) > 0:
        print(f"\nNews collected from {news_data[0]['Datetime']} to {news_data[-1]['Datetime']}")    
    else:
        print("No News updated")
    
    driver.close()
    
    return df_news