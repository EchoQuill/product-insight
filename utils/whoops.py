from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

options = Options()
options.add_argument('--headless')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('--user-agent=Mozilla/5.0')

driver = webdriver.Chrome(options=options)
driver.get("https://www.amazon.in/dp/B07JQFQK7S")

soup = BeautifulSoup(driver.page_source, 'html.parser')

price = soup.select_one('#priceblock_ourprice, .a-price-whole')
rating = soup.select_one('.a-icon-alt')
image = soup.select_one('#landingImage')
price_cut_per = soup.select_one('.savingsPercentage')

print({
    "price": price.text.strip() if price else None,
    "rating": rating.text.strip() if rating else None,
    "image": image['src'] if image else None,
    "alt": image['alt'] if image else None,
    "pricecut": price_cut_per.text.strip() if price_cut_per else None
})

driver.quit()
