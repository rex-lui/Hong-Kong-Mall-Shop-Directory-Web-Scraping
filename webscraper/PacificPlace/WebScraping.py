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
import ast

#Configure parameter
config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))
mall = config['general']['mall']
shoplisturl = config['url']['shoplisturl']
stylelisturl = config['url']['stylelisturl']
fnblisturl = config['url']['fnblisturl']
shopflooridmapping = eval(config['mapping']['shopflooridmapping'])

#Get shop category data and export into csv
def getShopCategory():
    #Create empty DataFrame for shop category
    shopcategory = pd.DataFrame()

    for type, url in zip(['Shopping','Dining'],[stylelisturl,fnblisturl]):
        #Get shop category
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')

        for category_list in soup.find_all('div', class_ = 'directoryListing__sort--scrollable--scroll'):
            for category in category_list.find_all('li', attrs = {'data-cat': 'shop'}):
                try:
                    shop_category_id = category.find('a').get('href').replace('#','')
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

            for category in category_list.find_all('li', attrs = {'data-cat': 'dine'}):
                try:
                    shop_category_id = category.find('a').get('href').replace('#','')
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
    shopcategory.drop(shopcategory[shopcategory.shop_category_id == '0'].index, inplace = True)
    shopcategory = shopcategory.loc[:, ['mall','type','shop_category_id','shop_category_name','update_date']]
    return shopcategory

def getShopMaster():
    shopcategory = getShopCategory()
    #Create empty DataFrame for shop master
    shoplist = pd.DataFrame()
    shopdetail = pd.DataFrame()

    for type, url in zip(['Shopping','Dining'],[stylelisturl,fnblisturl]):
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')

        directory_items = soup.find('script', text = re.compile('directoryItems')).string
        directory_items_str = directory_items.replace('window.directoryItems = ','')\
                                .replace(';','').replace('\'','\"')\
                                    .replace('id:','"id":').replace('url','"url"').replace('category','"category"').replace('logoUrl','"logoUrl"').replace('title','"title"')\
                                        .replace('description','"description"').replace('location','"location"').replace('floor','"floor"').replace('keywords','"keywords"')\
                                            .replace('itemName','"itemName"').replace('favouriteItemType','"favouriteItemType"').replace('isAbove','"isAbove"').replace('hasOffers','"hasOffers"')\
                                                .replace('hasGifts','"hasGifts"').replace('hasBirthday','"hasBirthday"').replace('type','"type"').replace('alt:','"alt":')\
                                                    .replace('true','True').replace('false','False').strip()
        directory_items_list = eval(directory_items_str)
        for item in directory_items_list:
            try:
                shop_id = item['itemName']
            except:
                shop_id = np.nan

            try:
                shop_number = item['location'].replace('<br>','')
            except:
                shop_number = np.nan

            try:
                shop_floor = item['floor'].split(',')[0]
            except:
                shop_floor = np.nan

            try:
                shop_category_id = item['category'].replace(' ',';')
            except:
                shop_category_id = np.nan

            try:
                shop_category_name = ';'.join([shopcategory.loc[shopcategory['shop_category_id'] == cat, 'shop_category_name'].values[0] for cat in shop_category_id.split(';')])
            except:
                shop_category_name = np.nan

            try:
                shop_detail_link = item['url']
            except:
                shop_detail_link = np.nan

            shoplist = shoplist.append(
                                {
                                    'type':type,
                                    'shop_id':shop_id,
                                    'shop_number':shop_number,
                                    'shop_floor':shop_floor,
                                    'shop_category_id':shop_category_id,
                                    'shop_category_name':shop_category_name,
                                    'shop_detail_link':shop_detail_link
                                    }, ignore_index=True
                                    )

    for url in shoplist['shop_detail_link']:
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')
        for header in soup.find_all('section', class_ = 'standardHeader'):
            try:
                shop_name = header.find('h1', class_ = 'standardHeader__brand--name').text
            except:
                shop_name = np.nan
        
        for detail in soup.find_all('section', class_ = 'shopDetails'):
            try:
                opening_hours = detail.find('div', class_ = 'shopDetails__details--hours').find('a', class_ = 'today').text.replace('Opening Hours','').replace('\r','').replace('\n','').strip()
            except:
                opening_hours = np.nan

            try:
                phone = detail.find('div', class_ = 'shopDetails__details--hours').find('a', class_ = 'icon-phone').text.replace('(852)','').replace(' ','')
            except:
                phone = np.nan

        tcurl = url.replace('/en/','/zh-hk/')
        page = requests.get(tcurl)
        soup = BeautifulSoup(page.content, 'html.parser')
        for header in soup.find_all('section', class_ = 'standardHeader'):
            try:
                shop_name_zh = header.find('h1', class_ = 'standardHeader__brand--name').text
            except:
                shop_name_zh = np.nan

        shopdetail = shopdetail.append(
                    {
                        'shop_detail_link':url,
                        'shop_name_en':shop_name,
                        'shop_name_tc':shop_name_zh,
                        'phone':phone,
                        'opening_hours':opening_hours
                        }, ignore_index=True
                        )

    #Merge shop list and shop detail into shop master
    shopmaster = pd.merge(shoplist, shopdetail, on = 'shop_detail_link')
    shopmaster['update_date'] = dt.date.today()
    shopmaster['mall'] = mall
    shopmaster['shop_floor'] = shopmaster['shop_floor'].map(shopflooridmapping)
    shopmaster['loyalty_offer'] = np.nan
    shopmaster['voucher_acceptance'] = np.nan
    shopmaster['tag'] = np.nan
    shopmaster = shopmaster.loc[:, ['mall','type','shop_id','shop_name_en','shop_name_tc','shop_number','shop_floor','phone','opening_hours','loyalty_offer','voucher_acceptance','shop_category_id','shop_category_name','tag','update_date']]
    return shopmaster