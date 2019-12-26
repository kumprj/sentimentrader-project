#!/usr/bin/env python

import json
import requests
import time
from datetime import date


def main():
    generateListToemail()

def generateListToEmail():
    url = '.. end point ..'
    todaysDate = date.today()
    todaysDate = todaysDate.strftime("%m/%d/%y")
    todaysDate = todaysDate.replace('/','_')

    resp = requests.get(f'{url}/{todaysDate}')
    jsonData = []

    if (resp.ok):
        jsonData = json.loads(resp.content)

    masterList = []
    stringListToEmail = []
    for backtestEntry in jsonData:
        # print(backtestEntry)
        currentWinRate = backtestEntry['win_rate']
        currentWinRate = currentWinRate.replace('%','')
        currentWinRateAsInt = int(currentWinRate)
        if (currentWinRateAsInt > 20 and currentWinRateAsInt < 80):
            continue

        # If we get this far, the win rates are really good or really bad, so append it to the list.
        masterList.append(backtestEntry)

    for entry in masterList:  
        stringToEmail = f'''Ticker {entry["symbol"]} has a win rate of {entry["win_rate"]} for time period {entry["observation_period"]}. The median return is {entry['avg_return']}, avg win is {entry['avg_win']} and avg loss is {entry['avg_loss']} over a total of {entry['total_trades']} trades.'''
        stringListToEmail.append(stringToEmail)
    
    return stringListToEmail


if __name__ == '__main__':
    main()