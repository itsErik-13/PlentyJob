import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def search_linkedin(query, location="madrid"):
    driver = get_driver()
    offers = []
    
    try:
        # LinkedIn public jobs url
        formatted_query = query.replace(" ", "%20")
        formatted_location = location.replace(" ", "%20")
        # Construct the search URL
        if query:
            url = f"https://www.linkedin.com/jobs/search?keywords={formatted_query}&location={formatted_location}"
        else:
            url = f"https://www.linkedin.com/jobs/search?location={formatted_location}"
        
        driver.get(url)
        
        # Scroll down to load more jobs (LinkedIn lazy loads)
        last_height = driver.execute_script("return document.body.scrollHeight")
        for _ in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # LinkedIn public job card classes
        job_cards = soup.find_all('div', class_='base-card')
        
        if not job_cards:
             job_cards = soup.find_all('li', class_='result-card')

        for card in job_cards:
            try:
                title_elem = card.find('h3', class_='base-search-card__title')
                title = title_elem.get_text(strip=True) if title_elem else "N/A"
                
                company_elem = card.find('h4', class_='base-search-card__subtitle')
                company = company_elem.get_text(strip=True) if company_elem else "N/A"
                
                location_elem = card.find('span', class_='job-search-card__location')
                loc = location_elem.get_text(strip=True) if location_elem else "N/A"
                
                # Salary (LinkedIn public search sometimes shows it)
                salary = "N/A"
                salary_elem = card.find('span', class_='job-search-card__salary-info')
                if salary_elem:
                    salary = salary_elem.get_text(strip=True).replace('\n', '').strip()
                else:
                    # Fallback: check metadata text for currency symbols
                    metadata = card.find('div', class_='base-card__metadata')
                    if metadata:
                        text = metadata.get_text(strip=True)
                        if "€" in text or "$" in text:
                            # Try to extract the salary part (simple heuristic)
                            parts = text.split('\n')
                            for part in parts:
                                if "€" in part or "$" in part:
                                    salary = part.strip()
                                    break
                
                # Fallback: Search entire card text
                if salary == "N/A":
                    card_text = card.get_text(separator=' ', strip=True)
                    if "€" in card_text:
                         import re
                         match = re.search(r'([\d\.]+\s*[-–]?\s*[\d\.]*)\s*€', card_text)
                         if match:
                             salary = match.group(0)

                link_elem = card.find('a', class_='base-card__full-link')
                link = link_elem['href'] if link_elem else "N/A"
                
                offer = {
                    "title": title,
                    "company": company,
                    "location": loc,
                    "salary": salary,
                    "link": link,
                    "source": "LinkedIn"
                }
                offers.append(offer)
            except Exception as e:
                continue

    except Exception as e:
        print(f"Error searching LinkedIn: {e}")
    finally:
        driver.quit()
        
    return offers

if __name__ == "__main__":
    results = search_linkedin("programador python", "madrid")
    print(json.dumps(results, indent=2, ensure_ascii=False))
