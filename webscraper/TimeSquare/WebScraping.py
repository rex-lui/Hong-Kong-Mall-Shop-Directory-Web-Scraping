#Import necessary package
from click import option
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
shopflooridmapping = eval(config['mapping']['shopflooridmapping'])

#Get shop category data and export into csv
def getShopCategory():
    #Create empty DataFrame for shop category
    shopcategory = pd.DataFrame()

    for type, url in zip(['Shopping','Dining'],[shoplisturl,fnblisturl]):
        #Get shop category
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')
        for cat_filter in soup.find_all(class_ = 'filter_shop_by_category'):
            for cat in cat_filter.find_all('option'):
                try:
                    shop_category_id = cat.get('value')
                except:
                    shop_category_id = np.nan

                try:
                    shop_category_name = cat.text
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
    shopcategory.drop(shopcategory[shopcategory.shop_category_name == 'All Categories'].index, inplace = True)
    shopcategory = shopcategory.loc[:, ['mall','type','shop_category_id','shop_category_name','update_date']]
    return shopcategory

#Get shop master data and export into csv
def getShopMaster():
    shopcategory = getShopCategory()
    #Create empty DataFrame for shop master
    shoplist = pd.DataFrame()
    shoplisttc = pd.DataFrame()
    shopdetail = pd.DataFrame()

    for type, url in zip(['Shopping','Dining'],[shoplisturl,fnblisturl]):
        #Get shop list
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')
        for shop in soup.find_all('article', class_ = 'shop-item'):
            try:
                shop_detail_link = shop.find('a').get('href')
            except:
                shop_detail_link = np.nan
            try:
                shop_id = shop_detail_link[shop_detail_link.find('shop=') + 5:shop_detail_link.find('shop=') + 41].replace(' ','')
            except:
                shop_id = np.nan

            try:
                shop_number = shop.find('p', class_ = 'floor').text.split(' ')[0].replace('\t','').replace('\n','')
            except:
                shop_number = np.nan

            try:
                shop_floor = shop.get('class')[4]
            except:
                shop_floor = np.nan

            try:
                shop_category_id = shop.get('class')[3]
            except:
                shop_category_id = np.nan

            try:
                shop_category_name = shopcategory.loc[shopcategory['shop_category_id'] == shop_category_id, 'shop_category_name'].values[0]
            except:
                shop_category_name = np.nan

            try:
                shop_name = shop.find('div', class_ = 'shop-name').text.replace('\t','').replace('\n','').replace(' ','')
            except:
                shop_name = np.nan

            try:
                # if '.jpeg' in shop.find('img', style_ = 'background: transparent').get('src'):
                #     fnb_zone = 'ZoneA'
                if '8AF8294E-5295-EC11-B400-00224817122A_202202241716110763.jpeg' in str(shop.find('div', class_ = 'shop-name').find('img')):
                    fnb_zone = 'ZoneB'
                elif 'DE69FB22-F695-EC11-B400-00224817122A_202202251248420186.jpg' in str(shop.find('div', class_ = 'shop-name').find('img')):
                    fnb_zone = 'ZoneC'
                elif 'DE69FB22-F695-EC11-B400-00224817122A_202202251249230660.jpg' in str(shop.find('div', class_ = 'shop-name').find('img')):
                    fnb_zone = 'ZoneD'
                else:
                    fnb_zone = np.nan
            except:
                fnb_zone = np.nan

            shoplist = shoplist.append(
                {
                    'type':type,
                    'shop_id':shop_id,
                    'shop_name_en': shop_name,
                    'tag': fnb_zone,
                    'shop_number':shop_number,
                    'shop_floor':shop_floor,
                    'shop_category_id':shop_category_id,
                    'shop_category_name':shop_category_name,
                    'shop_detail_link': shop_detail_link
                    }, ignore_index=True
                    )
            
        #Get shop list
        url_tc = url.replace('/shop-dine/shopping/','/zh-hant/shop-dine/shopping/').replace('/shop-dine/dine/','/zh-hant/shop-dine/dine/')
        page = requests.get(url_tc)
        soup = BeautifulSoup(page.content, 'html.parser')
        for shop in soup.find_all('article', class_ = 'shop-item'):
            try:
                shop_detail_link = shop.find('a').get('href').replace('/zh-hant/','/')
            except:
                shop_detail_link = np.nan
            
            try:
                shop_id = shop_detail_link[shop_detail_link.find('shop=') + 5:shop_detail_link.find('shop=') + 41].replace(' ','')
            except:
                shop_id = np.nan

            try:
                shop_name_zh = shop.find('div', class_ = 'shop-name').text.replace('\t','').replace('\n','').replace(' ','')
            except:
                shop_name_zh = np.nan
            
            shoplisttc = shoplisttc.append(
                {
                    'shop_id': shop_id,
                    'shop_name_tc': shop_name_zh
                    }, ignore_index=True
            )
    
    #Merge shop list and shop detail into shop master
    shopmaster = shoplist.merge(shoplisttc, on = 'shop_id', how = 'left')
    shopmaster['update_date'] = dt.date.today()
    shopmaster['mall'] = mall
    shopmaster['voucher_acceptance'] = np.nan
    shopmaster['loyalty_offer'] = np.nan
    shopmaster['phone'] = np.nan
    shopmaster['opening_hours'] = np.nan
    # shopmaster['shop_floor'] = shopmaster['shop_floor'].map(shopflooridmapping)
    shopmaster = shopmaster.loc[:, ['mall','type','shop_id','shop_name_en','shop_name_tc','shop_number','shop_floor','phone','opening_hours','loyalty_offer','voucher_acceptance','shop_category_id','shop_category_name','tag','update_date']]
    return shopmaster

# TODO:  Need to fix to extract the phone and open hour of shop