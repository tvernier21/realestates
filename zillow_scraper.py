import numpy as np
import pandas as pd
import time
import random
from pathlib import Path


from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

##### GLOBAL VARIABLES: SET BEFORE RUNNING
class ZillowScrapper:
    URL = "https://www.zillow.com/homes/"
    FILENAME = 'data/houses_sell.csv'

    def initiateDriver(self):
        options = webdriver.ChromeOptions()
        options.add_argument('window-size=700,1000')
        driver = webdriver.Chrome('/Users/thibaultvernier/dev/chromedriver', options=options)
        return driver

    def load_data(self):
        """Load old data"""
        return pd.read_csv(self.FILENAME)

    def save_data(self, df):
        """Save new data and merge with old"""
        if Path(self.FILENAME).is_file():
            pd.concat([self.load_data(), df]).to_csv(self.FILENAME, index=False)
        else:
            df.to_csv(self.FILENAME, index=False)

    def findListings(self, content):
        house_list = content.find('ul', {'class': 'photo-cards photo-cards_wow photo-cards_short photo-cards_extra-attribution'})
        listings = house_list.find_all('article', {'class': 'list-card list-card-additional-attribution list-card-additional-attribution-space list-card_not-saved'})
        return listings

    def parse(self, listings, verbose=False):
        all_houses = []
        for i, house in enumerate(listings):
            try:
                house_info = house.find('div', {'class': 'list-card-info'})
                url = house.a['href']
                address = house.a.address.text
                street, city, statezip = address.split(",")
                state, zipcode = statezip.split()
                house_info = house_info.find('div', {'class': 'list-card-heading'})
                price = house_info.div.text
                bds, ba, sqft = house_info.find_all('li')[:3]
                # insert into dataframe
                house_data = {"url": url,
                              "street": street,
                              "city": city,
                              "state": state,
                              "zip": zipcode,
                              "bds": int(bds.text.split()[0].strip()),
                              "ba": int(ba.text.split()[0].strip()),
                              "sqft": int(sqft.text.split()[0].strip().replace(',','')),
                              "price": int(price[1:].replace(',',''))}
                all_houses.append(house_data)
                if verbose:
                    print("Success -----", i+1)
            except:
                if verbose:
                    print("Failed ------", i+1)
                    print(house)
        return all_houses

    def run(self, zipcodes):
        driver = self.initiateDriver()

        # all_houses = []
        for zipcode in zipcodes:
            print(f"Scraping {zipcode}")
            total_pages = page = 1
            while page <= total_pages:
                url = self.URL + str(zipcode) + f"/{page}_p"      # create link to specific zip code
                driver.get(url)                              # set browser to use this page
                time.sleep(3)                                # let the scripts load

                try:
                    elem = driver.find_element_by_tag_name("body")
                    pagedowns = 7
                    while pagedowns:
                        elem.send_keys(Keys.PAGE_DOWN)
                        time.sleep(random.randint(1,2))          # adding random time intervals
                        pagedowns-=1

                    html = driver.page_source
                    content = BeautifulSoup(html, 'lxml')

                    # Find how many pages of listings the zip code holds
                    if page == 1:
                        try:
                            total_pages = int(content.find('span', {"class": "Text-c11n-8-37-0__aiai24-0 eBcXID"}).text.split()[-1])
                        except:
                            pass

                    print(f'\tPage {page} of {total_pages}')

                    try:
                        listings = self.findListings(content)
                        # all_houses.extend(self.parse(listings))
                        all_houses = self.parse(listings)
                    except:
                        print("--No houses")

                    page += 1
                    self.save_data(pd.DataFrame(all_houses))
                except:
                    pass

        driver.quit()



if __name__ == '__main__':
    zipcodes = pd.read_csv('data/philly_zipcodes.csv')
    zipcodes = list(zipcodes.CODE.values)
    print(zipcodes)
    print(len(zipcodes))
    # bot = ZillowScrapper()
    # bot.run(zipcodes)
