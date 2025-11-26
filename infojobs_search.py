import time
import json
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_driver():
    options = Options()
    # Important: Do NOT use headless mode if we want the user to solve the captcha manually
    options.add_argument("--start-maximized") 
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    
    # Add a realistic user agent
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def search_infojobs(query, location="madrid", status_callback=None):
    driver = get_driver()
    offers = []
    
    if status_callback:
        status_callback("driver_ready", driver)
    
    try:
        # Construct the search URL
        # InfoJobs search URL format
        if query:
            combined_query = f"{query} {location}"
        else:
            combined_query = location
            
        formatted_query = combined_query.replace(" ", "%20")
        url = f"https://www.infojobs.net/jobsearch/search-results/list.xhtml?keyword={formatted_query}"
        
        logging.info(f"Navigating to: {url}")
        driver.get(url)
        
        # MANUAL INTERVENTION BLOCK
        print("\n" + "="*50)
        print("⚠️  MANUAL ACTION REQUIRED ⚠️")
        print("Please check the opened Chrome window.")
        print("1. If you see a Cookie banner, accept it.")
        print("2. If you see a CAPTCHA or 'Robot Check', solve it.")
        print("3. Ensure the job list is visible.")
        print("4. DO NOT CLOSE THE BROWSER WINDOW.")
        print("5. The script will automatically proceed when it detects job cards or after 60 seconds.")
        print("="*50 + "\n")
        
        # Wait for user to solve captcha (poll for job cards)
        max_wait = 60
        start_time = time.time()
        while time.time() - start_time < max_wait:
            if status_callback:
                status_callback("waiting_input", driver)
                
            try:
                # Check if we have job cards
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                if soup.find_all('div', class_='sui-AtomCard') or soup.find_all('li', class_='ij-OfferCard'):
                    logging.info("Job cards detected! Proceeding...")
                    break
            except:
                pass
            time.sleep(2)
        
        if status_callback:
            status_callback("scraping", driver)
            
        logging.info("Resuming scraping...")
        
        # Save page source for debugging
        with open("debug_infojobs_manual.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        
        # Scroll down to load more results (InfoJobs uses infinite scroll or pagination)
        # The user's script scrolled to bottom. Let's do a few scrolls.
        last_height = driver.execute_script("return document.body.scrollHeight")
        for _ in range(5): # Scroll a few times
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            
        # Parse content
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Selectors based on user's script and standard InfoJobs structure
        # User's script used: ul.ij-ComponentList and a.ij-OfferCardContent-description-title-link
        
        # Try to find job cards with the new structure (divs instead of lis)
        job_items = soup.find_all('div', class_='sui-AtomCard')
        
        if not job_items:
             # Fallback to finding by title class if card container is elusive
             logging.info("Standard card container not found, trying to find by title class...")
             titles = soup.find_all('h2', class_='ij-OfferCardContent-description-title')
             job_items = [t.find_parent('div', class_='sui-AtomCard') for t in titles if t.find_parent('div', class_='sui-AtomCard')]

        logging.info(f"Found {len(job_items)} potential job cards.")

        for card in job_items:
            try:
                # Title
                title_elem = card.find('a', class_='ij-OfferCardContent-description-title-link')
                if not title_elem:
                    # Try h2
                    title_elem = card.find('h2', class_='ij-OfferCardContent-description-title')
                
                title = title_elem.get_text(strip=True) if title_elem else "N/A"
                
                # Link
                link = "N/A"
                if title_elem and title_elem.name == 'a':
                    link = title_elem['href']
                elif title_elem and title_elem.find('a'):
                    link = title_elem.find('a')['href']
                
                if link != "N/A":
                    if link.startswith("//"):
                        link = "https:" + link
                    elif link.startswith("/"):
                        link = "https://www.infojobs.net" + link
                
                # Company
                company_elem = card.find('h3', class_='ij-OfferCardContent-description-subtitle')
                company = company_elem.get_text(strip=True) if company_elem else "N/A"
                
                # Location, Date, and Salary
                loc = "N/A"
                date_posted = "N/A"
                salary = "N/A"
                
                details_list = card.find('ul', class_='ij-OfferCardContent-description-list')
                if details_list:
                    items = details_list.find_all('li')
                    for item in items:
                        text = item.get_text(strip=True)
                        # Check for specific salary class
                        if item.find('span', class_='ij-OfferCardContent-description-salary'):
                             salary = text
                        elif "€" in text or "bruto" in text.lower() or "s/a" in text.lower() or "salario" in text.lower():
                             if "no disponible" not in text.lower():
                                 salary = text
                        elif "hace" in text.lower():
                            date_posted = text
                        elif "presencial" in text.lower() or "híbrido" in text.lower() or "teletrabajo" in text.lower():
                            pass
                        elif len(text) < 30 and "contrato" not in text.lower() and "jornada" not in text.lower():
                             if loc == "N/A":
                                 loc = text
                
                # Fallback: Search entire card text for salary if not found
                if salary == "N/A":
                    card_text = card.get_text(separator=' ', strip=True)
                    if "€" in card_text:
                        # Simple heuristic: find the part with €
                        import re
                        match = re.search(r'([\d\.]+\s*[-–]?\s*[\d\.]*)\s*€', card_text)
                        if match:
                            salary = match.group(0) + " (Est.)"

                offer = {
                    "title": title,
                    "company": company,
                    "location": loc,
                    "salary": salary,
                    "link": link,
                    "source": "InfoJobs"
                }
                offers.append(offer)
            except Exception as e:
                continue

    except Exception as e:
        logging.error(f"Error searching InfoJobs: {e}")
    finally:
        # driver.quit() # Keep driver open? No, script ends.
        driver.quit()
        
    return offers

if __name__ == "__main__":
    results = search_infojobs("programador python", "madrid")
    print(json.dumps(results, indent=2, ensure_ascii=False))

