import json
import os
import re
import datetime
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

is_ci = os.environ.get('CI') == 'true'  # GitHub Actions sets this automatically



# scrapes prisjagt to find the lowest price of a product currently to see if the 6-month price of a subscription is worth it

def clean_search_query(product_name):
    # remove color in parentheses e.g. "(obsidian)", "(sort)"
    name = re.sub(r'\(.*?\)', '', product_name)
    # remove generic words that hurt search results
    name = re.sub(r'\bsmartphone\b|\bLTE\b', '', name, flags=re.IGNORECASE)
    # clean up extra whitespace
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def get_market_price(page, product_name):
    query = clean_search_query(product_name).replace(' ', '+')
    url = f"https://prisjagt.dk/search?availability=AVAILABLE&query={query}&category=pc%3Amobiltelefoner%7Cpc%3Asmartwatches%7Cpc%3Ahovedtelefoner%7Cpc%3Atablets&sort=score"

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(2000)
        page.wait_for_selector('[data-test="ProductGridCard"]', timeout=8000)
    except:
        print(f"  → Could not load results for: {product_name}")
        return None

    first_card = page.query_selector('[data-test="ProductGridCard"]')
    if not first_card:
        return None

    # target price by sentry element attribute
    price_el = first_card.query_selector('[data-sentry-element="Component"][data-sentry-component="Text"].font-heaviest')
    if not price_el:
        # fallback: just grab all Text components and find the price one
        all_text = first_card.query_selector_all('[data-sentry-component="Text"]')
        for el in all_text:
            text = el.inner_text().strip()
            if 'kr' in text:
                digits = "".join(re.findall(r'\d+', text))
                return int(digits) if digits else None
        return None

    raw = price_el.inner_text().strip()
    digits = "".join(re.findall(r'\d+', raw))
    return int(digits) if digits else None

def scrape_prisjagt():
    os.makedirs(os.path.join(BASE_DIR, 'data/prisjagt'), exist_ok=True)

    # load all existing JSONs to get product names
    providers = [
        ('data/telmore/telmore_offers.json', 'product_name'),
        ('data/oister/oister_offers.json', 'product_name'),
        ('data/elgiganten/elgiganten_offers.json', 'product'),
        ('data/cbb/cbb_offers.json', 'product_name')
    ]

    products = []
    for path, name_field in providers:
        full_path = os.path.join(BASE_DIR, path)
        if os.path.exists(full_path):
            with open(full_path, encoding='utf-8') as f:
                offers = json.load(f)
            for offer in offers:
                name = offer.get(name_field, '')
                if name:
                    products.append(name)

    # deduplicate
    products = list(set(products))

    results = {}
    date_time = datetime.datetime.now().strftime("%d-%m-%Y-%H:%M")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=is_ci)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="da-DK",
        )

        page = context.new_page()

        # bypass cookie popup by setting consent cookie
        context.add_cookies([
            {
                "name": "consentDate",
                "value": "2026-02-23T17:25:15.142Z",
                "domain": "prisjagt.dk",
                "path": "/"
            },
            {
                "name": "consentUUID",
                "value": "b7d4dfb8-a27d-43a9-bca2-4b1dbb3205ff_53",
                "domain": "prisjagt.dk",
                "path": "/"
            }
        ])

        page.goto("https://prisjagt.dk", wait_until="domcontentloaded")

        for product_name in products:
            print(f"Looking up: {product_name}")
            price = get_market_price(page, product_name)
            results[product_name] = {
                "market_price": price,
                "looked_up_at": date_time
            }
            print(f"  → {price} kr.")

        browser.close()

    with open(os.path.join(BASE_DIR, 'data/prisjagt/prisjagt_prices.json'), 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

    print(f"\nLooked up {len(results)} products.")


if __name__ == "__main__":
    scrape_prisjagt()