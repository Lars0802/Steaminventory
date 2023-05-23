# does not work anymore
import os
import io
import time
import datetime
import csv
import glob

import requests
import json
import pandas as pd
from pandas.io.parsers import read_csv

# returns items in given inventory
def getInventory(id):
    id = str(id)
    print(id)

    # paths
    path_csv = 'Steaminventory/data/temp/'+id+'.csv'
    path_json = 'Steaminventory/data/temp/'+id+'.json'
    url_id = 'https://steamcommunity.com/id/{}/inventory/json/730/2'
    url_profiles = 'https://steamcommunity.com/profiles/{}/inventory/json/730/2'

    # decide, wheter profile-id or steam64-id is used
    if id.isnumeric():
        url = url_profiles
    else:
        url = url_id

    data = requests.get(url.format(id))
    data.encoding='utf-8-sig'
    inv = json.loads(data.text)

    # remove, if file is already present
    if os.path.isfile(path_json):
        os.remove(path_json)
    else:
        pass
    if os.path.isfile(path_csv):
        os.remove(path_csv)
    else:
        pass
    with io.open(os.path.join(path_json), 'w') as inv_json:
        json.dump(inv, inv_json, indent=4, sort_keys=True)

    # retry, if request wasnt successful
    start = datetime.datetime.now()
    while data.status_code != 200:
        try:
            if os.path.isfile(path_json):
                os.remove(path_json)
            data = requests.get(url.format(id))
            data.encoding='utf-8-sig'
            inv = json.loads(data.text)
            
            with io.open(os.path.join(path_json), 'w') as inv_json:
                json.dump(inv, inv_json, indent=4, sort_keys=True)
        except Exception as e:
            print(e)
        time.sleep(1)
        print(data.status_code)
    print(datetime.datetime.now()-start)

    # get every item in inventory
    descriptions = inv['rgDescriptions']

    with open(path_csv, 'w', encoding="utf-8") as file:
        head = csv.DictWriter(file, delimiter = ',', fieldnames=['item', 'classid', 'amount'])
        head.writeheader()

        for item in descriptions:
            file.write(str(descriptions[item]['market_name']) + ', ' + str(descriptions[item]['classid']) + ', ' + str(getCount(descriptions[item]['classid'], inv)) + '\n')

# gets amount of given item in inventory
# src: https://stackoverflow.com/questions/29824111/get-a-users-steam-inventory
def getCount(classid, data):
    inventory = data["rgInventory"]
    count = 0
    for item in inventory:
        if inventory[item]["classid"] == classid:
            count += 1
    return count

# gets current market price of desired item
def getPrice(item):
    print(item)
    path = 'Steaminventory/data/temp/price_'+item+'.json'
    url = 'https://steamcommunity.com/market/search/render/?'
    params = {
        'search_descriptions' : '0',
        'sort_column' : 'default',
        'sort_dir' : 'desc',
        'appid' : '730',
        'norender' : '1',
        'count' : '1',
        'query' : item
    }
    response = requests.get(url, params)
    response.encoding='utf-8-sig'
    data = json.loads(response.text)
    with open(path, 'w') as file:
        json.dump(data, file, indent=4, sort_keys=True)

    while response.status_code != 200:
        try:
            if os.path.isfile(path):
                os.remove(path)
            response = requests.get(url, params)
            response.encoding='utf-8-sig'
            data = json.loads(response.text)
            with open(path, 'w') as file:
                json.dump(data, file, indent=4, sort_keys=True)
        except Exception as e:
            print(e)
        time.sleep(1)
        print(response.status_code)

    try:
        return data['results'][0]['sell_price']
    except:
        return 'No price found'

def price():
    print('Enter item:')
    item = str(input())
    try:
        print(getPrice(item))
    except Exception as e:
        print(e)

def inventory():
    print('Enter Inventory ID:')
    id = str(input())
    try:
        getInventory(id)
    except Exception as e:
        print(e)

def createDirectory():
    try:
        os.makedirs('Steaminventory/data/temp')
    except:
        pass
    if os.path.isfile('Steaminventory/data/prices.csv'):
        os.remove('Steaminventory/data/prices.csv')

def main():
    createDirectory()

    prices = open('Steaminventory/data/prices.csv', 'a', encoding="utf-8")
    prices.write('item,price,sum' + '\n')

    with open('Steaminventory/data/accounts.txt', 'r') as accounts:
        for account in accounts:
            getInventory(account.strip())
            df = pd.read_csv('Steaminventory/data/temp/'+account.strip()+'.csv')

            for x in df.index:
                row = df.iloc[[x]]
                count = row.to_string(columns=['amount'], index_names=None, header=False, index=False)
                items = row.to_string(columns=['item'], index_names=None, header=False, index=False)
                print(count)
                price_item = getPrice(items.replace('|', '')) / 100
                prices.write(str(items) + ', ' + str(price_item) + ', ' + '%.2f' %(float(price_item) * float(count)) + '\n')

    prices.close()
    pr = read_csv('Steaminventory/data/prices.csv')
    prices = open('Steaminventory/data/prices.csv', 'a', encoding="utf-8")
    prices.write('Summe, ' + str('%.2f' %(pr['sum'].sum())))
    prices.close()            

    # remove used files
    files = glob.glob('Steaminventory/data/temp/*')
    for file in files:
        try:
            os.remove(file)
        except Exception as e:
            print(e)

            
if __name__ == '__main__':
    main()
