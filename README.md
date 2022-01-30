# Hong Kong Mall Shop Directory Web Scraping
This repository is to extract the shop directory of all major Hong Kong malls by web scraping.
The data will be used for afterward data analysis.

## Table of contents
* [Objective](#objective)
* [Setup](#setup)
* [Repository directory](#repository-directory)
* [Method](#method)
* [Export data](#export-data)
* [Roadmap](#roadmap)
* [Usage](#usage)

## Objective
As a data analytics staff in mall leasing department of a sizable property company in Hong Kong, it is a good idea to always montior the merchants leasing situation of competitor malls in Hong Kong. To monitor in a timely manner, this repository aims to develop a pipeline of web scraping procedure and everyone can easily replicate and output the shop directory data.

## Setup
...

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
Depends on the website design, different web scraping methods will be applied.
If the website is not java based, Beautiful Soup is mainly be used in the web scraper.
Since shop list page usually do not contain every detail of the shop, data in shop list page and data in shop detail page are scrapped separately and are joined together into a shop master data.
For the website is java based, the web site API will be called to have web scraping instead.

## Export data
...

## Roadmap
...

## Usage
Please refer to license page.
