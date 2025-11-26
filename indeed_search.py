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
    options.add_argument("--headless") # Run in headless mode
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def search_indeed(query, location="madrid"):
    driver = get_driver()
    offers = []
    
    try:
        # Format query and location for URL
        formatted_query = query.replace(" ", "+")
        formatted_location = location.replace(" ", "+")
        
        # Construct the search URL
        if formatted_query:
            url = f"https://es.indeed.com/jobs?q={formatted_query}&l={formatted_location}"
        else:
            url = f"https://es.indeed.com/jobs?l={formatted_location}"
        
        driver.get(url)
        time.sleep(3) # Wait for page to load
        
        # Indeed often has popups or captchas. Headless might be detected.
        # We'll try to parse the page content.
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Indeed structure changes frequently. This is a best-effort selector.
        # Look for job cards. Common classes: 'job_seen_beacon', 'result', 'job_seen_beacon'
        job_cards = soup.find_all('div', class_='job_seen_beacon')
        
        if not job_cards:
            # Fallback for different layout
            job_cards = soup.find_all('td', class_='resultContent')

        for card in job_cards:
            try:
                title_elem = card.find('h2', class_='jobTitle')
                title = title_elem.get_text(strip=True) if title_elem else "N/A"
                
                company_elem = card.find('span', class_='companyName')
                if not company_elem:
                     company_elem = card.find('span', attrs={'data-testid': 'company-name'})
                company = company_elem.get_text(strip=True) if company_elem else "N/A"
                
                location_elem = card.find('div', class_='companyLocation')
                if not location_elem:
                    location_elem = card.find('div', attrs={'data-testid': 'text-location'})
                loc = location_elem.get_text(strip=True) if location_elem else "N/A"
                
                # Salary
                salary = "N/A"
                salary_elem = card.find('div', class_='salary-snippet-container')
                if not salary_elem:
                     salary_elem = card.find('div', attrs={'data-testid': 'attribute_snippet_testid'})
                if not salary_elem:
                    # Check metadata div
                    metadata = card.find('div', class_='metadata')
                    if metadata:
                        text = metadata.get_text(strip=True)
                        if "€" in text or "$" in text:
                            salary = text
                
                if salary_elem:
                    salary = salary_elem.get_text(strip=True)

                # Fallback: Search entire card text
                if salary == "N/A":
                    card_text = card.get_text(separator=' ', strip=True)
                    if "€" in card_text:
                         import re
                         match = re.search(r'([\d\.]+\s*[-–]?\s*[\d\.]*)\s*€', card_text)
                         if match:
                             salary = match.group(0)

                link_elem = card.find('a', href=True)
                # Sometimes the link is on the title
                if title_elem and title_elem.find('a'):
                    link_elem = title_elem.find('a')
                
                link = "https://es.indeed.com" + link_elem['href'] if link_elem else "N/A"
                
                offer = {
                    "title": title,
                    "company": company,
                    "location": loc,
                    "salary": salary,
                    "link": link,
                    "source": "Indeed"
                }
                offers.append(offer)
            except Exception as e:
                continue

    except Exception as e:
        print(f"Error searching Indeed: {e}")
    finally:
        driver.quit()
        
    return offers

if __name__ == "__main__":
    results = search_indeed("programador python", "madrid")
    print(json.dumps(results, indent=2, ensure_ascii=False))
