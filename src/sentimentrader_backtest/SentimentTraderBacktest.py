import csv
import time
from datetime import date
import os
import sys
# from itertools import izip as izip
import psycopg2
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from pyvirtualdisplay import Display
import boto3
from botocore.exceptions import ClientError
from credentials import loadCredentials

# Sample Hedgers url. These will need revised.
# 1) Cotton: https://sentimentrader.com/users/backtest/?indicator_smoothing=0&index_filter=0&market_environment=0&index_ma_slope=0&lookback_period=16&observation_value=1&observation_period=4&indicator_condition=3&indicator_level=30000&index=COTTON&indicator=Cotton+Hedgers+Position
# Global Variables to specify High and Low Extreme Sentiment
LOW_EXTREME = '20'
HIGH_EXTREME = '80'
credentials = loadCredentials()
database_user = credentials["database"]["username"]
database_password = credentials["database"]["password"]
database_db = credentials["database"]["database"]
database_host = credentials["database"]["host"]
database_port = credentials["database"]["port"]

def main():
    query_database()


def rds_connect():
    return psycopg2.connect(user = database_user,
        password = database_password,
        host = database_host,
        port = database_port,
        database = database_db)


def query_database():
    connection = rds_connect()
    cursor = connection.cursor()
    test_extreme = HIGH_EXTREME
    select_query = '''select name, indicator, "10DayMA" from public."indicator10daymovingaverage"
                        where ((length("indicator")<6
                        and "indicator" not in('gex','po_oj')) or name like '%%Optix%%')
                        and CAST("10DayMA" AS float) > %s
                        '''  
    
    cursor.execute(select_query, [test_extreme])
    positiveOptixIndicatorQueryList = cursor.fetchall() # Add all of the results to a list. Creates list of tuples

    test_extreme = LOW_EXTREME
    select_query = '''select name, indicator, "10DayMA" from public."indicator10daymovingaverage"
                        where ((length("indicator")<6
                        and "indicator" not in('gex','po_oj')) or name like '%%Optix%%')
                        and CAST("10DayMA" AS float) < %s
                        '''
   
    cursor.execute(select_query, [test_extreme])
    negativeOptixIndicatorQueryList = cursor.fetchall()

    # Combine our positive and negative lists.
    optixIndicatorQueryList = positiveOptixIndicatorQueryList + negativeOptixIndicatorQueryList

    # Gets each element from the tuples the database returns
    optixNameList = [x[0] for x in optixIndicatorQueryList]
    indicatorNameList = [x[1] for x in optixIndicatorQueryList]
    lastCloseList = [x[2] for x in optixIndicatorQueryList]

    # Pass our lists to generate the list of backtests
    generate_list_of_backtests(optixNameList, indicatorNameList, lastCloseList)


