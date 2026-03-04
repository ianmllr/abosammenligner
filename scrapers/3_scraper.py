import json
import re
import datetime
import dataclasses
import requests
import os
from pathlib import Path
from playwright.sync_api import sync_playwright


BASE_DIR = Path(__file__).parent.parent
IMAGE_DIR = BASE_DIR / "public" / "images" / "3"
DATA_DIR  = BASE_DIR / "data" / "3"

BASE_URL = "https://www.3.dk"

CATEGORY_URLS: dict[str, str] = {
    f"{BASE_URL}/shop/mobiler/apple/":    "phone",
    f"{BASE_URL}/shop/mobiler/samsung/":  "phone",
    f"{BASE_URL}/shop/mobiler/motorola/": "phone",
    f"{BASE_URL}/shop/mobiler/oneplus/":  "phone",
    f"{BASE_URL}/shop/mobiler/nothing/":  "phone",
    f"{BASE_URL}/shop/mobiler/":          "phone",
    f"{BASE_URL}/shop/tablets/":          "tablet",
}

CONSENT_COOKIES = [
    {"name": "cookieconsent_status", "value": "allow", "domain": ".3.dk", "path": "/"},
    {
        "name": "CookieConsent",
        "value": "{stamp:%27*%27%2Cnecessary:true%2Cpreferences:true%2Cstatistics:true%2Cmarketing:true%2Cver:1}",
        "domain": ".3.dk",
        "path": "/",
    },
]

# keywords that indicate an image is not a product photo
IMAGE_SKIP_KEYWORDS = [
    "logo", "badge", "award", "mobilsiden", "sticker", "icon", "sprite",
    "trustpilot", "payment", "flag", "ribbon", "stamp", "anbefalet",
    "lsiden", "lille", "siden_anbefalet",
]

HEADLESS = os.environ.get("CI") == "true"


@dataclasses.dataclass
class Offer:
    link: str
    product_name: str
    image_url: str
    provider: str = "3"
    type: str = "phone"
    signup_price: int = 0
    data_gb: int = 0
    price_without_subscription: int | None = None
    price_with_subscription: int | None = None
    discount_on_product: int = 0
    min_cost_6_months: int | None = None
    subscription_price_monthly: int | None = None
    saved_at: str = ""


def parse_price(text: str) -> int | None:
    if not text:
        return None
    digits = re.sub(r"[\D.]", "", text)
    return int(digits) if digits else None


def download_image(image_url: str, product_name: str) -> str:
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
    src = (el.get_attribute("src") or "").lower()
    alt = (el.get_attribute("alt") or "").lower()

    if not src or src.endswith(".svg"):
        return False
    if any(kw in src for kw in IMAGE_SKIP_KEYWORDS):
        return False
    if alt.startswith("css-") or any(kw in alt for kw in IMAGE_SKIP_KEYWORDS):
        return False

    try:
        box = el.bounding_box()
        if box and (box["width"] < 100 or box["height"] < 100):
            return False
    except Exception:
        pass

    return True


def find_product_image(page) -> str:
    selectors = [
        ".slick-active img",
        '[class*="carousel"] img',
        '[class*="slider"] img',
        "picture img",
        "img",
    ]

    img_el = next(
        (el for selector in selectors for el in page.query_selector_all(selector) if _is_product_image(el)),
        None,
    )
    if not img_el:
        return ""

    src = img_el.get_attribute("src") or ""
    if src.startswith("//"):
        return "https:" + src
    if src.startswith("/"):
        return BASE_URL + src
    return src


def get_storage_buttons(page) -> list:
    gb_pattern = re.compile(r"\d+\s*GB", re.IGNORECASE)

    # Strategy 1: buttons inside the "Størrelse" section
    storrelse_el = page.locator("text=/Størrelse/").first
    if storrelse_el.count():
        parent = None
        for level in range(2, 6):
            candidate = storrelse_el.locator(f"xpath=ancestor::*[{level}]").first
            if candidate.locator("text=/\\d+\\s*GB/i").count() > 1:
                parent = candidate
                break
        if parent is None:
            parent = storrelse_el.locator("xpath=ancestor::*[3]").first

        buttons = [btn for btn in parent.locator("button").all() if gb_pattern.search(btn.text_content() or "")]
        if buttons:
            return buttons

        for tag in ("li", "div", "span", "a"):
            clickable = [
                el for el in parent.locator(tag).all()
                if gb_pattern.search(el.text_content() or "")
                and el.get_attribute("role") in ("button", "option", "tab", "radio")
            ]
            if clickable:
                return clickable

    # Strategy 2: any button on the page with a GB amount
    buttons = [btn for btn in page.query_selector_all("button") if gb_pattern.search(btn.inner_text())]
    return buttons or [None]


def extract_upfront_price(page, btn) -> int | None:
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

    # 4. Any standalone "X.XXX kr." element (skip monthly prices)
    for el in page.locator(r"text=/\d{1,3}\.\d{3}\s*kr\.?/").all():
        raw = el.text_content() or ""
        if "/md" in raw or "md." in raw:
            continue
        match = re.search(r"(\d{1,3}(?:\.\d{3})+)", raw)
        if match:
            return int(match.group(1).replace(".", ""))

    return None


