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

#Get shop category data and export into csv
def getShopCategory():
    #Create empty DataFrame for shop category
    shopcategory = pd.DataFrame()

    for type, url in zip(['Shopping','Dining'],[shoplisturl,fnblisturl]):
        #Get shop category
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')
        for i in soup.find_all(class_ = 'filter_option_btn category'):
            try:
                shop_category_id = i.get('value')
            except:
                shop_category_id = np.nan

            try:
                shop_category_name = i.text
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
    shopcategory.drop(shopcategory[shopcategory.shop_category_id == '0'].index, inplace = True)
    shopcategory = shopcategory.loc[:, ['mall','type','shop_category_id','shop_category_name','update_date']]
    return shopcategory

#Get shop master data and export into csv
def getShopMaster():
    shopcategory = getShopCategory()
    #Create empty DataFrame for shop master
    shoplist = pd.DataFrame()
    shopdetail = pd.DataFrame()

    #Create floor mapping
    shop_floor_id_mapping = {'1':'B3','2':'B2','3':'B1','4':'GF','5':'1F','6':'2F','7':'3F','8':'4F','9':'5F','10':'6F','11':'7F','12':'8F','13':'9F','14':'9F','15':'10F','16':'11F','17':'12F','18':'13F','20':'14F','21':'15F','22':'17F'}

    for type, url in zip(['Shopping','Dining'],[shoplisturl,fnblisturl]):
        #Get shop list
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')
        for shop in soup.find_all(class_ = 'grid_item_shop'):
            try:
                shop_id = shop.get('shop_id')
            except:
                shop_id = np.nan

            try:
                shop_number = shop.get('shop_number')
            except:
                shop_number = np.nan

            try:
                shop_floor = shop.get('shop_floor_id')
            except:
                shop_floor = np.nan

            try:
                shop_category_id = shop.get('shop_category_id')
            except:
                shop_category_id = np.nan

            try:
                shop_category_name = shopcategory.loc[shopcategory['shop_category_id'] == shop_category_id, 'shop_category_name'].values[0]
            except:
                shop_category_name = np.nan

            try:
                shop_name = shop.get('shop_name')
                if shop_name.find(' img ') == -1:
                    shop_name = shop_name
                else:
                    shop_name = shop_name[:shop_name.find(' img ')]

            except:
                shop_name = np.nan

            try:
                shop_name_zh = shop.get('shop_name_zh')
            except:
                shop_name_zh = np.nan
            
            try:
                if 'zoneA' in shop.find(class_ = 'grid_item_shop_text').find('img').get('src'):
                    fnb_zone = 'ZoneA'
                elif 'zoneB' in shop.find(class_ = 'grid_item_shop_text').find('img').get('src'):
                    fnb_zone = 'ZoneB'
                elif 'zoneC' in shop.find(class_ = 'grid_item_shop_text').find('img').get('src'):
                    fnb_zone = 'ZoneC'
                elif 'zoneD' in shop.find(class_ = 'grid_item_shop_text').find('img').get('src'):
                    fnb_zone = 'ZoneD'
            except:
                fnb_zone = np.nan

            shoplist = shoplist.append(
                {
                    'type':type,
                    'shop_id':shop_id,
                    'shop_name_en': shop_name,
                    'shop_name_tc': shop_name_zh,
                    'tag': fnb_zone,
                    'shop_number':shop_number,
                    'shop_floor':shop_floor,
                    'shop_category_id':shop_category_id,
                    'shop_category_name':shop_category_name
                    }, ignore_index=True
                    )

    #Get shop detail
    for shop_id in shoplist['shop_id']:
        shopdetailurl = shopdetailbasicurl + shop_id
        page = requests.get(shopdetailurl)
        soup = BeautifulSoup(page.content, 'html.parser')

        try:
            item = soup.find(class_ = 'underline', text = 'Phone')
            value = ';'.join([tag.text for tag in item.find_next_siblings('p')])
            phone = value.replace(' ','')
        except:
            phone = np.nan

        try:
            item = soup.find(class_ = 'underline', text = 'Opening Hours')
            value = ';'.join([tag.text for tag in item.find_next_siblings('p')])
            opening_hours = value.strip().replace('        -        ',' - ')
        except:
            opening_hours = np.nan

        try:
            item = soup.find(class_ = 'underline', text = 'VIC Offer')
            value = ';'.join([tag.text for tag in item.find_next_siblings('p')])
            vic_offer = value
        except:
            vic_offer = np.nan
    
        shopdetail = shopdetail.append(
                {
                    'shop_id':shop_id,
                    'phone': phone,
                    'opening_hours': opening_hours,
                    'loyalty_offer':vic_offer
                    }, ignore_index=True
                    )
    
    #Merge shop list and shop detail into shop master
    shopmaster = pd.merge(shoplist, shopdetail, on = 'shop_id')
    shopmaster['update_date'] = dt.date.today()
    shopmaster['mall'] = mall
    shopmaster['voucher_acceptance'] = np.nan
    shopmaster['shop_floor'] = shopmaster['shop_floor'].map(shop_floor_id_mapping)
    shopmaster = shopmaster.loc[:, ['mall','type','shop_id','shop_name_en','shop_name_tc','shop_number','shop_floor','phone','opening_hours','loyalty_offer','voucher_acceptance','shop_category_id','shop_category_name','tag','update_date']]
    return shopmaster