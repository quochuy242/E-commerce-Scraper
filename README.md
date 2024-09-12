# Nike Scraper

This repository contains a Nike Scraper tool designed to extract product information from Nike's website.

## Description

The Nike Scraper is an asynchronous web scraping tool that extracts product details from Nike's website. It uses Selenium for web navigation and HTTPX for making asynchronous HTTP requests.

## Features

- Scrape product information from Nike's website
- Extract product titles, subtitles, prices, and image URLs
- Asynchronous scraping for improved performance
- Scrolling functionality to load all products
- Save scraped data to JSON file

## How to use

Instructions on how to install and set up the Nike Scraper:

1. Clone this repository
2. Install the required dependencies

```bash
pip install -r requirements.txt
```

3. Run the script

```bash
python3 main.py
```

The script will start scraping Nike's website and save the results to `nike_products.json`

## License

This project is licensed under the Apache License 2.0. See the LICENSE file for details.

## Disclaimer

This tool is for educational purposes only.