def run_backtest(backtestUrl, driver):
    driver.get(backtestUrl)
    time.sleep(5)
    
    # Clicks the back-test url button to run the backtest.
    driver.find_element_by_xpath("//span[contains(@class,'run-text')]").click()
    time.sleep(12)

    # Try catch to see if our backtest actually has data, or if there's no historical trades. If no historical trades, continue.
    try:
        isInvalid = driver.find_element_by_xpath("//div[@id='backtest-results']/div/div[2]/div[2]/div/p").get_attribute("textContent").strip() # Checks for text that there were no trades.
        failedTestSymbol = driver.find_element_by_xpath("//div[@id='backtest-results']/div/div[2]/div[1]/div[1]/div/div/div/h3").get_attribute("textContent").strip() # Symbol
        failedIndicatorSymbol = driver.find_element_by_xpath("//div[@id='backtest-results']/div/div[2]/div[1]/div[2]/div/div/div/h3").get_attribute("textContent").strip() # Indicator
        failedIndicatorLevel = driver.find_element_by_xpath("//div[@id='backtest-results']/div/div[2]/div[1]/div[2]/div/div/div/h4[2]").get_attribute("textContent").strip() # Indicator Level
        failedLookbackPeriod = driver.find_element_by_xpath("//div[@id='backtest-results']/div/div[2]/div[1]/div[3]/div/div/div/h3").get_attribute("textContent").strip()             
        failedObservationPeriod = driver.find_element_by_xpath("//div[@id='backtest-results']/div/div[2]/div[1]/div[4]/div/div/div/h3").get_attribute("textContent").strip() 
        
        print('''%s 
            Symbol %s
            Indicator %s
            failedIndicatorLevel %s
            failedLookbackPeriod %s
            failedObservationPeriod %s
            ''' % (isInvalid, failedTestSymbol, failedIndicatorSymbol, failedIndicatorLevel, failedLookbackPeriod, failedObservationPeriod))            
        return
    except Exception:
        pass

    print('Backtest is a valid test with historical data. Proceeding..')     
    # Get values of Backtest Summary section. TODO: Can probably get these from the variables in generate_list_of_backtests(), but it works.
    # Column 1
    currentTestSymbol = driver.find_element_by_xpath("//div[@id='summary-body']/div/div[1]/div/div/div/h3").get_attribute("textContent").strip() # Symbol
    print('Running backtest of %s' % (currentTestSymbol))
    currentTestIndexFilter = driver.find_element_by_xpath("//div[@id='summary-body']/div/div[1]/div/div/div/h4[1]").get_attribute("textContent").strip() # Index Filter
    currentTestIndexFilterSwap = driver.find_element_by_xpath("//div[@id='summary-body']/div/div[1]/div/div/div/h4[2]").get_attribute("textContent").strip() # Index Filter Swap
    currentTestIndexMASlope = driver.find_element_by_xpath("//div[@id='summary-body']/div/div[1]/div/div/div/h4[3]").get_attribute("textContent").strip() # Index MA Slope

    # Column 2
    currentTestIndicator = driver.find_element_by_xpath("//div[@id='summary-body']/div/div[2]/div/div/div/h3").get_attribute("textContent").strip() # Indicator
    currentTestIndicatorSmoothing = driver.find_element_by_xpath("//div[@id='summary-body']/div/div[2]/div/div/div/h4[1]").get_attribute("textContent").strip() # Indicator Smoothing
    currentTestIndicatorLevel = driver.find_element_by_xpath("//div[@id='summary-body']/div/div[2]/div/div/div/h4[2]").get_attribute("textContent").strip() # Indicator Level
    
    # Column 3
    currentTestLookbackPeriod = driver.find_element_by_xpath("//div[@id='summary-body']/div/div[3]/div/div/div/h3").get_attribute("textContent").strip() # Lookback Period
    currentTestStartdate = driver.find_element_by_xpath("//div[@id='summary-body']/div/div[3]/div/div/div/h4[1]").get_attribute("textContent").strip() # Start Date
    currentTestEndDate = driver.find_element_by_xpath("//div[@id='summary-body']/div/div[3]/div/div/div/h4[2]").get_attribute("textContent").strip() # End Date

    # Column 4
    currentTestObservationPeriod = driver.find_element_by_xpath("//div[@id='summary-body']/div/div[4]/div/div/div/h3").get_attribute("textContent").strip() # Observation Period
    currentTestOverlapping = driver.find_element_by_xpath("//div[@id='summary-body']/div/div[4]/div/div/div/h4[1]").get_attribute("textContent").strip() # Exclude Overlapping
    currentTestMarketEnvironment = driver.find_element_by_xpath("//div[@id='summary-body']/div/div[4]/div/div/div/h4[2]").get_attribute("textContent").strip() # Market Environment

    # Backtest Statistics Table
    # Row 1
    currentTotalReturn = driver.find_element_by_xpath("//div[@id='stat_tab']/div[1]/div[1]/div[1]/div[2]").get_attribute("textContent").strip() # Total Return
    currentAvgReturn = driver.find_element_by_xpath("//div[@id='stat_tab']/div[1]/div[1]/div[2]/div[2]").get_attribute("textContent").strip() # Average Return
    currentZSCore = driver.find_element_by_xpath("//div[@id='stat_tab']/div[1]/div[1]/div[3]/div[2]").get_attribute("textContent").strip() # Z-Score
    currentBuyHoldReturn = driver.find_element_by_xpath("//div[@id='stat_tab']/div[1]/div[1]/div[4]/div[2]").get_attribute("textContent").strip() # Buy & Hold Return

    # Row 2
    currentWinRatePercent = driver.find_element_by_xpath("//div[@id='stat_tab']/div[1]/div[2]/div[1]/div[2]").get_attribute("textContent").strip() # Win Rate
    currentAvgWin = driver.find_element_by_xpath("//div[@id='stat_tab']/div[1]/div[2]/div[2]/div[2]").get_attribute("textContent").strip() # Average Win %
    currentAvgLoss = driver.find_element_by_xpath("//div[@id='stat_tab']/div[1]/div[2]/div[3]/div[2]").get_attribute("textContent").strip() # Average Loss %
    currentMaxRisk = driver.find_element_by_xpath("//div[@id='stat_tab']/div[1]/div[2]/div[4]/div[2]").get_attribute("textContent").strip() # Max Risk

    # Row 3
    currentTotalTrades = driver.find_element_by_xpath("//div[@id='stat_tab']/div[1]/div[3]/div[1]/div[2]").get_attribute("textContent").strip() # Total Trades
    currentTotalPositive = driver.find_element_by_xpath("//div[@id='stat_tab']/div[1]/div[3]/div[2]/div[2]").get_attribute("textContent").strip() # Total Positive
    currentTotalNegative = driver.find_element_by_xpath("//div[@id='stat_tab']/div[1]/div[3]/div[3]/div[2]").get_attribute("textContent").strip() # Total Negative
    currentTimeInMarket = driver.find_element_by_xpath("//div[@id='stat_tab']/div[1]/div[3]/div[4]/div[2]").get_attribute("textContent").strip() # % Time In Market
    todaysDate = date.today()
    todaysDate = todaysDate.strftime("%m/%d/%y")

    connection = rds_connect()
    current_test_data = (currentTestSymbol, currentTestIndicator, currentTestLookbackPeriod, currentTestObservationPeriod, currentTestIndexFilter,
                    currentTestIndicatorSmoothing, currentTestStartdate, currentTestEndDate, currentTestOverlapping, currentTestIndexFilterSwap, currentTestIndicatorLevel,
                    currentTestMarketEnvironment, currentTestIndexMASlope, currentTotalReturn, currentAvgReturn, currentZSCore, currentBuyHoldReturn, currentWinRatePercent,
                    currentAvgWin, currentAvgLoss, currentMaxRisk, currentTotalTrades, currentTotalPositive, currentTotalNegative, 
                    currentTimeInMarket, todaysDate, currentTotalReturn, currentAvgReturn, currentZSCore, currentBuyHoldReturn, currentWinRatePercent, currentAvgWin,
                    currentAvgLoss, currentMaxRisk, currentTotalTrades, currentTotalPositive, currentTotalNegative, currentTimeInMarket)
    sql_insert = '''insert into "backtest_results" (symbol, indicator, lookback_period, observation_period, index_filter, indicator_smoothing, 
                    test_start_date, test_end_date, exclude_overlapping, index_filter_swap, indicator_level, market_environment, 
                    index_ma_slope, total_return, avg_return, z_score, buy_hold_return, win_rate, avg_win,
                    avg_loss, max_risk, total_trades, total_pos, total_neg, time_in_mkt, todays_date)                    
                    values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (indicator, observation_period, todays_date)
                    DO UPDATE SET total_return = %s,
                    avg_return = %s,
                    z_score = %s,
                    buy_hold_return = %s,
                    win_rate = %s,
                    avg_win = %s,
                    avg_loss = %s,
                    max_risk = %s,
                    total_trades = %s,
                    total_pos = %s,
                    total_neg = %s,
                    time_in_mkt = %s;
                    '''
    cursor = connection.cursor()
    cursor.execute(sql_insert, current_test_data)
    connection.commit()
    cursor.close()
    connection.close()
    print('Backtest Table updated for %s for period %s' % (currentTestIndicator, currentTestObservationPeriod))

    # End backtest loop
