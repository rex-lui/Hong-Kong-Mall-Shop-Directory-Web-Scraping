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

        for category_list in soup.find_all('div', class_ = 'tabs'):
            for category in category_list.find_all('a', attrs = {'data-key': 'categories'}):
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
        for card_grid in soup.find_all('div', class_ = 'card-grid--shop'):
            for card in card_grid.find_all('div', class_ = 'card-grid__item'):
                try:
                    shop_detail_link = card.find('a', class_ = 'has-text-dark-grey').get('href')
                except:
                    shop_detail_link = np.nan

                try:
                    shop_id = shop_detail_link.split('/')[-1]
                except:
                    shop_id = np.nan

                try:
                    shop_name = card.find('a', class_ = 'has-text-dark-grey').text.strip()
                except:
                    shop_name = np.nan

                try:
                    shop_category_id = ';'.join(card.get('data-filter-categories').strip().split('||')[1:])
                except:
                    shop_category_id = np.nan

                try:
                    shop_category_name = ';'.join([shopcategory.loc[shopcategory['shop_category_id'] == cat, 'shop_category_name'].values[0] for cat in shop_category_id.split(';')])
                except:
                    shop_category_name = np.nan

                try:
                    shop_floor = card.get('data-filter-location').strip().split('||')[-1]
                except:
                    shop_floor = np.nan

                shoplist = shoplist.append(
                                    {
                                        'type':type,
                                        'shop_id':shop_id,
                                        'shop_name_en':shop_name,
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
        for content in soup.find_all('div', class_ = 'column has-text-centered is-size-6 is-10-desktop is-offset-1-desktop'):
            for shop_info in content.find_all('div', class_ = 'shop-info'):
                try:
                    shop_number = shop_info.find('i', class_ = 'fa-map-marker-alt').find_parent('div', class_ = 'shop-info__item').text
                    shop_number = shop_number.strip()
                except:
                    shop_number = np.nan

                try:
                    opening_hours = shop_info.find('i', class_ = 'fa-clock').find_parent('div', class_ = 'shop-info__item').text
                    opening_hours = ';'.join(item.strip().replace('\r','').replace('\n','').replace('\t','') for item in opening_hours.split('\r\n'))
                except:
                    opening_hours = np.nan

                try:
                    phone = shop_info.find('i', class_ = 'fa-phone').find_parent('div', class_ = 'shop-info__item').text
                    phone = phone.replace(' ','').replace('\r','').replace('\n','').replace('\t','')
                except:
                    phone = np.nan

        tcurl = combined_url.replace('/en/','/zh-hk/')
        page = requests.get(tcurl)
        soup = BeautifulSoup(page.content, 'html.parser')
        for content in soup.find_all('div', class_ = 'column has-text-centered is-size-6 is-10-desktop is-offset-1-desktop'):
            try:
                shop_name_zh = content.find('h1', class_ = 'title').text
            except:
                shop_name_zh = np.nan

        shopdetail = shopdetail.append(
                    {
                        'shop_detail_link':url,
                        'shop_number':shop_number,
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