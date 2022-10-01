# pull candidates from steam store

import json
from re import S
import sys
import requests
from bs4 import BeautifulSoup

from steam_pull import request_page_soup

applist = set()
donelist = []

def scrape_store_page(url):
    soup = request_page_soup(url)

    conf = soup.find(id="application_config")
    for k in conf.attrs:
        if k.startswith("data-section"):
            section = json.loads(conf[k])
            if "appids" in section:
                ids = section["appids"]
                for id in ids:
                    if id in donelist: continue
                    applist.add(id)

def check_app_list(file):
    with open(file) as f:
        app_ids = json.loads(f.read())
    for id in app_ids:
        if id in donelist: continue
        applist.add(id)

TASKS = ["store", "list", "api"]
task = None if len(sys.argv) < 2 else sys.argv[1]
if task not in TASKS: task = None

with open("scraped_apps.txt", encoding="utf-8") as f:
    donelist = [int(l.strip()) for l in f.readlines()]    

if not task or task == "store":
    scrape_store_page("https://store.steampowered.com/tags/en/Indie/")
elif task == 'list':
    check_app_list('app_list.json')
elif task == 'api':
    print('todo')

with open("candidates.txt", "w", encoding="utf-8") as f:
    f.writelines([f"https://store.steampowered.com/app/{id}/\n" for id in applist])