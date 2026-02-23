import json
import time
import datetime
import re
import requests
from playwright.sync_api import sync_playwright
import os

# setup

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.makedirs(os.path.join(BASE_DIR, 'data/telmore'), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, 'public/images/telmore'), exist_ok=True)

def clean_product_name(product_name):
    # stop at storage size bc we don't need to save color
    match = re.search(r'(\d+\s?gb)', product_name, re.IGNORECASE)
    if match:
        return product_name[:match.end()].strip()
    return product_name


def download_image(image_url, product_name):
    if not image_url or not product_name:
        return ""

    filename = re.sub(r'[^a-z0-9]', '_', product_name.lower()) + ".webp"
    save_path = os.path.join(BASE_DIR, f"public/images/elgiganten/{filename}")
    os.makedirs(os.path.join(BASE_DIR, "public/images/elgiganten"), exist_ok=True)

    if os.path.exists(save_path):
        return f"/images/elgiganten/{filename}"  # web path for the JSON

    response = requests.get(image_url)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(response.content)
        return f"/images/elgiganten/{filename}"  # web path for the JSON
    return ""

def scrape_elgiganten():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1920, "height": 10000}
        )

        page = context.new_page()
        date_time = datetime.datetime.now().strftime("%d-%m-%Y-%H:%M")

        cleaned_results = []

        max_pages = 3

        for page_num in range(1, max_pages + 1):
            if page_num == 1:
                url = "https://www.elgiganten.dk/mobil-tablet-smartwatch/mobiltelefon"
            else:
                url = f"https://www.elgiganten.dk/mobil-tablet-smartwatch/mobiltelefon/page-{page_num}"

            print(f"scanning page {page_num}: {url}")

            try:
                page.goto(url, wait_until="networkidle")
                page.wait_for_selector('a[data-testid="product-card"]', timeout=10000)
            except Exception as e:
                print(f"Couldn't load page {page_num} or found no products: {e}")
                continue

            product_cards = page.query_selector_all('a[data-testid="product-card"]')
            print(f"Found {len(product_cards)} products on page {page_num}")

            for card in product_cards:
                card_html = card.inner_html()

                if "Mindstepris" in card_html or "mobilrabat" in card_html.lower():
                    sku = card.get_attribute('data-item-id')
                    name_el = card.query_selector('h2')
                    product_name = name_el.inner_text().strip() if name_el else "Ukendt model"

                    price_data = page.evaluate(f"""async () => {{
                        const res = await fetch('/api/price/{sku}');
                        return res.ok ? res.json() : null;
                    }}""")

                    api_payload = {"type": "Telecom", "sku": str(sku), "step": "identification"}
                    raw_data = page.evaluate("""async (payload) => {
                        const res = await fetch('/api/subscriptions', {
                            method: 'POST',
                            headers: { 'Content-Type': 'text/plain;charset=UTF-8' },
                            body: JSON.stringify(payload)
                        });
                        return res.ok ? res.json() : null;
                    }""", api_payload)

                    if raw_data and 'data' in raw_data:
                        d = raw_data.get('data', {})
                        sub = d.get('subscription', {})

                        # get image url and download it
                        image_el = card.query_selector('.product-card-image img')
                        raw_image_url = image_el.get_attribute('src') if image_el else None
                        local_image_path = download_image(raw_image_url, product_name)

                        current_price_list = price_data.get('price', {}).get('current', []) if price_data else []

                        price_without_subscription = current_price_list[0] if current_price_list else None
                        price_with_subscription = d.get('upfrontPrice')

                        # only calculate discount if both prices are available
                        if price_without_subscription is not None and price_with_subscription is not None:
                            discount = int(price_without_subscription - price_with_subscription)
                        else:
                            discount = ""

                        price_with_subscription = d.get('upfrontPrice')

                        entry = {
                            "product": product_name,
                            "image_url": local_image_path,
                            "sku": sku,
                            "provider": d.get('provider', {}).get('name'),
                            "title": sub.get('name'),
                            "data_gb": sub.get('monthlyDataPlanGB'),
                            "price_without_subscription": price_without_subscription,
                            "price_with_subscription": price_with_subscription,
                            "min_cost_6_months": d.get('minimalTotalCost'),
                            "subscription_price_monthly": d.get('monthlyCost', {}).get('total'),
                            "discount_on_product": discount,
                            "benefits": sub.get('bulletPoints', []),
                            "saved_at": date_time,
                            "sold_out": "false"
                        }
                        cleaned_results.append(entry)

                    time.sleep(0.5)

            time.sleep(2)

        with open(os.path.join(BASE_DIR, 'data/elgiganten/elgiganten_offers.json'), 'w', encoding='utf-8') as f:
            json.dump(cleaned_results, f, ensure_ascii=False, indent=4)

        print(f"\n Scanned {max_pages} pages. Saved {len(cleaned_results)} offers 'elgiganten_offers.json'")
        browser.close()


if __name__ == "__main__":
    scrape_elgiganten()