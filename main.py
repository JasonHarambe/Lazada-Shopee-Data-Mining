# Web Scraping
from selenium import webdriver
from selenium.common.exceptions import *

# Data manipulation
import pandas as pd
import requests
import re
import flask
from flask import jsonify
from flask import request

webdriver_path = 'env/bin/chromedriver'

options = webdriver.ChromeOptions()
options.add_argument('--headless') 
options.add_argument('start-maximized') 
options.add_argument('disable-infobars')
options.add_argument('--disable-extensions')

def find_item(item):
    lazada_url = 'https://www.lazada.com.my/'
    search_item = str(item)

    # Open the Chrome browser
    browser = webdriver.Chrome(webdriver_path, options=options)
    browser.get(lazada_url)

    search_bar = browser.find_element_by_xpath('/html/body/div[2]/div/div[1]/div/div/div[2]/div/div[2]/form/div/div[1]/input[1]')
    search_bar.send_keys(search_item)
    search_bar.submit()
  
    # Faced with CAPTCHA problem. Unable to bypass captcha thus putting this project on hold.
    # slider = browser.find_element_by_id('nocaptcha')
    # move = ActionChains(browser)
    # move.click_and_hold(slider).move_by_offset(40,0).release().perform()

    item_titles = browser.find_elements_by_class_name('c16H9d')
    item_prices = browser.find_elements_by_class_name('c13VH6')
    item_links = browser.find_elements_by_class_name('cRjKsc')

    lazada_titles_list = []
    lazada_prices_list = []
    lazada_links_list = []

    for title in item_titles:
        lazada_titles_list.append(title.text)
    for price in item_prices:
        lazada_prices_list.append(price.text)
    for links in item_links:
        a = links.find_element_by_tag_name('a')
        lazada_links_list.append(a.get_attribute('href'))

    browser.quit()
    print('lazada parsed.')
    # browser.find_element_by_xpath('//*[@class=”ant-pagination-next” and not(@aria-disabled)]')

    df_lazada = pd.DataFrame(
        zip(lazada_titles_list, lazada_prices_list, lazada_links_list), 
        columns=['Item Name', 'Price', 'URL'])

    df_lazada['Price'] = df_lazada['Price'].str.replace('RM', '').astype(float)
    df_lazada = df_lazada[df_lazada['Item Name'].str.contains('x2') == False]
    
    #Shopee API is relatively easier
    shopee_url = 'https://shopee.com.my'
    keyword_search = str(item)

    headers = {
    'User-Agent': 'Chrome',
    'Referer': '{}search?keyword={}'.format(shopee_url, keyword_search)
    }

    url = 'https://shopee.com.my/api/v2/search_items/?by=relevancy&keyword={}&limit=100&newest=0&order=desc&page_type=search'.format(keyword_search)

    # Shopee API request
    r = requests.get(url, headers = headers).json()

    # Shopee scraping script
    shopee_titles_list = []
    shopee_prices_list = []
    shopee_historical_list = []
    shopee_rating_list = []

    for item in r['items']:
        shopee_titles_list.append(item['name'])
        shopee_prices_list.append(item['price_min'])
        shopee_historical_list.append(item['historical_sold'])
        shopee_rating_list.append(item['item_rating']['rating_star'])

    df_shopee = pd.DataFrame(
        zip(shopee_titles_list, shopee_prices_list, shopee_historical_list, shopee_rating_list), 
        columns=['Item Name', 'Price', 'Sold', 'Rating'])

    # Remove the ‘RM’ string from Price and change column type to float
    df_shopee['Price'] = df_shopee['Price'] / 100000

    # Some of the items are actually x2 packs. Remove them too
    df_shopee = df_shopee[df_shopee['Item Name'].str.contains(
        '[2x\s]{3}|twin', 
        flags=re.IGNORECASE, 
        regex=True) == False]

    print('shopee requested.')
    # Add column [‘Platform’] for each platforms
    df_lazada['Platform'] = 'Lazada'
    df_shopee['Platform'] = 'Shopee'

    # Concatenate the Dataframes
    df = pd.concat([df_lazada,df_shopee])
    print('df complete...')

    # print(df.groupby(['Platform']).describe())

    json_output = df.to_json(orient='split')

    # df.to_csv('output.csv')
    print('json done...')

    return json_output


# This part can be optional --> API function
app = flask.Flask(__name__)
app.config['DEBUG'] = True

@app.route('/', methods=['GET'])
def home():
    return '<p>Price Comparison Webpage</p>'

# URL should be in the format of 'http://127.0.0.1:5000/api/v1?search=bunny%20tail
# %20 will be translated to 'space'

@app.route('/api/v1', methods=['GET'])
def api():
    if 'search' in request.args:
        search = str(request.args.get('search'))
        result = find_item(search)

        return jsonify(result)

    else: 
        return 'Error: No search item.'

app.run()
