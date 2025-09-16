import asyncio
from bs4 import BeautifulSoup

from apps.crawlers.selenium_helper import SeleniumHelper
from apps.routes.crawl import logger
from apps.crawlers.request_helper import RequestHelper


def is_site_dynamic(url: str, timeout: int = 15) -> bool:
    """
    Determines if a site is likely dynamic by comparing the content
    loaded by requests and a headless browser (Selenium).
    """
    logger.info(f"Performing dynamic site check for: {url}")

    requests_text = ""
    selenium_text = ""

    # 1. Fetch with Requests
    try:
        request_helper = RequestHelper()
        response = request_helper.request(url, timeout=timeout)
        if response:
            requests_text = BeautifulSoup(response.text, 'html.parser').get_text()
        else:
            logger.warning("Requests fetch failed during dynamic check. Assuming site needs Selenium.")
            return True
    except Exception as e:
        logger.error(f"Error fetching with requests during dynamic check: {e}. Assuming site needs Selenium.")
        return True

    # 2. Fetch with Selenium
    try:
        selenium_helper = SeleniumHelper()
        driver = selenium_helper.get_driver(headless=True, page_load_strategy="eager")  # eager for speed
        _, selenium_text = selenium_helper.get_page_source(url, timeout=timeout)
        selenium_helper.quit_driver()
    except Exception as e:
        logger.error(f"Error fetching with Selenium during dynamic check: {e}. Falling back to requests-based crawl.")
        return False

    # 3. Compare content length
    len_req = len(requests_text.strip())
    len_sel = len(selenium_text.strip())

    # If selenium text is more than 30% longer, consider it dynamic.
    if len_req > 0 and (len_sel - len_req) / len_req > 0.3:
        logger.info(f"Site is DYNAMIC. Requests length: {len_req}, Selenium length: {len_sel}")
        return True

    logger.info(f"Site is STATIC. Requests length: {len_req}, Selenium length: {len_sel}")
    return False


async def crawl_website(base_url: str):
    filename = base_url.rstrip("/").split("/")[-1]

    request_helper = RequestHelper()
    sitemap_urls = request_helper.get_sitemaps_from_robots_txt(base_url)

    if len(sitemap_urls) > 0:
        logger.info("Sitemap found. Scraping through Sitemap URLs using requests.")
        all_urls = []
        for sitemap in sitemap_urls:
            all_urls.extend(list(request_helper.get_urls_from_sitemap(sitemap)))
        return request_helper.scrape_using_sitemap_urls(all_urls, filename)

    loop = asyncio.get_event_loop()
    is_dynamic = await loop.run_in_executor(None, is_site_dynamic, base_url)

    if is_dynamic:
        logger.info("Site appears to be dynamic. Using Selenium for crawling.")
        selenium_helper = SeleniumHelper()
        return await loop.run_in_executor(
            None, selenium_helper.scrape_entire_website_with_selenium, base_url, filename
        )
    else:
        logger.info("Site appears to be static. Using Requests for crawling.")
        return await request_helper.scrape_entire_website_with_main_url_async(base_url, filename)


if __name__ == '__main__':
    asyncio.run(crawl_website(base_url="https://www.gms-store.com/"))
