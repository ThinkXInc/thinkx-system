import pandas as pd
import requests as re
from bs4 import BeautifulSoup

URL = "https://www.asahi-net.or.jp/~ax2s-kmtn/ref/iso3166-1.html"

# fetch html from url
request = re.get(URL) 
HTMLtext = request.content
soup = BeautifulSoup(HTMLtext, 'html5lib')

# write html file to desired file
with open("../../models/data/country_codes_name_ja.html", "w", encoding = 'utf-8') as file:
    file.write(str(soup.prettify()))

# dictionary to scape data
data = {}

# read local HTML file
file = open("../../models/data/country_codes_name_ja.html", 'r')
HTMLfile = file.read()
soup = BeautifulSoup(HTMLfile, 'lxml')

# append ISO3166-1-numeric key to japanese name value
table = soup.find('table', attrs={'class':'basic'})
table_body = table.find('tbody')
rows = table_body.find_all('tr')
for row in rows:
    cols = row.find_all('td')
    cols = [ele.text.strip() for ele in cols]
    for ele in cols:      
        data[cols[3].upper()] =  cols[1]
  
# read csv file with limiters
df = pd.read_csv('../../models/data/country_codes.csv',
            dtype = {   "ISO3166-1-numeric": object, 
                        "M49":object,
                        "Sub-region Code": object,
                        "Region Code": object,
                        "ISO4217-currency_minor_unit":object,
                        "Continent" : str},
            na_filter = False)

# compare the keys of data and add the column for japanese names
df["offical_name_ja"] = df["ISO3166-1-Alpha-3"].apply(lambda x : data.get(x, ""))

# write to csv
df.to_csv('../../models/data/country_codes.csv',mode = 'w', index=False, float_format="%.10g")

# close file
file.close()