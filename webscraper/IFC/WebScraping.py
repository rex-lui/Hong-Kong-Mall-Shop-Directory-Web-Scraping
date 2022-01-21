#Import necessary package
import requests
import re
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import datetime as dt
import configparser
import os
import json

#Configure parameter
config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))
mall = config['general']['mall']
shoplisturl = config['url']['shoplisturl']
fnblisturl = config['url']['fnblisturl']

def getShopCategory():
    #Create empty DataFrame for shop category
    shopcategory = pd.DataFrame()
    
    for type, url in zip(['Shopping','Dining'],[shoplisturl,fnblisturl]):
        #Get shop category
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')
        for section in soup.find_all('div', class_ = 'section-search-result', id = 'category'):
            for section_filter in section.find_all('div', attrs = {'class': 'section-filter'}):
                for cat in section_filter.find_all('a'):
                    try:
                        shop_category_id = cat.get('href')
                    except:
                        shop_category_id = np.nan

                    try:
                        shop_category_name = cat.text
                    except:
                        shop_category_name = np.nan

                    shopcategory = shopcategory.append(
                            {
                                'type':type,
                                'shop_category_id':shop_category_id,
                                'shop_category_name':shop_category_name
                                }, ignore_index=True
                                )

    shopcategory['update_date'] = dt.date.today()
    shopcategory['mall'] = mall
    shopcategory['shop_category_id'] = shopcategory['shop_category_id'].apply(lambda x:x.replace('#',''))
    shopcategory.drop(shopcategory[shopcategory.shop_category_id == 'all'].index, inplace = True)
    shopcategory = shopcategory.loc[:, ['mall','type','shop_category_id','shop_category_name','update_date']]
    return shopcategory

#Get shop master data and export into csv
def getShopMaster():
    shopcategory = getShopCategory()
    #Create empty DataFrame for shop master
    shoplist = pd.DataFrame()
    shopdetail = pd.DataFrame()

    for type, url in zip(['Shopping','Dining'],[shoplisturl,fnblisturl]):
        #Get shop category
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')

        for section in soup.find_all('div', class_ = 'section-search-result', id = 'category'):
            for inner in section.find_all('div', class_ = 'inner'):
                for shop in inner.find_all('div', attrs = {'data-cate': shopcategory['shop_category_id']}):
                    try:
                        shop_detail_link = shop.find('a', class_ = 'fullLayer').get('href')
                    except:
                        shop_detail_link = np.nan

                    try:
                        if shop_detail_link[-1] == '/':
                            shop_id = shop_detail_link[:-1].split('/')[-1]
                        else:
                            shop_id = shop_detail_link[:-1].split('/')[-1]
                    except:
                        shop_id = np.nan

                    try:
                        shop_category_id = shop.get('data-cate')
                    except:
                        shop_category_id = np.nan

                    try:
                        shop_category_name = shopcategory.loc[shopcategory['shop_category_id'] == shop_category_id, 'shop_category_name'].values[0]
                    except:
                        shop_category_name = np.nan

                    shoplist = shoplist.append(
                                        {
                                            'type':type,
                                            'shop_id':shop_id,
                                            'shop_category_id':shop_category_id,
                                            'shop_category_name':shop_category_name,
                                            'shop_detail_link':shop_detail_link
                                            }, ignore_index=True
                                            )

    for shop_detail_link in shoplist['shop_detail_link'].unique():
        url = shop_detail_link
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')

        for content in soup.find_all('div', class_ = 'content'):
            try:
                shop_name = content.find('div', class_ = 'companyTitle').text.strip()
            except:
                shop_name = np.nan

            for detail in content.find_all('div', class_ = 'col-sm-4'):
                try:
                    shop_location = detail.find('span', text = 'location').find_next_sibling('div')
                    shop_number = shop_location.text.strip()
                    if 'level-1' in shop_location.find('a').get('href'):
                        shop_floor = '1F'
                    elif 'level-2' in shop_location.find('a').get('href'):
                        shop_floor = '2F'
                    elif 'level-3' in shop_location.find('a').get('href'):
                        shop_floor = '3F'
                    elif 'level-4' in shop_location.find('a').get('href'):
                        shop_floor = '4F'
                    else:
                        shop_floor = np.nan
                except:
                    shop_location = np.nan
                    shop_number = np.nan
                    shop_floor = np.nan

                try:
                    opening_hours = detail.find('span', text = 'opening hours').find_next_sibling('div').text.strip().replace('\n','').replace('\r','').replace('\t','')
                except:
                    opening_hours = np.nan

                try:
                    phone = detail.find('span', text = 'phone').find_next_sibling('div').text.replace(' ','').replace('\n','').replace('\r','').replace('\t','')
                except:
                    phone = np.nan

                try:
                    tag = ';'.join(tag.text for tag in detail.find('span', text = 'category').find_next_sibling('div').find_all('a', class_ = 'cate'))
                except:
                    tag = np.nan

        tcurl = url.replace('/mall/','/tc/mall/')
        page = requests.get(tcurl)
        soup = BeautifulSoup(page.content, 'html.parser')

        for content in soup.find_all('div', class_ = 'content'):
            try:
                shop_name_zh = content.find('div', class_ = 'companyTitle').text.strip()
            except:
                shop_name_zh = np.nan

        shopdetail = shopdetail.append(
            {
                'shop_detail_link': shop_detail_link,
                'shop_name_en': shop_name,
                'shop_name_tc': shop_name_zh,
                'shop_number': shop_number,
                'shop_floor': shop_floor,
                'opening_hours': opening_hours,
                'phone': phone,
                'tag': tag
            }, ignore_index = True
        )

    shopmaster = pd.merge(shoplist, shopdetail, on = 'shop_detail_link')
    shopmaster['update_date'] = dt.date.today()
    shopmaster['mall'] = mall
    shopmaster['loyalty_offer'] = np.nan
    shopmaster['voucher_acceptance'] = np.nan
    shopmaster = shopmaster.loc[:, ['mall','type','shop_id','shop_name_en','shop_name_tc','shop_number','shop_floor','phone','opening_hours','loyalty_offer','voucher_acceptance','shop_category_id','shop_category_name','tag','update_date']]
    return shopmaster