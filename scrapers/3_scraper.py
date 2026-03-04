import json
import re
import datetime
import dataclasses
import requests
import os
from pathlib import Path
from urllib.parse import unquote
from playwright.sync_api import sync_playwright


BASE_DIR = Path(__file__).parent.parent
IMAGE_DIR = BASE_DIR / "public" / "images" / "3"
DATA_DIR  = BASE_DIR / "data" / "3"

BASE_URL = "https://www.3.dk"

# All mobile category pages to crawl for product links
CATEGORY_URLS = [
    f"{BASE_URL}/shop/mobiler/apple/",
    f"{BASE_URL}/shop/mobiler/samsung/",
    f"{BASE_URL}/shop/mobiler/google/",
    f"{BASE_URL}/shop/mobiler/motorola/",
    f"{BASE_URL}/shop/mobiler/oneplus/",
    f"{BASE_URL}/shop/mobiler/nothing/",
    f"{BASE_URL}/shop/mobiler/",
]

# Consent cookies to skip the cookie banner on 3.dk
CONSENT_COOKIES = [
    {"name": "cookieconsent_status", "value": "allow", "domain": ".3.dk", "path": "/"},
    {
        "name": "CookieConsent",
        "value": "{stamp:%27*%27%2Cnecessary:true%2Cpreferences:true%2Cstatistics:true%2Cmarketing:true%2Cver:1}",
        "domain": ".3.dk",
        "path": "/",
    },
]

# Substrings in an image src/srcset that indicate it is NOT a product photo
IMAGE_SKIP_SRC = [
    "logo", "badge", "award", "mobilsiden", "sticker", "icon", "sprite",
    "trustpilot", "payment", "flag", "ribbon", "stamp", "anbefalet",
    "lsiden", "lille", "siden_anbefalet",
]

# Substrings in an image alt text that indicate it is NOT a product photo
IMAGE_SKIP_ALT = ["anbefalet", "badge", "award", "logo", "mobilsiden"]

# Run headless in CI, visible locally (useful for debugging)
HEADLESS = os.environ.get("CI") == "true"

@dataclasses.dataclass
class Offer:
    link: str
    product_name: str
    image_url: str
    provider: str = "3"
    signup_price: int = 0
    data_gb: int = 0
    price_without_subscription: int | None = None
    price_with_subscription: int | None = None
    discount_on_product: int = 0
    min_cost_6_months: int | None = None
    subscription_price_monthly: int | None = None
    saved_at: str = ""


def parse_price(text: str) -> int | None:
    # cleans price and saves as int
    if not text:
        return None
    digits = re.sub(r"\D", "", text.replace(".", ""))
    return int(digits) if digits else None


def download_image(image_url: str, product_name: str) -> str:
    # downloads file unless img already exists, returns local path or empty string on failure
    if not image_url or not product_name:
        return ""

    filename = re.sub(r"[^a-z0-9]", "_", product_name.lower()) + ".webp"
    save_path = IMAGE_DIR / filename

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    if save_path.exists():
        return f"/images/3/{filename}"

    try:
        response = requests.get(image_url, timeout=15)
        if response.status_code == 200:
            save_path.write_bytes(response.content)
            return f"/images/3/{filename}"
    except Exception as e:
        print(f"  Could not download image for '{product_name}': {e}")

    return ""

def _is_product_image(el) -> bool:
    # checks if image is likely to be a product photo based on src, srcset, alt text, and dimensions
    src    = (el.get_attribute("src")    or "").lower()
    srcset = (el.get_attribute("srcset") or "").lower()
    alt    = (el.get_attribute("alt")    or "").lower()

    # Decode percent-encoding twice to handle double-encoded URLs (%2520 → space)
    def decode_twice(s):
        try:
            return unquote(unquote(s))
        except Exception:
            return s

    if not src or src.endswith(".svg"):
        return False

    # Reject images whose src/srcset contains a known non-product keyword
    for text in (src, decode_twice(src), srcset, decode_twice(srcset)):
        if any(keyword in text for keyword in IMAGE_SKIP_SRC):
            return False

    # Reject images with CSS-generated class names in the alt (e.g. "css-Inf9qcb") — these are badges
    if alt.startswith("css-") or any(keyword in alt for keyword in IMAGE_SKIP_ALT):
        return False

    # Reject images that are too small (< 100 px in either dimension)
    try:
        w = int(el.get_attribute("width")  or 0)
        h = int(el.get_attribute("height") or 0)
        if (w and w < 100) or (h and h < 100):
            return False
    except (ValueError, TypeError):
        pass

    try:
        box = el.bounding_box()
        if box and (box["width"] < 100 or box["height"] < 100):
            return False
    except Exception:
        pass

    return True


