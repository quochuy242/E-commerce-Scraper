import asyncio
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import httpx
from loguru import logger
from utils import (
    ALL_PRODUCT_URL,
    NUM_SCROLL,
    HEADER,
    extract_product,
    get_html,
    get_product_url,
    save_to_json,
    scroll_website,
)
from tqdm import tqdm


async def main():
    start_time = time.time()
    logger.info(f"____Starting scraping at {time.strftime('%Y-%m-%d %H:%M:%S')}____")

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    # chrome_options.add_argument(f"user-agent={HEADER}")

    driver = webdriver.Chrome(
        options=chrome_options, service=Service(executable_path="./chromedriver")
    )

    try:
        driver.get(ALL_PRODUCT_URL)
        page_source = await scroll_website(driver, NUM_SCROLL)

        async with httpx.AsyncClient() as client:
            html = await get_html(url=None, client=client, page_source=page_source)
            urls = get_product_url(html)

            tasks = [
                extract_product(url, client)
                for url in tqdm(urls, desc="Extracting product's details")
            ]
            products = await asyncio.gather(*tasks)

        filename = "nike_products.json"
        save_to_json(products, filename=filename)
        logger.success(f"Data saved to {filename}")

        logger.success(
            f"Execution time: {time.time() - start_time:.2f} seconds - {len(products)} products"
        )

    finally:
        driver.quit()


if __name__ == "__main__":
    asyncio.run(main())
