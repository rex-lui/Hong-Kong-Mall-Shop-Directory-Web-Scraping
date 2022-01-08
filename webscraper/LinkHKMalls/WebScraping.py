#Import necessary package
import requests
import re
from bs4 import BeautifulSoup
import json
import pandas as pd
import numpy as np
import datetime as dt
import configparser
import os

#Configure parameter
config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))
mall = config['general']['mall']
shoplistapi = config['api']['shoplistapi']
fnblistapi = config['api']['fnblistapi']
shopdetailapi = config['api']['shopdetailapi']
floorlist = config['mapping']['floorlist']

#Get shop category data and export into csv
def getShopCategory():
    #Create empty DataFrame for shop category
    shopcategory = pd.DataFrame()
    
    for type, api in zip(['Shopping','Dining'],[shoplistapi,fnblistapi]):
        #Get shop category
        shoplistrequest = requests.get(api)
        shoplistresponse = json.loads(shoplistrequest.content)

        for category in shoplistresponse['data']['category']:
            try:
                shop_category_id = str(int(category['shopCategoryTypeId']))
            except:
                shop_category_id = np.nan

            try:
                shop_category_name = category['shopCategoryThumbnailAltTextEn']
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
    shopcategory.drop(shopcategory[shopcategory.shop_category_name == 'ALL CUISINES'].index, inplace = True)
    shopcategory = shopcategory.loc[:, ['mall','type','shop_category_id','shop_category_name','update_date']]
    return shopcategory

#Get shop master data and export into csv
def getShopMaster():
    #Create empty DataFrame for shop master
    shoplist = pd.DataFrame()
    shopdetail = pd.DataFrame()
    shopcategory = getShopCategory()
    
    for type, api in zip(['Shopping','Dining'],[shoplistapi,fnblistapi]):
        #Get the first page and total page count
        shoplistrequest = requests.get(api + '&pageSize=10')
        shoplistresponse = json.loads(shoplistrequest.content)
        current_page = shoplistresponse['data']['pageInfo']['curPage']
        total_page = shoplistresponse['data']['pageInfo']['pageCount']

        while current_page <= total_page:
            combine_api = api + '&pageSize=10&pageNo=' + str(current_page)
            shoplistrequest = requests.get(combine_api)
            shoplistresponse = json.loads(shoplistrequest.content)
            for shop in shoplistresponse['data']['shopList']:
                try:
                    current_page = current_page
                except:
                    current_page = np.nan

                try:
                    total_page = total_page
                except:
                    total_page = np.nan
                
                try:
                    mall = ''.join([parts.capitalize() for parts in shop['shopCentreNameEn'].split(' ')])
                    mall = mall.replace('T.o.pThisIsOurPlace/700NathanRoad','TOP')
                except:
                    mall = np.nan

                try:
                    shop_id = str(int(shop['shopId']))
                except:
                    shop_id = np.nan
                
                try:
                    shop_number = shop['shopNo']
                except:
                    shop_number = np.nan

                shoplist = shoplist.append(
                        {
                            'current_page':current_page,
                            'total_page':total_page,
                            'mall':mall,
                            'type':type,
                            'shop_id':shop_id,
                            'shop_number':shop_number
                            }, ignore_index=True
                            )
            current_page = current_page + 1

    for i, shop_id in enumerate(shoplist['shop_id'].unique()):
        combine_api = shopdetailapi + str(shop_id)
        shopdetailrequest = requests.get(combine_api)
        shopdetailresponse = json.loads(shopdetailrequest.content)
        try:
            shop_name = shopdetailresponse['data']['shopInfo']['shopNameEn'].replace('<br />','').replace('\n','').replace('\t','').replace('\r','')
        except:
            shop_name = np.nan

        try:
            shop_name_zh = shopdetailresponse['data']['shopInfo']['shopNameTc'].replace('<br />','').replace('\n','').replace('\t','').replace('\r','')
        except:
            shop_name_zh = np.nan

        try:
            shop_location = shopdetailresponse['data']['shopInfo']['locationEn']
            exist = set()
            exist_add = exist.add
            shop_location_split = [parts.strip().replace('/','').replace('.','').replace('MTR Floor','MTRF')\
                .replace('Level 1','1F').replace('Level 2','2F').replace('Level 3','3F').replace('Level 4','4F')\
                    .replace('L1F','1F').replace('L2F','2F').replace('L3F','3F').replace('L4F','4F').replace('L5F','5F')\
                        .replace('L1','1F').replace('L2','2F').replace('L3','3F').replace('L4','4F').replace('L5','5F')\
                            .replace('UG 1F','UG1F').replace('UG 2F','UG2F') for parts in shop_location.replace('and',',').split(',')]
            shop_location_split = [x for x in shop_location_split if not (x in exist or exist_add(x))]
            shop_floor = ';'.join([parts for parts in shop_location_split if parts in floorlist])
        except:
            shop_floor = np.nan

        try:
            phone = shopdetailresponse['data']['shopInfo']['telephone'].replace(' ','').replace('<br />','').replace('\n','').replace('\t','').replace('\r','')
        except:
            phone = np.nan

        try:
            opening_hours = shopdetailresponse['data']['shopInfo']['openingHoursEn'].replace('<br />','').replace('\n','').replace('\t','').replace('\r','')
        except:
            opening_hours = np.nan

        try:
            shop_category_name = shopdetailresponse['data']['shopInfo']['shopTypeTextEn'].replace('<br/>',';')
            if shop_category_name[-1] == ';':
                shop_category_name = shop_category_name[:-1]
        except:
            shop_category_name = np.nan

        try:
            shop_category_id = ';'.join([shopcategory.loc[shopcategory['shop_category_name'] == cat, 'shop_category_id'].values[0] for cat in shop_category_name.split(';')])
        except:
            shop_category_id = np.nan

        shopdetail = shopdetail.append(
                {
                    'shop_id':shop_id,
                    'shop_name_en':shop_name,
                    'shop_name_tc':shop_name_zh,
                    'shop_floor':shop_floor,
                    'phone': phone,
                    'opening_hours': opening_hours,
                    'shop_category_id':shop_category_id,
                    'shop_category_name':shop_category_name
                    }, ignore_index=True
                    )
    shopmaster = pd.merge(shoplist, shopdetail, on = 'shop_id')
    shopmaster['update_date'] = dt.date.today()
    shopmaster['loyalty_offer'] = np.nan
    shopmaster['voucher_acceptance'] = np.nan
    shopmaster['tag'] = np.nan
    shopmaster['shop_floor'] = shopmaster['shop_floor'].apply(lambda x: 'Others' if x == '' else x)
    shopmaster = shopmaster.loc[:, ['mall','type','shop_id','shop_name_en','shop_name_tc','shop_number','shop_floor','phone','opening_hours','loyalty_offer','voucher_acceptance','shop_category_id','shop_category_name','tag','update_date']]
    shopmaster = shopmaster.sort_values('mall')
    return shopmaster