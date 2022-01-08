#Import necessary package
import requests
import re
from bs4 import BeautifulSoup
import json
import pandas as pd
import numpy as np
import math
import datetime as dt
import configparser
import os
import html

#Configure parameter
config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))
mall = config['general']['mall']
shoplistapi = config['api']['shoplistapi']
shoplisttcapi = config['api']['shoplisttcapi']
fnblistapi = config['api']['fnblistapi']
fnblisttcapi = config['api']['fnblisttcapi']

#Get shop category data and export into csv
def getShopCategory():
    #Create empty DataFrame for shop category
    shopcategory = pd.DataFrame()
    for type, api in zip(['Shopping','Dining'],[shoplistapi,fnblistapi]):
        #Get shop category
        shoplistrequest = requests.get(api)
        shoplistresponse = json.loads(shoplistrequest.content)
        for cat in [cat for cat in shoplistresponse['modular_content'].keys() if 'shop_primary_tag' in cat or 'restaurant_primary_tag' in cat]:
            try:
                shop_category_id = shoplistresponse['modular_content'][cat]['system']['codename'].replace('shop_primary_tag___','').replace('restaurant_primary_tag___','')
            except:
                shop_category_id = np.nan
            
            try:
                shop_category_name = shoplistresponse['modular_content'][cat]['system']['name'].replace('Shop Primary Tag - ','').replace('Restaurant Primary Tag - ','')
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
    shopcategory = shopcategory.loc[:, ['mall','type','shop_category_id','shop_category_name','update_date']]
    return shopcategory

def getShopMaster():
    #Create empty DataFrame for shop master
    shoplist = pd.DataFrame()
    shoplisttc = pd.DataFrame()
    shopcategory = getShopCategory()

    for type, api, tcapi in zip(['Shopping','Dining'],[shoplistapi,fnblistapi],[shoplisttcapi,fnblisttcapi]):
        shoplistrequest = requests.get(api)
        shoplistresponse = json.loads(shoplistrequest.content)
        for shop in shoplistresponse['items']:
            try:
                shop_id = shop['elements']['url_pattern']['value'].strip()
            except:
                shop_id = np.nan

            try:
                shop_name = shop['elements']['metadata__meta_title']['value'].strip()
            except:
                shop_name = np.nan

            try:
                shop_number = shop['elements']['shop_number']['value'].strip()
            except:
                shop_number = np.nan

            try:
                shop_floor = ';'.join([floor['name'].replace('/','').strip() for floor in shop['elements']['floor']['value']])
            except:
                shop_floor = np.nan

            try:
                phone = shop['elements']['phone']['value'].replace(' ','').replace('\n','').replace('\t','').replace('\r','')
            except:
                phone = np.nan

            try:
                CLEANR = re.compile('<.*?>')
                opening_hours = re.sub(CLEANR, '', html.unescape(shop['elements']['opening_hours']['value'])).replace('\n','').replace('\t','').replace('\r','')
            except:
                opening_hours = np.nan

            try:
                if shop['elements']['is_accept_bespoke_dollar']['value'][0]['codename'] == 'yes':
                    is_accept_bespoke_dollar = 'Accept Bespoke Dollar'
                else:
                    is_accept_bespoke_dollar = 'Not accept Bespoke Dollar'
            except:
                is_accept_bespoke_dollar = ''

            try:
                if shop['elements']['is_accept_point_registration']['value'][0]['codename'] == 'yes':
                    is_accept_point_registration = 'Accept Point Registration'
                else:
                    is_accept_point_registration = 'Not accept Point Registration'
            except:
                is_accept_point_registration = ''

            loyalty_offer_combination = []
            if (is_accept_bespoke_dollar == '') & (is_accept_point_registration == ''):
                loyalty_offer = np.nan
            else:
                if is_accept_bespoke_dollar != np.nan:
                    loyalty_offer_combination.append(is_accept_bespoke_dollar)
                if is_accept_point_registration != np.nan:
                    loyalty_offer_combination.append(is_accept_point_registration)
                loyalty_offer = ';'.join(loyalty_offer_combination)

            try:
                if shop['elements']['accept_landmark_gift_certificate']['value'][0]['codename'] == 'yes':
                    voucher_acceptance = '1'
                else:
                    voucher_acceptance = '0'
            except:
                voucher_acceptance = np.nan

            try:
                shop_category_id = ';'.join([cat.replace('shop_primary_tag___','').replace('restaurant_primary_tag___','') for cat in shop['elements']['primary_tags']['value']])
            except:
                shop_category_id = np.nan

            try:
                shop_category_name_list = [shopcategory.loc[shopcategory['shop_category_id'] == cat, 'shop_category_name'].values[0] for cat in shop_category_id.split(';')]
                shop_category_name = ';'.join(shop_category_name_list)
            except:
                shop_category_name = np.nan

            try:
                tag = ';'.join([cat.replace('shop_sec_tag___','').replace('restaurant_sec_tag___','') for cat in shop['elements']['secondary_tags']['value']])
            except:
                tag = np.nan

            shoplist = shoplist.append(
                            {
                                'type':type,
                                'shop_id':shop_id,
                                'shop_name_en': shop_name,
                                'shop_number':shop_number,
                                'shop_floor':shop_floor,
                                'phone':phone,
                                'opening_hours':opening_hours,
                                'loyalty_offer':loyalty_offer,
                                'voucher_acceptance':voucher_acceptance,
                                'shop_category_id':shop_category_id,
                                'shop_category_name':shop_category_name,
                                'tag':tag
                                }, ignore_index=True
                                )

        shoplisttcrequest = requests.get(tcapi)
        shoplisttcresponse = json.loads(shoplisttcrequest.content)
        for shop in shoplisttcresponse['items']:
            try:
                shop_id = shop['elements']['url_pattern']['value'].strip()
            except:
                shop_id = np.nan

            try:
                shop_name_zh = shop['elements']['metadata__meta_title']['value'].strip()
            except:
                shop_name_zh = np.nan

            shoplisttc = shoplisttc.append(
                            {
                                'shop_id':shop_id,
                                'shop_name_tc': shop_name_zh
                                }, ignore_index=True
                                )
                                

    shopmaster = pd.merge(shoplist, shoplisttc, on = 'shop_id')
    shopmaster['update_date'] = dt.date.today()
    shopmaster['mall'] = mall
    shopmaster = shopmaster.loc[:, ['mall','type','shop_id','shop_name_en','shop_name_tc','shop_number','shop_floor','phone','opening_hours','loyalty_offer','voucher_acceptance','shop_category_id','shop_category_name','tag','update_date']]
    return shopmaster