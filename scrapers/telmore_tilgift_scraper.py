import json
import os
import re
import datetime
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_URL = "https://www.telmore.dk"


def download_image(image_url, product_name):
    if not image_url:
        return ""

    filename = re.sub(r'[^a-z0-9]', '_', product_name.lower()) + ".webp"
    save_path = os.path.join(BASE_DIR, f"public/images/telmore/{filename}")
    os.makedirs(os.path.join(BASE_DIR, "public/images/telmore"), exist_ok=True)

    if os.path.exists(save_path):
        return f"/images/telmore/{filename}"

    try:
        img_response = requests.get(image_url, timeout=15)
        if img_response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(img_response.content)
            return f"/images/telmore/{filename}"
    except Exception as e:
        print(f"  Image download failed for {product_name}: {e}")
    return ""


def scrape_detail_page(page, url):
    page.goto(url, timeout=60000, wait_until="domcontentloaded")
    page.wait_for_timeout(2500)
    html = page.content()
    soup = BeautifulSoup(html, 'html.parser')

    min_cost_6_months = None
    discount_on_product = None
    subscription_price_monthly = None
    image_url = ""

    # min cost
    disclaimer = soup.find('p', class_='text--xs') or soup.find('p', class_='mb-0')
    if disclaimer:
        text = disclaimer.get_text(" ", strip=True)
        m = re.search(r'Mindstepris\s*:\s*(\d[\d.]*)\s*kr', text, re.IGNORECASE)
        if m:
            min_cost_6_months = int(m.group(1).replace('.', ''))
        else:
            m = re.search(r'Mindstepris\s+kr\.?\s*:\s*(\d+)', text, re.IGNORECASE)
            if m:
                min_cost_6_months = int(m.group(1))

    # discount
    discount_span = soup.find('span', string=re.compile(r'Mobilrabat|Rabat', re.IGNORECASE))
    if discount_span:
        discount_val = "".join(re.findall(r'\d+', discount_span.get_text()))
        if discount_val:
            discount_on_product = int(discount_val)

    # subscription monthly price
    for strong in soup.find_all('strong'):
        t = strong.get_text(strip=True)
        m = re.search(r'(\d+)\s*kr\./md', t, re.IGNORECASE)
        if m:
            subscription_price_monthly = int(m.group(1))
            break

    # img
    img_tag = soup.find('img', class_='product-list-card-campaign-image')
    if img_tag:
        src = img_tag.get('src', '')
        if src.startswith('//'):
            image_url = 'https:' + src
        else:
            image_url = src
    # Fallback
    if not image_url:
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if 'ctfassets' in src:
                image_url = src
                break

    return min_cost_6_months, discount_on_product, subscription_price_monthly, image_url


def scrape_telmore_tilgift():
    os.makedirs(os.path.join(BASE_DIR, 'data/telmore'), exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, 'public/images/telmore'), exist_ok=True)

    listing_url = "https://www.telmore.dk/shop/tilgift/"
    date_time = datetime.datetime.now().strftime("%d-%m-%Y-%H:%M")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        page = browser.new_page(viewport={"width": 1920, "height": 1080})

        # --- Scrape listing page ---
        print(f"Loading listing: {listing_url}")
        page.goto(listing_url, timeout=60000, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        listing_html = page.content()
        soup = BeautifulSoup(listing_html, 'html.parser')

        cards = soup.find_all('div', class_='tlm-product-list-card')
        print(f"Found {len(cards)} tilgift offers")

        scraped_data = []

        for card in cards:
            name_tag = card.find('strong', class_='h4')
            brand_tag = card.find('span', class_='gray--text')
            price_tag = card.find('span', class_='tlm-product-list-card__price')
            link_tag = card.find('a', href=True)

            product_name = name_tag.get_text(strip=True) if name_tag else ""
            brand = brand_tag.get_text(strip=True) if brand_tag else ""
            full_name = f"{brand} {product_name}".strip() if brand else product_name

            # Product price (what you pay for the gift item)
            product_price = None
            if price_tag:
                val = "".join(re.findall(r'\d+', price_tag.get_text()))
                if val:
                    product_price = int(val)

            href = link_tag['href'] if link_tag else ""
            detail_url = (BASE_URL + href) if href.startswith('/') else href

            print(f"  Scraping detail: {full_name} -> {detail_url}")
            min_cost_6_months, discount_on_product, subscription_price_monthly, image_url = scrape_detail_page(page, detail_url)

            # Download image
            local_image = download_image(image_url, full_name) if image_url else ""

            name_lower = full_name.lower()
            if "tab" in name_lower:
                product_type = "tablet"
            elif "beoplay" in name_lower or "airpods" in name_lower:
                product_type = "sound"
            else:
                product_type = "gift"

            # price_with_subscription = what you pay for the gift item
            price_with_subscription = product_price
            # price_without_subscription = gift price before subscription discount
            price_without_subscription = None
            if price_with_subscription is not None and discount_on_product is not None:
                price_without_subscription = price_with_subscription + discount_on_product

            item = {
                "link": detail_url,
                "product_name": full_name,
                "image_url": local_image,
                "provider": "Telmore",
                "type": product_type,
                "price_without_subscription": price_without_subscription,
                "price_with_subscription": price_with_subscription,
                "subscription_price_monthly": subscription_price_monthly,
                "discount_on_product": discount_on_product,
                "min_cost_6_months": min_cost_6_months,
                "saved_at": date_time
            }

            if "brugt" in full_name.lower():
                print(f"  Skipping used product: {full_name}")
                continue

            scraped_data.append(item)
            print(f"    price_with_subscription={price_with_subscription}, discount_on_product={discount_on_product}, min_cost_6_months={min_cost_6_months}")

        browser.close()

    out_path = os.path.join(BASE_DIR, 'data/telmore/telmore_tilgift_offers.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(scraped_data, f, ensure_ascii=False, indent=4)

    print(f"\nExported {len(scraped_data)} tilgift offers to {out_path}")


if __name__ == "__main__":
    scrape_telmore_tilgift()

