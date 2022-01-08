#%%
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
shopdetailbasictcurl = config['url']['shopdetailbasictcurl']

#Get shop category data and export into csv
def getShopCategory():
    #Create empty DataFrame for shop category
    shopcategory = pd.DataFrame()

    url = shoplisturl
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    for i in soup.find_all(class_ = 'selectAllCat'):
        for j in i.find_all('option'):
            if j.get('value') == None:
                pass
            else:
                try:
                    shop_category_id = j.get('value')
                except:
                        shop_category_id = np.nan

                try:
                    shop_category_name = j.text
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
    shopcategory['type'] = shopcategory['shop_category_name'].apply(lambda x: 'Dining' if any(keyword in x.lower() for keyword in ['food','dining']) else 'Shopping')
    shopcategory = shopcategory.loc[:, ['mall','type','shop_category_id','shop_category_name','update_date']]
    return shopcategory

#Get shop master data and export into csv
def getShopMaster():
    shopcategory = getShopCategory()
    #Create empty DataFrame for shop master
    shoplist = pd.DataFrame()
    shopdetail = pd.DataFrame()
    
    url = shoplisturl
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    
    for shop in soup.find_all(class_ = 'shopEntry'):
        for shopbrand in shop.find(class_ = 'shopEntryBrand'):
            try:
                shopbrandlink = shopbrand.get('href')
                shopbrandlinkid = shopbrandlink.find('?id=')
                shop_id = shopbrandlink[shopbrandlinkid+4:]
            except:
                shop_id = np.nan
            
            try:
                shop_name = shopbrand.text
            except:
                shop_name = np.nan
        
        try:
            shop_number = shop.find(class_ = 'shopEntryLocation').text
        except:
            shop_number = np.nan
        
        try:
            exist = set()
            exist_add = exist.add
            shop_floor = shop.find(class_ = 'shopEntryFloor').text.strip()
            shop_floor_split = [parts.strip().replace('L','')+'F' for parts in shop_floor.split('  ')]
            shop_floor_split = [x for x in shop_floor_split if not (x in exist or exist_add(x))]
            shop_floor = ';'.join(shop_floor_split)
        except:
            shop_floor = np.nan
        
        try:
            shop_category_name = shop.find(class_ = 'shopEntryCategory').text
        except:
            shop_category_name = np.nan
    
        try:
            shop_category_id = shopcategory.loc[shopcategory['shop_category_name'] == shop_category_name, 'shop_category_id'].values[0]
        except:
            shop_category_id = np.nan
    
        try:
            if shop.find(class_ = 'shopEntryCard').find_all(src = re.compile('ico_the_one_card')):
                loyalty_offer = 'The ONE Card'
            else:
                loyalty_offer = np.nan
        except:
            loyalty_offer = np.nan
    
        try:
            if shop.find(class_ = 'shopEntryCard').find_all(src = re.compile('ico_cash_coupon')):
                voucher_acceptance = '1'
            else:
                voucher_acceptance = np.nan
        except:
            voucher_acceptance = np.nan
        
        shoplist = shoplist.append(
                    {
                        'shop_id':shop_id,
                        'shop_name_en': shop_name,
                        'shop_number':shop_number,
                        'shop_floor':shop_floor,
                        'shop_category_id':shop_category_id,
                        'shop_category_name':shop_category_name,
                        'loyalty_offer':loyalty_offer,
                        'voucher_acceptance':voucher_acceptance
                        }, ignore_index=True
                        )
    #Get shop detail
    for shop_id in shoplist['shop_id']:
        shopdetailurl = shopdetailbasictcurl + shop_id
        page = requests.get(shopdetailurl)
        soup = BeautifulSoup(page.content, 'html.parser')
    
        for shopdetailinner in soup.find_all(class_ = 'shopDetailsInner'):
            try:
                shop_name_zh = shopdetailinner.find('span').text
            except:
                shop_name_zh = np.nan
        
        shopdetailurl = shopdetailbasicurl + shop_id
        page = requests.get(shopdetailurl)
        soup = BeautifulSoup(page.content, 'html.parser')
    
        for shopdetailcontent in soup.find_all(class_ = 'shopDetailsContent'):
            try:
                phone = shopdetailcontent.find('th', text = 'Telephone').find_next_sibling('td').find_next_sibling('td').text
                phone = phone.replace(' ','').replace('\n','').replace('\r','').replace('<br>','')
            except:
                phone = np.nan
            
            try:
                opening_hours = shopdetailcontent.find('th', text = 'Opening Time').find_next_sibling('td').find_next_sibling('td').text
                opening_hours = opening_hours = opening_hours.replace('\n','').replace('\r','').replace('<br>','')
            except:
                opening_hours = np.nan
                
        shopdetail = shopdetail.append(
                    {
                        'shop_id':shop_id,
                        'shop_name_tc':shop_name_zh,
                        'phone': phone,
                        'opening_hours': opening_hours
                        }, ignore_index=True
                        )
    
    #Merge shop list and shop detail into shop master
    shopmaster = pd.merge(shoplist, shopdetail, on = 'shop_id')
    shopmaster['update_date'] = dt.date.today()
    shopmaster['mall'] = mall
    shopmaster['type'] = shopmaster['shop_category_name'].apply(lambda x: 'Dining' if any(keyword in x.lower() for keyword in ['food','dining']) else 'Shopping')
    shopmaster['tag'] = np.nan
    shopmaster = shopmaster.loc[:, ['mall','type','shop_id','shop_name_en','shop_name_tc','shop_number','shop_floor','phone','opening_hours','loyalty_offer','voucher_acceptance','shop_category_id','shop_category_name','tag','update_date']]
    return shopmaster