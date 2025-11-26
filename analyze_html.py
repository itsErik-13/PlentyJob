from bs4 import BeautifulSoup

try:
    with open('debug_infojobs_manual.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # Find all h2 elements
    h2s = soup.find_all('h2')
    print(f"Found {len(h2s)} h2 elements.")
    
    for h2 in h2s:
        text = h2.get_text(strip=True)
        if "Python" in text or "Developer" in text:
            print(f"\n--- Job Found: {text} ---")
            print(f"H2 Classes: {h2.get('class')}")
            
            # Parent (Link or Card)
            parent = h2.parent
            print(f"Parent Tag: {parent.name}")
            print(f"Parent Classes: {parent.get('class')}")
            
            # Grandparent (Card?)
            grandparent = parent.parent
            print(f"Grandparent Tag: {grandparent.name}")
            print(f"Grandparent Classes: {grandparent.get('class')}")
            
            # Great-grandparent (List Item?)
            greatgrandparent = grandparent.parent
            print(f"Great-grandparent Tag: {greatgrandparent.name}")
            print(f"Great-grandparent Classes: {greatgrandparent.get('class')}")
            
            # Break after finding a few to avoid spam
            if "Python" in text:
                break
                
except Exception as e:
    print(f"Error: {e}")
