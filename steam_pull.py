from turtle import pos
from bs4 import BeautifulSoup
import requests


def get_app_body(url):
    # req = requests.get(url)
    # if req.status_code != 200:
    #     print(f'encountered err {req.status_code}')
    #     exit()

    # page_str = req.text

    with open("file.txt", encoding="utf-8") as f:
        page_str = f.read()

    page_body = BeautifulSoup(page_str, features="html.parser")
    return page_body


def get_app_stats(app_body):
    app_stats = {"links": {"dev": [], "publisher": [], "game": None}}
    
    info_panel = app_body.find("div", {"class": "glance_ctn_responsive_left"})

    # get review scores
    review_info = { i["itemprop"]: i["content"] for i in info_panel.find_all("meta") }
    app_stats["total_reviews"] = review_info["reviewCount"]
    app_stats["review_score"] = review_info["ratingValue"]

    # get release date
    release_date = info_panel.find("div", {"class": "release_date"}).find("div", {"class": "date"}).text
    app_stats["release_date"] = release_date

    # search for dev/publisher sites
    # TODO

    # search for game website
    links = app_body.find_all("a", {"class": "linkbar"})
    possible_web_links = [lk for lk in links if "Visit the website" in lk.text]
    if len(possible_web_links) > 0:
        app_stats["links"]["game"] = clean_steam_redirect(
            possible_web_links[0]['href'])

    scrape_links_for_socials(app_stats)

    return app_stats


def scrape_links_for_socials(app_stats):
    links = app_stats['links']
    # TODO
    pass


def get_app_candidates():
    # TODO add candidate file and pull names from
    return ["https://store.steampowered.com/app/1708680/Kingdom_Two_Crowns_Norse_Lands/"]


RED_URL_PREF = "https://steamcommunity.com/linkfilter/?url="
def clean_steam_redirect(red_url):
    if red_url.startswith(RED_URL_PREF):
        return red_url[len(RED_URL_PREF):]
    return red_url


def get_entry(stats):
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
        data_entry = get_entry(candi_stats)
        buffer.append(data_entry)
        if len(buffer) >= MAX_BUFFER:
            flush_buffer(buffer)


def main():
    candidates = get_app_candidates()
    do_work(candidates)


if __name__ == "__main__":
    main()