def extract_subscription_info(page) -> tuple[int | None, int | None, int | None]:
    """Returns (discount_on_product, subscription_price_monthly, min_cost_6_months)."""
    discount_on_product = None
    mobilrabat_el = page.locator("text=/Mobilrabat/").first
    if mobilrabat_el.count():
        discount_on_product = parse_price(mobilrabat_el.text_content() or "")

    subscription_price_monthly = None
    for text in page.locator(r"text=/\d+\s*kr\.?\/md/").all_text_contents():
        match = re.search(r"([\d.]+)\s*kr\.?/md", text)
        if match:
            subscription_price_monthly = int(match.group(1).replace(".", ""))
            break

    # take the last number to avoid picking up "6" from "6 mdr."
    min_cost_6_months = None
    mindste_el = page.locator("text=/Mindstepris/").first
    if mindste_el.count():
        numbers = re.findall(r"(\d{1,3}(?:\.\d{3})+|\d+)", mindste_el.text_content() or "")
        if numbers:
            min_cost_6_months = int(numbers[-1].replace(".", ""))

    return discount_on_product, subscription_price_monthly, min_cost_6_months


def _read_static_storage_label(page, product_name: str) -> str:
    """Reads storage size from the Størrelse row when there are no clickable buttons."""
    storrelse_el = page.locator("text=/Størrelse/").first
    if storrelse_el.count():
        row = storrelse_el.locator("xpath=ancestor::*[3]").first

        for bold_sel in ("strong", "b", "[class*='bold']", "[class*='Bold']"):
            bold_el = row.locator(bold_sel).first
            if bold_el.count():
                m = re.search(r"(\d+\s*(?:GB|TB))", bold_el.text_content() or "", re.IGNORECASE)
                if m:
                    return m.group(1).replace(" ", "")

        m = re.search(r"(\d+\s*(?:GB|TB))", row.text_content() or "", re.IGNORECASE)
        if m:
            return m.group(1).replace(" ", "")

    m = re.search(r"(\d+\s*GB)", product_name, re.IGNORECASE)
    return m.group(1).replace(" ", "") if m else ""


def scrape_product_page(page, url: str, saved_at: str, product_type: str = "phone") -> list[Offer]:
    try:
        page.goto(url, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(1500)
    except Exception as e:
        print(f"  Could not load {url}: {e}")
        return []

    name_el = page.query_selector("h1")
    product_name = name_el.inner_text().strip() if name_el else ""
    if not product_name:
        print(f"  No product name found at {url}")
        return []

    image_url = find_product_image(page)
    offers = []

    for btn in get_storage_buttons(page):
        if btn is not None:
            btn_text = btn.inner_text().strip()
            m = re.search(r"(\d+\s*(?:GB|TB))", btn_text, re.IGNORECASE)
            storage_label = m.group(1).replace(" ", "") if m else btn_text
            try:
                btn.click()
                page.wait_for_timeout(800)
            except Exception as e:
                print(f"  Could not click '{storage_label}' button, using displayed value: {e}")
        else:
            storage_label = _read_static_storage_label(page, product_name)

        full_name = f"{product_name} {storage_label}".strip() if storage_label else product_name

        price_without_subscription = extract_upfront_price(page, btn)
        discount_on_product, subscription_price_monthly, min_cost_6_months = extract_subscription_info(page)

        if price_without_subscription is not None and discount_on_product is not None:
            price_with_subscription = price_without_subscription - discount_on_product
        else:
            betal_nu_el = page.locator("text=Betal nu").locator("xpath=following-sibling::*[1]").first
            price_with_subscription = parse_price(betal_nu_el.text_content()) if betal_nu_el.count() else None

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
            type=product_type,
            price_without_subscription=price_without_subscription,
            price_with_subscription=price_with_subscription,
            discount_on_product=discount_on_product or 0,
            min_cost_6_months=min_cost_6_months,
            subscription_price_monthly=subscription_price_monthly,
            saved_at=saved_at,
        ))

    return offers


def collect_product_links(page) -> list[tuple[str, str]]:
    seen_urls: set[str] = set()
    product_links: list[tuple[str, str]] = []

    for cat_url, product_type in CATEGORY_URLS.items():
        print(f"Scanning category: {cat_url} (type={product_type})")
        try:
            page.goto(cat_url, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)
        except Exception as e:
            print(f"  Could not load {cat_url}: {e}")
            continue

        # scroll to trigger lazy-loaded product cards
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1500)

        link_selector = 'a[href*="/shop/mobiler/"], a[href*="/shop/tablets/"]'
        for anchor in page.query_selector_all(link_selector):
            href = anchor.get_attribute("href") or ""
            # at least 4 slashes = product page, not a category
            if href.count("/") >= 4 and "?" not in href:
                full_url = f"{BASE_URL}{href}" if href.startswith("/") else href
                if full_url not in seen_urls:
                    seen_urls.add(full_url)
                    product_links.append((full_url, product_type))

    return product_links


def scrape_3():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

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
        context.add_cookies(CONSENT_COOKIES)  # type: ignore[arg-type]
        page = context.new_page()

        product_links = collect_product_links(page)
        print(f"\nFound {len(product_links)} unique product pages\n")

        for url, product_type in product_links:
            print(f"Scraping: {url} (type={product_type})")
            for offer in scrape_product_page(page, url, saved_at, product_type):
                if offer.product_name and offer.product_name not in seen_names:
                    seen_names.add(offer.product_name)
                    all_offers.append(offer)

    output_path = DATA_DIR / "3_offers.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump([dataclasses.asdict(o) for o in all_offers], f, ensure_ascii=False, indent=4)

    print(f"\nDone. Saved {len(all_offers)} offers to '{output_path}'")


if __name__ == "__main__":
    scrape_3()

