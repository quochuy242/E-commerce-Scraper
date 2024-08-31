import asyncio
import time
import httpx

from utils import (
    ALL_PRODUCT_URL,
    extract_product,
    get_html,
    get_product_url,
    save_to_json,
)


async def main():
    start_time = time.time()
    # Fetch all product URLs
    async with httpx.AsyncClient() as client:
        html = await get_html(ALL_PRODUCT_URL, client)
        urls = get_product_url(html)
        tasks = [extract_product(url, client) for url in urls]
        products = await asyncio.gather(*tasks)

    # Save data to JSON file
    filename = "nike_products.json"
    save_to_json(products, filename=filename)
    print(f"Data saved to {filename}")

    # Calculate and print execution time
    print(
        f"Execution time: {time.time() - start_time:.2f} seconds - {len(products)} products"
    )


if __name__ == "__main__":
    asyncio.run(main())
