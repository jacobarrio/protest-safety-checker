#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time

def scrape_oversight_dashboard_selenium():
    """Scrape House Oversight Dashboard by paginating through results"""
    
    print("🔍 Scraping House Oversight Immigration Dashboard (Selenium)...")
    
    chrome_options = Options()
    chrome_options.binary_location = '/usr/bin/chromium-browser'
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    
    service = Service('/usr/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    url = "https://oversightdemocrats.house.gov/immigration-dashboard"
    
    print("  Loading page...")
    driver.get(url)
    
    # Wait for table
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table#incidentTable tbody tr"))
        )
        print("  ✅ Table loaded")
    except Exception as e:
        print(f"  ❌ Timeout: {e}")
        driver.quit()
        return None
    
    time.sleep(3)
    
    all_incidents = []
    page_num = 0
    
    while True:
        print(f"  Scraping page {page_num + 1}...")
        
        # Get current page HTML
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table', id='incidentTable')
        
        if not table:
            print("    No table found")
            break
        
        tbody = table.find('tbody')
        if not tbody:
            print("    No tbody found")
            break
        
        rows = tbody.find_all('tr')
        
        # Check if we hit the "No data available" row
        if len(rows) == 1:
            td = rows[0].find('td')
            if td and 'no data available' in td.text.lower():
                print("    Reached end (no more data)")
                break
        
        page_incidents = 0
        
        for row in rows:
            cols = row.find_all('td')
            
            if len(cols) < 4:
                continue
            
            # Check if first column has a link - indicates normal row
            first_col_has_link = cols[0].find('a') is not None
            
            if not first_col_has_link:
                # Bad row: Category, Unknown, Location, Title
                # Only 4 columns total
                category = cols[0].text.strip()
                date = cols[1].text.strip()  # Usually "Unknown"
                state = cols[2].text.strip()
                
                title_td = cols[3]
                title_link = title_td.find('a')
                if title_link:
                    title = title_link.text.strip()
                    source_url = title_link.get('href', '')
                else:
                    title = title_td.text.strip()
                    source_url = ''
            else:
                # Good row: Has link in col[0]
                title_td = cols[0]
                
                # Check if 4 or 5 columns
                if len(cols) == 5:
                    # Title, Title(dup), Date, Category, Location
                    date = cols[2].text.strip()
                    category = cols[3].text.strip()
                    state = cols[4].text.strip()
                elif len(cols) == 4:
                    # Title, Date, Category, Location (no dup)
                    date = cols[1].text.strip()
                    category = cols[2].text.strip()
                    state = cols[3].text.strip()
                else:
                    continue
                
                title_link = title_td.find('a')
                if title_link:
                    title = title_link.text.strip()
                    source_url = title_link.get('href', '')
                else:
                    title = title_td.text.strip()
                    source_url = ''
            
            incident = {
                'date': date,
                'location': state,
                'category': category,
                'title': title,
                'source_url': source_url
            }
            
            all_incidents.append(incident)
            page_incidents += 1
        
        print(f"    Found {page_incidents} incidents")
        
        if page_incidents == 0:
            break
        
        # Try to click "Next" button
        try:
            next_button = driver.find_element(By.CSS_SELECTOR, "a.page-link[aria-label='Next']")
            
            # Check if next button is disabled
            parent_li = next_button.find_element(By.XPATH, "..")
            if 'disabled' in parent_li.get_attribute('class'):
                print("    Reached last page")
                break
            
            # Use JavaScript click to avoid interception
            driver.execute_script("arguments[0].click();", next_button)
            time.sleep(2)
            page_num += 1
            
        except Exception as e:
            print(f"    No more pages: {e}")
            break
    
    driver.quit()
    
    if not all_incidents:
        print("  ⚠️  No incidents extracted")
        return None
    
    df = pd.DataFrame(all_incidents)
    df.to_csv('protest_data_oversight.csv', index=False)
    print(f"✅ Scraped {len(all_incidents)} incidents → saved to protest_data_oversight.csv")
    
    return df

if __name__ == "__main__":
    data = scrape_oversight_dashboard_selenium()
    if data is not None:
        print(f"\n📊 Sample data:")
        print(data.head(10))
        
        print(f"\n📈 Category breakdown:")
        categories = data['category'].str.split(', ').explode()
        print(categories.value_counts())
