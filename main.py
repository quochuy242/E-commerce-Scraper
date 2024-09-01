import asyncio
import time
import httpx
from utils import (
    ALL_PRODUCT_URL,
    extract_product,
    get_html_from_driver,
    get_product_url,
    save_to_json,
    scroll_website,
    NUM_SCROLL,
    logger,
)
import datetime as dt

from selenium import webdriver
from tqdm import tqdm


async def main():
    logger.info(f"____Starting scraping at {dt.datetime.now()}____")
    start_time = time.time()

    # Initial Chrome Driver
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run Chrome in headless mode (without GUI)
    driver = webdriver.Chrome(options=options)
    driver.get(url=ALL_PRODUCT_URL)

    # Scroll the website to get all products
    scroll_website(driver, NUM_SCROLL)

    # Fetch all product URLs
    async with httpx.AsyncClient() as client:
        html = await get_html_from_driver(driver)
        urls = get_product_url(html)
        tasks = [
            extract_product(url, client)
            for url in tqdm(urls, desc="Extracting product")
        ]
        products = await asyncio.gather(*tasks)

    # Close the WebDriver
    driver.quit()

    # Save data to JSON file
    filename = "nike_products.json"
    save_to_json(products, filename=filename)
    logger.success(f"Data saved to {filename}")

    # Calculate and print execution time
    logger.success(
        f"Execution time: {time.time() - start_time:.2f} seconds - {len(products)} products"
    )


if __name__ == "__main__":
    asyncio.run(main())
