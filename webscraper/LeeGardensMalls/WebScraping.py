#Import necessary package
import requests
import re
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import datetime as dt
import configparser
import os

#Configure parameter
config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))
mall = config['general']['mall']
shoplisturl = config['url']['shoplisturl']
fnblisturl = config['url']['fnblisturl']
shopdetailbasicurl = config['url']['shopdetailbasicurl']
shopfloormapping = eval(config['mapping']['shopfloormapping'])

def getShopCategory():
    #Create empty DataFrame for shop category
    shopcategory = pd.DataFrame()

    for type, url in zip(['Shopping','Dining'],[shoplisturl,fnblisturl]):
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')

        for search_cat in soup.find_all('div', id = 'shopSearchCate'):
            for cat_div in search_cat.find_all('div', text = 'CATEGORY'):
                for cat in cat_div.find_next_sibling('ul').find_all('a', class_ = 'CateCate'):
                    try:
                        shop_category_id = cat.get('title')
                    except:
                        shop_category_id = np.nan

                    try:
                        shop_category_name = cat.text
                    except:
                        shop_category_name = np.nan

                    shopcategory = shopcategory.append(
                            {
                                'type':'Dinning',
                                'shop_category_id':shop_category_id,
                                'shop_category_name':shop_category_name
                                }, ignore_index=True
                                )

    shopcategory['update_date'] = dt.date.today()
    shopcategory['mall'] = mall
    shopcategory.drop(shopcategory[shopcategory.shop_category_id == 'All Categories'].index, inplace = True)
    shopcategory = shopcategory.loc[:, ['mall','type','shop_category_id','shop_category_name','update_date']]
    return shopcategory

def getShopMaster():
    shopcategory = getShopCategory()
    #Create empty DataFrame for shop master
    shoplist = pd.DataFrame()
    shopdetail = pd.DataFrame()

    for type, url in zip(['Shopping','Dining'],[shoplisturl,fnblisturl]):
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')

        for resultTable in soup.find_all('div', id = 'resultTable'):
            for shop in resultTable.find_all('tr'):
                try:
                    shop_id = shop.find('td').find('a').get('title')
                    shop_id = shop_id.replace('\r','').replace('\n','').replace('\t','').strip()
                except:
                    shop_id = np.nan

                try:
                    shop_detail_link = shop.find('td').find('a').get('href')
                except:
                    shop_detail_link = np.nan

                try:
                    shop_category_id = shop.find('td').find('a').find('span').text
                except:
                    shop_category_id = np.nan

                try:
                    shop_category_name = shopcategory.loc[shopcategory['shop_category_id'] == shop_category_id, 'shop_category_name'].values[0]
                except:
                    shop_category_name = np.nan

                try:
                    mall = ''.join([char.capitalize() for char in shop.find('td').find_next_sibling('td').text.split(' ')])
                except:
                    mall = np.nan

                try:
                    shop_number = shop.find('td').find_next_sibling('td').find_next_sibling('td').text
                    shop_number = shop_number.replace('\r','').replace('\n','').replace('\t','').strip()
                except:
                    shop_number = np.nan

                try:
                    shop_floor = mall
                except:
                    shop_floor = np.nan

                shoplist = shoplist.append(
                            {
                                'mall':mall,
                                'type':type,
                                'shop_id':shop_id,
                                'shop_number':shop_number,
                                'shop_floor':shop_floor,
                                'shop_category_id':shop_category_id,
                                'shop_category_name':shop_category_name,
                                'shop_detail_link':shop_detail_link
                                }, ignore_index=True
                                )

    for shop_detail_link in shoplist['shop_detail_link']:
        shopdetailurl = shopdetailbasicurl + shop_detail_link
        page = requests.get(shopdetailurl)
        soup = BeautifulSoup(page.content, 'html.parser')

        for detail in soup.find_all('div', class_ = 'shopDetail'):
            for desc in detail.find_all('div', class_ = 'descPart'):
                try:
                    shop_name = desc.find('h1', itemprop = 'name').text
                    shop_name = shop_name.replace('\r','').replace('\n','').replace('\t','').strip()
                except:
                    shop_name = np.nan

            try:
                phone = ';'.join([str for str in detail.find('span', itemprop = 'telephone').find_parent().strings][1:])
                phone = phone.replace('\r','').replace('\n','').replace('\t','').replace(' ','')
            except:
                phone = np.nan

            try:
                opening_hours = ';'.join([str.replace('\r','').replace('\n','').replace('\t','').strip() for str in detail.find('span', itemprop = 'openingHours').find_parent().strings][1:])
                opening_hours = opening_hours.strip()
            except:
                opening_hours = np.nan

        shopdetailtcurl = shopdetailbasicurl + shop_detail_link.replace('lang=en-US','lang=zh-HK')
        page = requests.get(shopdetailtcurl)
        soup = BeautifulSoup(page.content, 'html.parser')

        for detail in soup.find_all('div', class_ = 'shopDetail'):
            for desc in detail.find_all('div', class_ = 'descPart'):
                try:
                    shop_name_zh = desc.find('h1', itemprop = 'name').text
                    shop_name_zh = shop_name_zh.replace('\r','').replace('\n','').replace('\t','').strip()
                except:
                    shop_name_zh = np.nan

        shopdetail = shopdetail.append(
                            {
                                'shop_detail_link':shop_detail_link,
                                'shop_name_en':shop_name,
                                'shop_name_tc':shop_name_zh,
                                'phone':phone,
                                'opening_hours':opening_hours
                                }, ignore_index=True
                                )

    #Merge shop list and shop detail into shop master
    shopmaster = pd.merge(shoplist, shopdetail, on = 'shop_detail_link')
    shopmaster['update_date'] = dt.date.today()
    shopmaster['loyalty_offer'] = np.nan
    shopmaster['voucher_acceptance'] = np.nan
    shopmaster['tag'] = np.nan
    shopmaster = shopmaster.loc[:, ['mall','type','shop_id','shop_name_en','shop_name_tc','shop_number','shop_floor','phone','opening_hours','loyalty_offer','voucher_acceptance','shop_category_id','shop_category_name','tag','update_date']]
    shopmaster = shopmaster.sort_values(['mall','type'])
    return shopmaster