import requests
from bs4 import BeautifulSoup
import json
import datetime
import re
import os


# setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.makedirs(os.path.join(BASE_DIR, 'data/telmore'), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, 'public/images/telmore'), exist_ok=True)


url = "https://www.oister.dk/tilbehor-til-abonnement"
response = requests.get(url)
date_time = datetime.datetime.now().strftime("%d-%m-%Y-%H:%M")

def download_image(image_url, product_name):
    if not image_url or not product_name:
        return ""

    filename = re.sub(r'[^a-z0-9]', '_', product_name.lower()) + ".webp"
    save_path = os.path.join(BASE_DIR, f"public/images/oister/{filename}")
    os.makedirs(os.path.join(BASE_DIR, "public/images/oister"), exist_ok=True)

    if os.path.exists(save_path):
        return f"/images/oister/{filename}"  # web path for the JSON

    response = requests.get(image_url)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(response.content)
        return f"/images/oister/{filename}"  # web path for the JSON
    return ""


if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')

    offer_list = soup.find_all('div', class_='col--double-padding-bottom')
    promo_card = soup.find('div', class_='section-promo-voice-card')
    if promo_card:
        offer_list = [promo_card] + list(offer_list)

    scraped_data = []

    for offer in offer_list:
        item = {
            "product_name": "",
            "image_url": "",
            "provider": "Oister",
            "signup_price": 99,
            "data_gb": "",
            "price_without_subscription": "",
            "price_with_subscription": "",
            "min_cost_6_months": "",
            "subscription_price_monthly": "",
            "discount_on_product": "",
            "saved_at": date_time,
            "sold_out": "false"
        }

        # image url
        image_div = offer.find('div', class_="ribbon-container")
        if image_div:
            img_tag = image_div.select_one('img.d-none.d-sm-block')
            if img_tag:
                raw_src = img_tag.get('srcset') or img_tag.get('data-srcset')
                if raw_src:
                    src_url = raw_src.split(' ')[0]
                    if ".png" in src_url:
                        src_url = src_url.split(".png")[0] + ".png"
                    item["image_url"] = f"https://www.oister.dk{src_url}"

        # campaign
        punchline_div = offer.find('div', class_='card__punchline')
        if punchline_div:

            # name of the discounted product - must be before download_image
            strong_tag = punchline_div.find('strong')
            if strong_tag:
                item["product_name"] = strong_tag.get_text(strip=True)

            full_text = punchline_div.get_text(strip=True).replace("inkl. ", "")

            match = re.search(r'\(Værdi\s?(.*?)\)', full_text)

            if match:
                raw_discount = match.group(1).strip()
                clean_number = raw_discount.replace(".", "").replace(",-", "")

                try:
                    item["discount_on_product"] = int(clean_number)
                    item["price_without_subscription"] = int(clean_number)
                    item["price_with_subscription"] = 0
                except ValueError:
                    item["discount_on_product"] = clean_number

        # download image now that we have the product name
        item["image_url"] = download_image(item["image_url"], item["product_name"])

        product_card = offer.find('div', class_='card--product')

        if product_card:
            options = product_card.find_all('div', class_='card__option')
            if len(options) >= 2:
                t_amount = options[0].find('h3', class_='card__text-data').text.strip()
                t_type = options[0].find('h4', class_='card__text-type').text.strip()

                d_amount = options[1].find('h3', class_='card__text-data').text.strip()
                d_type = options[1].find('h4', class_='card__text-type').text.strip()

                item["data_gb"] = f"{d_amount} {d_type}"
                item["talk"] = f"{t_amount} {t_type}"

            all_data_fields = product_card.find_all('h3', class_='card__text-data')
            if len(all_data_fields) >= 3:
                try:
                    price = int(all_data_fields[2].text.strip().replace('.', ''))
                    item["subscription_price_monthly"] = price
                    item["min_cost_6_months"] = price * 6 + 99
                except ValueError:
                    item["subscription_price_monthly"] = all_data_fields[2].text.strip()

            callout_element = product_card.find('div', class_='card__callout')
            if callout_element:
                strong_tag = callout_element.find('strong')
                if strong_tag:
                    item["eu_data"] = strong_tag.text.strip()

            sold_out_element = product_card.find('div', class_='card__btn')
            if sold_out_element:
                if "Udsolgt" in sold_out_element.get_text(strip=True):
                    item["sold_out"] = 'true'

        if product_card:
            scraped_data.append(item)

    with open(os.path.join(BASE_DIR, 'data/oister/oister_offers.json'), 'w', encoding='utf-8') as f:
        json.dump(scraped_data, f, ensure_ascii=False, indent=4)

    print(f"Exported {len(scraped_data)} offers to 'data/oister/oister_offers.json'")

else:
    print(f"Error! Could not fetch the page. Status code: {response.status_code}")