import json
import datetime
import re
import requests
import os
from playwright.sync_api import sync_playwright

# setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def download_image(image_url, product_name):
    if not image_url or not product_name:
        return ""

    # cbb uses relative image paths, so we prepend the domain
    if image_url.startswith('/'):
        image_url = f"https://www.cbb.dk{image_url}"

    # clean product name to create a safe filename
    filename = re.sub(r'[^a-z0-9]', '_', product_name.lower()) + ".webp"
    save_path = os.path.join(BASE_DIR, f"public/images/cbb/{filename}")
    os.makedirs(os.path.join(BASE_DIR, "public/images/cbb"), exist_ok=True)

    if os.path.exists(save_path):
        return f"/images/cbb/{filename}"

    try:
        response = requests.get(image_url)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return f"/images/cbb/{filename}"
    except Exception as e:
        print(f"Couldn't download image for {product_name}: {e}")

    return ""


def parse_price(text):
    # extract integer price from a string like '1.064 kr.' or '39 kr./md.
    if not text:
        return None
    cleaned = re.sub(r'\D', '', text.replace('.', ''))
    try:
        return int(cleaned)
    except ValueError:
        return None


def get_min_cost_from_page(page, url):
    # minimum 6 month price is more complicated to extract because of the way CBB structures their offers with a mix of upfront price and subscription options
    # returns int or None
    try:
        page.goto(url, wait_until="networkidle", timeout=30000)

        # "kontant price" is the upfront price (that you can't actually pay)
        # it's the "phones price" but it's artifical since you have to buy a subscription
        # but we need it to calculate the min 6 month cost
        kontant_price = None

        kontant_block = page.locator('text=Kontant').first
        if kontant_block:
            parent = kontant_block.locator('xpath=ancestor::div[contains(@class,"payment") or contains(@class,"option") or contains(@class,"row")][1]')
            price_text = parent.locator('.price, [class*="price"], strong').first.text_content()
            kontant_price = parse_price(price_text)

        if not kontant_price:
            # fallback: grab "Betales nu" total and subtract fragt (65 kr default)
            betales_nu = page.locator('text=Betales nu').locator('xpath=following-sibling::*[1]').first.text_content()
            fragt_text = page.locator('text=Fragt').locator('xpath=following-sibling::*[1]').first.text_content()
            total = parse_price(betales_nu)
            fragt = parse_price(fragt_text) or 65
            if total:
                kontant_price = total - fragt

        # subscription (first months can be discounted)
        promo_price = None
        promo_months = None
        regular_price = None

        # different ways to find default selected subscription
        selected_sub = page.locator('[class*="selected"] .subscription-price, [class*="active"] .subscription-price').first
        if not selected_sub.count():
            # fallback: just take the first subscription option (CBB pre-selects the cheapest)
            selected_sub = page.locator('[class*="subscription"], [class*="abonnement"]').first

        # the info text under the subscription price contains the promo structure
        # look for this pattern anywhere on the page within the selected block
        info_texts = page.locator('text=/kr\\.?\\/md\\. i \\d+ md/').all_text_contents()

        for info in info_texts:
            # Try to match the full pattern: "39kr./md. i 2 md. - Herefter 129 kr."
            m = re.search(
                r'([\d.]+)\s*kr\.?/md\.?\s+i\s+(\d+)\s+md\.?\s*[-–]\s*[Hh]erefter\s+([\d.]+)\s*kr',
                info.replace('\xa0', ' ')
            )
            if m:
                promo_price = int(m.group(1).replace('.', ''))
                promo_months = int(m.group(2))
                regular_price = int(m.group(3).replace('.', ''))
                break  # use the first (default/cheapest) match

        if kontant_price and promo_price is not None and promo_months is not None and regular_price is not None:
            remaining_months = 6 - promo_months
            if remaining_months < 0:
                remaining_months = 0
            min_cost = kontant_price + (promo_months * promo_price) + (remaining_months * regular_price)
            return min_cost

        # if no promo structure found, try simpler: kontant + 6 * monthly_price
        # (for subscriptions without a promo period)
        if kontant_price:
            monthly_texts = page.locator('text=/\\d+ kr\\.?\\/md/').all_text_contents()
            for t in monthly_texts:
                m = re.search(r'([\d.]+)\s*kr\.?/md', t)
                if m:
                    monthly = int(m.group(1).replace('.', ''))
                    return kontant_price + (6 * monthly)

    except Exception as e:
        print(f"  Error scraping {url}: {e}")

    return None


def build_entry(phone, page, date_time):
    product_name = phone.get("headline", "Ukendt model")

    # format product link
    url_path = phone.get("url")
    product_link = f"https://www.cbb.dk{url_path}" if url_path else ""

    # get image
    raw_image_url = phone.get("image", {}).get("url")
    local_image_path = download_image(raw_image_url, product_name)

    # price
    price_with_subscription = phone.get("priceInt")

    # check stock status
    sold_out = "true" if phone.get("buttonText", "").upper() == "UDSOLGT" else "false"

    # get accurate min cost by visiting the product page
    min_cost = None
    if product_link:
        print(f"  Fetching min cost for: {product_name}")
        min_cost = get_min_cost_from_page(page, product_link)
        if min_cost:
            print(f"    → {min_cost} kr.")
        else:
            print(f"    → Could not extract min cost")

    return {
        "link": product_link,
        "product_name": product_name,
        "image_url": local_image_path,
        "provider": "CBB",
        "signup_price": 0,
        "data_gb": 0,
        "price_without_subscription": 0,
        "price_with_subscription": price_with_subscription,
        "subscription_price_monthly": 0,
        "min_cost_6_months": min_cost,
        "discount_on_product": 0,
        "saved_at": date_time,
        "sold_out": sold_out
    }


def scrape_cbb():
    os.makedirs(os.path.join(BASE_DIR, 'data/cbb'), exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, 'public/images/cbb'), exist_ok=True)

    date_time = datetime.datetime.now().strftime("%d-%m-%Y-%H:%M")
    cleaned_results = []

    # cbb's direct api endpoint for loading phones
    api_url = "https://www.cbb.dk/api/product/load-phones/"
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    print("Fetching product list from CBB API...")
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        raw_data = response.json()
    except requests.RequestException as e:
        print(f"Couldn't fetch data from CBB API: {e}")
        return

    phones_list = raw_data.get("content", {}).get("phones", [])
    print(f"Found {len(phones_list)} products in JSON")

    is_ci = os.environ.get('CI') == 'true'

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=is_ci)
        context = browser.new_context(
            locale="da-DK",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        # accept cookies up front by injecting consent cookies
        context.add_cookies([
            {"name": "CookieInformationConsent", "value": "true", "domain": ".cbb.dk", "path": "/"},
        ])
        page = context.new_page()

        for phone in phones_list:
            entry = build_entry(phone, page, date_time)
            cleaned_results.append(entry)

        browser.close()

    # save output
    output_path = os.path.join(BASE_DIR, 'data/cbb/cbb_offers.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(cleaned_results, f, ensure_ascii=False, indent=4)

    print(f"\nScraping complete. Saved {len(cleaned_results)} offers to 'cbb_offers.json'")


if __name__ == "__main__":
    scrape_cbb()