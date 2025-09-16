import json
import queue
import re
from pathlib import Path
from time import sleep
from urllib.parse import urlsplit, urlunsplit, quote, unquote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoAlertPresentException, InvalidArgumentException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from libs.constants import SCROLL_TO_END_SCRIPT, SCROLL_TO_TOP_SCRIPT
from libs.logger import color_string, get_logger
from libs.logger.constants import Colors

# remove control chars and common invisible Unicode marks
_INVISIBLE_RE = re.compile(r'[\x00-\x20\u200B-\u200F\u202A-\u202E]+')
_SCHEME_RE = re.compile(r'^https?://', re.I)


class SeleniumHelper:

    def __init__(
        self,
    ):
        self.driver = None
        self.proxies = None
        self.logger, self.listener = get_logger("SeleniumHelper")
        self.listener.start()

    def get_driver(
        self,
        use_incognito: bool = True,
        headless: bool = False,
        headers: dict = None,
        page_load_strategy: str = "normal",
        javascript_enabled: bool = True,
        chrome_profile_path=None
    ):
        chrome_options = Options()

        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--allow-insecure-localhost')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        chrome_options.page_load_strategy = page_load_strategy
        chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

        if chrome_profile_path:
            chrome_options.add_argument(
                f'--user-data-dir={chrome_profile_path}'
            )
            chrome_options.add_argument('--ignore-certificate-errors')

        if use_incognito:
            chrome_options.add_argument('--incognito')
        if headless:
            chrome_options.add_argument("--headless")

        if not javascript_enabled:
            prefs = {"profile.managed_default_content_settings.javascript": 2}
            chrome_options.add_experimental_option("prefs", prefs)

        chrome_options.add_argument(
            "--disable-blink-features=AutomationControlled"
        )
        _driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        if headers:
            def interceptor(request):
                for key, value in headers.items():
                    request.headers[key] = value

            _driver.request_interceptor = interceptor
        self.logger.info('Selenium driver started')
        # For headless stability
        _driver.set_page_load_timeout(60)
        _driver.set_script_timeout(60)
        self.driver = _driver
        return _driver

    @staticmethod
    def _sanitize_for_nav(u: str) -> str:
        if not isinstance(u, str):
            u = str(u)
        u = _INVISIBLE_RE.sub('', u.strip())

        if not _SCHEME_RE.match(u):
            u = "https://" + u.lstrip("/")

        parts = urlsplit(u)
        if not parts.netloc:
            raise ValueError(f"Bad URL (no host): {repr(u)}")

        # percent-encode path/query/fragment safely
        path = quote(unquote(parts.path), safe='/:@-._~!$&\'()*+,;=')
        query = quote(unquote(parts.query), safe='&=:@-._~!$\'()*+,;/?')
        frag = quote(unquote(parts.fragment), safe=':@-._~!$&\'()*+,;=/?: ')

        return urlunsplit((parts.scheme.lower(), parts.netloc, path, query, frag))

    def get_page_source(self, url: str, timeout: int = 10):
        raw = url
        safe_url = self._sanitize_for_nav(url)
        self.logger.debug(f"Navigating | raw={repr(raw)} | sanitized={safe_url}")

        try:
            self.driver.get(safe_url)
        except InvalidArgumentException:
            # Log and rethrow so you can see the exact difference
            self.logger.error(f"driver.get() rejected URL | raw={repr(raw)} | sanitized={safe_url}")
            raise

        try:
            WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        except Exception as e:
            self.logger.warning(f"Timeout waiting for page to load: {e}")

        html = self.driver.page_source
        self.logger.debug(f'Page source retrieved for {safe_url}')
        soup = BeautifulSoup(html, 'html.parser')
        soup_text = soup.get_text()
        text = soup_text.strip().replace('\n', '').replace('\t', '').replace('\r', '').replace('\v', '').replace('\f',
                                                                                                                 '').replace(
            '\xa0', '')
        cleaned_text = re.sub(r'\s+', ' ', soup_text.strip())
        return text, cleaned_text

    @staticmethod
    def highlight_element(element):
        driver = element.parent

        def apply_style(s):
            driver.execute_script("arguments[0].setAttribute('style', arguments[1]);",
                                  element, s)

        original_style = element.get_attribute('style')
        apply_style("background: yellow; border: 2px solid red;")
        sleep(.3)
        apply_style(original_style)

    def get_alert_element(self):
        try:
            alert = self.driver.switch_to.alert
            return alert
        except NoAlertPresentException:
            self.logger.debug("Checked for alert, No alert at the moment.")
            return None

    @staticmethod
    def clear_input_field(input_field):
        input_field.clear()
        sleep(1)
        input_field.send_keys(Keys.CONTROL + "a")
        input_field.send_keys(Keys.BACKSPACE)
        sleep(1)

    def is_site_up(self, url: str, timeout: int = 10) -> bool:
        try:
            resp = requests.get(
                url=url,
                timeout=timeout,
                verify=False
            )
            return resp.status_code == 200
        except Exception as error:
            self.logger.error(f'Error while requesting {url} -> {error}.')
            return False

    def load_page(
        self,
        url: str,
        page_name: str = "Page",
        check_site_status: bool = False,
        timeout: int = 10
    ) -> None:
        try:
            if check_site_status and not self.is_site_up(url):
                raise RuntimeError(
                    color_string(
                        f"{page_name} appears to be down.", Colors.BRIGHT_RED
                    )
                )

            self.driver.get(url=url)
            WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            self.logger.info(f"{page_name} loaded successfully.")
        except Exception as e:
            self.logger.error(f"Error loading page {page_name}: {e}")
            raise e

    def load_whole_page(self, sleep_time: float = 1):
        sleep(sleep_time)
        self.driver.execute_script(SCROLL_TO_END_SCRIPT)
        sleep(sleep_time)
        self.driver.execute_script(SCROLL_TO_END_SCRIPT)
        sleep(sleep_time)
        self.driver.execute_script(SCROLL_TO_TOP_SCRIPT)


    def close_driver(self, sleep_time=1):
        sleep(sleep_time)
        self.driver.close()
        self.logger.info('Driver closed successfully.')

    def quit_driver(self, sleep_time=1):
        sleep(sleep_time)
        self.driver.quit()
        self.logger.info('Driver quit successfully.')

    def _save_scrape_results(self, filename: str, data: list, pdf_urls: list, errored_urls: list = None) -> str:
        base_documents_dir = Path(__file__).resolve().parent.parent.parent.parent / 'documents'
        crawl_dir = base_documents_dir / filename
        crawl_dir.mkdir(exist_ok=True)

        main_data_path = crawl_dir / 'scraped_data.json'
        pdf_data_path = crawl_dir / 'pdf_urls.json'
        errored_data_path = crawl_dir / 'errored_urls.json'
        self.logger.debug(f'Saving main data to {main_data_path}')
        with open(main_data_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        if pdf_urls:
            self.logger.debug(f'Saving PDF URLs to {pdf_data_path}')
            with open(pdf_data_path, 'w', encoding='utf-8') as f:
                json.dump(pdf_urls, f, indent=4, ensure_ascii=False)

        if errored_urls:
            self.logger.debug(f'Saving errored URLs to {errored_data_path}')
            with open(errored_data_path, 'w', encoding='utf-8') as f:
                json.dump(errored_urls, f, indent=4, ensure_ascii=False)

        return str(crawl_dir.resolve())

    def scrape_entire_website_with_selenium(self, main_url, filename):
        self.logger.info(f"Starting Selenium crawl for {main_url}")

        urls_to_visit = queue.Queue()
        urls_to_visit.put(main_url)

        processed_urls = {main_url}
        data = []
        pdf_urls = []
        errored_urls = []

        self.get_driver(headless=True)

        while not urls_to_visit.empty():
            url = urls_to_visit.get()

            path = urlparse(url).path.lower()
            doc_extensions = ['.pdf', '.docx', '.doc', '.xls', '.xlsx']
            img_extensions = ['.jpg', '.jpeg', '.png']

            if any(path.endswith(ext) for ext in doc_extensions):
                self.logger.info(f"Skipping document link: {url}")
                pdf_urls.append(url)
                continue
            if any(path.endswith(ext) for ext in img_extensions):
                self.logger.info(f"Skipping image link: {url}")
                continue

            try:
                self.logger.debug(f"Navigating to {url} with Selenium")
                safe_url = self._sanitize_for_nav(url)
                self.driver.get(safe_url)
                WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

                html = self.driver.page_source
                soup = BeautifulSoup(html, 'html.parser')

                soup_text = soup.get_text()
                cleaned_text = re.sub(r'\s+', ' ', soup_text.strip())

                if cleaned_text:
                    data.append({
                        'url': url,
                        'heading': soup.title.string if soup.title else url.split('/')[-1],
                        'data': soup_text,
                        'cleanedData': cleaned_text
                    })

                base_netloc = urlparse(url).netloc
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if href and not href.startswith('mailto:') and not href.startswith('tel:'):
                        abs_url = urljoin(url, href)
                        parsed_abs = urlparse(abs_url)

                        if parsed_abs.scheme in ['http', 'https'] and parsed_abs.netloc == base_netloc:
                            clean_url = urlunsplit((parsed_abs.scheme, parsed_abs.netloc, parsed_abs.path, '', ''))
                            if clean_url not in processed_urls:
                                processed_urls.add(clean_url)
                                urls_to_visit.put(clean_url)

            except Exception as e:
                self.logger.error(f"Error scraping {url} with Selenium: {e}")
                errored_urls.append(url)

        self.quit_driver()

        return self._save_scrape_results(filename, data, pdf_urls, errored_urls)