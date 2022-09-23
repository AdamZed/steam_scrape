from typing import Set
from bs4 import BeautifulSoup
import requests

USE_TEST_FILE = True
TEST_FILE = "file.txt"

def get_app_body(url):
    if not USE_TEST_FILE:
        soup = request_page_soup(url)
    else:
        with open(TEST_FILE, encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), features="html.parser")

    if soup is None:
        exit(-1)
    return soup


def get_app_stats(app_body):
    app_stats = { }
    
    info_panel = app_body.find("div", {"class": "glance_ctn_responsive_left"})

    # get app title
    title = app_body.find(id="appHubAppName").text
    app_stats["title"] = title

    # get review scores
    review_info = { i["itemprop"]: i["content"] for i in info_panel.find_all("meta") }
    app_stats["total_reviews"] = review_info["reviewCount"]
    app_stats["review_score"] = review_info["ratingValue"]

    # get release date
    release_date = info_panel.find("div", {"class": "release_date"}).find("div", {"class": "date"}).text
    app_stats["release_date"] = release_date
    
    # get price
    current_price = app_body.find("meta", {"itemprop": "price"})["content"]
    app_stats["current_price"] = current_price

    # search for devs/publishers
    devs = [l for l in info_panel.find_all("a") if "/developer/" in l['href']]
    pubs = [l for l in info_panel.find_all("a") if "/publisher/" in l['href']]
    app_stats["developers"] = ", ".join((d.text for d in devs))
    app_stats["publishers"] = ", ".join((p.text for p in pubs))

    steam_dev_links = set()
    for link in devs: steam_dev_links.add(link["href"])
    for link in pubs: steam_dev_links.add(link["href"])
    external_links = find_sites_for_steamdevs(steam_dev_links)

    # search for game website
    page_links = app_body.find_all("a", {"class": "linkbar"})
    possible_web_links = [lk for lk in page_links if "Visit the website" in lk.text]
    if len(possible_web_links) > 0:
        external_links.add(clean_steam_redirect(
            possible_web_links[0]['href']))

    app_stats["socials"] = scrape_links_for_socials(external_links)

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
    page_links = soup.find_all("a", {'href': True})
    for l in page_links:
        href = l["href"]
        if not is_contact_page and "contact" in l.text.lower():
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

    return socials

def get_app_candidates():
    # TODO add candidate file and pull names from
    return ["https://store.steampowered.com/app/991170/Barn_Finders/"]


RED_URL_PREF = "https://steamcommunity.com/linkfilter/?url="
def clean_steam_redirect(red_url):
    if red_url.startswith(RED_URL_PREF):
        return red_url[len(RED_URL_PREF):]
    return red_url


def get_csv_entry_for_stats(stats):
    # TODO
    pass


def flush_buffer(buffer):
    # TODO
    pass


MAX_BUFFER = 10
def do_work(candidates):
    buffer = []

    for candi in candidates:
        print(f"fetching {candi}")
        candi_dom = get_app_body(candi)
        candi_stats = get_app_stats(candi_dom)

        print(candi_stats)

        data_entry = get_csv_entry_for_stats(candi_stats)
        buffer.append(data_entry)
        if len(buffer) >= MAX_BUFFER:
            flush_buffer(buffer)

def request_page_soup(url):
    req = requests.get(url)
    if req.status_code != 200:
        print(f'failed link req: {url}')
        return None
    return BeautifulSoup(req.text, features="html.parser")
    
def main():
    candidates = get_app_candidates()
    do_work(candidates)


if __name__ == "__main__":
    main()
