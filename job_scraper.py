import pandas as pd
import re
import time
import random
from fake_useragent import UserAgent
import urllib.parse
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import os

class JobScraper:
    def __init__(self, keywords, job_title, salary_range, resume, remote_only=False):
        self.keywords = keywords
        self.job_title = job_title
        self.salary_range = salary_range
        self.resume = resume
        self.remote_only = remote_only
        self.jobs = []
        self.user_agent = UserAgent()
        self.driver = None
        self.wait = None
        
    def setup_driver(self):
        """Set up undetected ChromeDriver"""
        try:
            options = uc.ChromeOptions()
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-extensions')
            
            self.driver = uc.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, 10)
            self.driver.set_page_load_timeout(30)
            return self.driver
        except Exception as e:
            print(f"Error setting up ChromeDriver: {str(e)}")
            raise

    def handle_page_load(self, url, max_retries=3):
        """Handle page load with retries"""
        for attempt in range(max_retries):
            try:
                self.driver.get(url)
                time.sleep(random.uniform(1, 2))
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                return True
            except Exception as e:
                print(f"Error loading page (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(1, 3))
                else:
                    return False

    def extract_salary(self, text):
        """Extract salary information from text"""
        if not text:
            return None
            
        patterns = {
            'yearly': [
                r'\$(\d{2,3}(?:,\d{3})*(?:\.\d{2})?)[K]?\s*-\s*\$?(\d{2,3}(?:,\d{3})*(?:\.\d{2})?)[K]?\s*(?:a year|annual|annually|/year|per year)',
                r'\$(\d{2,3}(?:,\d{3})*(?:\.\d{2})?)[K]?\s*(?:a year|annual|annually|/year|per year)'
            ],
            'hourly': [
                r'\$(\d{2,3}(?:,\d{3})*(?:\.\d{2})?)\s*-\s*\$?(\d{2,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:an hour|/hour|per hour|hourly)',
                r'\$(\d{2,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:an hour|/hour|per hour|hourly)'
            ],
            'monthly': [
                r'\$(\d{2,3}(?:,\d{3})*(?:\.\d{2})?)[K]?\s*-\s*\$?(\d{2,3}(?:,\d{3})*(?:\.\d{2})?)[K]?\s*(?:a month|monthly|/month|per month)',
                r'\$(\d{2,3}(?:,\d{3})*(?:\.\d{2})?)[K]?\s*(?:a month|monthly|/month|per month)'
            ]
        }
        
        for period, period_patterns in patterns.items():
            for pattern in period_patterns:
                if matches := re.findall(pattern, text, re.IGNORECASE):
                    values = []
                    for match in matches[0] if isinstance(matches[0], tuple) else [matches[0]]:
                        if match:
                            clean_value = float(match.replace(',', '').replace('K', '000'))
                            values.append(clean_value)
                    
                    if not values:
                        continue
                    
                    salary = sum(values) / len(values)
                    
                    # Convert to yearly
                    if period == 'hourly':
                        salary *= 40 * 52  # 40-hour week
                    elif period == 'monthly':
                        salary *= 12
                    
                    return salary
        return None

    def rate_job(self, salary):
        """Rate job based on salary range"""
        if not salary:
            return 2
        if salary >= self.salary_range[0]:
            return 1
        if salary <= self.salary_range[1] * 1.1:
            return 3
        return 2

    def save_results(self):
        """Save job results to CSV"""
        try:
            if not self.jobs:
                print("No jobs to save!")
                return False

            df = pd.DataFrame(self.jobs)
            output_file = os.path.abspath('job_results.csv')
            df.to_csv(output_file, index=False, encoding='utf-8')
            
            print(f"\nSaved {len(self.jobs)} jobs to: {output_file}")
            for rating, desc in [(1, "Match requirements"), (2, "Partial match"), (3, "Overqualified")]:
                count = len(df[df['rating'] == rating])
                print(f"Rating {rating} ({desc}): {count}")
            
            return True
        except Exception as e:
            print(f"Error saving results: {str(e)}")
            return False

    def extract_job_details(self, job_soup):
        """Extract job details from soup"""
        summary = ""
        salary_text = None
        
        # Get salary from Pay section
        if pay_header := job_soup.find('h3', string='Pay'):
            if salary_section := pay_header.find_next('div'):
                salary_text = salary_section.get_text(strip=True)
                print(f"Found salary: {salary_text}")
        
        # Get job description
        if job_desc := job_soup.find('div', {'id': 'jobDescriptionText'}):
            summary = job_desc.get_text(strip=True)
        else:
            # Try structured sections
            sections = ['Requirements', 'Responsibilities', 'Qualifications', 'Skills', "What You'll Do"]
            for section in sections:
                if header := job_soup.find(['h3', 'h4'], string=lambda s: s and section.lower() in s.lower()):
                    if section_div := header.find_next('div'):
                        summary += f"{section}: {section_div.get_text(strip=True)}\n\n".replace('\n', ' ').replace('  ', ' ')
        
        # Clean up text
        summary = ' '.join(summary.split())
        summary = summary.encode('ascii', 'ignore').decode('ascii')
        if len(summary) > 1000:
            summary = summary[:997] + "..."
            
        return summary, salary_text

    def scrape_indeed(self):
        """Scrape jobs from Indeed"""
        try:
            print(f"Searching Indeed for '{self.keywords}' jobs...")
            if self.remote_only:
                print("Filtering for remote jobs only")
            
            self.setup_driver()
            
            # Build search URL
            params = {
                'q': f"{self.keywords} remote" if self.remote_only else self.keywords,
                'l': 'Remote' if self.remote_only else '',
                'fromage': '14',
                'sort': 'date',
                'sc': '0kf:attr(DSQF7)' if self.remote_only else ''
            }
            url = f"https://www.indeed.com/jobs?{urllib.parse.urlencode(params)}"
            
            if not self.handle_page_load(url):
                return
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            job_cards = soup.find_all('div', {'class': ['job_seen_beacon', 'jobsearch-ResultsList', 'tapItem']})
            print(f"\nFound {len(job_cards)} job cards")
            
            processed_urls = set()
            for job in job_cards:
                try:
                    # Get job URL and check for duplicates
                    if not (job_link := job.find('a', {'class': ['jcs-JobTitle', 'jobTitle']}, href=True)):
                        continue
                    
                    job_url = 'https://www.indeed.com' + job_link['href']
                    if job_url in processed_urls:
                        print("Skipping duplicate")
                        continue
                    processed_urls.add(job_url)
                    
                    # Get basic job info
                    title = job_link.get_text(strip=True)
                    company = "Company not found"
                    if company_elem := job.find('span', {'data-testid': 'company-name'}):
                        company = company_elem.get_text(strip=True).split(',')[0].strip()
                        company = company.encode('ascii', 'ignore').decode('ascii')
                    
                    print(f"\nProcessing: {title} at {company}")
                    
                    # Get detailed job info
                    self.driver.get(job_url)
                    time.sleep(1)
                    job_soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                    
                    summary, salary_text = self.extract_job_details(job_soup)
                    salary = self.extract_salary(salary_text)
                    
                    # Store job data
                    self.jobs.append({
                        'title': title,
                        'company': company,
                        'summary': summary[:500],
                        'salary_text': salary_text or "Not specified",
                        'salary_value': salary,
                        'rating': self.rate_job(salary),
                        'company_rating': None,  # Disabled for now
                        'source': 'Indeed',
                        'url': job_url
                    })
                    
                    self.driver.back()
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"Error processing job: {str(e)}")
                    continue
            
            print(f"\nProcessed {len(self.jobs)} jobs from Indeed")
            self.save_results()
            
        except Exception as e:
            print(f"Error during scraping: {str(e)}")
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass

if __name__ == '__main__':
    try:
        print("Starting job scraper...")
        scraper = JobScraper(
            keywords='business intelligence data analyst Tableau',
            job_title='Business Intelligence Developer',
            salary_range=(90000, 120000),
            resume='path/to/resume',
            remote_only=True
        )
        scraper.scrape_indeed()
    except Exception as e:
        print(f"Error: {str(e)}")