# Loop through List of URLs, insert results into postgres database.


def initiate_backtest(webPageList):

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

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless')
    driver = webdriver.Chrome('/usr/bin/chromedriver', options=chrome_options)
    # To run as root, use above 3 lines. To run as regular user, the below is fine.
    # driver = webdriver.Chrome('/usr/bin/chromedriver')
    driver.get('https://sentimentrader.com/')

    # Login to sentimentrader.com
    username_field = driver.find_element_by_id('username')
    password_field = driver.find_element_by_id('password')

    username_field.send_keys(username)
    password_field.send_keys(password)
    password_field.send_keys(Keys.RETURN)
    print('Successfully logged in')

    for backtestUrl in webPageList:
        run_backtest(backtestUrl, driver)

    # Close driver for chrome.
    driver.close()
    
# end initiate_backtest

# Get low and high extremes to backtest.
def get_closest_optix_extreme(lastClose):
    lastClose = float(lastClose)
    if lastClose < float(LOW_EXTREME):
        return LOW_EXTREME
    return HIGH_EXTREME
# end get_closest_optix_extreme

# Generate our list of backtests to loop through. TODO: Default values supplied, may need customization options.
def generate_list_of_backtests(optixNameList, indicatorNameList, lastCloseList):
    # Sample Optix url: 
    # https://sentimentrader.com/users/backtest/?indicator_smoothing=0&index_filter=0&market_environment=0&index_ma_slope=0&lookback_period=16&observation_value=3&observation_period=4&indicator_condition=3&indicator_level=80&index=SPY&indicator=SPY+Optix 
    
    # Dynamic URL    
    baseUrl = 'https://sentimentrader.com/users/backtest/?indicator_smoothing=indicatorSmoothingValue&index_filter=indexFilterValue&market_environment=marketEnvironmentValue&index_ma_slope=maSlopeValue&lookback_period=lookbackPeriodValue&observation_value=observationValue&observation_period=observationPeriodValue&indicator_condition=indicatorConditionValue&indicator_level=indicatorLevelValue&index=indexValue&indicator=indicatorValue'
    webPageList = []
    listOfObservationValues = ['1', '3', '6', '9', '12'] # Months back to test.
    indicatorSmoothingValue = '4' # 10 Day MA
    indexFilterValue = '0' 
    marketEnvironmentValue = '0'
    maSlopeValue = '0'
    lookbackPeriodValue = '16' # All History    
    observationPeriodValue = '4' # 4 is months
    indicatorConditionValue = '3' # 3 is above
    indicatorLevelValue = '0' 

    for optixName, indicatorName, lastClose in zip(optixNameList, indicatorNameList, lastCloseList):

        fullLengthIndicatorName = indicatorName
        for lengthOfTime in listOfObservationValues:
            isACompany = False
            if len(fullLengthIndicatorName) < 6 and fullLengthIndicatorName != 'gex' and fullLengthIndicatorName !='po_oj': 
                isACompany = True

            currentBackTestUrl = baseUrl # Make a local copy of the base URL for manipulation.
            if isACompany:
                indicatorCompanySymbol = indicatorName + "+Optix" # NFLX+Optix
                currentBackTestUrl = currentBackTestUrl.replace('indicatorValue', indicatorCompanySymbol)                
            else:
                optixName = optixName.replace(" ", "+") # Replace "SPY Optix with SPY+Optix"                    
                currentBackTestUrl = currentBackTestUrl.replace('indicatorValue', optixName)            

            indicatorName = indicatorName.replace('etf_','') # Indicator is entered into db as etf_indexname i.e. etf_lqd, so we split that off.
            indicatorName = indicatorName.replace('po_','') # Indicator is entered into db as po_indexname i.e. po_xx, so we split that off.
            indicatorName = indicatorName.replace('country_','') # Indicator is entered into db as country_indexname i.e. country_xx, so we split that off.
            indicatorName = indicatorName.replace('model_score_','') # Indicator is entered into db as model_score_indexname i.e. model_score_xx, so we split that off.
            indicatorName = indicatorName.upper()

            if indicatorName == 'EFA': continue # Edge case for unused ETF.
            if indicatorName == 'XBT': indicatorName = 'BITCOIN' # Edge case where the indicator value does not match the sentimentrader url.
            if indicatorName == 'INT' or indicatorName == 'SHORT': indicatorName = 'SPY' # Edge case - Short/Intermediate Term Optimism isn't an indicator.

            currentBackTestUrl = currentBackTestUrl.replace('indexValue', indicatorName) # Append the index/commodity/etf that we are backtesting.
            
            # Set default
            currentBackTestUrl = currentBackTestUrl.replace('observationValue', lengthOfTime)
            currentBackTestUrl = currentBackTestUrl.replace('indicatorSmoothingValue', indicatorSmoothingValue)
            currentBackTestUrl = currentBackTestUrl.replace('indexFilterValue', indexFilterValue)
            currentBackTestUrl = currentBackTestUrl.replace('marketEnvironmentValue', marketEnvironmentValue)
            currentBackTestUrl = currentBackTestUrl.replace('maSlopeValue', maSlopeValue)
            currentBackTestUrl = currentBackTestUrl.replace('lookbackPeriodValue', lookbackPeriodValue)
            currentBackTestUrl = currentBackTestUrl.replace('observationPeriodValue', observationPeriodValue)
            

            indicatorLevelValue = get_closest_optix_extreme(lastClose) # Check if we're at a low extreme or high extreme. If its a stock, append accordingly.
            currentExtreme = indicatorLevelValue
            if isACompany:
                indicatorLevelValue = indicatorLevelValue + "&is_sp1500=yes"

            currentBackTestUrl = currentBackTestUrl.replace('indicatorLevelValue', indicatorLevelValue) # Set the value low or high extreme.
            
            if currentExtreme == LOW_EXTREME:
                indicatorConditionValue = '4'
                currentBackTestUrl = currentBackTestUrl.replace('indicatorConditionValue', indicatorConditionValue)
            else:
                currentBackTestUrl = currentBackTestUrl.replace('indicatorConditionValue', indicatorConditionValue)                   

            # Append URL to our list to backtest for each period of time.       
            # print(currentBackTestUrl)     
            webPageList.append(currentBackTestUrl)  

        # end time period back tests of 1/3/6/9/12 months          
    # end for loop of optix name, indicator, last close

    initiate_backtest(webPageList)
# end generate_list_of_backtests


if __name__ == "__main__":
    main()