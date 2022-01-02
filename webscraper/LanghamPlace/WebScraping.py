#%%
#Import necessary package
import requests
from requests.auth import HTTPBasicAuth
import re
from bs4 import BeautifulSoup
import json
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
apikey = config['api']['apikey']
shoplistapi = config['api']['shoplistapi']
fnblistapi = config['api']['fnblistapi']
shopcatapi = config['api']['shopcatapi']
fnbcatapi = config['api']['fnbcatapi']
headers = {
    'Accept': 'application/json',
    'Api-key': apikey,
    'Application': 'website',
    'Locale': 'en'
    }
headerstc = {
    'Accept': 'application/json',
    'Api-key': apikey,
    'Application': 'website',
    'Locale': 'zh-hk'
    }

def getShopCategory():
    #Create empty DataFrame for shop category
    shopcategory = pd.DataFrame()
    for type, api in zip(['Shopping','Dining'],[shopcatapi,fnbcatapi]):
        catrequest = requests.get(api, headers = headers)
        catresponse = json.loads(catrequest.content)

        for cat in catresponse['data']['content']['category_list']:
            try:
                shop_category_id = str(cat['id']).replace('.0','')
            except:
                shop_category_id = np.nan

            try:
                shop_category_name = cat['name']
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
    shopcategory = shopcategory.loc[:, ['mall','type','shop_category_id','shop_category_name','update_date']]
    return shopcategory

def getLastPage(api):
    shoplistrequest = requests.get(api, headers = headers)
    shoplistresponse = json.loads(shoplistrequest.content)
    return shoplistresponse['meta']['last_page']

def getShopMaster():
    shopcategory = getShopCategory()
    #Create empty DataFrame for shop master
    shoplist = pd.DataFrame()
    shoplisttc = pd.DataFrame()

    #Create floor mapping
    shop_floor_id_mapping = {'B3':'B3F','B2':'B2F','B1':'B1F','G':'GF','L1':'1F','L2':'2F','L3':'3F','L4':'4F','L5':'5F','L6':'6F','L7':'7F','L8':'8F','L9':'9F','L10':'10F','L11':'11F','L12':'12F','L13':'13F'}

    for type, api in zip(['Shopping','Dining'],[shoplistapi,fnblistapi]):
        LastPage = getLastPage(api)
        page = 1
        while page <= LastPage:
            api = api + '&page=' + str(page)
            shoplistrequest = requests.get(api, headers = headers)
            shoplistresponse = json.loads(shoplistrequest.content)

            for shop in shoplistresponse['data']:
                try:
                    shop_id = str(shop['id']).replace('.0','')
                except:
                    shop_id = np.nan

                try:
                    shop_name = shop['store_name']
                except:
                    shop_name = np.nan

                try:
                    shop_location = shop['address']['location']
                    shop_floor = shop_location.split(' ')[0]
                    shop_number = ' '.join(shop_location.split(' ')[1:])

                except:
                    shop_floor = np.nan
                    shop_number = np.nan

                try:
                    phone = shop['mobile'].replace(' ','')
                except:
                    phone = np.nan

                try:
                    opening_hours = ';'.join([date['day_of_week'] + ': ' + date['start_time'] + ' - ' + date['end_time'] for date in shop['opening_hour']])
                except:
                    opening_hours = np.nan

                try:
                    if shop['has_lp_voucher'] == True:
                        voucher_acceptance = '1'
                    else:
                        voucher_acceptance = np.nan
                except:
                    voucher_acceptance = np.nan

                try:
                    shop_category_id = str(shop['store_category_id']).replace('.0','')
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
                            'shop_name_en': shop_name,
                            'shop_number':shop_number,
                            'shop_floor':shop_floor,
                            'phone':phone,
                            'opening_hours':opening_hours,
                            'voucher_acceptance':voucher_acceptance,
                            'shop_category_id':shop_category_id,
                            'shop_category_name':shop_category_name
                            }, ignore_index=True
                            )

            shoplisttcrequest = requests.get(api, headers = headerstc)
            shoplisttcresponse = json.loads(shoplisttcrequest.content)
            for shop in shoplisttcresponse['data']:
                try:
                    shop_id = str(shop['id']).replace('.0','')
                except:
                    shop_id = np.nan

                try:
                    shop_name_tc = shop['store_name']
                except:
                    shop_name_tc = np.nan

                shoplisttc = shoplisttc.append(
                        {
                            'shop_id':shop_id,
                            'shop_name_tc': shop_name_tc
                            }, ignore_index=True
                            )
            page = page + 1

    shopmaster = pd.merge(shoplist, shoplisttc, on = 'shop_id')
    shopmaster['update_date'] = dt.date.today()
    shopmaster['mall'] = mall
    shopmaster['loyalty_offer'] = np.nan
    shopmaster['tag'] = np.nan
    shopmaster['shop_floor'] = shopmaster['shop_floor'].map(shop_floor_id_mapping)
    shopmaster = shopmaster.loc[:, ['mall','type','shop_id','shop_name_en','shop_name_tc','shop_number','shop_floor','phone','opening_hours','loyalty_offer','voucher_acceptance','shop_category_id','shop_category_name','tag','update_date']]
    return shopmaster