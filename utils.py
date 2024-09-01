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


class Product(BaseModel):
    title: str
    subtitle: str
    price: int
    url: str
    image_url: Dict[str, str]


logger.add(LOG_FILE, format="{time} {level} {message}", level="INFO")


async def scroll_website(driver: webdriver.Chrome, num_scroll: int | str) -> None:
    """
    Scroll website to load all products
    """
    last_height = driver.execute_script("return document.body.scrollHeight")

    if isinstance(num_scroll, str) and num_scroll == "str":
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            await asyncio.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                logger.info("Scroll to bottom")
                break
            last_height = new_height
    else:
        for _ in range(num_scroll):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            await asyncio.sleep(2)


async def get_html_from_driver(driver: webdriver.Chrome) -> HTMLParser:
    """
    Parsing html from website driver
    """
    return HTMLParser(driver.page_source)


async def get_html_from_url(url: str, client: httpx.AsyncClient) -> str:
    """
    Get HTML from url

    Args:
        url (str): URL to get HTML
        client (httpx.AsyncClient): HTTPX client

    Returns:
        str: HTML content
    """
    resp = await client.get(url, headers=HEADER)
    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError:
        logger.warning(f"Error while requesting: {resp.status_code}")
        return ""
    return HTMLParser(resp.text)


def get_product_url(html: HTMLParser) -> List[str]:
    products = html.css("div.product-card__body")
    return [
        product.css_first("a.product-card__link-overlay").attributes["href"]
        for product in tqdm(products, desc="Getting the url of each product")
    ]


def convert_price(price: str) -> int:
    return int(price.replace("₫", "").replace(",", ""))


def get_image_url(html: HTMLParser) -> Dict[str, str]:
    """
    Get image url from html

    Args:
        html (HTMLParser): class HTMLParser

    Returns:
        Dict[str, str]: Based on {<color>: <image_url>}, if not found, return {'Default': <image_url>}
    """
    images = html.css_first("div#colorway-picker-container").css("a img")
    if images:
        return {image.attributes["alt"]: image.attributes["src"] for image in images}
    else:
        images: str = (
            html.css_first("div#hero-image").css_first("img").attributes["src"]
        )
        images_resize = images.replace("_1728_", "_144_")
        return {"Default": images_resize}


async def extract_product(url: str, client: httpx.AsyncClient) -> Product:
    """
    Extract product information from url

    Args:
        url (str): URL to extract product information
        client (httpx.AsyncClient): HTPPX Client

    Returns:
        Product: returning product information
    """
    html = await get_html_from_url(url, client)
    return Product(
        title=html.css_first("h1#pdp_product_title").text(),
        subtitle=html.css_first("h1#pdp_product_subtitle").text(),
        price=convert_price(html.css_first("div#price-container").text()),
        url=url,
        image_url=get_image_url(html),
    )


def save_to_json(products: List[Product], filename: str) -> None:
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(
            [product.model_dump() for product in products],
            f,
            ensure_ascii=False,
            indent=4,
        )
