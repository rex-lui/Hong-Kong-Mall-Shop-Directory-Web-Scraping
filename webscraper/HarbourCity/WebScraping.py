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
shoplistapi = config['api']['shoplistapi']
shoplisttcapi = config['api']['shoplisttcapi']
fnblistapi = config['api']['fnblistapi']
fnblisttcapi = config['api']['fnblisttcapi']

#Get shop category data and export into csv
def getShopCategory():
    #Create empty DataFrame for shop category
    shopcategory = pd.DataFrame()

    #Get shop category
    type = 'Shopping'
    url = shoplisturl
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    for listing_category in soup.find_all('div', class_= 'listing__category', attrs = {'data-tab':'category'}):
        for category in listing_category.find_all('button', class_ = 'button'):
            try:
                shop_category_id = category.get('data-filter')
            except:
                shop_category_id = np.nan

            try:
                shop_category_name = category.text
            except:
                shop_category_name = np.nan

            shopcategory = shopcategory.append(
                {
                    'type':type,
                    'shop_category_id':shop_category_id,
                    'shop_category_name':shop_category_name
                    }, ignore_index=True
                    )
    
    type = 'Dining'
    url = fnblisturl
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    for listing_category in soup.find_all('div', class_= 'select-box'):
        for category in listing_category.find_all('option'):
            try:
                shop_category_id = category.get('value')
            except:
                shop_category_id = np.nan

            try:
                shop_category_name = category.text
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
    shopcategory.drop(shopcategory[shopcategory.shop_category_id == 'all'].index, inplace = True)
    shopcategory.drop(shopcategory[shopcategory.shop_category_id == 'All'].index, inplace = True)
    shopcategory = shopcategory.loc[:, ['mall','type','shop_category_id','shop_category_name','update_date']]
    return shopcategory

#Get shop master data and export into csv
def getShopMaster():
    #Create empty DataFrame for shop master
    shoplist = pd.DataFrame()
    shoplisttc = pd.DataFrame()

    for type, api, tcapi in zip(['Shopping','Dining'],[shoplistapi,fnblistapi],[shoplisttcapi,fnblisttcapi]):
        shoplistrequest = requests.get(api)
        shoplistresponse = json.loads(shoplistrequest.content)
        for shop in shoplistresponse:
            try:
                shop_id = int(shop['page_id'])
            except:
                shop_id = np.nan

            try:
                shop_name = shop['title']
            except:
                shop_name = np.nan

            try:
                shop_location = shop['address']
            except:
                shop_location = np.nan

            try:
                if shop['level'] == 'LCX':
                    shop_floor = 'LCX'
                else:
                    shop_floor = shop['level'].replace('L','')\
                        .replace('10','10F').replace('11','11F').replace('12','12F').replace('13','13F').replace('14','14F')\
                            .replace('G','GF').replace('1','1F').replace('2','2F').replace('3','3F').replace('4','4F')\
                                .replace('5','5F').replace('6','6F').replace('7','7F').replace('8','3F').replace('9','9F')\
                                    .replace('1F4FF','14F').replace('1F0F','10F')
            except:
                shop_floor = np.nan

            try:
                shop_number = shop['shop_no']
            except:
                shop_number = np.nan

            try:
                phone = ';'.join(shop['phone']).replace(' ','')
            except:
                phone = np.nan

            try:
                regex_htmltag = re.compile('<.*?>')
                opening_hours = re.sub(regex_htmltag, '', html.parser.unescape(shop['opening_hours_en'])).replace('\n','')
            except:
                opening_hours = np.nan

            if type == 'Shopping':
                try:
                    shop_category_id = ';'.join([category['slug'] for category in shop['category']]).replace('-','')
                except:
                    shop_category_id = np.nan

                try:
                    shop_category_name = ';'.join([html.parser.unescape(category['name']) for category in shop['category']])
                except:
                    shop_category_name = np.nan
            elif type == 'Dining':
                try:
                    shop_category_id = ';'.join([cuisine['slug'] for cuisine in shop['cuisine']]).replace('_','')
                except:
                    shop_category_id = np.nan

                try:
                    shop_category_name = ';'.join([html.parser.unescape(cuisine['name']) for cuisine in shop['cuisine']])
                except:
                    shop_category_name = np.nan

            shoplist = shoplist.append(
                        {
                            'type':type,
                            'shop_id':shop_id,
                            'shop_name_en': shop_name,
                            'shop_location':shop_location,
                            'shop_floor':shop_floor,
                            'shop_number':shop_number,
                            'phone':phone,
                            'opening_hours':opening_hours,
                            'shop_category_id':shop_category_id,
                            'shop_category_name':shop_category_name
                            }, ignore_index=True
                            )

        shoplisttcrequest = requests.get(tcapi)
        shoplisttcresponse = json.loads(shoplisttcrequest.content)
        for shop in shoplisttcresponse:
            try:
                shop_id = int(shop['page_id'])
            except:
                shop_id = np.nan

            try:
                shop_name_zh = shop['title']
            except:
                shop_name_zh = np.nan

            shoplisttc = shoplisttc.append(
                    {
                        'type':type,
                        'shop_id':shop_id,
                        'shop_name_tc': shop_name_zh
                        }, ignore_index=True
                        )

    #Merge shop list eng and tc into shop master
    shopmaster = pd.merge(shoplist, shoplisttc, on = ['type','shop_id'])
    shopmaster['update_date'] = dt.date.today()
    shopmaster['mall'] = mall
    shopmaster['shop_id'] = shopmaster['shop_id'].astype(str)
    shopmaster['shop_id'] = shopmaster['shop_id'].apply(lambda x: x.replace('.0',''))
    shopmaster['shop_floor'] = shopmaster['shop_location'].fillna('') + ' - ' + shopmaster['shop_floor']
    shopmaster['loyalty_offer'] = np.nan
    shopmaster['voucher_acceptance'] = np.nan
    shopmaster['tag'] = np.nan
    shopmaster = shopmaster.loc[:, ['mall','type','shop_id','shop_name_en','shop_name_tc','shop_number','shop_floor','phone','opening_hours','loyalty_offer','voucher_acceptance','shop_category_id','shop_category_name','tag','update_date']]
    return shopmaster