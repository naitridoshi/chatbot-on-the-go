import gzip
import io
import asyncio
import json
import os
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlsplit

import requests
import urllib3
from bs4 import BeautifulSoup

from libs.constants import BASIC_HEADERS
from apps.crawlers import logger

from libs.logger import color_string

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class RequestHelper:
    def __init__(self, proxies: dict = None, headers: dict = BASIC_HEADERS):
        self.session = requests.Session()
        if proxies:
            self.session.proxies.update(proxies)
        self.session.headers.update(headers)

    def request(self, url: str, method: str = 'GET', timeout: int = 10,params:dict=None,payload:dict | list =None):
        logger.debug(f"Requesting {url} ...")

        for try_request in range(1, 5):
            start_time = time.time()
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=payload,
                    verify=False,
                    timeout=timeout,
                    stream=True
                )
                time_taken = f'{time.time() - start_time:.2f} seconds'
                if response.status_code == 200:
                    logger.debug(
                        f'Try: {try_request}, ' 
                        f'Status Code: {response.status_code}, ' 
                        f'Response Length: ' 
                        f'{len(response.text) / 1024 / 1024:.2f} MB, ' 
                        f'Time Taken: {color_string(time_taken)}.'
                    )
                    return response
                else:
                    logger.warning(
                        f'REQUEST FAILED - {try_request}: ' 
                        f'Status Code: {response.status_code}, ' 
                        f'Time Taken: {color_string(time_taken)}.'
                    )
            except Exception as err:
                logger.error(
                    f'ERROR OCCURRED - {try_request}: Time Taken ' 
                    f"{color_string(f'{time.time() - start_time:.2f} seconds')}"
                    f', Error: {err}'
                )

        return None

    def get_list_of_urls(self, url: str):
        response = self.request(url)
        if response is None:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        base_netloc = urlparse(url).netloc
        
        found_urls = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            # Join the URL to make it absolute
            abs_url = urljoin(url, href)
            # Parse it again to check the domain
            parsed_abs = urlparse(abs_url)
            
            # Check if it's an http/https URL and belongs to the same domain
            if parsed_abs.scheme in ['http', 'https'] and parsed_abs.netloc == base_netloc:
                found_urls.add(abs_url)

        logger.debug(f'Extracted {len(found_urls)} URLs from {url}')
        return found_urls

    def get_data_from_url_using_soup(self, url: str):
        response = self.request(url)
        if response is None:
            print("response is none")
            return None, None
        logger.debug(
            f'Got the response for {url}, data length: {len(response.text)}'
        )
        soup = BeautifulSoup(response.text, 'html.parser')
        soup_text = soup.get_text()
        text = soup_text.strip().replace('\n', '').replace('\t', '').replace(
            '\r',
            ''
        ).replace('\v', '').replace('\f', '').replace('\xa0', '')
        cleaned_text = re.sub(r'\s+', ' ', soup_text.strip())
        return text, cleaned_text

    def get_sitemaps_from_robots_txt(self, base_url: str) -> list[str]:
        parsed = urlsplit(base_url)
        if not parsed.scheme or not parsed.netloc:
            return []

        origin = f"{parsed.scheme}://{parsed.netloc}/"
        robots_url = urljoin(origin, "robots.txt")
        logger.debug(f"Fetching robots.txt from {robots_url}")

        response = self.request(robots_url)
        if response is None or response.status_code != 200:
            logger.warning(f"Could not fetch or access robots.txt from {robots_url}")
            return []

        pattern = re.compile(
            r'^\s*(?:#\s*)?sitemap\s*:\s*([^\s#]+)',
            re.IGNORECASE | re.MULTILINE
        )
        raw_urls = [m.group(1).strip() for m in pattern.finditer(response.text)]

        sitemaps = []
        seen = set()
        for u in raw_urls:
            # Absolute or relative?
            if not urlsplit(u).scheme:
                u = urljoin(origin, u)
            if u not in seen:
                seen.add(u)
                sitemaps.append(u)

        logger.debug(f"Found {len(sitemaps)} sitemap(s) in {robots_url}: {sitemaps}")
        return sitemaps

    def _process_url(self, url: str, main_url: str = None):
        """
        Processes a single URL: constructs full URL, skips certain file types, and scrapes data.
        Returns a tuple: (full_url, scraped_data, is_skipped)
        """
        if main_url and not str(url).startswith("http"):
            full_url = urljoin(main_url, url)
        else:
            full_url = url
        full_url = self._ensure_scheme(full_url)

        logger.debug(f"Processing url - {full_url}")

        path = urlparse(full_url).path.lower()
        doc_extensions = ['.pdf', '.docx', '.doc', '.xls', '.xlsx']
        img_extensions = ['.jpg', '.jpeg', '.png']

        if 'ebook' in full_url or 'download' in full_url or any(path.endswith(ext) for ext in doc_extensions):
            logger.info(f"Skipping document/download - {full_url}")
            return full_url, None, True

        if any(path.endswith(ext) for ext in img_extensions):
            logger.info(f"Skipping image - {full_url}")
            return full_url, None, True

        _data, _cleaned_data = self.get_data_from_url_using_soup(full_url)

        if _data:
            scraped_data = {
                'url': full_url,
                'heading': full_url.split('/')[-1],
                'data': _data,
                'cleanedData': _cleaned_data
            }
            return full_url, scraped_data, False

        return full_url, None, False

    def scrape_entire_website_with_main_url(self, main_url, filename, max_workers=10):
        import queue
        import threading

        urls_queue = queue.Queue()
        processed_urls = set()
        data = []
        pdf_urls = []
        data_lock = threading.Lock()

        def worker():
            while True:
                url = urls_queue.get()
                if url is None:
                    break  # Sentinel

                try:
                    full_url, scraped_data, is_skipped = self._process_url(url, main_url=main_url)

                    if is_skipped:
                        with data_lock:
                            pdf_urls.append(full_url)
                        continue

                    if scraped_data:
                        with data_lock:
                            data.append(scraped_data)

                    if not is_skipped:
                        fresh_urls = self.get_list_of_urls(full_url)
                        if fresh_urls:
                            for new_url in fresh_urls:
                                with data_lock:
                                    if new_url not in processed_urls:
                                        processed_urls.add(new_url)
                                        urls_queue.put(new_url)
                except Exception as e:
                    logger.error(f"Error in worker processing {url}: {e}")
                finally:
                    urls_queue.task_done()

        threads = []
        for i in range(max_workers):
            thread = threading.Thread(target=worker, name=f"Worker-{i+1}")
            thread.start()
            threads.append(thread)

        initial_urls = self.get_list_of_urls(main_url)
        if initial_urls:
            with data_lock:
                for url in initial_urls:
                    if url not in processed_urls:
                        processed_urls.add(url)
                        urls_queue.put(url)
        else:
            logger.error('Failed to retrieve initial URLs')
            # Need to stop workers if we return early
            for _ in range(max_workers):
                urls_queue.put(None)
            for t in threads:
                t.join()
            return

        urls_queue.join()

        # Stop workers
        for _ in range(max_workers):
            urls_queue.put(None)
        for t in threads:
            t.join()

        return self._save_scrape_results(filename, data, pdf_urls)

    @staticmethod
    def clean_text_from_json(filename: str):
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            for item in data:
                item['data'] = re.sub(r'\s+', ' ', item['data'].strip())
            with open('data2.json', 'w') as f:
                json.dump(data, f, indent=4)
            logger.debug('Cleaned text saved to data2.json')
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error processing file {filename}: {e}")

    def get_urls_from_sitemap(self, sitemap_url: str, recursive: bool = True, max_depth: int = 3) -> set[str]:

        seen_sitemaps: set[str] = set()
        found_urls: set[str] = set()

        def _fetch_bytes(url: str) -> bytes | None:
            resp = self.request(url)
            if resp is None:
                return None
            # Handle gzipped sitemaps by extension or by content-type
            ctype = (resp.headers.get("Content-Type") or "").lower()
            is_gzip = url.lower().endswith(".gz") or "application/gzip" in ctype or "gzip" in ctype
            try:
                raw = resp.content
                if is_gzip:
                    with gzip.GzipFile(fileobj=io.BytesIO(raw)) as gz:
                        return gz.read()
                return raw
            except Exception as e:
                logger.error(f"Failed to read sitemap bytes from {url}: {e}")
                return None

        def _iter_locs(root: ET.Element):
            # Namespace-agnostic: match any tag ending with 'loc'
            for el in root.iter():
                if isinstance(el.tag, str) and el.tag.endswith("loc") and el.text:
                    yield el.text.strip()

        def _parse_and_collect(url: str, depth: int):
            if url in seen_sitemaps:
                return
            seen_sitemaps.add(url)

            data = _fetch_bytes(url)
            if not data:
                logger.warning(f"Empty sitemap response from {url}")
                return

            try:
                root = ET.fromstring(data)
            except ET.ParseError as e:
                logger.error(f"XML parse error for {url}: {e}")
                return

            root_tag = root.tag.lower()
            # Normalize tag by stripping namespace, e.g. '{ns}urlset' -> 'urlset'
            if "}" in root_tag:
                root_tag = root_tag.split("}", 1)[1]

            if root_tag == "urlset":
                for loc in _iter_locs(root):
                    loc = loc.strip()
                    abs_url = urljoin(url, loc)  # <-- use 'url' (current sitemap), not sitemap_url
                    abs_url = self._ensure_scheme(abs_url)  # ensure https://
                    found_urls.add(abs_url)

            elif root_tag == "sitemapindex":
                for loc in _iter_locs(root):
                    child = urljoin(url, loc)  # <-- use 'url' here too
                    child = self._ensure_scheme(child)
                    if recursive and depth < max_depth:
                        _parse_and_collect(child, depth + 1)
                    else:
                        logger.debug(f"Skipping deeper recursion for child sitemap: {child}")
            else:
                # Some sites return HTML or non-sitemap content at the URL
                logger.warning(f"Unrecognized sitemap root tag '{root_tag}' for {url}")

        _parse_and_collect(sitemap_url, depth=0)
        logger.debug(f"Collected {len(found_urls)} URLs from sitemap(s)")
        return found_urls

    async def scrape_entire_website_with_main_url_async(self, main_url: str, filename: str, max_workers: int = 10):
        queue = asyncio.Queue()
        processed_urls = set()

        results = []
        pdf_urls = []
        errored_urls = []

        # Helper to run blocking I/O in a thread to not block the event loop
        async def run_in_thread(func, *args):
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, func, *args)

        # 1. First, process the main_url itself.
        logger.info(f"Scraping the main entry point: {main_url}")
        main_content, main_cleaned_content = await run_in_thread(self.get_data_from_url_using_soup, main_url)
        
        if main_content:
            results.append({'url': main_url, 'data': main_content, 'cleanedData': main_cleaned_content})
            processed_urls.add(main_url)
        else:
            logger.error(f"Failed to scrape content from the main URL: {main_url}")
            errored_urls.append(main_url)
            return self._save_scrape_results(filename, results, pdf_urls, errored_urls)

        # 2. Now, look for more URLs on the main page to seed the queue.
        initial_urls = await run_in_thread(self.get_list_of_urls, main_url)
        if initial_urls:
            for url in initial_urls:
                if url not in processed_urls:
                    processed_urls.add(url)
                    await queue.put(url)
        else:
            logger.info("No further URLs found on the main page. Treating as a single page.")

        async def worker(name: str):
            while True:
                try:
                    # Wait for a URL from the queue, with a timeout to allow graceful exit
                    current_url = await asyncio.wait_for(queue.get(), timeout=5.0)
                    if current_url is None:
                        queue.task_done()
                        break
                except asyncio.TimeoutError:
                    # If the queue is empty and other workers are also waiting, we might be done.
                    if queue.empty():
                        break
                    continue

                if not str(current_url).startswith("http"):
                    full_url = urljoin(main_url, current_url)
                else:
                    full_url = current_url

                logger.debug(f"[{name}] Processing: {full_url}")

                # Skip certain file types
                if any(ext in full_url for ext in ['.pdf', '.ebook', '.download', ".docx", ".doc", ".xls", ".xlsx"]):
                    logger.info(f"[{name}] Skipping PDF/download: {full_url}")
                    pdf_urls.append(full_url)
                elif not any(ext in full_url for ext in ['.jpg', '.png', '.jpeg']):
                    # Scrape data and find new URLs concurrently
                    data_task = run_in_thread(self.get_data_from_url_using_soup, full_url)
                    urls_task = run_in_thread(self.get_list_of_urls, full_url)
                    _data, new_urls = await asyncio.gather(data_task, urls_task)

                    got_data = _data and _data[0] is not None
                    got_urls = new_urls is not None

                    if not got_data and not got_urls:
                        errored_urls.append(full_url)

                    if got_data:
                        results.append({'url': full_url, 'data': _data[0], 'cleanedData': _data[1]})

                    if got_urls:
                        for url in new_urls:
                            if url not in processed_urls:
                                processed_urls.add(url)
                                await queue.put(url)
                queue.task_done()

        # Create and start worker tasks
        tasks = [asyncio.create_task(worker(f"Worker-{i+1}")) for i in range(max_workers)]
        await queue.join() # Wait for all items in the queue to be processed

        for _ in range(max_workers):
            await queue.put(None)

        await asyncio.gather(*tasks) # Wait for worker tasks to finish

        # Save results
        return self._save_scrape_results(filename, results, pdf_urls, errored_urls)

    @staticmethod
    def _save_scrape_results(filename: str, data: list, pdf_urls: list, errored_urls: list = None) -> str:
        """Saves scraped data, PDF URLs, and errored URLs to JSON files inside a new directory in the documents directory."""
        # Get the project's documents directory
        base_documents_dir = Path(__file__).resolve().parent.parent.parent.parent / 'documents'
        # Create a new directory for the current crawl
        crawl_dir = base_documents_dir / filename
        crawl_dir.mkdir(exist_ok=True)

        # Define file paths within the new directory
        main_data_path = crawl_dir / 'scraped_data.json'
        pdf_data_path = crawl_dir / 'pdf_urls.json'
        errored_data_path = crawl_dir / 'errored_urls.json'

        # Save main data
        logger.debug(f'Saving main data to {main_data_path}')
        with open(main_data_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        # Save PDF URLs
        if pdf_urls:
            logger.debug(f'Saving PDF URLs to {pdf_data_path}')
            with open(pdf_data_path, 'w', encoding='utf-8') as f:
                json.dump(pdf_urls, f, indent=4, ensure_ascii=False)

        # Save Errored URLs
        if errored_urls:
            logger.debug(f'Saving errored URLs to {errored_data_path}')
            with open(errored_data_path, 'w', encoding='utf-8') as f:
                json.dump(errored_urls, f, indent=4, ensure_ascii=False)
        
        return str(crawl_dir.resolve())

    @staticmethod
    def _ensure_scheme(u:str, default: str = "https://") -> str:
        _SCHEME_RE = re.compile(r'^https?://', re.I)
        u = u.strip()
        if not _SCHEME_RE.match(u):
            return default + u.lstrip("/")
        return u

    def scrape_using_sitemap_urls(self, main_list_of_urls, filename, max_workers=10):
        import queue
        import threading

        urls_queue = queue.Queue()
        data = []
        pdf_urls = []
        data_lock = threading.Lock()

        for url in main_list_of_urls:
            urls_queue.put(url)

        def worker():
            while True:
                url = urls_queue.get()
                if url is None:
                    break

                try:
                    full_url, scraped_data, is_skipped = self._process_url(url)

                    if is_skipped:
                        with data_lock:
                            pdf_urls.append(full_url)
                        continue

                    if scraped_data:
                        with data_lock:
                            data.append(scraped_data)
                except Exception as e:
                    logger.error(f"Error processing url {url}: {e}")
                finally:
                    urls_queue.task_done()

        threads = []
        for i in range(max_workers):
            thread = threading.Thread(target=worker, name=f"Worker-{i + 1}")
            thread.start()
            threads.append(thread)

        urls_queue.join()

        # Stop workers
        for _ in range(max_workers):
            urls_queue.put(None)
        for t in threads:
            t.join()

        return self._save_scrape_results(filename, data, pdf_urls)

if __name__ == '__main__':
    requs = RequestHelper()
    res=requs.request("https://www.quintelaepenalva.pt/?")
    print(res.text)