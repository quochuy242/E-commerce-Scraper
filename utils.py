import asyncio
import json
from loguru import logger
from typing import Dict, List

import httpx
from pydantic import BaseModel
from selectolax.parser import HTMLParser
from selenium import webdriver
from tqdm import tqdm

HEADER = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:129.0) Gecko/20100101 Firefox/129.0"
}

ALL_PRODUCT_URL = "https://www.nike.com/vn/w/mens-shoes-nik1zy7ok"
NUM_SCROLL: int | str = "all"
LOG_FILE = "./log/nike_scraper.txt"
SCROLL_PAUSE_TIME = 5


class Product(BaseModel):
    """
    Represents a product with its details.
    """

    title: str | None = ""
    subtitle: str | None = ""
    price: int | None = 0
    url: str | None = ""
    image_url: Dict[str, str] | None = {"0": "0"}


logger.add(LOG_FILE, format="{time} {level} {message}", level="INFO")


async def scroll_website(driver: webdriver.Chrome, num_scroll: int | str) -> str:
    """
    Scrolls the website to load all products.

    Args:
        driver (webdriver.Chrome): The Selenium WebDriver instance.
        num_scroll (int | str): Number of times to scroll or "all" for full page scroll.

    Returns:
        str: The page source after scrolling.
    """
    scroll_count = 0
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        scroll_count += 1
        logger.info(f"Scrolling {scroll_count} times")
        await asyncio.sleep(SCROLL_PAUSE_TIME)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height or (
            isinstance(num_scroll, int) and scroll_count >= num_scroll
        ):
            logger.info("Scroll to bottom")
            break
        last_height = new_height
    return driver.page_source


async def get_html(
    url: str, client: httpx.AsyncClient, page_source: str
) -> HTMLParser | None:
    """
    Fetches HTML content from a URL or uses provided page source.
    Args:
        url (str): The URL to fetch HTML from.
        client (httpx.AsyncClient): The HTTP client for making requests.
        page_source (str): Pre-fetched page source, if available.

    Returns:
        HTMLParser | None: Parsed HTML content or None if request fails.
    """
    if page_source:
        return HTMLParser(page_source)

    try:
        resp = await client.get(url, headers=HEADER, follow_redirects=True)
        resp.raise_for_status()
        return HTMLParser(resp.text)
    except httpx.HTTPStatusError:
        logger.warning(f"Error while requesting {url}: {resp.status_code}")
        return None


def get_product_url(html: HTMLParser) -> List[str]:
    """
    Extracts product URLs from the HTML content.

    Args:
        html (HTMLParser): Parsed HTML content.
    Returns:
        List[str]: List of product URLs.
    """
    return [
        product.css_first("a.product-card__link-overlay").attributes["href"]
        for product in tqdm(
            html.css("div.product-card__body"), desc="Getting the url of each product"
        )
    ]


def convert_price(price: str) -> int:
    """
    Converts a price string to an integer.

    Args:
        price (str): Price string with currency symbol and commas.

    Returns:
        int: Price as an integer.
    """
    return int(price.replace("₫", "").replace(",", ""))


def get_image_url(html: HTMLParser) -> Dict[str, str]:
    """
    Extracts image URLs from the product page.

    Args:
        html (HTMLParser): Parsed HTML content of the product page.

    Returns:
        Dict[str, str]: Dictionary of image colors and their URLs.
    """
    images = html.css_first("div#colorway-picker-container")
    if images:
        return {
            img.attributes["alt"]: img.attributes["src"] for img in images.css("a img")
        }
    else:
        image = html.css_first("div#hero-image img")
        return (
            {"Default": image.attributes["src"].replace("_1728_", "_144_")}
            if image
            else {}
        )


async def extract_product(url: str, client: httpx.AsyncClient) -> Product:
    """
    Extracts product details from a given URL.

    Args:
        url (str): URL of the product page.
        client (httpx.AsyncClient): The HTTP client for making requests.

    Returns:
        Product: A Product object containing the extracted details.
    """
    html = await get_html(url, client, page_source=None)
    await asyncio.sleep(1)
    if not isinstance(html, HTMLParser):
        return Product()
    return Product(
        title=html.css_first("h1#pdp_product_title").text(),
        subtitle=html.css_first("h1#pdp_product_subtitle").text(),
        price=convert_price(html.css_first("div#price-container").text()),
        url=url,
        image_url=get_image_url(html),
    )


def save_to_json(products: List[Product], filename: str) -> None:
    """
    Saves a list of Product objects to a JSON file.

    Args:
        products (List[Product]): List of Product objects to save.
        filename (str): Name of the file to save the JSON data.
    """
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(
            [product.model_dump() for product in products],
            f,
            ensure_ascii=False,
            indent=4,
        )
