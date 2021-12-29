#Import necessary package
import requests
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
shopdetailbasicurl = config['url']['shopdetailbasicurl']
shoplistapi = config['api']['shoplistapi']
shoplisttcapi = config['api']['shoplisttcapi']
fnblistapi = config['api']['fnblistapi']
fnblisttcapi = config['api']['fnblisttcapi']

#Get shop category data and export into csv
def getShopCategory():
    #Create empty DataFrame for shop category
    shopcategory = pd.DataFrame()
    for type, url in zip(['Shopping','Dining'],[shoplisturl,fnblisturl]):
        #Get shop category
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')
        for tab in soup.find_all(class_ = 'tab-content', attrs = {'data-tab-id':'category_id'}):
            for tabtext in tab.find_all('div', class_ = 'tab-text'):
                try:
                    shop_category_id = tabtext.get('data-category-id')
                except:
                    shop_category_id = np.nan

                try:
                    shop_category_name = tabtext.text
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

#Get shop master data and export into csv
def getShopMaster():
    shopcategory = getShopCategory()
    #Create empty DataFrame for shop master
    shoplist = pd.DataFrame()
    shoplisttc = pd.DataFrame()
    shopdetail = pd.DataFrame()

    #Create floor mapping
    floor_list = ['B2F','B1F','GF','1F','2F','3F','4F','5F','6F','7F','8F','9F','10F']

    for type, api, tcapi in zip(['Shopping','Dining'],[shoplistapi,fnblistapi],[shoplisttcapi,fnblisttcapi]):
        shoplistrequest = requests.get(api)
        shoplistresponse = json.loads(shoplistrequest.content)
        for shop in shoplistresponse['items']:
            try:
                shop_id = shop['guid']
            except:
                shop_id = np.nan

            try:
                shop_name = shop['name']
            except:
                shop_name = np.nan

            try:
                exist = set()
                exist_add = exist.add
                shop_location = shop['location'].replace('(10/F)',', 10F')
                shop_location_split = [parts.strip().replace('/','') for parts in shop_location.split(',')]
                shop_location_split = [element.replace('B1','B1F').replace('B2','B2F') for element in shop_location_split]
                shop_location_split = [x for x in shop_location_split if not (x in exist or exist_add(x))]
                shop_floor = ';'.join([parts for parts in shop_location_split if parts in floor_list])
                shop_location_split.remove(shop_floor)
                shop_number = ';'.join(shop_location_split)

            except:
                shop_location = np.nan
                shop_floor = np.nan
                shop_number = np.nan

            try:
                shop_tag = shop['tag']
            except:
                shop_tag = np.nan

            try:
                shop_detaillink = shop['umbraco_link']
            except:
                shop_detaillink = np.nan

            shoplist = shoplist.append(
                    {
                        'type':type,
                        'shop_id':shop_id,
                        'shop_name_en': shop_name,
                        'tag': shop_tag,
                        'shop_number':shop_number,
                        'shop_floor':shop_floor,
                        'shop_detaillink':shop_detaillink
                        }, ignore_index=True
                        )

        shoplisttcrequest = requests.get(tcapi)
        shoplisttcresponse = json.loads(shoplisttcrequest.content)
        for shop in shoplisttcresponse['items']:
            try:
                shop_id = shop['guid']
            except:
                shop_id = np.nan

            try:
                shop_name_zh = shop['name']
            except:
                shop_name_zh = np.nan

            shoplisttc = shoplisttc.append(
                    {
                        'type':type,
                        'shop_id':shop_id,
                        'shop_name_tc': shop_name_zh
                        }, ignore_index=True
                        )

    for shopdetaillink in shoplist['shop_detaillink']:
        shopdetailurl = shopdetailbasicurl + shopdetaillink
        page = requests.get(shopdetailurl)
        soup = BeautifulSoup(page.content, 'html.parser')

        try:
            phone = soup.find('div', class_ = 'icon-phone').find_parent().find_next_sibling('div').find(class_ = 'twsi__info-content-text').text
            phone = phone.replace(' ','').replace('\t','')
        except:
            phone = np.nan

        try:
            opening_hours = soup.find('div', class_ = 'icon-clock').find_parent().find_next_sibling('div').find(class_ = 'twsi__info-content-text').text
        except:
            opening_hours = np.nan
        
        try:
            loyalty_offer = soup.find('div', class_ = 'twsi__kdollar-text').text
        except:
            loyalty_offer = np.nan

        try:
            shop_category_list = [cat.text for cat in soup.find('div', class_ = 'twsi__tag').find_all(class_ = 'twsi__tag-item')]
            shop_category_list = ['Fashion' if item == 'Fashion & Accessories' else item for item in shop_category_list]
            shop_category_name = ';'.join(shop_category_list)

            shop_category_id_list = [shopcategory.loc[shopcategory['shop_category_name'] == cat, 'shop_category_id'].values[0] for cat in shop_category_list]
            shop_category_id = ';'.join(shop_category_id_list)
        except:
            shop_category_name = np.nan
            shop_category_id = np.nan
        
        shopdetail = shopdetail.append(
                    {
                        'shop_detaillink':shopdetaillink,
                        'phone': phone,
                        'opening_hours': opening_hours,
                        'loyalty_offer':loyalty_offer,
                        'shop_category_id':shop_category_id,
                        'shop_category_name':shop_category_name
                        }, ignore_index=True
                        )
        
    #Merge shop list and shop detail into shop master
    shoplist = pd.merge(shoplist, shoplisttc, on = ['type','shop_id'])
    shopmaster = pd.merge(shoplist, shopdetail, on = 'shop_detaillink')
    shopmaster['update_date'] = dt.date.today()
    shopmaster['mall'] = mall
    shopmaster['voucher_acceptance'] = np.nan
    shopmaster = shopmaster.loc[:, ['mall','type','shop_id','shop_name_en','shop_name_tc','shop_number','shop_floor','phone','opening_hours','loyalty_offer','voucher_acceptance','shop_category_id','shop_category_name','tag','update_date']]
    return shopmaster