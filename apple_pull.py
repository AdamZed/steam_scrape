from scrape_util import request_page_soup, scrape_links_for_socials

def pull_app_store(app_url):

    app_stats = { "url": app_url }

    soup = request_page_soup(app_url)
    site = soup.find(lambda t: t.name == "a" and "Developer Website" in t.text)

    app_stats["title"] = soup.find("h1", {"class": "app-header__title"}).contents[0].strip()
    app_stats["developer"] = soup.find("h2", {"class":"app-header__identity"}).find("a").text.strip()
    app_stats["price"] = soup.find("li", {"class":"app-header__list__item--price"}).text
    app_stats["socials"] = scrape_links_for_socials([site["href"]])

    rating_section = soup.find("figcaption", {"class": "star-rating__count"}).text
    app_stats["avg_rating"], app_stats["review_count"] = rating_section.split(" • ", 1)
    
    print(app_stats)

       
if __name__ == "__main__":
    pull_app_store("https://apps.apple.com/us/app/altos-odyssey/id1182456409")