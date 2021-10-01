#!/usr/bin/python
__author__ = 'Lars Thomsen'
__version__ = '0.0.1'
__status__ = 'Development'
__date__ = '2021/09/30'
# last modified: 2021/10/01

import os
import io
import time
import datetime
import csv

import requests
import json
import pandas as pd

# returns items in given inventory
def getInventory(id):
    id = str(id)
    print(id)

    # paths
    path_csv = 'Steaminventory/data/inv/'+id+'.csv'
    path_json = 'Steaminventory/data/inv/'+id+'.json'
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
    path = 'Steaminventory/data/items/price_'+item+'.json'
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
        return data['results'][0]['sell_price_text']
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

def main():
    if os.path.isfile('Steaminventory/data/prices.txt'):
        os.remove('Steaminventory/data/prices.txt')

    with open('Steaminventory/data/accounts.txt', 'r') as accounts:
        for account in accounts:
            getInventory(account.strip())
            df = pd.read_csv('Steaminventory/data/inv/'+account.strip()+'.csv')

            for x in df.index:
                row = df.iloc[[x]]
                items = row.to_string(columns=['item'], index_names=None, header=False, index=False)
                prices = open('Steaminventory/data/prices.txt', 'a', encoding="utf-8")
                prices.write(str(items) + ': ' + str(getPrice(items.replace('|', ''))) + '\n')
                prices.close()
            
            

    
if __name__ == '__main__':
    main()