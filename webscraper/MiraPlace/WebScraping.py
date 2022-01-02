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
shopkiosklisturl = config['url']['shopkiosklisturl']

#Get shop category data and export into csv
def getShopCategory():
    #Create empty DataFrame for shop category
    shopcategory = pd.DataFrame()

    for type, url in zip(['Shopping','Dining'],[shoplisturl,fnblisturl]):
        #Get shop category
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')
        for form in soup.find_all('div', class_ = 'category'):
            for category in form.find_all('option'):
                try:
                    shop_category_id = category.get('value')
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

#Get shop master data and export into csv
def getShopMaster():
    shopcategory = getShopCategory()
    shoplist = pd.DataFrame()
    shopdetail = pd.DataFrame()
    shopdetailtc = pd.DataFrame()

    #Create floor mapping
    floor_list = ['B1','B2','B3','G','1','2','3','4','5','6']

    for type, url in zip(['Shopping','Dining'],[shoplisturl,fnblisturl]):
        #Get shop list
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')
        for list in soup.find_all('div', class_ = 'mypull'):
            for shop in list.find_all('li'):
                try:
                    shop_detail_link = shop.get('onclick').split(',')[-2].strip('\'')
                except:
                    shop_detail_link = np.nan

                try:
                    shop_id = shop_detail_link.split('/')[-2]
                except:
                        shop_id = np.nan

                try:
                    shop_name = shop.text
                except:
                    shop_name = np.nan

                try:
                    shop_category_id = shop.get('cattype')
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
                    'shop_name_en': shop_name,
                    'shop_category_id':shop_category_id,
                    'shop_category_name':shop_category_name,
                    'shop_detail_link':shop_detail_link
                    }, ignore_index=True
                        )

    for shop_detail_link in shoplist['shop_detail_link']:
        if shop_detail_link != '':
            shopdetailurl = shop_detail_link
            shopdetailtcurl = shop_detail_link.replace('shop','tc/shop')
            page = requests.get(shopdetailurl)
            soup = BeautifulSoup(page.content, 'html.parser')
            for shop in soup.find_all('div', class_ = 'shopping-content'):
                try:
                    shop_location = soup.find('td', text = 'Address').find_next_sibling('td').text
                    exist = set()
                    exist_add = exist.add
                    shop_location_split = [parts.strip().replace('L','').replace('/F','') for parts in shop_location.split(',')]
                    shop_location_split = [x for x in shop_location_split if not (x in exist or exist_add(x))]
                    shop_floor = ';'.join([parts for parts in shop_location_split if parts in floor_list])
                    shop_location_split.remove(shop_floor)
                    shop_number = ';'.join(shop_location_split)
                    shop_floor = shop_floor + 'F'
                except:
                    shop_location = np.nan
                    shop_floor = np.nan
                    shop_number = np.nan

                try:
                    phone = soup.find('td', text = 'Telephone').find_next_sibling('td').text.replace(' ','')
                except:
                    phone = np.nan

                try:
                    opening_hours = soup.find('td', text = 'Opening Hours').find_next_sibling('td').text.replace(' ','')
                except:
                    opening_hours = np.nan
            
            shopdetail = shopdetail.append(
                    {
                        'shop_detail_link':shop_detail_link,
                        'shop_location':shop_location,
                        'shop_floor':shop_floor,
                        'shop_number':shop_number,
                        'phone': phone,
                        'opening_hours':opening_hours
                        }, ignore_index=True
                        )

            page = requests.get(shopdetailtcurl)
            soup = BeautifulSoup(page.content, 'html.parser')
            for shop in soup.find_all('div', class_ = 'shopping-content'):
                try:
                    shop_name_zh = soup.find('td', text = '店鋪名稱').find_next_sibling('td').text
                except:
                    shop_name_zh = np.nan

            shopdetailtc = shopdetailtc.append(
                    {
                        'shop_detail_link':shop_detail_link,
                        'shop_name_tc':shop_name_zh
                        }, ignore_index=True
                        )
    #Merge shop list and shop detail into shop master
    shopmaster = pd.merge(shoplist, shopdetail, on = 'shop_detail_link', how = 'left')
    shopmaster = pd.merge(shopmaster, shopdetailtc, on = 'shop_detail_link', how = 'left')
    shopmaster['update_date'] = dt.date.today()
    shopmaster['mall'] = mall
    shopmaster['loyalty_offer'] = np.nan
    shopmaster['voucher_acceptance'] = np.nan
    shopmaster['tag'] = np.nan
    shopmaster = shopmaster.loc[:, ['mall','type','shop_id','shop_name_en','shop_name_tc','shop_number','shop_floor','phone','opening_hours','loyalty_offer','voucher_acceptance','shop_category_id','shop_category_name','tag','update_date']]

    #Get kiosk list
    shopkiosklist = pd.DataFrame()
    url = shopkiosklisturl
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    for row in soup.find_all('div', class_ = 'row'):
        for kiosk in row.find_all('div', class_ = 'col-lg-4'):
            try:
                shop_id = kiosk.find('h4').text.replace(' ','_')
            except:
                shop_id = np.nan

            try:
                shop_name = kiosk.find('h4').text
            except:
                shop_name = np.nan

            try:
                shop_detail = kiosk.find('p').text
                shop_category_name = shop_detail.split('\n')[0]
                shop_category_id = shop_detail.split('\n')[0]
                shop_location = shop_detail.split('\n')[1]
                exist = set()
                exist_add = exist.add
                shop_location_split = [parts.strip().replace('L','').replace('/F','') for parts in shop_location.split(',')]
                shop_location_split = [x for x in shop_location_split if not (x in exist or exist_add(x))]
                shop_floor = ';'.join([parts for parts in shop_location_split if parts in floor_list])
                shop_location_split.remove(shop_floor)
                shop_number = ';'.join(shop_location_split)
                shop_floor = shop_floor + 'F'
                opening_hours = shop_detail.split('\n')[2]
                phone = shop_detail.split('\n')[3]
                try:
                    phone = re.findall(r'\d{4}\s\d{4}', phone)[0].replace(' ','')
                except:
                    phone = np.nan

            except:
                shop_detail = np.nan
                shop_id = np.nan
                shop_name = np.nan
                shop_category_id = np.nan
                shop_category_name = np.nan
                shop_floor = np.nan
                shop_number = np.nan
                opening_hours = np.nan
                phone = np.nan

            shopkiosklist = shopkiosklist.append(
                                {
                                    'shop_id':shop_id,
                                    'shop_name_en':shop_name,
                                    'shop_name_tc':shop_name,
                                    'shop_category_id':shop_category_id,
                                    'shop_category_name':shop_category_name,
                                    'shop_floor':shop_floor,
                                    'shop_number':shop_number,
                                    'opening_hours':opening_hours,
                                    'phone':phone
                                    }, ignore_index=True
                                    )

    shopkiosklist['update_date'] = dt.date.today()
    shopkiosklist['mall'] = mall
    shopkiosklist['type'] = 'Shopping'
    shopkiosklist['loyalty_offer'] = np.nan
    shopkiosklist['voucher_acceptance'] = np.nan
    shopkiosklist['tag'] = np.nan
    shopkiosklist = shopkiosklist.loc[:, ['mall','type','shop_id','shop_name_en','shop_name_tc','shop_number','shop_floor','phone','opening_hours','loyalty_offer','voucher_acceptance','shop_category_id','shop_category_name','tag','update_date']]

    #Merge shop list and Kiosk list
    shopmaster = pd.concat([shopmaster, shopkiosklist], ignore_index = True)
    return shopmaster