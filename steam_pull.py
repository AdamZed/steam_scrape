import csv
import time
import re
from bs4 import BeautifulSoup
import requests

def get_app_body(url):
    soup = request_page_soup(url)
    if soup is None:
        print(f'failed link req: {url}')
    return soup


def get_app_id_from_url(app_url):
    return re.search(r"app\/([0-9]*)\/", app_url).group(1)
    
    
def get_app_stats(app_body, app_url):
    app_stats = { "url": app_url }
    app_stats['id'] = get_app_id_from_url(app_url)

    info_panel = app_body.find("div", {"class": "glance_ctn_responsive_left"})

    # get app title
    title = app_body.find(id="appHubAppName")
    if not title: return None # page probably blocked by account sign in
    app_stats["title"] = title.text

    # get release date
    release_date = info_panel.find("div", {"class": "release_date"})
    if release_date: app_stats["release_date"] = release_date.find("div", {"class": "date"}).text
    
    # search for devs/publishers
    dev_list = info_panel.find(id="developers_list")
    devs = [l for l in dev_list.find_all("a")]
    pubs = [l for l in info_panel.find_all("a") if l not in devs]
    app_stats["developers"] = ", ".join((d.text for d in devs))
    app_stats["publishers"] = ", ".join((p.text for p in pubs))

    steam_dev_links = set()
    for link in devs:
        if "/developer/" not in link and "/curator/" not in link: continue
        steam_dev_links.add(link["href"])
    for link in pubs:
        if "/publisher/" not in link and "/curator/" not in link: continue
        steam_dev_links.add(link["href"])
    external_links = find_sites_for_steamdevs(steam_dev_links)

    # search for game website
    page_links = app_body.find_all("a", {"class": "linkbar"})
    possible_web_links = [lk for lk in page_links if "Visit the website" in lk.text]
    if len(possible_web_links) > 0:
        game_site = clean_steam_redirect(
            possible_web_links[0]['href'])
        external_links.add(game_site)
        app_stats["game_site"] = game_site

    app_stats.update(scrape_links_for_socials(external_links))
    
    try:
        # get review scores
        review_info = { i["itemprop"]: i["content"] for i in info_panel.find_all("meta") }

        if "reviewCount" in review_info:
            app_stats["total_reviews"] = review_info["reviewCount"]
            app_stats["review_score"] = review_info["ratingValue"]

        # get price
        current_price = app_body.find("meta", {"itemprop": "price"})["content"]
        app_stats["current_price"] = current_price

        price_section = app_body.find("div", {"class": "game_area_purchase_game_wrapper"})
        if price_section:
            original_price_div = price_section.find("div", {"class": "discount_original_price"})
            if original_price_div:
                original_price = original_price_div.text[5:]
                app_stats["original_price"] = original_price
            else:
                app_stats["original_price"] = current_price
        else:
            app_stats["original_price"] = current_price

        # get monthly average and peak players
        #app_stats["monthly_avg"], app_stats["monthly_peak"] = get_month_player_stats(app_url)

    except (AttributeError, TypeError):
        pass
    
    return app_stats


def find_sites_for_steamdevs(steam_dev_links):
    links = set()
    for d_link in steam_dev_links:
        soup = request_page_soup(d_link)
        if soup is None: continue
        curator_url = soup.find("a", {"class": "curator_url"})
        if curator_url:
            links.add(clean_steam_redirect(curator_url["href"]))
    return links 
            

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


STEAMCHART_URL = "https://steamcharts.com/app/"
def get_month_player_stats(app_id):
    soup = request_page_soup(f'{STEAMCHART_URL}{app_id}')
    if not soup:
        return "N/A", "N/A"
    chart_rows = soup.find("tbody").find("tr", {"class": "odd"}).find_all("td")
    return (chart_rows[1].text, chart_rows[4].text)


CANDI_FILE = "candidates.txt"
def get_app_candidates():
    with open(CANDI_FILE) as f:
        candidates = [l.strip() for l in f.readlines()]
    return candidates


RED_URL_PREF = "https://steamcommunity.com/linkfilter/?url="
def clean_steam_redirect(red_url):
    if red_url.startswith(RED_URL_PREF):
        return red_url[len(RED_URL_PREF):]
    return red_url


FIELDS = ['url', 'id', 'title', 'release_date', 'developers', 'publishers', 'linkedins', 'mailtos', 'contact_pages', 'game_site', 'current_price', 'original_price', 'total_reviews', 'review_score', 'monthly_avg', 'monthly_peak']
def flush_buffer_to_csv(buffer, file_name):
    with open(file_name, 'a', newline='', encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, restval='', fieldnames=FIELDS)
        for row in buffer: writer.writerow(row)
    with open("scraped_apps.txt", 'a') as f:
        for row in buffer: f.write(f'{row["id"]}\n')
    buffer.clear() 

def create_csv(file_name):
    with open(file_name, 'w', newline='', encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=FIELDS)
        writer.writeheader()


MAX_BUFFER = 10
def do_work(steam_urls):
    buffer = []
    data_file_name = f'data/data_{int(time.time())}.csv'
    create_csv(data_file_name)

    for steam_app_url in steam_urls:
        print(f"fetching {steam_app_url}")
        st_app_dom = get_app_body(steam_app_url)
        if not st_app_dom:
            print("failed to fetch, stopping")
            flush_buffer_to_csv(buffer)
            exit(-1)

        data_entry = get_app_stats(st_app_dom, steam_app_url)
        if not data_entry: continue

        buffer.append(data_entry)
        if len(buffer) >= MAX_BUFFER:
            flush_buffer_to_csv(buffer, data_file_name)
    
    flush_buffer_to_csv(buffer, data_file_name)

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
    
def main():
    steam_urls = get_app_candidates()
    do_work(steam_urls)


if __name__ == "__main__":
    main()
