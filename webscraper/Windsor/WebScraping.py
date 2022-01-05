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

        for category_selected in soup.find_all('select', class_ = 'categorySelected'):
            for cat in category_selected.find_all('option'):
                try:
                    shop_category_id = cat.get('value')
                except:
                    shop_category_id = np.nan

                try:
                    shop_category_name = cat.text.split('\r\n')[0].strip()
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
        shopcategory.drop(shopcategory[shopcategory.shop_category_name == 'All'].index, inplace = True)
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
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')

        for shop in soup.find_all('div', class_ = 'shop'):
            try:
                shop_floor = shop.get('floorid').replace('/','').strip()
            except:
                shop_floor = np.nan

            try:
                shop_category_id = shop.get('catid')
            except:
                shop_category_id = np.nan

            try:
                shop_category_name = shopcategory.loc[shopcategory['shop_category_id'] == shop_category_id, 'shop_category_name'].values[0]
            except:
                shop_category_name = np.nan

            for shop_body in shop.find_all('div', class_= 'card shop-body'):
                for shop_content in shop_body.find_all('div', class_= 'card-body shop-body-content'):
                    try:
                        shop_detail_link = shop_content.find(class_= 'card-title').find('a').get('href')
                        shoplinkid = shop_detail_link.find('&id=')
                        shop_id = shop_detail_link[shoplinkid+4:].replace('&lang=en','')
                    except:
                        shop_detail_link = np.nan
                        shop_id = np.nan

                    try:
                        shop_name = shop_content.find(class_= 'card-title').find('a').text
                    except:
                        shop_name = np.nan

                    try:
                        shop_number = shop_content.find(src = re.compile('ShopDetail_icon_shopNo')).find_parent('td').find_next_sibling('td').find_next_sibling('td').text
                    except:
                        shop_number = np.nan

                for shop_footer in shop_body.find_all('div', class_= 'card-footer'):
                    try:
                        if shop_footer.find(class_ = 'shop-tag-club'):
                            loyalty_offer = 'WINDSOR CLUB Offer'
                        else:
                            loyalty_offer = np.nan
                    except:
                        loyalty_offer = np.nan

                    try:
                        if shop_footer.find(class_ = 'shop-tag-coupon'):
                            voucher_acceptance = '1'
                        else:
                            voucher_acceptance = np.nan
                    except:
                        voucher_acceptance = np.nan

            shoplist = shoplist.append(
                                {
                                    'type':type,
                                    'shop_id':shop_id,
                                    'shop_name_en':shop_name,
                                    'shop_number':shop_number,
                                    'shop_floor':shop_floor,
                                    'shop_category_id':shop_category_id,
                                    'shop_category_name':shop_category_name,
                                    'loyalty_offer':loyalty_offer,
                                    'voucher_acceptance':voucher_acceptance,
                                    'shop_detail_link':shop_detail_link
                                    }, ignore_index=True
                                    )

        urltc = url.replace('en','tc')
        page = requests.get(urltc)
        soup = BeautifulSoup(page.content, 'html.parser')

        for shop in soup.find_all('div', class_ = 'shop'):
            for shop_body in shop.find_all('div', class_= 'card shop-body'):
                for shop_content in shop_body.find_all('div', class_= 'card-body shop-body-content'):
                    try:
                        shop_detail_link = shop_content.find(class_= 'card-title').find('a').get('href')
                        shoplinkid = shop_detail_link.find('&id=')
                        shop_id = shop_detail_link[shoplinkid+4:].replace('&lang=tc','')
                    except:
                        shop_detail_link = np.nan
                        shop_id = np.nan

                    try:
                        shop_name_zh = shop_content.find(class_= 'card-title').find('a').text
                    except:
                        shop_name_zh = np.nan

            shoplisttc = shoplisttc.append(
                                {
                                    'shop_id':shop_id,
                                    'shop_name_tc':shop_name_zh
                                    }, ignore_index=True
                                    )

    for shop_detail_link in shoplist['shop_detail_link']:
        shopdetailurl = shopdetailbasicurl + shop_detail_link
        page = requests.get(shopdetailurl)
        soup = BeautifulSoup(page.content, 'html.parser')

        for shop_detail in soup.find_all('div', class_ = 'shop-detail'):
            for shop_table in shop_detail.find_all('table', class_ = 'shop-table'):
                try:
                    opening_hours = shop_table.find(src = re.compile('ShopDetail_icon_time')).find_parent('td').find_next_sibling('td').find_next_sibling('td').text
                    opening_hours = ';'.join([opening_hour.strip() for opening_hour in opening_hours.split('\r\n')])
                except:
                    opening_hours = np.nan

                try:
                    phone = shop_table.find(src = re.compile('ShopDetail_icon_tel')).find_parent('td').find_next_sibling('td').find_next_sibling('td').text
                    phone = phone.replace(' ','')
                except:
                    phone = np.nan

                shopdetail = shopdetail.append(
                        {
                            'shop_detail_link':shop_detail_link,
                            'opening_hours':opening_hours,
                            'phone':phone
                            }, ignore_index=True
                            )

    shoplist = pd.merge(shoplist, shoplisttc, on = 'shop_id')
    shopmaster = pd.merge(shoplist, shopdetail, on = 'shop_detail_link')
    shopmaster['update_date'] = dt.date.today()
    shopmaster['mall'] = mall
    shopmaster['tag'] = np.nan
    shopmaster = shopmaster.loc[:, ['mall','type','shop_id','shop_name_en','shop_name_tc','shop_number','shop_floor','phone','opening_hours','loyalty_offer','voucher_acceptance','shop_category_id','shop_category_name','tag','update_date']]
    shopmaster = shopmaster[shopmaster['shop_number'] != r'(非商店)']
    return shopmaster