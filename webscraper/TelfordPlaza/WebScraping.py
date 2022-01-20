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
shoplistapi = config['api']['shoplistapi']
fnblistapi = config['api']['fnblistapi']

def getShopCategory():
    #Create empty DataFrame for shop category
    shopcategory = pd.DataFrame()
    
    for type, api in zip(['Shopping','Dining'],[shoplistapi,fnblistapi]):
        #Get shop category
        shoplistrequest = requests.get(api)
        shoplistresponse = json.loads(shoplistrequest.content)
        for filter in shoplistresponse['filters']:
             if filter['id'] == 'Cuisine':
                 for cat in filter['inputs']:
                    try:
                        shop_category_id = cat['value']
                    except:
                        shop_category_id = np.nan

                    try:
                        shop_category_name = cat['label']
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
    shopcategory.drop(shopcategory[shopcategory.shop_category_id == 'All'].index, inplace = True)
    shopcategory = shopcategory.loc[:, ['mall','type','shop_category_id','shop_category_name','update_date']]
    return shopcategory

#Get shop master data and export into csv
def getShopMaster():
    shopcategory = getShopCategory()
    #Create empty DataFrame for shop master
    shoplist = pd.DataFrame()
    shoplisttc = pd.DataFrame()

    for type, api in zip(['Shopping','Dining'],[shoplistapi,fnblistapi]):
        shoplistrequest = requests.get(api)
        shoplistresponse = json.loads(shoplistrequest.content)

        for shop in shoplistresponse['shops']:
            try:
                shop_id = shop['shopID']
            except:
                shop_id = np.nan

            try:
                shop_name = shop['text']
            except:
                shop_name = np.nan

            try:
                shop_location = shop['location']['text']
                shop_location_split = shop_location.split(',')
                shop_number = shop_location_split[0]
                shop_floor = (shop_location_split[-1] + ';'.join(shop_location_split[1:-1])).replace('/','').strip()
            except:
                shop_location = np.nan
                shop_number = np.nan
                shop_floor = np.nan

            try:
                phone = shop['tel'].replace(' ','')
            except:
                phone = np.nan

            try:
                opening_hours = shop['time'].strip()
            except:
                opening_hours = np.nan

            try:
                shop_category_id = ';'.join(shop['cuisine'])
            except:
                shop_category_id = np.nan

            try:
                shop_category_name = ';'.join([shopcategory.loc[shopcategory['shop_category_id'] == cat, 'shop_category_name'].values[0] for cat in shop_category_id.split(';')])
            except:
                shop_category_name = np.nan

            try:
                shop_discount = ';'.join([discount['text'] for discount in shop['discount']])
                if 'MTR Points Promotion' in shop_discount:
                    loyalty_offer = 'MTR Points Promotion'
                else:
                    loyalty_offer = np.nan

                if ('Voucher' in shop_discount) or ('Coupon' in shop_discount):
                    voucher_acceptance = '1'
                else:
                    voucher_acceptance = np.nan
            except:
                loyalty_offer = np.nan
                voucher_acceptance = np.nan

            shoplist = shoplist.append(
                                    {
                                        'type':type,
                                        'shop_id':shop_id,
                                        'shop_number':shop_number,
                                        'shop_floor':shop_floor,
                                        'shop_name_en':shop_name,
                                        'phone':phone,
                                        'opening_hours':opening_hours,
                                        'loyalty_offer':loyalty_offer,
                                        'voucher_acceptance':voucher_acceptance,
                                        'shop_category_id':shop_category_id,
                                        'shop_category_name':shop_category_name
                                        }, ignore_index=True
                                        )

        tcapi = api.replace('/en/','/tch/')
        shoplisttcrequest = requests.get(tcapi)
        shoplisttcresponse = json.loads(shoplisttcrequest.content)

        for shop in shoplisttcresponse['shops']:
            try:
                shop_id = shop['shopID']
            except:
                shop_id = np.nan

            try:
                shop_name_zh = shop['text']
            except:
                shop_name_zh = np.nan

            shoplisttc = shoplisttc.append(
                                    {
                                        'type':type,
                                        'shop_id':shop_id,
                                        'shop_name_tc':shop_name_zh
                                        }, ignore_index=True
                                        )
    shopmaster = pd.merge(shoplist, shoplisttc, on = ['type','shop_id'])
    shopmaster['update_date'] = dt.date.today()
    shopmaster['mall'] = mall
    shopmaster['tag'] = np.nan
    shopmaster = shopmaster.loc[:, ['mall','type','shop_id','shop_name_en','shop_name_tc','shop_number','shop_floor','phone','opening_hours','loyalty_offer','voucher_acceptance','shop_category_id','shop_category_name','tag','update_date']]
    return shopmaster