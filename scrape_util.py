import requests
from bs4 import BeautifulSoup
import csv


HEADERS = {'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:101.0) Gecko/20100101 Firefox/101.0"}
COOKIES = {'birthtime': '568022401'}

def request_page_soup(url):
    try:
        req = requests.get(url, headers=HEADERS, cookies=COOKIES)
    except Exception:
        return None
    if req.status_code != 200:
        return None
    return BeautifulSoup(req.text, features="html.parser")

def scrape_links_for_socials(links):
    socials = {"linkedins": set(), "mailtos": set(), "contact_pages": set()}
    
    for link in links:
        check_socials(link, socials)
    
    for link in socials["contact_pages"]:
        check_socials(link, socials, is_contact_page=True)

    for k in socials:
        if len(socials[k]) == 0: socials[k] = "N/A"
        else: socials[k] = " | ".join(socials[k])
    return socials

def check_socials(link, socials, is_contact_page=False):
    soup = request_page_soup(link)
    if soup is None:
        socials["contact_pages"].add(link)
        return

    page_links = soup.find_all("a", {'href': True})
    for l in page_links:
        href = l["href"]
        if not is_contact_page and "contact" in l.text.lower() and not href.startswith("mailto:"):
            if not href.startswith("http"): href = link + href
            if not href.startswith("https"): href = href.replace("http", "https")
            socials["contact_pages"].add(href)
        if "mailto:" in href:
            socials["mailtos"].add(href)
        elif "linkedin" in href:
            socials["linkedins"].add(href) 

def flush_buffer_to_csv(buffer, file_name, fields):
    with open(file_name, 'a', newline='', encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, restval='', fieldnames=fields)
        for row in buffer: writer.writerow(row)
    with open("scraped_apps.txt", 'a') as f:
        for row in buffer: f.write(f'{row["id"]}\n')
    buffer.clear() 

def create_csv(file_name, fields):
    with open(file_name, 'w', newline='', encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        writer.writeheader()