# Hong Kong Mall Shop Directory Web Scraping
This repository is to extract the shop directory of all major Hong Kong malls by web scraping.
The data will be used for data analysis afterwards.

## Table of contents
* [Objective](#objective)
* [Setup](#setup)
* [Repository directory](#repository-directory)
* [Method](#method)
* [Export data](#export-data)
* [Roadmap](#roadmap)
* [Usage](#usage)

## Objective
As working in mall leasing department of a sizable property company in Hong Kong, it is a good idea to montior the merchants leasing situation of competitor malls in ongoing basis. To monitor in a timely manner, this repository aims to develop a pipeline of web scraping procedure so it is easier to replicate and output the shop directory data.

## Setup
Run "export_data.ipynb" to export the malls' shop directory into "data" folder. By default, all malls will be extracted in one go. If you need to extract particular mall(s), you may amend "mall" variable to only include the desired mall(s).

## Repository directory
    .
    ├── README.md
    ├── LICENSE.txt
    ├── data                    # Exported web scraping data
    │   └── (Malls folder)
    ├── webscraper              # Web scraper script
    │   └── (Malls folder)
    └── export_data.ipynb

## Method
Depending on the website design, different web scraping methods will be applied.
If the website is not java based, BeautifulSoup is mainly used in the web scraper.
Since shop list page usually does not contain the shop details, data in shop list page and shop detail page are scrapped separately then combined into a shop master data.
For the website which is java based, the designated website API will be called to have web scraping instead.

## Export data
In this project, there are two main functions (getShopCategory, getShopMaster) to extract the shop categories and shop master data from each mall. The data fields have been standardized among all malls. If no corresponding data could be extracted on the website, NULL will be placed in the fields.

Below is the definition of exported data set:

_Shop Category_

| Field name         | Data type | Description                                               |
|:-------------------|:----------|:----------------------------------------------------------|
| mall               | String    | Name of the mall                                          |
| type               | String    | Type of the shop (Either Shopping or Dinning)             |
| shop_category_id   | String    | A unique identifier of the shop category assigned by mall |
| shop_category_name | String    | Name of the shop category                                 |
| update_date        | Date      | Date of web scraping                                      |

_Shop Master_

| Field name         | Data type | Description                                                                                            |
|:-------------------|:----------|:-------------------------------------------------------------------------------------------------------|
| mall               | String    | Name of the mall                                                                                       |
| type               | String    | Type of the shop (Either Shopping or Dinning)                                                          |
| shop_id            | String    | A system generated unique identifier of the shop assigned by mall                                      |
| shop_name_en       | String    | Name of the shop in English                                                                            |
| shop_name_tc       | String    | Name of the shop in Traditional Chinese                                                                |
| shop_number        | String    | A unique identifier of the shop assigned by mall and usually used to indicate the location of the shop |
| shop_floor         | String    | The floor the shop being located in the mall                                                           |
| phone              | String    | Contact phone number of the shop                                                                       |
| opening_hours      | String    | Opening hours of the shop                                                                              |
| loyalty_offer      | String    | Indicate name of mall loyalty offer with the shop                                                      |
| voucher_acceptance | Boolean   | Flag to indicate whether the shop accept mall vouchers                                                 |
| shop_category_id   | String    | A unique identifier of the shop category assigned by mall                                              |
| shop_category_name | String    | Name of the shop category                                                                              |
| tag                | String    | Other additional tagging added to the shop by mall                                                     |
| update_date        | Date      | Date of web scraping                                                                                   |

## Roadmap

2 - 3 malls web scrapers are expected to add to this project on weekly basis

_Malls has been web scraped:_
- [x] CityGate
- [x] Citylink
- [x] CityPlaza
- [x] Citywalk
- [x] Elements
- [x] FestivalWalk
- [x] HarbourCity
- [x] IFC
- [x] ISquare
- [x] K11ArtMall
- [x] K11Musea
- [x] Landmark
- [x] LanghamPlace
- [x] LeeGardenMalls
- [x] LinkHKMalls
- [x] LukYeungGalleria
- [x] MaritimeSquare
- [x] MiraPlace
- [x] OlympianCity
- [x] PacificPlace
- [x] ParadiseMall
- [x] PlazaAscot
- [x] PlazaHollywood
- [x] PopCorn
- [x] TelfordPlaza
- [x] TheLane
- [x] TheLohas
- [x] TheOne
- [x] TimeSquare
- [x] Tmtplaza
- [x] Windsor

_Malls to be web scraped:_
- [ ] Megabox
- [ ] TheForest
- [ ] DPark
- [ ] D2Place
- [ ] 1881Heritage
- [ ] MOKO
- [ ] NewTownPlaza
- [ ] OtherSHKPMalls
- [ ] MOSTown
- [ ] MetroCity
- [ ] OtherHendersonMalls
- [ ] FashionWalk
- [ ] OtherHangLungMalls

## Usage
Please refer to [license](https://github.com/rex-lui/Hong-Kong-Mall-Shop-Directory-Web-Scraping/blob/a9673679e1279a7a394bb75c5bfa6ce08508295b/LICENSE) page.
