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

        for category_list in soup.find_all('div', class_ = 'tenant-filter__tab__content', attrs = {'data-key': 'cat'}):
            for category in category_list.find_all('a', class_ = 'tenant-filter__tab__content__link'):
                try:
                    shop_category_id = category.get('data-q')
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
    shopcategory.drop(shopcategory[shopcategory.shop_category_id.isna()].index, inplace = True)
    shopcategory = shopcategory.loc[:, ['mall','type','shop_category_id','shop_category_name','update_date']]
    return shopcategory

def getShopMaster():
    shopcategory = getShopCategory()
    #Create empty DataFrame for shop master
    shoplist = pd.DataFrame()
    shopdetail = pd.DataFrame()
    for type, url in zip(['Shopping','Dining'],[shoplisturl,fnblisturl]):
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')
        for container in soup.find_all('div', class_ = 'tenant-grid__container'):
            for shop in container.find_all('div', class_ = 'tenant-tile'):
                try:
                    shop_category_id = ';'.join(shop.get('data-cat').split('|'))
                except:
                    shop_category_id = np.nan
                
                try:
                    shop_category_name = ';'.join([shopcategory.loc[shopcategory['shop_category_id'] == cat, 'shop_category_name'].values[0] for cat in shop_category_id.split(';')])
                except:
                    shop_category_name = np.nan
                
                try:
                    shop_floor = shop.get('data-level')
                except:
                    shop_floor = np.nan
    
                try:
                    desc = shop.find('div', class_ = 'tenant-tile__text').find('a', class_ = 'tenant-tile__desc')
                    shop_detail_link = desc.get('href')
                    shop_id = shop_detail_link.split('/')[-1]
                except:
                    shop_detail_link = np.nan
                    shop_id = np.nan
                
                shoplist = shoplist.append(
                                        {
                                            'type':type,
                                            'shop_id':shop_id,
                                            'shop_floor':shop_floor,
                                            'shop_category_id':shop_category_id,
                                            'shop_category_name':shop_category_name,
                                            'shop_detail_link':shop_detail_link
                                            }, ignore_index=True
                                            )
    
    for url in shoplist['shop_detail_link']:
        combined_url = shopdetailbasicurl + url
        page = requests.get(combined_url)
        soup = BeautifulSoup(page.content, 'html.parser')
        for container in soup.find_all('div', class_ = 'tenant-info__container'):
            content = container.find('div', class_ = 'column is-6').find_next_sibling('div', class_ = 'column is-6')
            for brand in content.find_all('div', class_ = 'tenant-info__brand'):
                try:
                    shop_name = brand.find('h1', class_ = 'tenant-info__title').text
                except:
                    shop_name = np.nan

            for contact in content.find_all('div', class_ = 'tenant-info__contacts'):
                try:
                    shop_number = contact.find('i', class_ = 'fa-map-marker-alt').find_parent('a').text
                except:
                    shop_number = np.nan

                try:
                    phone = contact.find('i', class_ = 'fa-phone-alt').find_parent('a').text
                    phone = phone.replace(' ','').replace('\r','').replace('\n','').replace('\t','')
                except:
                    phone = np.nan

            for open in content.find_all('div', class_ = 'tenant-info__opening-hours'):
                try:
                    opening_hours = open.find('div', class_ = 'tenant-info__opening-hours__item').text
                    opening_hours = opening_hours.replace('\r',' ').replace('\n',' ').replace('\t','').strip()
                except:
                    opening_hours = np.nan
    
        tcurl = combined_url.replace('/en/','/zh-hk/')
        page = requests.get(tcurl)
        soup = BeautifulSoup(page.content, 'html.parser')
        for container in soup.find_all('div', class_ = 'tenant-info__container'):
            content = container.find('div', class_ = 'column is-6').find_next_sibling('div', class_ = 'column is-6')
            for brand in container.find_all('div', class_ = 'tenant-info__brand'):
                try:
                    shop_name_zh = brand.find('h1', class_ = 'tenant-info__title').text
                except:
                    shop_name_zh = np.nan
    
        shopdetail = shopdetail.append(
                            {
                                'shop_detail_link':url,
                                'shop_number':shop_number,
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