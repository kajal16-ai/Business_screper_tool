# scraper/google_maps_scraper.py

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests
import time
import re

def find_instagram_handle(business_name):
    query = f"{business_name} site:instagram.com"
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        url = f"https://www.bing.com/search?q={query}"
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        for item in soup.select('li.b_algo h2 a'):
            href = item.get('href')
            if 'instagram.com' in href:
                match = re.search(r'instagram\.com/([^/?#&]+)', href)
                if match:
                    handle = match.group(1)
                    if re.match(r'^[A-Za-z0-9_.]+$', handle):
                        return f"@{handle}"
        return "-"
    except Exception as e:
        print(f"[ERROR] Instagram search failed for '{business_name}': {e}")
        return "-"

def find_instagram_from_website(website_url):
    try:
        res = requests.get(website_url, timeout=10)
        if res.status_code == 200:
            match = re.search(r'https://(www\.)?instagram\.com/[A-Za-z0-9_.]+', res.text)
            if match:
                return match.group(0)
    except:
        pass
    return "-"

def find_linkedin_url(business_name, city):
    query = f"{business_name} {city} site:linkedin.com"
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        url = f"https://www.bing.com/search?q={query}"
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        for item in soup.select('li.b_algo h2 a'):
            href = item.get('href')
            if 'linkedin.com/company' in href or 'linkedin.com/in' in href:
                return href
        return "-"
    except Exception as e:
        print(f"[ERROR] LinkedIn search failed for '{business_name}': {e}")
        return "-"
    
def find_linkedin_from_website(website_url):
    import requests, re
    try:
        res = requests.get(website_url, timeout=10)
        if res.status_code == 200:
            match = re.search(r'https://(www\.)?linkedin\.com/[^"\']+', res.text)
            if match:
                return match.group(0)
    except:
        pass
    return "-"


def scrape_google_maps(city, keyword):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    listings = []
    seen_names = set()
    priority_list = []
    fallback_list = []

    try:
        search_url = f"https://www.google.com/maps/search/{keyword}+in+{city}"
        driver.get(search_url)

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.Nv2PK'))
        )

        scrollable_div = driver.find_element(By.XPATH, '//div[@role="feed"]')
        for _ in range(5):
            driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', scrollable_div)
            time.sleep(2)

        cards = driver.find_elements(By.CSS_SELECTOR, 'div.Nv2PK')
        print(f"[INFO] Found {len(cards)} listings")

        for index, card in enumerate(cards):
            if len(priority_list) >= 10:
                break

            try:
                driver.execute_script("arguments[0].scrollIntoView();", card)
                time.sleep(1)
                card.click()
                time.sleep(3)

                name = driver.find_element(By.XPATH, '//h1[contains(@class,"DUwDvf")]').text
                if name in seen_names:
                    continue
                seen_names.add(name)

                try:
                    phone = driver.find_element(By.XPATH, '//button[contains(@data-item-id, "phone")]').text.strip()
                except:
                    phone = "-"

                try:
                    website = driver.find_element(By.XPATH, '//a[contains(@data-tooltip, "Open website")]').get_attribute('href')
                except:
                    website = "-"

                instagram = find_instagram_handle(name)
                time.sleep(2)
                if instagram == "-" and website != "-":
                    instagram = find_instagram_from_website(website)
                time.sleep(2)

                linkedin = find_linkedin_url(name, city)
                time.sleep(2)

                data = {
                    'name': name,
                    'phone': phone,
                    'website': website,
                    'instagram': instagram,
                    'linkedin': linkedin
                }

                if instagram != "-" and linkedin != "-":
                    priority_list.append(data)
                else:
                    fallback_list.append(data)

                print(f"[OK] {index+1}. {name} | {phone} | {website} | {instagram} | {linkedin}")

            except Exception as e:
                print(f"[ERROR] Card {index+1} failed: {e}")
                continue

    except Exception as e:
        print(f"[FATAL] Google Maps page failed: {e}")
    finally:
        driver.quit()

    listings = priority_list[:10]
    if len(listings) < 10:
        listings.extend(fallback_list[:(10 - len(listings))])

    return listings