import psycopg2
import csv
import time
import os
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from pyvirtualdisplay import Display
from credentials import loadCredentials

__author__ = "Joseph Wells (Primary), Robert Kump (Secondary)"

# User Information
credentials = loadCredentials()
sentiment_user = credentials["sentimentrader"]["username"]
sentiment_password = credentials["sentimentrader"]["password"]

username = sentiment_user
password = sentiment_password


# Chrome Driver is required in path or specify path within argument (which chromedriver to find
# Initiate driver and browser instance
display = Display(visible=0, size=(800, 800))  
display.start()
# driver = webdriver.Chrome('/usr/bin/chromedriver') # No options webdriver
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--no-sandbox')
# chrome_options.add_argument('--headless') # Unnecessary in this case but a common chrome option to add.
driver = webdriver.Chrome('/usr/bin/chromedriver', options=chrome_options)
driver.get('https://sentimentrader.com/')

# Login and download
username_field = driver.find_element_by_id('username')
password_field = driver.find_element_by_id('password')

username_field.send_keys(username)
password_field.send_keys(password)
password_field.send_keys(Keys.RETURN)

driver.get('https://sentimentrader.com/users/ws/todaysentiment')
time.sleep(10)
driver.close()
print('Sentiment report downloaded')

# remove key column for import
# Amazon Linux Image default downloads dir: /root/Downloads/
with open('/root/Downloads/sentimenTrader_Daily_Sentiment_Data.csv', 'r') as fin, open('/root/Downloads/sentimenTrader_Daily_Sentiment_DataE.csv', 'w') as fout:
    reader = csv.reader(fin) 
    reader.next() #skip header
    writer = csv.writer(fout)
    for row in reader:
        writer.writerow(row[1:])
        
# write new data to stage table CHECK insert statment
database_user = credentials["database"]["username"]
database_password = credentials["database"]["password"]
database_db = credentials["database"]["database"]
database_host = credentials["database"]["host"]
database_port = credentials["database"]["port"]

connection = psycopg2.connect(user = database_user,
                        password = database_password,
                        host = database_host,
                        port = database_port,
                        database = database_db)

# dailyIndicatorSTG is our Daily Indicator table in the db.
with open ('/root/Downloads/sentimenTrader_Daily_Sentiment_DataE.csv', 'r') as f:
    cursor = connection.cursor()
    cursor.execute('delete from "dailyIndicatorSTG";')
    cursor.copy_from(f,'"dailyIndicatorSTG"', sep=',')
    connection.commit()
    cursor.close()
    connection.close()
    print('sent to stagetable')

# Update prd table with updates made today 
connection = psycopg2.connect(user = database_user,
                        password = database_password,
                        host = database_host,
                        port = database_port,
                        database = database_db)
cursor = connection.cursor()
cursor.execute('''
                   insert into indicatorprd  ("indicator","value","date")
                    select S."indicator",
                              S."last_close",
                              S."update_date" 
                    from public."dailyIndicatorSTG" S
                    left join (select "indicator", max("date") as "date" from public.indicatorprd group by "indicator") P
                    on P."indicator"=S."indicator"
                    where P."date"!=S.update_date
                    ''')
connection.commit()
cursor.close()
connection.close()
print('PRD table Updated')

# Removed files
os.remove("/root/Downloads/sentimenTrader_Daily_Sentiment_Data.csv")
os.remove("/root/Downloads/sentimenTrader_Daily_Sentiment_DataE.csv")
