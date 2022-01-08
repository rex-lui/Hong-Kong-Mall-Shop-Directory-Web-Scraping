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
shopdetailbasictcurl = config['url']['shopdetailbasictcurl']
shopflooridmapping = eval(config['mapping']['shopflooridmapping'])

#Get shop category data and export into csv
def getShopCategory():
    #Create empty DataFrame for shop category
    shopcategory = pd.DataFrame()

    for type, url in zip(['Shopping','Dining'],[shoplisturl,fnblisturl]):
        #Get shop category
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')

        for search in soup.find_all('div', attrs = {'data-type':'category'}):
            for key in search.find_all('button', class_ = 'searchKey'):
                try:
                    shop_category_id = key.get('data-key')
                except:
                    shop_category_id = np.nan

                try:
                    shop_category_name = key.text
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
    
    for type, url in zip(['Shopping','Dining'],[shoplisturl,fnblisturl]):
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')
    
        for shopcube in soup.find_all(class_ = 'shopCube'):
            try:
                if type == 'Shopping':
                    shopdetaillink = shopcube.get('href')
                    shopdetaillinkid = shopdetaillink.find('/Shop/')
                    shop_id = shopdetaillink[shopdetaillinkid+6:]
                elif type == 'Dining':
                    shopdetaillink = shopcube.get('href')
                    shopdetaillinkid = shopdetaillink.find('/Dining/')
                    shop_id = shopdetaillink[shopdetaillinkid+8:]
            except:
                shop_id = np.nan
    
            try:
                shop_floor = shopcube.get('data-floor')
            except:
                shop_floor = np.nan
    
            try:
                shop_category_id = shopcube.get('data-category')
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
                                'shop_floor':shop_floor,
                                'shop_category_id':shop_category_id,
                                'shop_category_name':shop_category_name
                                }, ignore_index=True
                                )
    
    for shop_id in shoplist['shop_id']:
        shopdetailurl = shopdetailbasicurl + shop_id
        page = requests.get(shopdetailurl)
        soup = BeautifulSoup(page.content, 'html.parser')
    
        for detail in soup.find_all('div', class_ = 'col-md-9'):
            try:
                shop_name = detail.find(class_ = 'font-weight-bold').text
            except:
                shop_name = np.nan
            
            try:
                shop_number = detail.find(src = re.compile('icon_location')).find_next_sibling('div').text.split(',')[0]
            except:
                shop_number = np.nan
            
            try:
                opening_hours = detail.find(src = re.compile('icon_time')).find_next_sibling('div').text
                opening_hours = opening_hours.replace('\n','').replace('\r','').replace('<br>','')
            except:
                opening_hours = np.nan
            
            try:
                phone = detail.find(src = re.compile('icon_tel')).find_next_sibling('div').text
                phone = phone.replace(' ','').replace('\n','').replace('\r','').replace('<br>','')
            except:
                phone = np.nan
            
            try:
                item = detail.find(class_ = 'flex-wrap')
                taglist = ';'.join([tag.text.strip().replace(';','') for tag in item.findChildren('button')])
                taglist = taglist.replace('\u200b','').replace('\n','').replace('\r','').replace('<br>','')
            except:
                taglist = np.nan
        
        shopdetailtcurl = shopdetailbasictcurl + shop_id
        page = requests.get(shopdetailtcurl)
        soup = BeautifulSoup(page.content, 'html.parser')
    
        for detail in soup.find_all('div', class_ = 'col-md-9'):
            try:
                shop_name_zh = detail.find(class_ = 'font-weight-bold').text
            except:
                shop_name_zh = np.nan
    
        shopdetail = shopdetail.append(
            {
                'shop_id':shop_id,
                'shop_name_en':shop_name,
                'shop_name_tc':shop_name_zh,
                'shop_number':shop_number,
                'phone':phone,
                'opening_hours':opening_hours,
                'tag':taglist
                }, ignore_index=True
                )
    #Merge shop list and shop detail into shop master
    shopmaster = pd.merge(shoplist, shopdetail, on = 'shop_id')
    shopmaster['update_date'] = dt.date.today()
    shopmaster['mall'] = mall
    shopmaster['shop_floor'] = shopmaster['shop_floor'].map(shopflooridmapping)
    shopmaster['loyalty_offer'] = np.nan
    shopmaster['voucher_acceptance'] = np.nan
    shopmaster = shopmaster.loc[:, ['mall','type','shop_id','shop_name_en','shop_name_tc','shop_number','shop_floor','phone','opening_hours','loyalty_offer','voucher_acceptance','shop_category_id','shop_category_name','tag','update_date']]
    return shopmaster