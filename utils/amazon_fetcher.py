from curl_cffi import requests
from bs4 import BeautifulSoup as bsoup

from . import log

# Curl_cffi is a life saver really, helped bypass amazon request block thingy successfully!
# I thought I would have to use selenium or similar, but thankfully not! otherwise would have had to cancel this project
# Selinum won't work with hosts (Atleast not on the one I use!)
# As the main goal is to automate the fetching part. I don't want to have a static site instead, 
# dynamic not only sounds cool, but is cooler as well :>

# On to the main topic, this won't do. We can't be certain when amazon decides to block the request.
# I'll use sqlite database to store these results of successfull fetches in advance to add a fallback
# Incase request fails to run successfully.


# Headers used for request
global_headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.amazon.in/",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

def fetch_start_pg(url):
    log.customPrint(f"Fetch Initialised 🏁 ({url})", "light_green")
    res = requests.get(url, headers=global_headers, impersonate="chrome120")

    if "To discuss automated access" in res.text:
        log.customPrint(f"Fetch failed successfully! 🤭 Returning None. ({url})", "light_red")
        return None

    soup = bsoup(res.text, 'html.parser')

    price = soup.select_one('#priceblock_ourprice, .a-price-whole')
    rating = soup.select_one('.a-icon-alt')
    image = soup.select_one('#landingImage')
    price_cut_per = soup.select_one('.savingsPercentage')


    """Stars"""
    stars = []
    a_tags = soup.select('a.a-size-base.a-link-normal._cr-ratings-histogram_style_histogram-row-container__Vh7Di')
    # all stars containing a-link-normal has atleast 1 star in it!
    # we will just use 0 for rest instead of fetching and handling rest

    for i in a_tags:
        stars.append(i.get('aria-label'))

    """Reviews"""
    review_blocks = soup.select('#cm-cr-dp-review-list .review')
    reviews = []

    for block in review_blocks:
        user = block.select_one('.a-profile-name')
        # Ensure span tag doesn't have ANY class.
        # Video breaks the fetch, since it contains span.
        # Thankfully those span tags contains classes...
        text_div = block.select_one('.review-text-content')
        if text_div:
            text = text_div.find('span', class_=False)
        else:
            text = None
        #print(text)

        if user and text:
            reviews.append({
                "user": user.text.strip(),
                "text": text.text.strip()
            })

    result_dict = {
        "price": price.text.strip() if price else None,
        "rating": rating.text.strip() if rating else None,
        "image": image["src"] if image else None,
        "alt": image["alt"] if image else None,
        "pricecut": price_cut_per.text.strip() if price_cut_per else None,
        "reviews": reviews,
        "stars": stars
    }

    """for i in result_dict.values():
        if i != None:
            log.customPrint("Fetch finished successfully! 💯", "medium_purple")
            return result_dict"""
    
    
    if any(value is not None for value in result_dict.values()):
        log.customPrint(f"Fetch finished successfully! 💯 ({url})", "medium_purple")
        return result_dict

    log.customPrint(f"Fetch finished but seems like something is wrong, all None! ({url})", "light_red")
    return None

    

    
if __name__ == "__main__":
    print(fetch_start_pg("https://www.amazon.in/dp/9386473429"))