def find_product_image(page) -> str:
    # find product image by looking for common carousel patterns first, if not then falls back to scanning all images
    carousel_selectors = [
        ".slick-active img",
        '[class*="carousel"] img',
        '[class*="slider"] img',
        "picture img",
    ]

    img_el = None

    # try more specific carousel selectors first
    for selector in carousel_selectors:
        for el in page.query_selector_all(selector):
            if _is_product_image(el):
                img_el = el
                break
        if img_el:
            break

    # fall back to scanning every image on the page
    if not img_el:
        for el in page.query_selector_all("img"):
            if _is_product_image(el):
                img_el = el
                break

    if not img_el:
        return ""

    src = img_el.get_attribute("src") or ""
    if src.startswith("//"):
        return "https:" + src
    if src.startswith("/"):
        return BASE_URL + src
    return src


def get_storage_buttons(page) -> list:
    # gets storage size options by looking for buttons with "GB" in the text, returns list of button elements or [None] if not found
    all_buttons = page.query_selector_all('button[class*="css-1qu461p"]')
    storage_buttons = [
        btn for btn in all_buttons
        if re.search(r"\d+\s*GB", btn.inner_text(), re.IGNORECASE)
    ]
    return storage_buttons or [None]

def extract_upfront_price(page, btn) -> int | None:
    """
    Extract the full (no-subscription) price for the currently selected storage.

    Tries four strategies in order, returning the first one that succeeds:
      1. Read the price directly from the storage button text (e.g. "512 GB  9.199 kr.")
      2. Find the "Størrelse" row and read the price next to it
      3. Find the "Betal kontant" button and read its price span
      4. Scan all elements for a standalone "X.XXX kr." pattern
    """
    kr_pattern = r"(\d{1,3}(?:\.\d{3})+|\d{4,})\s*kr"

    # 1. Price inside the active storage button
    if btn is not None:
        match = re.search(kr_pattern, btn.inner_text().strip())
        if match:
            return int(match.group(1).replace(".", ""))

    # 2. "Størrelse" section row
    storrelse_el = page.locator("text=/Størrelse/").first
    if storrelse_el.count():
        row_text = storrelse_el.locator("xpath=ancestor::*[3]").first.text_content() or ""
        match = re.search(kr_pattern, row_text)
        if match:
            return int(match.group(1).replace(".", ""))

    # 3. "Betal kontant" button
    kontant_el = page.locator("text=Betal kontant").first
    if kontant_el.count():
        parent = kontant_el.locator("xpath=ancestor::button[1]")
        if parent.count():
            return parse_price(parent.locator("span").first.text_content())

    # 4. Any standalone "X.XXX kr." element (skip monthly prices like "270 kr./md.")
    for el in page.locator(r"text=/\d{1,3}\.\d{3}\s*kr\.?/").all():
        raw = el.text_content() or ""
        if "/md" in raw or "md." in raw:
            continue
        match = re.search(r"(\d{1,3}(?:\.\d{3})+)", raw)
        if match:
            return int(match.group(1).replace(".", ""))

    return None


def extract_subscription_info(page) -> tuple[int | None, int | None, int | None]:
    """
    Returns:
        discount_on_product     – "Mobilrabat" discount applied when buying with a subscription
        subscription_price_monthly – monthly subscription price in kr.
        min_cost_6_months       – total minimum cost over 6 months (upfront + 6x monthly)
    """
    # Mobilrabat: discount badge shown next to the selected subscription plan
    discount_on_product = None
    mobilrabat_el = page.locator("text=/Mobilrabat/").first
    if mobilrabat_el.count():
        discount_on_product = parse_price(mobilrabat_el.text_content() or "")

    # Monthly price: look for any "X kr./md." pattern on the page
    subscription_price_monthly = None
    for text in page.locator(r"text=/\d+\s*kr\.?\/md/").all_text_contents():
        match = re.search(r"([\d.]+)\s*kr\.?/md", text)
        if match:
            subscription_price_monthly = int(match.group(1).replace(".", ""))
            break

    # Minimum cost over 6 months (shown as "Mindstepris X.XXX kr.")
    min_cost_6_months = None
    mindste_el = page.locator("text=/Mindstepris/").first
    if mindste_el.count():
        raw = mindste_el.text_content() or ""
        # Use the LAST number to avoid accidentally picking up "6" from "6 mdr."
        numbers = re.findall(r"(\d{1,3}(?:\.\d{3})+|\d+)", raw)
        if numbers:
            min_cost_6_months = int(numbers[-1].replace(".", ""))

    return discount_on_product, subscription_price_monthly, min_cost_6_months


