#Import necessary package
import requests
import re
from bs4 import BeautifulSoup
import json
import html
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
shopdetailurl = config['url']['shopdetailurl']
shoplistapi = config['api']['shoplistapi']

def getShopCategory():
    #Create empty DataFrame for shop category
    shopcategory = pd.DataFrame()

    #Get shop category
    for type, url in zip(['Shopping','Dining'],[shoplisturl,fnblisturl]):
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser', from_encoding = 'iso-8859-1')

        for cat_list in soup.find_all('div', class_ = 'category-list-items'):
            for cat_list_cat in cat_list.find_all('div', class_ = 'category-list-category'):
                for cat in cat_list_cat.find_all('li'):
                    try:
                        shop_category_id = cat.text.strip()
                    except:
                        shop_category_id = np.nan

                    try:
                        shop_category_name = cat.text.strip()
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
    shopcategory.drop(shopcategory[shopcategory.shop_category_id == 'ALL'].index, inplace = True)
    shopcategory = shopcategory.loc[:, ['mall','type','shop_category_id','shop_category_name','update_date']]
    return shopcategory

#Get shop master data and export into csv
def getShopMaster():
    shopcategory = getShopCategory()
    #Create empty DataFrame for shop master
    shoplist = pd.DataFrame()
    shopdetail = pd.DataFrame()

    #Generate shop list from the mall api
    api = shoplistapi
    shoplistrequest = requests.get(api)
    shoplistresponse = json.loads(shoplistrequest.content)
    for shop in shoplistresponse['search']:
        try:
            shop_id = shop['url']
        except:
            shop_id = np.nan

        try:
            shop_number = shop['url']
        except:
            shop_number = np.nan

        try:
            shop_name = shop['label_en']
        except:
            shop_name = np.nan

        try:
            shop_name_zh = shop['label_tc']
        except:
            shop_name_zh = np.nan

        try:
            type = shop['category']
        except:
            type = np.nan

        shoplist = shoplist.append(
            {
                'type': type,
                'shop_id': str(shop_id),
                'shop_number': shop_number,
                'shop_name_en': shop_name,
                'shop_name_tc': shop_name_zh
            }, ignore_index = True
        )

    for shop_id in shoplist['shop_id'].unique():
        combine_url = shopdetailurl + str(shop_id).replace('&', '%26')
        page = requests.get(combine_url)
        soup = BeautifulSoup(page.content, 'html.parser', from_encoding = 'iso-8859-1')

        for shop_info in soup.find_all('div', class_ = 'shop-info-col'):
            try:
                shop_category_name = ';'.join([cat.text for cat in shop_info.find_all('div', class_ = 'shop-category')])
            except:
                shop_category_name = np.nan

            try:
                shop_category_id = ';'.join([shopcategory.loc[shopcategory['shop_category_name'] == cat, 'shop_category_id'].values[0] for cat in shop_category_name.split(';')])
            except:
                shop_category_id = np.nan

            try:
                phone = shop_info.find('p', class_ = 'shop-phone').text.replace('Telephone: ','').replace(' ','')
            except:
                phone = np.nan

            try:
                opening_hours = shop_info.find('p', class_ = 'shop-time').text.replace('Opening Hours: ','').strip()
            except:
                opening_hours = np.nan

        for shop_map in soup.find_all('section', class_ = 'vc_row shop-map'):
            try:
                shop_floor = shop_map.find('div', class_ = 'shop-map-floor').text.replace('/','').replace('\n','').replace('\r','').replace('\t','')
            except:
                shop_floor = np.nan

            shopdetail = shopdetail.append(
            {
                'shop_id': shop_id,
                'shop_floor':shop_floor,
                'shop_category_id': shop_category_id,
                'shop_category_name': shop_category_name,
                'phone': phone,
                'opening_hours':opening_hours
            }, ignore_index = True
        )

    #Merge shop list and shop detail into shop master
    shopmaster = pd.merge(shoplist, shopdetail, on = 'shop_id')
    shopmaster['update_date'] = dt.date.today()
    shopmaster['mall'] = mall
    shopmaster['loyalty_offer'] = np.nan
    shopmaster['voucher_acceptance'] = np.nan
    shopmaster['tag'] = np.nan
    shopmaster = shopmaster.loc[:, ['mall','type','shop_id','shop_name_en','shop_name_tc','shop_number','shop_floor','phone','opening_hours','loyalty_offer','voucher_acceptance','shop_category_id','shop_category_name','tag','update_date']]
    return shopmaster