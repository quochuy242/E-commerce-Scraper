import json
from typing import Dict, List

import httpx
from pydantic import BaseModel
from selectolax.parser import HTMLParser

HEADER = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:129.0) Gecko/20100101 Firefox/129.0"
}

ALL_PRODUCT_URL = "https://www.nike.com/vn/w/mens-shoes-nik1zy7ok"


class Product(BaseModel):
    title: str
    subtitle: str
    price: int
    url: str
    image_url: Dict[str, str]


async def get_html(url: str, client: httpx.AsyncClient) -> str:
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
        print(f"Error while requesting: {resp.status_code}")
        return ""
    return HTMLParser(resp.text)


def get_product_url(html: HTMLParser) -> List[str]:
    products = html.css("div.product-card__body")
    return [
        product.css_first("a.product-card__link-overlay").attributes["href"]
        for product in products
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
    html = await get_html(url, client)
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
