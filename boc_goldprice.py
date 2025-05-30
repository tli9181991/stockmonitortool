import pandas as pd
import requests
from bs4 import BeautifulSoup as bs
# from selenium import webdriver
import time
import os
import sys
from datetime import datetime

import warnings
warnings.filterwarnings("ignore")

LINK = 'https://www.bochk.com/whk/rates/preciousMetal/preciousMetalTradingPrices-enquiry.action?lang=en'
INIT_9999GOLD_PRICE = 8094

def get_gcf_price():
    url = 'https://www.investing.com/commodities/gold-news/'
    
    t_content = requests.get(url, headers = {"User-Agent":  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'})
    content_bs = bs(t_content.content, 'html')
    
    price = content_bs.find('div', {'data-test': 'instrument-price-last'}).text
    price = float(price.replace(',', ''))

    return price

def fetch_gcf_price():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    gcf_price = get_gcf_price()
    df_gcf = pd.DataFrame([{'GC=F': gcf_price}])
    df_gcf.index = [now]
    df_gcf = update_data(df_gcf, "./data/gcf_price.csv")
    return df_gcf

def update_data(df, save_path):
    if os.path.isfile(save_path):
        df_hist = pd.read_csv(save_path, index_col=0)
        cur_dt = df.index[-1]
        last_dt = df_hist.index[-1]
        if str(cur_dt) != str(last_dt):
            df_new = pd.concat([df_hist, df])
            df_new.to_csv(save_path)
        else:
            df_new = df_hist
    else:
        df_new = df
        df_new.to_csv(save_path)
    return df_new

def get_boc_gold_prices():
    request_status = False
    try:
        r = requests.get(LINK,timeout=3)
        request_status = True
    except:
        pass
        
    if not request_status:
        df_buy = pd.read_csv('./data/boc_gold_buy.csv', index_col=0)
        df_sell = pd.read_csv('./data/boc_gold_sell.csv', index_col=0)
        return df_buy, df_sell
    
    full_page = bs(r.content, 'html.parser')
    
    boc_gold_price = full_page.find_all('table')
    
    index = []
    rows_vals = []
    datetime = []
    for table_array in boc_gold_price[0].find_all('tr'):
        if len(table_array.find_all('th')) != 0:
            for th_val in table_array.find_all('th'):
                if th_val.text != '\n':
                    index.append(th_val.text)
        if len(table_array.find_all('td')) == 4:
            rows_val = []
            for td_val in table_array.find_all('td'):
                rows_val.append(td_val.text)
            rows_vals.append(rows_val)
        elif len(table_array.find_all('td')) == 1:
            datetime.append(table_array.find_all('td')[0].text.split(': ')[1].split('\n')[0])
    datetime = pd.to_datetime(datetime)
    
    item_list = []
    sell_list = []
    buy_list = []
    for row_val in rows_vals:
        item_list.append(row_val[0] + "(" + row_val[1] + ")")
        buy_list.append(int(row_val[2].replace(',', '').split('.')[0]))
        sell_list.append(int(row_val[3].replace(',', '').split('.')[0]))
        
    df_buy = pd.DataFrame([buy_list], columns=item_list, index=datetime)
    df_sell = pd.DataFrame([sell_list], columns=item_list, index=datetime)
    
    df_buy = update_data(df_buy, 'boc_gold_buy.csv')
    df_sell = update_data(df_sell, 'boc_gold_sell.csv')
    
    return df_buy, df_sell

if __name__== '__main__':
    last_date_time = ""
    print(f"Init Buy: {INIT_9999GOLD_PRICE}")
    while True:
        df_buy, df_sell = get_boc_gold_prices()
        date_time = df_buy.index[-1]
        last_9999_buy = df_buy['Gold bullion of 0.9999 fineness(10 g)'].iloc[-1]
        last_9999_sell = df_sell['Gold bullion of 0.9999 fineness(10 g)'].iloc[-1]
        
        df_gcf = fetch_gcf_price()
        gcf_price = df_gcf['GC=F'].iloc[-1]
        
        if str(date_time) != str(last_date_time):
            
            sys.stdout.flush()
            print_str = f"\r{date_time}  Last 9999 gold buy: {last_9999_buy}\tsell: {last_9999_sell}\tgc=f: {gcf_price}"
            sys.stdout.write(print_str)
            
            df_buy.index = pd.to_datetime(df_buy.index)
            ax = df_buy['Gold bullion of 0.9999 fineness(10 g)'].plot()  # s is an instance of Series
            fig = ax.get_figure()
            fig.savefig('./data/9999gold_buy_price_plot.png')
            
            last_date_time = date_time
        time.sleep(60)
        # sys.stdout.flush()