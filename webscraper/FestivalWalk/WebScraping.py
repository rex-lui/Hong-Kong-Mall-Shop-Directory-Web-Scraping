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
shopdetailbasicurl = config['url']['shopdetailbasicurl']
shopfloormapping = eval(config['mapping']['shopfloormapping'])

#Get shop category data and export into csv
def getShopCategory():
    #Create empty DataFrame for shop category
    shopcategory = pd.DataFrame()

    url = shoplisturl
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    for catlist in soup.find_all('ul', class_ = 'cate-list'):
        for cat in catlist.find_all('li'):
            if cat.find(class_ = 'dinning'):
                for a in cat.find_all('a'):
                    try:
                        shop_category_id = a.get('href')
                        catidpos = shop_category_id.find('?cateid=')
                        shop_category_id = shop_category_id[catidpos + 8:]
                    except:
                        shop_category_id = np.nan

                    try:
                        shop_category_name = a.text.replace('\n','')
                    except:
                        shop_category_name = np.nan

                    shopcategory = shopcategory.append(
                        {
                            'type':'Dinning',
                            'shop_category_id':shop_category_id,
                            'shop_category_name':shop_category_name
                            }, ignore_index=True
                            )
            else:
                for a in cat.find_all('a'):
                    try:
                        shop_category_id = a.get('href')
                        catidpos = shop_category_id.find('?cateid=')
                        shop_category_id = shop_category_id[catidpos + 8:]
                    except:
                        shop_category_id = np.nan

                    try:
                        shop_category_name = a.text.replace('\n','')
                    except:
                        shop_category_name = np.nan

                    shopcategory = shopcategory.append(
                        {
                            'type':'Shopping',
                            'shop_category_id':shop_category_id,
                            'shop_category_name':shop_category_name
                            }, ignore_index=True
                            )
                        
    shopcategory['update_date'] = dt.date.today()
    shopcategory['mall'] = mall
    shopcategory['shop_category_id_int'] = shopcategory['shop_category_id'].astype('int')
    shopcategory = shopcategory.sort_values(['shop_category_id_int','type'], ascending = True).reset_index()
    shopcategory.drop_duplicates(['mall','shop_category_id','shop_category_name','update_date'], inplace = True)
    shopcategory = shopcategory.loc[:, ['mall','type','shop_category_id','shop_category_name','update_date']]
    return shopcategory

#Get shop master data and export into csv
def getShopMaster():
    shopcategory = getShopCategory()
    #Create empty DataFrame for shop master
    shoplist = pd.DataFrame()
    shopdetail = pd.DataFrame()

    for shop_category_id in shopcategory['shop_category_id']:
        url = shoplisturl + '?cateid=' + shop_category_id
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')

        for shop in soup.find_all('div', class_ = 'item'):
            try:
                type = shopcategory[shopcategory['shop_category_id'] == shop_category_id]['type'].values[0]
            except:
                type = np.nan
            
            try:
                shop_detail_link = shop.find('a').get('href')
            except:
                shop_detail_link = np.nan

            try:
                shop_id_pos = shop_detail_link.find('/')
                shop_id = shop_detail_link[shop_id_pos+1:]
            except:
                shop_id = np.nan

            try:
                shop_category_name = shopcategory.loc[shopcategory['shop_category_id'] == shop_category_id, 'shop_category_name'].values[0]
            except:
                shop_category_name = np.nan

            shoplist = shoplist.append(
                        {
                            'type':type,
                            'shop_id':shop_id,
                            'shop_category_id':shop_category_id,
                            'shop_category_name':shop_category_name,
                            'shop_detail_link':shop_detail_link
                            }, ignore_index=True
                            )

    shoplist = shoplist.groupby(['type','shop_id','shop_detail_link']).agg(
        shop_category_id = ('shop_category_id', ';'.join),
        shop_category_name = ('shop_category_name', ';'.join)
        ).reset_index()

    for shop_detail_link in shoplist['shop_detail_link']:
        shopdetailurl = shopdetailbasicurl + shop_detail_link
        page = requests.get(shopdetailurl)
        soup = BeautifulSoup(page.content, 'html.parser')

        for shop_info in soup.find_all('div', class_ = 'shop-info'):
            try:
                shop_name = shop_info.find('h1', class_ = 'shop-name').text.replace('\r','').replace('\n','').strip()
            except:
                shop_name = np.nan

            try:
                shop_location = shop_info.find('p', class_ = 'location').text.replace('\r','').replace('\n','').replace('\t','').strip()
                shop_number = shop_location.split('/')[0].replace(' ','')
                phone = shop_location.split('/')[1].replace(' ','').replace('FloorPlan','')

                hyphen_pos = shop_number.find('-')
                shop_floor = shop_number[4:hyphen_pos]

            except:
                shop_location = np.nan
                shop_number = np.nan
                phone = np.nan
                shop_floor = np.nan

            try:
                opening_hours = shop_info.find('p', class_ = 'opening-hour').text.replace('Opening Hours:','').strip()
            except:
                opening_hours = np.nan

            try:
                if shop_info.find('h1', class_ = 'shop-name').find_all(class_ = 'gifticon'):
                    voucher_acceptance = '1'
                else:
                    voucher_acceptance = np.nan
            except:
                voucher_acceptance = np.nan

        shopdetailtcurl = shopdetailurl.replace('en', 'tc')
        page = requests.get(shopdetailtcurl)
        soup = BeautifulSoup(page.content, 'html.parser')

        for shop_info in soup.find_all('div', class_ = 'shop-info'):
            try:
                shop_name_zh = shop_info.find('h1', class_ = 'shop-name').text.replace('\r','').replace('\n','').strip()
            except:
                shop_name_zh = np.nan

        shopdetail = shopdetail.append(
                        {
                            'shop_detail_link':shop_detail_link,
                            'shop_name_en':shop_name,
                            'shop_name_tc':shop_name_zh,
                            'shop_number':shop_number,
                            'shop_floor':shop_floor,
                            'phone':phone,
                            'opening_hours':opening_hours,
                            'voucher_acceptance':voucher_acceptance
                            }, ignore_index=True
                            )

    #Merge shop list and shop detail into shop master
    shopmaster = pd.merge(shoplist, shopdetail, on = 'shop_detail_link')
    shopmaster['update_date'] = dt.date.today()
    shopmaster['mall'] = mall
    shopmaster['shop_floor'] = shopmaster['shop_floor'].map(shopfloormapping)
    shopmaster.loc[shopmaster['shop_number'] =='ShopUG','shop_floor'] = 'UGF'
    shopmaster['loyalty_offer'] = np.nan
    shopmaster['tag'] = np.nan
    shopmaster = shopmaster.loc[:, ['mall','type','shop_id','shop_name_en','shop_name_tc','shop_number','shop_floor','phone','opening_hours','loyalty_offer','voucher_acceptance','shop_category_id','shop_category_name','tag','update_date']]
    return shopmaster