def scrape_product_page(page, url: str, saved_at: str) -> list[Offer]:
    # scrapes product of different options
    try:
        page.goto(url, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(1500)
    except Exception as e:
        print(f"  Could not load {url}: {e}")
        return []

    # Product name (always the page's <h1>)
    name_el = page.query_selector("h1")
    product_name = name_el.inner_text().strip() if name_el else ""
    if not product_name:
        print(f"  No product name found at {url}")
        return []

    image_url = find_product_image(page)
    storage_buttons = get_storage_buttons(page)

    offers = []

    for btn in storage_buttons:
        # Click the storage button to update prices, then read the storage label
        if btn is not None:
            btn_text = btn.inner_text().strip()
            match = re.search(r"(\d+\s*GB)", btn_text, re.IGNORECASE)
            storage_label = match.group(1).replace(" ", "") if match else btn_text
            try:
                btn.click()
                page.wait_for_timeout(800)
            except Exception as e:
                print(f"  Could not click '{storage_label}' button: {e}")
                continue
        else:
            # No storage buttons, try to read storage from the product title
            match = re.search(r"(\d+\s*GB)", product_name, re.IGNORECASE)
            storage_label = match.group(1).replace(" ", "") if match else ""

        full_name = f"{product_name} {storage_label}".strip() if storage_label else product_name

        # prices
        price_without_subscription = extract_upfront_price(page, btn)
        discount_on_product, subscription_price_monthly, min_cost_6_months = extract_subscription_info(page)

        # price with subscription = upfront price minus mobilrabat discount
        if price_without_subscription is not None and discount_on_product is not None:
            price_with_subscription = price_without_subscription - discount_on_product
        else:
            # Fallback: read the "Betal nu" total directly from the page
            betal_nu_el = page.locator("text=Betal nu").locator("xpath=following-sibling::*[1]").first
            price_with_subscription = parse_price(betal_nu_el.text_content()) if betal_nu_el.count() else None

        # if min_cost_6_months can't be  read, calculate it ourselves
        if not min_cost_6_months and price_with_subscription and subscription_price_monthly:
            min_cost_6_months = price_with_subscription + 6 * subscription_price_monthly

        local_image_path = download_image(image_url, full_name)

        print(
            f"    {full_name}: "
            f"kontant={price_without_subscription}, "
            f"sub={price_with_subscription}, "
            f"rabat={discount_on_product}, "
            f"min6={min_cost_6_months}, "
            f"md={subscription_price_monthly}"
        )

        offers.append(Offer(
            link=url,
            product_name=full_name,
            image_url=local_image_path,
            price_without_subscription=price_without_subscription,
            price_with_subscription=price_with_subscription,
            discount_on_product=discount_on_product or 0,
            min_cost_6_months=min_cost_6_months,
            subscription_price_monthly=subscription_price_monthly,
            saved_at=saved_at,
        ))

    return offers

def collect_product_links(page) -> list[str]:
    """
    Visit every category page and collect unique product URLs.
    Product pages have at least 3 path segments (e.g. /shop/mobiler/apple/iphone-16/).
    """
    seen_urls: set[str] = set()
    product_links: list[str] = []

    for cat_url in CATEGORY_URLS:
        print(f"Scanning category: {cat_url}")
        try:
            page.goto(cat_url, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)
        except Exception as e:
            print(f"  Could not load {cat_url}: {e}")
            continue

        # Scroll to the bottom to trigger lazy-loaded product cards
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1500)

        for anchor in page.query_selector_all('a[href*="/shop/mobiler/"]'):
            href = anchor.get_attribute("href") or ""
            path_segments = [p for p in href.strip("/").split("/") if p]

            # At least 3 segments means it's a product page, not a category page
            is_product_page = len(path_segments) >= 3
            has_no_query_params = "?" not in href

            if is_product_page and has_no_query_params:
                full_url = f"{BASE_URL}{href}" if href.startswith("/") else href
                if full_url not in seen_urls:
                    seen_urls.add(full_url)
                    product_links.append(full_url)

    return product_links


def scrape_3():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    saved_at = datetime.datetime.now().strftime("%d-%m-%Y-%H:%M")
    all_offers: list[Offer] = []
    seen_names: set[str] = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
            locale="da-DK",
        )
        context.add_cookies(CONSENT_COOKIES)
        page = context.new_page()

        product_links = collect_product_links(page)
        print(f"\nFound {len(product_links)} unique product pages\n")

        for url in product_links:
            print(f"Scraping: {url}")
            for offer in scrape_product_page(page, url, saved_at):
                if offer.product_name and offer.product_name not in seen_names:
                    seen_names.add(offer.product_name)
                    all_offers.append(offer)

        context.close()
        browser.close()

    output_path = DATA_DIR / "3_offers.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump([dataclasses.asdict(o) for o in all_offers], f, ensure_ascii=False, indent=4)

    print(f"\nDone. Saved {len(all_offers)} offers to '{output_path}'")


if __name__ == "__main__":
    scrape_3()

