import json
import datetime
import re
import requests
import os
from playwright.sync_api import sync_playwright

# setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

is_ci = os.environ.get('CI') == 'true'


def download_image(image_url, product_name):
    if not image_url or not product_name:
        return ""

    filename = re.sub(r'[^a-z0-9]', '_', product_name.lower()) + ".webp"
    save_path = os.path.join(BASE_DIR, f"public/images/3/{filename}")
    os.makedirs(os.path.join(BASE_DIR, "public/images/3"), exist_ok=True)

    if os.path.exists(save_path):
        return f"/images/3/{filename}"

    try:
        response = requests.get(image_url, timeout=15)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return f"/images/3/{filename}"
    except Exception as e:
        print(f"  Couldn't download image for {product_name}: {e}")

    return ""


def parse_price(text):
    """Extract integer price from a Danish price string like '8.699 kr.' or '270 kr./md.'"""
    if not text:
        return None
    digits = re.sub(r'[^\d]', '', text.replace('.', ''))
    try:
        return int(digits) if digits else None
    except ValueError:
        return None


def scrape_product_page(page, url, date_time):
    """Visit a single product page on 3.dk and extract all relevant offer data."""
    try:
        page.goto(url, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(1500)
    except Exception as e:
        print(f"  Could not load {url}: {e}")
        return []

    results = []

    # --- Product name ---
    name_el = page.query_selector('h1')
    product_name = name_el.inner_text().strip() if name_el else ""
    if not product_name:
        print(f"  Could not find product name at {url}")
        return []

    # --- Image ---
    # 3.dk renders the main product image inside a picture element in the left-side gallery.
    # We look for the largest/most-relevant <img> by filtering out known non-product images.
    SKIP_SRC_PATTERNS = ['logo', 'badge', 'award', 'mobilsiden', 'sticker', 'icon', 'sprite',
                         'trustpilot', 'payment', 'flag', 'ribbon', 'stamp', 'anbefalet']
    SKIP_ALT_PATTERNS = ['anbefalet', 'badge', 'award', 'logo', 'mobilsiden']

    def _is_product_image(el):
        src = (el.get_attribute('src') or '').lower()
        alt = (el.get_attribute('alt') or '').lower()
        if not src or src.endswith('.svg'):
            return False
        if any(p in src for p in SKIP_SRC_PATTERNS):
            return False
        if any(p in alt for p in SKIP_ALT_PATTERNS):
            return False
        # Skip tiny images — check HTML attributes first, then rendered bounding box
        try:
            w = int(el.get_attribute('width') or 0)
            h = int(el.get_attribute('height') or 0)
            if (w and w < 80) or (h and h < 80):
                return False
        except (ValueError, TypeError):
            pass
        try:
            box = el.bounding_box()
            if box and (box['width'] < 80 or box['height'] < 80):
                return False
        except Exception:
            pass
        return True

    image_url = ""
    # 1. Try the active carousel slide first
    img_el = None
    for candidate_sel in [
        '.slick-active img',
        '[class*="carousel"] img',
        '[class*="slider"] img',
        'picture img',
    ]:
        for el in page.query_selector_all(candidate_sel):
            if _is_product_image(el):
                img_el = el
                break
        if img_el:
            break

    # 2. Fallback: walk all imgs and pick the first valid product image
    if not img_el:
        for el in page.query_selector_all('img'):
            if _is_product_image(el):
                img_el = el
                break

    if img_el:
        src = img_el.get_attribute('src') or ''
        if src.startswith('//'):
            src = 'https:' + src
        elif src.startswith('/'):
            src = 'https://www.3.dk' + src
        image_url = src

    # --- Storage size buttons ---
    # Each storage size is a separate button; clicking one updates all prices on the page.
    # Selector: buttons containing a <p> with "GB" text inside a div matching the size selector area.
    size_buttons = page.query_selector_all('button[class*="css-1qu461p"]')

    # Filter to only storage size buttons (those containing a <p> with GB and a price span)
    storage_buttons = []
    for btn in size_buttons:
        btn_text = btn.inner_text()
        if re.search(r'\d+\s*GB', btn_text, re.IGNORECASE):
            storage_buttons.append(btn)

    if not storage_buttons:
        # fallback: just scrape the current default storage displayed
        storage_buttons = [None]

    for btn in storage_buttons:
        # Determine the storage label for naming
        if btn is not None:
            btn_text = btn.inner_text().strip()
            storage_match = re.search(r'(\d+\s*GB)', btn_text, re.IGNORECASE)
            storage_label = storage_match.group(1).replace(' ', '') if storage_match else btn_text

            # click the storage size button to update prices
            try:
                btn.click()
                page.wait_for_timeout(800)
            except Exception as e:
                print(f"  Could not click storage button '{storage_label}': {e}")
                continue
        else:
            # no storage buttons found — figure out storage from page title/content
            storage_match = re.search(r'(\d+\s*GB)', product_name, re.IGNORECASE)
            storage_label = storage_match.group(1).replace(' ', '') if storage_match else ""

        full_name = f"{product_name} {storage_label}".strip() if storage_label else product_name

        # --- Price without subscription (kontant / upfront price) ---
        price_without_subscription = None

        # Strategy 1: The currently-selected storage button itself shows the upfront price.
        # After clicking, the active button typically carries a price like "9.199 kr." in its text.
        if btn is not None:
            # Re-query the active/selected storage button (it may have a different class when active)
            active_btn_text = btn.inner_text().strip()
            # Extract a price-like number from the button text, ignoring the GB label
            # e.g. "512 GB\n9.199 kr." → 9199
            price_match = re.search(r'(\d{1,3}(?:\.\d{3})+|\d{4,})\s*kr', active_btn_text)
            if price_match:
                price_without_subscription = int(price_match.group(1).replace('.', ''))

        # Strategy 2: Look for a "Størrelse" labelled row/section which shows "<X> GB ... <price> kr."
        # The row with the size name and price is a reliable source on 3.dk product pages.
        if not price_without_subscription:
            storrelse_el = page.locator('text=/Størrelse/').first
            if storrelse_el.count():
                # Walk up to the containing row and look for a kr. price
                row_text = storrelse_el.locator('xpath=ancestor::*[3]').first.text_content() or ''
                price_match = re.search(r'(\d{1,3}(?:\.\d{3})+|\d{4,})\s*kr', row_text)
                if price_match:
                    price_without_subscription = int(price_match.group(1).replace('.', ''))

        # Strategy 3: "Betal kontant" button — original approach
        if not price_without_subscription:
            kontant_el = page.locator('text=Betal kontant').first
            if kontant_el.count():
                parent = kontant_el.locator('xpath=ancestor::button[1]')
                if parent.count():
                    price_span = parent.locator('span').first
                    price_without_subscription = parse_price(price_span.text_content())

        # Strategy 4: Any element whose text matches a standalone price pattern "X.XXX kr."
        # near the top of the page (price summary area), avoiding monthly prices (kr./md.)
        if not price_without_subscription:
            for el in page.locator('text=/\\d{1,3}\\.\\d{3}\\s*kr\\.?/').all():
                raw = el.text_content() or ''
                if '/md' in raw or 'md.' in raw:
                    continue
                m = re.search(r'(\d{1,3}(?:\.\d{3})+)', raw)
                if m:
                    price_without_subscription = int(m.group(1).replace('.', ''))
                    break

        # --- Subscription / Mobilrabat ---
        # 3.dk shows a "Mobilrabat X.XXX kr." badge on the selected subscription
        discount_on_product = None
        mobilrabat_el = page.locator('text=/Mobilrabat/').first
        if mobilrabat_el.count():
            raw = mobilrabat_el.text_content() or ""
            discount_on_product = parse_price(raw)

        # --- Price with subscription (upfront price after mobilrabat) ---
        price_with_subscription = None
        if price_without_subscription is not None and discount_on_product is not None:
            price_with_subscription = price_without_subscription - discount_on_product
        else:
            # try "Betal nu" total minus fragt
            betales_nu_el = page.locator('text=Betal nu').locator('xpath=following-sibling::*[1]').first
            if betales_nu_el.count():
                price_with_subscription = parse_price(betales_nu_el.text_content())

        # --- Monthly subscription price ---
        subscription_price_monthly = None
        # Look for "X kr./md." pattern near the subscription selector
        maaned_texts = page.locator('text=/\\d+\\s*kr\\.?\\/md/').all_text_contents()
        for t in maaned_texts:
            m = re.search(r'([\d.]+)\s*kr\.?/md', t)
            if m:
                subscription_price_monthly = int(m.group(1).replace('.', ''))
                break

        # --- Min cost 6 months ---
        min_cost_6_months = None
        mindste_el = page.locator('text=/Mindstepris/').first
        if mindste_el.count():
            raw = mindste_el.text_content() or ''
            # Use the LAST price number in the sentence to avoid picking up "6" from "6 mdr."
            # Matches patterns like "5.020" or "10.319" (Danish thousands-separated numbers)
            matches = re.findall(r'(\d{1,3}(?:\.\d{3})+|\d+)', raw)
            if matches:
                min_cost_6_months = int(matches[-1].replace('.', ''))

        if not min_cost_6_months:
            # fallback: kontant + 6 * monthly
            if price_with_subscription is not None and subscription_price_monthly is not None:
                min_cost_6_months = price_with_subscription + 6 * subscription_price_monthly


        # download image (use the full_name for a unique filename per storage)
        local_image_path = download_image(image_url, full_name)

        entry = {
            "link": url,
            "product_name": full_name,
            "image_url": local_image_path,
            "provider": "3",
            "signup_price": 0,
            "data_gb": 0,
            "price_without_subscription": price_without_subscription,
            "price_with_subscription": price_with_subscription,
            "discount_on_product": discount_on_product or 0,
            "min_cost_6_months": min_cost_6_months,
            "subscription_price_monthly": subscription_price_monthly,
            "saved_at": date_time,
        }

        print(f"    {full_name}: kontant={price_without_subscription}, sub={price_with_subscription}, "
              f"rabat={discount_on_product}, min6={min_cost_6_months}, md={subscription_price_monthly}")

        results.append(entry)

    return results


def scrape_3():
    os.makedirs(os.path.join(BASE_DIR, 'data/3'), exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, 'public/images/3'), exist_ok=True)

    overview_url = "https://www.3.dk/shop/mobiler/apple/"
    categories = [
        "https://www.3.dk/shop/mobiler/apple/",
        "https://www.3.dk/shop/mobiler/samsung/",
        "https://www.3.dk/shop/mobiler/google/",
        "https://www.3.dk/shop/mobiler/motorola/",
        "https://www.3.dk/shop/mobiler/oneplus/",
        "https://www.3.dk/shop/mobiler/nothing/",
        "https://www.3.dk/shop/mobiler/",
    ]

    date_time = datetime.datetime.now().strftime("%d-%m-%Y-%H:%M")
    all_results = []
    seen_urls = set()
    seen_names = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=is_ci)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="da-DK",
        )
        # inject consent cookie to skip cookie banner
        context.add_cookies([
            {"name": "cookieconsent_status", "value": "allow",    "domain": ".3.dk", "path": "/"},
            {"name": "CookieConsent",        "value": "{stamp:%27*%27%2Cnecessary:true%2Cpreferences:true%2Cstatistics:true%2Cmarketing:true%2Cver:1}", "domain": ".3.dk", "path": "/"},
        ])
        page = context.new_page()

        # --- Collect product links from all category pages ---
        product_links = []

        for cat_url in categories:
            print(f"Scanning category: {cat_url}")
            try:
                page.goto(cat_url, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(2000)
            except Exception as e:
                print(f"  Could not load {cat_url}: {e}")
                continue

            # scroll to trigger lazy loading
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1500)

            # find all product card links — 3.dk uses anchors with /shop/mobiler/ paths
            anchors = page.query_selector_all('a[href*="/shop/mobiler/"]')
            for a in anchors:
                href = a.get_attribute('href') or ''
                # filter to individual product pages (not category pages)
                # product pages have more path segments than just /shop/mobiler/<brand>/
                parts = [p for p in href.strip('/').split('/') if p]
                if len(parts) >= 3 and href not in seen_urls:
                    full_url = f"https://www.3.dk{href}" if href.startswith('/') else href
                    # skip pagination / filter links
                    if '?' not in full_url and full_url not in seen_urls:
                        seen_urls.add(full_url)
                        product_links.append(full_url)

        print(f"\nFound {len(product_links)} unique product pages to scrape\n")

        # --- Scrape each product page ---
        for product_url in product_links:
            print(f"Scraping: {product_url}")
            entries = scrape_product_page(page, product_url, date_time)

            for entry in entries:
                name = entry["product_name"]
                if name and name not in seen_names:
                    seen_names.add(name)
                    all_results.append(entry)

        context.close()
        browser.close()

    output_path = os.path.join(BASE_DIR, 'data/3/3_offers.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=4)

    print(f"\nScraping complete. Saved {len(all_results)} offers to '3_offers.json'")


if __name__ == "__main__":
    scrape_3()

