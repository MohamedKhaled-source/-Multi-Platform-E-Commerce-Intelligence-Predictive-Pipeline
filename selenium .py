from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
import time
import pandas as pd

chrome_options = Options()
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
prefs = {"profile.managed_default_content_settings.images": 2}
chrome_options.add_experimental_option("prefs", prefs)
driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 10)

url = "https://www.elarabygroup.com/en/tvs-and-electronics/televisions/smart-tvs?p=3"

driver.get(url)

data = []

while True:
    current_count = len(driver.find_elements(By.CSS_SELECTOR, "div.product-item-info"))
    if current_count >= 100:
        break
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        load_more = driver.find_element(By.XPATH, "//button[contains(., 'Load More')]")
        load_more.click()
        print("Clicked Load More")
        time.sleep(2)
    except:
        print("No more products to load on main page.")
        break

products = driver.find_elements(By.CSS_SELECTOR , "div.product-item-info")[:100]

print(f"found {len(products)} in the page")

for p in products:

    try: 
        title = p.find_element(By.CSS_SELECTOR, ".product-item-link").text
    except: 
        title = None
    try: 
        price = p.find_element(By.CSS_SELECTOR , "span.price").text
    except: 
        price = None
    try: 
        rate = p.find_element(By.CSS_SELECTOR , "span.my-rating-badge__value").text
    except: 
        rate = None
    try: 
        link = p.find_element(By.CSS_SELECTOR, "a.product-item-link").get_attribute("href")
    except: 
        link = None
    if link:
        data.append({"title": title, "price": price, "rate": rate, "link": link})

final_data = []

for item in data:

    driver.get(item["link"])

    time.sleep(2)

    review_text = brand = type_ = size = resolution = warranty = None

    try:
        driver.find_element(By.XPATH, "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'review')]").click()

        time.sleep(1)

        reviews = driver.find_elements(By.CSS_SELECTOR, ".review-title")

        if reviews:
            review_text = reviews[0].get_attribute("textContent").strip()

    except:
        pass

    try:
        rows = driver.find_elements(By.CSS_SELECTOR, "#product-attribute-specs-table tr")
        specs = {}

        for row in rows:
            try: 
                key = row.find_element(By.TAG_NAME, "th").get_attribute("textContent").strip().lower()
                value = row.find_element(By.TAG_NAME, "td").get_attribute("textContent").strip()
                specs[key] = value

            except:
                continue

        for k, v in specs.items():
            if "brand" in k:
                brand = v
            elif "type" in k:
                type_ = v
            elif "size" in k:
                size = v
            elif "resolution" in k:
                resolution = v
            elif "warranty" in k:
                warranty = v

    except Exception :
        pass
    
    item["review"] = review_text
    item["brand"] = brand
    item["type"] = type_
    item["size"] = size
    item["resolution"] = resolution
    item["warranty"] = warranty

    final_data.append(item)

    print(f"scraped: {item['title']}")

driver.quit()

df = pd.DataFrame(final_data)

df.to_csv("data_sheet 1.csv", index=False, encoding="utf-8-sig")

print("Done! Check fixed_script.csv")