import argparse
import json
import concurrent.futures
from infojobs_search import search_infojobs
from indeed_search import search_indeed
from linkedin_search import search_linkedin

def search_all(query, location):
    results = []
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_infojobs = executor.submit(search_infojobs, query, location)
        future_indeed = executor.submit(search_indeed, query, location)
        future_linkedin = executor.submit(search_linkedin, query, location)
        
        try:
            results.extend(future_infojobs.result())
        except Exception as e:
            print(f"InfoJobs search failed: {e}")
            
        try:
            results.extend(future_indeed.result())
        except Exception as e:
            print(f"Indeed search failed: {e}")
            
        try:
            results.extend(future_linkedin.result())
        except Exception as e:
            print(f"LinkedIn search failed: {e}")
            
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search for jobs on InfoJobs, Indeed, and LinkedIn")
    parser.add_argument("query", help="Job title or keywords")
    parser.add_argument("location", help="Location (city or province)")
    
    args = parser.parse_args()
    
    print(f"Searching for '{args.query}' in '{args.location}'...")
    all_offers = search_all(args.query, args.location)
    
    print(json.dumps(all_offers, indent=2, ensure_ascii=False))
    print(f"\nFound {len(all_offers)} offers.")
