from curl_cffi import requests
from bs4 import BeautifulSoup as bsoup

import log
import re
import math

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

# Regex used
rating_regex = r"(\d+(\.\d+)?)(?=\s+out of\s+5)" # Whole ratings
total_rating_regex = r"(\d+)\s*ratings" # total rating counts
stars_regex = r"(\d+)\s*percent.*?(\d+)\s*stars" # 22 percent 5 stars

def check_regex(item, regex):
    result = re.search(regex, item)
    if result:
        return result.groups()
    else:
        return None
    
def get_reviews(review_blocks):
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

    return reviews

def calculate_star_int_per_tier(percentage, total_rating):
    """
    Why in the world would amazon round ratings for percentage.
    Just directly use accurate numbers 😓

    Ok so here's what my insane big 🧠 tells me to do:

    `['78 percent of reviews have 5 stars', '22 percent of reviews have 2 stars']` with total_rating as 6

    (6*22)/100 would be 1.68, so get results of 1/6*100 and 2/6*100 
    which are 16.5 and 33.3 respectively. subtract with 22 and find which has the lowest diff and select that!
    (in this case, 16 as the difference is 6 compares to 11 with 33)
    """

    # Ok so chatgpt approved the ^ above so lets do that!

    real_percentage_portion = (total_rating * percentage) / 100
    rounded_down_portion = math.floor(real_percentage_portion)
    rounded_up_portion = math.ceil(real_percentage_portion)
    int_portion = int(real_percentage_portion)
    print(real_percentage_portion, rounded_down_portion, rounded_up_portion, int_portion)

    rund_down_res = abs(((rounded_down_portion / total_rating) * 100) - percentage)
    rund_up_res = abs(((rounded_up_portion / total_rating) * 100) - percentage)
    int_res = abs(((int_portion / total_rating) * 100) - percentage)

    options = {
        rounded_down_portion: rund_down_res,
        rounded_up_portion: rund_up_res,
        int_portion: int_res
    }

    best_portion = min(options, key=options.get)

    # Don't ask me what happened above; it works.

    return int(best_portion)


def get_stars(a_tags, total_rating):
    total_rating = int(total_rating)
    stars = {
        "total_rating": total_rating,
        "1": {"stars": 0, "percentage": 0},
        "2": {"stars": 0, "percentage": 0},
        "3": {"stars": 0, "percentage": 0},
        "4": {"stars": 0, "percentage": 0},
        "5": {"stars": 0, "percentage": 0},
    }

    for i in a_tags:
        aria_label = i.get('aria-label')
        res = check_regex(aria_label, stars_regex)
        if res:
            percent = float(res[0])
            star_level = str(res[1])
            stars_count = calculate_star_int_per_tier(percent, total_rating)
            stars[star_level]["stars"] = stars_count
            stars[star_level]["percentage"] = percent

    return stars

def fetch_start_pg(url):
    """
    price -> Price of the product
    rating -> Total rating out of 5 (float)
    image -> Link to image of the product and alt of the image
    pricecut -> discounts if any
    reviews -> reviews by user if any
    starts -> total ratings and stars each level with their percentage
    """
    log.customPrint(f"Fetch Initialised 🏁 ({url})", "light_green")
    res = requests.get(url, headers=global_headers, impersonate="chrome120")

    if "To discuss automated access" in res.text:
        log.customPrint(f"Fetch failed successfully! 🤭 Returning None. ({url})", "light_red")
        return None

    soup = bsoup(res.text, 'html.parser')

    price = soup.select_one('#priceblock_ourprice, .a-price-whole')
    rating = soup.select_one('.a-icon-alt')
    total_rating = soup.select_one('#acrCustomerReviewText')
    total_rating = total_rating.text.strip() if total_rating else None
    image = soup.select_one('#landingImage')
    price_cut_per = soup.select_one('.savingsPercentage')


    temp = rating.text.strip()
    if temp:
        rating = float(check_regex(temp, rating_regex)[0])


    """Stars"""
    a_tags = soup.select('a.a-size-base.a-link-normal._cr-ratings-histogram_style_histogram-row-container__Vh7Di')
    # all stars containing a-link-normal has atleast 1 star in it!
    # we will just use 0 for rest instead of fetching and handling rest

    stars = get_stars(a_tags, check_regex(total_rating, total_rating_regex)[0])

    """Reviews"""
    review_blocks = soup.select('#cm-cr-dp-review-list .review')
    reviews = get_reviews(review_blocks)

    result_dict = {
        "title": None,
        "description": None,
        "price": float(price.text.strip()) if price else None,
        "rating": rating if rating else None,
        "image": {"url": image["src"] if image else None, "alt": image["alt"] if image else None},
        "pricecut": price_cut_per.text.strip() if price_cut_per else None,
        "reviews": reviews,
        "stars": stars
    }
    
    
    if any(value is not None for value in result_dict.values()):
        log.customPrint(f"Fetch finished successfully! 💯 ({url})", "medium_purple")
        return result_dict

    log.customPrint(f"Fetch finished but seems like something is wrong, all None! ({url})", "light_red")
    return None

    
if __name__ == "__main__":
    print(fetch_start_pg("https://www.amazon.in/dp/9386473429"))
    #print(calculate_star_int_per_tier(22, 6))
