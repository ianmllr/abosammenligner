import requests
from bs4 import BeautifulSoup
import re
from pathlib import Path
from typing import TypedDict
from scraper_utils import download_image_cached, now_timestamp, write_json, log, offer_summary

# setup
BASE_DIR = Path(__file__).resolve().parent.parent
AFFILIATE_PREFIX = "https://go.adt284.net/t/t?a=1666103641&as=2054240298&t=2&tk=1&url="
DATA_DIR = BASE_DIR / "data" / "oister"
IMAGE_DIR = BASE_DIR / "public" / "images" / "oister"
OUTPUT_PATH = DATA_DIR / "oister_offers.json"

# Blocked products due to bad naming by oister (will be skipped)
BLOCKED_PRODUCTS = [
    "Robotstøvsuger"
]


class OfferItem(TypedDict):
    link: str
    product_name: str
    image_url: str
    provider: str
    type: str
    price_without_subscription: int | str
    price_with_subscription: int | str
    min_cost_6_months: int | str
    subscription_price_monthly: int | str
    discount_on_product: int | str
    saved_at: str


def _bs4_str(value: object) -> str:
    return value if isinstance(value, str) else ""


def download_image(image_url, product_name):
    return download_image_cached(
        image_url,
        product_name,
        IMAGE_DIR,
        "/images/oister",
        base_url="https://www.oister.dk",
    )


def product_name_from_url(href: str, fallback_name: str) -> str:

    # the url pattern is always: <subscription-description>-inkl-<product-name>
    url = href.rstrip('/').split('/')[-1]  # take last path segment
    if '-inkl-' in url:
        product_part = url.split('-inkl-', 1)[1]
        words = product_part.replace('-', ' ').split()
        titled = []
        for w in words:
            # keep all-digit or alphanumeric model codes in their natural case but capitalise first letter
            titled.append(w[0].upper() + w[1:] if w else w)
        return ' '.join(titled)
    return fallback_name


def scrape_oister():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    url = "https://www.oister.dk/tilbehor-til-abonnement"
    response = requests.get(url)
    date_time = now_timestamp()

    if response.status_code != 200:
        log(f"Error! Could not fetch the page. Status code: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')

    offer_list = soup.find_all('div', class_='col--double-padding-bottom')
    promo_card = soup.find('div', class_='section-promo-voice-card')
    if promo_card:
        offer_list = [promo_card] + list(offer_list)

    scraped_data = []

    for offer in offer_list:
        item: OfferItem = {
            "link": "",
            "product_name": "",
            "image_url": "",
            "provider": "Oister",
            "type": "tablet",
            "price_without_subscription": "",
            "price_with_subscription": "",
            "min_cost_6_months": "",
            "subscription_price_monthly": 0,
            "discount_on_product": 0,
            "saved_at": date_time,
        }

        # image url
        image_div = offer.find('div', class_="ribbon-container")
        if image_div:
            # find all images and pick the one with 'tilgift' in src (the actual product)
            all_imgs = image_div.find_all('img')
            for img in all_imgs:
                src = _bs4_str(img.get('src')) or _bs4_str(img.get('data-src'))
                if 'tilgift' in src:
                    if src.startswith('/'):
                        item["image_url"] = f"https://www.oister.dk{src}"
                    else:
                        item["image_url"] = src
                    break

        # campaign
        punchline_div = offer.find('div', class_='card__punchline')
        if punchline_div:

            # name of the discounted product - must be before download_image
            strong_tag = punchline_div.find('strong')
            if strong_tag:
                item["product_name"] = strong_tag.get_text(strip=True)
                if "urbanista" in item["product_name"].lower():
                    item["type"] = "sound"

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

        # product link
        if product_card:
            link_tag = product_card.find('a')
            if link_tag:
                href = _bs4_str(link_tag.get('href'))
                if href:
                    full_link = f"https://www.oister.dk{href}" if href.startswith('/') else href
                    item["link"] = AFFILIATE_PREFIX + full_link
                    # if the punchline name is a generic category label (e.g. "Samsung tablet"),
                    # derive the proper name from the URL -> "Samsung Galaxy Tab A11"
                    GENERIC_LABELS = {'tablet', 'headphones', 'høretelefoner', 'earphones',
                                      'earbuds', 'speaker', 'højttaler', 'watch', 'ur'}
                    last_word = item["product_name"].split()[-1].lower() if item["product_name"] else ''
                    if last_word in GENERIC_LABELS and '-inkl-' in href:
                        better_name = product_name_from_url(href, item["product_name"])
                        if better_name and better_name != item["product_name"]:
                            log(f"  Enriched name from: '{item['product_name']}' -> '{better_name}'")
                            item["product_name"] = better_name


        if product_card:
            options = product_card.find_all('div', class_='card__option')
            if len(options) >= 2:
                pass  # data_gb and talk fields removed — not used by frontend

            all_data_fields = product_card.find_all('h3', class_='card__text-data')
            if len(all_data_fields) >= 3:
                try:
                    price = int(all_data_fields[2].text.strip().replace('.', ''))
                    item["subscription_price_monthly"] = price
                    item["min_cost_6_months"] = price * 6 + 99
                except ValueError:
                    item["subscription_price_monthly"] = all_data_fields[2].text.strip()


        if product_card:
            # Check if product is in blocklist
            product_name_lower = item.get("product_name", "").lower()
            is_blocked = any(keyword.lower() in product_name_lower for keyword in BLOCKED_PRODUCTS)
            
            if is_blocked:
                matched_keyword = next(keyword for keyword in BLOCKED_PRODUCTS if keyword.lower() in product_name_lower)
                log(f"  Skipping blocked product: {item['product_name']} (matched: '{matched_keyword}')")
            else:
                scraped_data.append(item)
                offer_summary(
                    item["product_name"],
                    sub=item["price_with_subscription"],
                    rabat=item["discount_on_product"],
                    kontant=item["price_without_subscription"],
                    min6=item["min_cost_6_months"],
                    md=item["subscription_price_monthly"],
                )

    write_json(OUTPUT_PATH, scraped_data)

    log(f"Exported {len(scraped_data)} offers to 'data/oister/oister_offers.json'")


if __name__ == "__main__":
    scrape_oister()