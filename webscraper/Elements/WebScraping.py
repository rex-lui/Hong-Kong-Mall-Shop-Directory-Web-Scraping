#%%
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
entertainmentlistapi = config['api']['entertainmentlistapi']
shopdetailurl = config['url']['shopdetailurl']

#%%
def getShopCategory():
    #Create empty DataFrame for shop category
    shopcategory = pd.DataFrame()

    for type, api in zip(['Shopping','Shopping','Dining'],[shoplistapi,entertainmentlistapi,fnblistapi]):
        #Get shop category
        shoplistrequest = requests.get(api)
        shoplistresponse = json.loads(shoplistrequest.content)
        for picker in shoplistresponse['selectPickers']:
            if picker['name'] == 'category':
                for cat in picker['fullLanguageOptions'].keys():
                    try:
                        shop_category_id = picker['fullLanguageOptions'][cat].strip()
                    except:
                        shop_category_id = np.nan

                    try:
                        shop_category_name = cat.split('|')[-1].strip()
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

#%%
#Get shop master data and export into csv
def getShopMaster():
    shopcategory = getShopCategory()
    #Create empty DataFrame for shop master
    shoplist = pd.DataFrame()
    shopdetail = pd.DataFrame()

    for type, api in zip(['Shopping','Shopping','Dining'],[shoplistapi,entertainmentlistapi,fnblistapi]):
        shoplistrequest = requests.get(api)
        shoplistresponse = json.loads(shoplistrequest.content)
        for shop_info in shoplistresponse['shopInfoList']:
            try:
                shop_detail_link = shop_info['slugUrl']
            except:
                shop_detail_link = np.nan

            try:
                shop_id = shop_detail_link.split('/')[-1]
            except:
                shop_id = np.nan

            try:
                shop_name = shop_info['englishName']
            except:
                shop_name = np.nan

            try:
                shop_name_zh = shop_info['tcName']
            except:
                shop_name_zh = np.nan

            try:
                shop_number = shop_info['shopNumber']
                shop_floor = shop_info['zone'] + ' ' + shop_number.split(',')[-1].replace('/', '')
                shop_number = ';'.join(shop_number.split(',')[:-1])
            except:
                shop_number = np.nan
                shop_floor = np.nan

            try:
                voucher_acceptance = shop_info['voucher']
                if voucher_acceptance != '':
                    voucher_acceptance = '1'
                else:
                    np.nan
            except:
                voucher_acceptance = np.nan

            try:
                shop_category_id = shop_info['category']
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
                                    'shop_number':shop_number,
                                    'shop_floor':shop_floor,
                                    'shop_name_en':shop_name,
                                    'shop_name_tc':shop_name_zh,
                                    'shop_category_id':shop_category_id,
                                    'shop_category_name':shop_category_name,
                                    'shop_category_id':shop_category_id,
                                    'shop_category_name':shop_category_name,
                                    'voucher_acceptance':voucher_acceptance,
                                    'shop_detail_link':shop_detail_link
                                    }, ignore_index=True
                                    )

    #Grab additional data from detail page
    for shop_detail_link in shoplist['shop_detail_link']:
        combine_url = shopdetailurl + shop_detail_link
        page = requests.get(combine_url)
        soup = BeautifulSoup(page.content, 'html.parser')

        for content in soup.find_all('div', class_ = 'row shopDetails__info__content'):
            try:
                phone = content.find('div', class_ = 'shopDetails__info__telephone').find('a').text
                phone = phone.strip()
            except:
                phone = np.nan

            try:
                opening_hours = content.find('div', class_ = 'shopDetails__info__time').find('p').text
                opening_hours = opening_hours.strip().replace('\n',' ').replace('\t',' ').replace('\r',' ')
            except:
                opening_hours = np.nan

        shopdetail = shopdetail.append(
                {
                    'shop_detail_link':shop_detail_link,
                    'phone':phone,
                    'opening_hours':opening_hours
                    }, ignore_index=True
                    )

    shopmaster = pd.merge(shoplist, shopdetail, on = 'shop_detail_link')
    shopmaster['update_date'] = dt.date.today()
    shopmaster['mall'] = mall
    shopmaster['loyalty_offer'] = np.nan
    shopmaster['tag'] = np.nan
    shopmaster = shopmaster.loc[:, ['mall','type','shop_id','shop_name_en','shop_name_tc','shop_number','shop_floor','phone','opening_hours','loyalty_offer','voucher_acceptance','shop_category_id','shop_category_name','tag','update_date']]
    return shopmaster