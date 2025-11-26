from bs4 import BeautifulSoup
import json

def test_parsing():
    try:
        with open('debug_infojobs_manual.html', 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        offers = []

        # Try to find job cards with the new structure (divs instead of lis)
        job_items = soup.find_all('div', class_='sui-AtomCard')
        
        if not job_items:
             # Fallback to finding by title class if card container is elusive
             print("Standard card container not found, trying to find by title class...")
             titles = soup.find_all('h2', class_='ij-OfferCardContent-description-title')
             job_items = [t.find_parent('div', class_='sui-AtomCard') for t in titles if t.find_parent('div', class_='sui-AtomCard')]

        print(f"Found {len(job_items)} potential job cards.")

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
                
                # Location and Date
                loc = "N/A"
                date_posted = "N/A"
                details_list = card.find('ul', class_='ij-OfferCardContent-description-list')
                if details_list:
                    items = details_list.find_all('li')
                    for item in items:
                        text = item.get_text(strip=True)
                        # Heuristic: Location usually doesn't have "hace" (date) or contract types
                        if "hace" in text.lower():
                            date_posted = text
                        elif "presencial" in text.lower() or "híbrido" in text.lower() or "teletrabajo" in text.lower():
                            pass
                        elif len(text) < 30 and "contrato" not in text.lower() and "jornada" not in text.lower():
                             if loc == "N/A":
                                 loc = text
                
                offer = {
                    "title": title,
                    "company": company,
                    "location": loc,
                    "link": link,
                    "source": "InfoJobs"
                }
                offers.append(offer)
            except Exception as e:
                print(f"Error parsing card: {e}")
                continue
        
        print(json.dumps(offers, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_parsing()
