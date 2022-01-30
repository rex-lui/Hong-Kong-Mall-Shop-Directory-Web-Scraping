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
shopcatapi = config['api']['shopcatapi']

def getShopCategory():
    #Create empty DataFrame for shop category
    shopcategory = pd.DataFrame()
    
    api = shopcatapi
    request = requests.get(api)
    response = json.loads(request.content)
    
    for type, i in zip(['Shopping','Dinning'],['shops','dining']):
        for tab in response['site']['en'][i]['category']:
            for cat in tab:
                try:
                    shop_category_id = cat.split('^')[1]
                except:
                    shop_category_id = np.nan
                
                try:
                    shop_category_name = cat.split('^')[0]
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

    api = shoplistapi
    request = requests.get(api)
    response = json.loads(request.content)

    for shop in response['data']['shops']:
        try:
            type = 'Shopping' if shop['shop_type'] == 'shops' else 'Dinning'
        except:
            type = np.nan

        try:
            shop_id = shop['Id']
        except:
            shop_id = np.nan

        try:
            shop_number = shop['Shop_no']
        except:
            shop_number = np.nan

        try:
            shop_floor = shop['Floor']
            shop_floor = shop_floor.replace('LB','LBF').replace('MTR','MTRF').replace('G','GF')
        except:
            shop_floor = np.nan

        try:
            shop_name = shop['Name']
        except:
            shop_name = np.nan

        try:
            shop_name_zh = shop['Cname']
        except:
            shop_name_zh = np.nan

        try:
            phone = shop['Phone'].replace(' ','').replace('<br>',';')
            if phone[0] == ';':
                phone = phone[1:]
        except:
            phone = np.nan

        try:
            opening_hours = shop['Biz_hour'].strip().replace('<br>',';').replace('<br/>',';')
            opening_hours = opening_hours.replace('\r','').replace('\n','').replace('\t','')
        except:
            opening_hours = np.nan

        try:
            loyalty_offer = 'Has iClub Privilege' if shop['Special'] == '1' else 'No iClub Privilege'
        except:
            loyalty_offer = np.nan

        try:
            voucher_acceptance = shop['Coupon']
        except:
            voucher_acceptance = np.nan

        try:
            cat_id1 = shop['Category']
            cat_id2 = shop['Category2']
            shop_category_id = ';'.join(element for element in [cat_id1, cat_id2] if element)
        except:
            shop_category_id = np.nan

        try:
            cat_name1 = shopcategory.loc[shopcategory['shop_category_id'] == cat_id1, 'shop_category_name'].values[0]
            cat_name2 = shopcategory.loc[shopcategory['shop_category_id'] == cat_id2, 'shop_category_name'].values[0] if cat_id2 != '' else ''
            shop_category_name = ';'.join(element for element in [cat_name1,cat_name2] if element)
        except:
            shop_category_name = np.nan

        shoplist = shoplist.append(
                                            {
                                                'type':type,
                                                'shop_id':shop_id,
                                                'shop_name_en':shop_name,
                                                'shop_name_tc':shop_name_zh,
                                                'shop_number':shop_number,
                                                'shop_floor':shop_floor,
                                                'phone':phone,
                                                'opening_hours':opening_hours,
                                                'loyalty_offer':loyalty_offer,
                                                'voucher_acceptance':voucher_acceptance,
                                                'shop_category_id':shop_category_id,
                                                'shop_category_name':shop_category_name
                                                }, ignore_index=True
                                                )

    shopmaster = shoplist
    shopmaster['update_date'] = dt.date.today()
    shopmaster['mall'] = mall
    shopmaster['tag'] = np.nan
    shopmaster = shopmaster.loc[:, ['mall','type','shop_id','shop_name_en','shop_name_tc','shop_number','shop_floor','phone','opening_hours','loyalty_offer','voucher_acceptance','shop_category_id','shop_category_name','tag','update_date']]
    shopmaster = shopmaster.sort_values(['type','shop_id'])
    return shopmaster