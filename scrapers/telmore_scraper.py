import json
import os
import requests
import datetime
import re
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.makedirs(os.path.join(BASE_DIR, 'data/telmore'), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, 'public/images/telmore'), exist_ok=True)

url = "https://www.telmore.dk/shop/mobiltelefoner"
date_time = datetime.datetime.now().strftime("%d-%m-%Y-%H:%M")

def download_image(image_url, product_name):
    if not image_url:
        return ""

    # create a clean filename from product name
    filename = re.sub(r'[^a-z0-9]', '_', product_name.lower()) + ".webp"
    save_path = os.path.join(BASE_DIR, f"public/images/telmore/{filename}")
    os.makedirs(os.path.join(BASE_DIR, "public/images/telmore"), exist_ok=True)

    if os.path.exists(save_path):
        return f"/images/telmore/{filename}"  # web path for the JSON

    response = requests.get(image_url)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(response.content)
        return f"/images/telmore/{filename}"  # web path for the JSON
    return ""

# img is dynamically loaded
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1920, "height": 10000})  # very tall viewport to load images for all products
    page.goto(url)
    page.wait_for_selector('div.carousel-image-wrapper')
    page.wait_for_timeout(3000)
    html = page.content()
    browser.close()

soup = BeautifulSoup(html, 'html.parser')

offer_list = soup.find_all('div', class_='col-md-6 col-12')

scraped_data = []

for offer in offer_list:
    item = {
        "product_name": "",
        "image_url": "",
        "provider": "Telmore",
        "signup_price": "",
        "data_gb": "",
        "price_without_subscription": "",
        "price_with_subscription": "",
        "discount_on_product": "",
        "min_cost_6_months": "",
        "saved_at": date_time
    }

    # product name
    name_tag = offer.find('strong', class_='h4')
    if name_tag:
        item["product_name"] = name_tag.get_text(strip=True)

    # image url
    img_div = offer.find('div', class_='carousel-image-wrapper')
    if img_div:
        img_tag = img_div.find('img')
        if img_tag:
            src_url = img_tag.get('src')
            if src_url:
                if src_url.startswith('//'):
                    item["image_url"] = f"https:{src_url}"
                else:
                    item["image_url"] = src_url

    item["image_url"] = download_image(item["image_url"], item["product_name"])

    # price with subscription
    price_tag = offer.find('span', class_='tlm-product-list-card__price')
    if price_tag:
        price_val = "".join(re.findall(r'\d+', price_tag.get_text()))
        if price_val:
            item["price_with_subscription"] = int(price_val)

    # discount
    discount_span = offer.find('span', string=re.compile(r'Mobilrabat', re.IGNORECASE))
    if discount_span:
        discount_val = "".join(re.findall(r'\d+', discount_span.get_text()))
        if discount_val:
            item["discount_on_product"] = int(discount_val)

    # min price
    min_price_span = offer.find('span', string=re.compile(r'Mindstepris', re.IGNORECASE))
    if min_price_span:
        min_val = "".join(re.findall(r'\d+', min_price_span.get_text()))
        if min_val:
            item["min_cost_6_months"] = int(min_val)

    # calculate price without subscription
    if item["price_with_subscription"] and item["discount_on_product"]:
        item["price_without_subscription"] = item["price_with_subscription"] + item["discount_on_product"]

    scraped_data.append(item)

# save results to json file
with open(os.path.join(BASE_DIR, 'data/telmore/telmore_offers.json'), 'w', encoding='utf-8') as f:
    json.dump(scraped_data, f, ensure_ascii=False, indent=4)

print(f"Exported {len(scraped_data)} offers")