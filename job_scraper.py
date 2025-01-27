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
import datetime

import argparse
import logging

parser = argparse.ArgumentParser()
parser.add_argument(
    "--log", 
    choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], 
    default="INFO", 
    help="Log level."
)
parser.add_argument(
    '-d', '--debug', 
    help="Print lots of debugging statements",
    action="store_const", 
    dest="loglevel", 
    const=logging.DEBUG, 
    default=logging.INFO
)
parser.add_argument(
    '-v', '--verbose',
    help="Be verbose",
    action="store_const", dest="loglevel", const=logging.DEBUG,
)
args = parser.parse_args()    
logging.basicConfig(level=args.loglevel)

class JobScraper:
    def __init__(self, keywords=None, job_title=None, salary_range=None, resume=None, 
                 remote_only=True, location=None, distance=None, 
                 experience_levels=None, education_level=None,
                 include_no_salary=False, top_percent=10, bottom_percent=10,
                 require_experience=False):
        self.keywords = keywords or []
        self.job_title = job_title
        self.salary_range = salary_range
        self.resume = resume
        self.remote_only = remote_only
        self.location = location
        self.distance = distance  # Distance in miles
        self.experience_levels = experience_levels or []
        self.education_level = education_level
        self.include_no_salary = include_no_salary
        # Rating parameters
        self.top_percent = top_percent
        self.bottom_percent = bottom_percent
        self.require_experience = require_experience
        self.jobs = []
        self.user_agent = UserAgent()
        self.driver = None
        self.wait = None
        self._driver_shared = False
        
    def setup_driver(self):
        """Set up undetected ChromeDriver"""
        if self.driver and self.wait:
            return self.driver
            
        try:
            options = uc.ChromeOptions()
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-extensions')
            
            self.driver = uc.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, 10)
            return self.driver
        except Exception as e:
            print(f"Error setting up ChromeDriver: {str(e)}")
            raise

    def handle_page_load(self, url, max_retries=3):
        """Handle page load with retries"""
        if not self.driver or not self.wait:
            self.setup_driver()
            
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
        """Rate job based on salary range and experience criteria"""
        if not salary and not self.include_no_salary:
            return None  # Job will be filtered out
            
        if not salary:
            return None  # Changed: Don't include jobs without salary unless explicitly allowed
            
        min_salary, max_salary = self.salary_range
        salary_range = max_salary - min_salary
        
        # Calculate thresholds using specified percentages
        top_threshold = max_salary - (salary_range * (self.top_percent / 100))
        bottom_threshold = min_salary + (salary_range * (self.bottom_percent / 100))
        
        # Calculate buffer zone around bottom threshold (10% up and down)
        buffer_size = bottom_threshold * (self.bottom_percent / 100)
        bottom_buffer_low = bottom_threshold - buffer_size
        bottom_buffer_high = bottom_threshold + buffer_size
        
        # Exclude jobs below the buffer zone
        if salary < bottom_buffer_low:
            return None   
        elif salary >= top_threshold:  # Initial rating based on salary
            rating = 1  # High rating
        elif bottom_buffer_low <= salary <= bottom_buffer_high:
            rating = 3  # Within bottom threshold buffer zone
        else:
            rating = 2  # Within normal range
        
        # Experience level criteria
        if self.require_experience and self.experience_levels and rating == 1:
            # Only check experience for jobs that would otherwise be rated 1
            job_exp_match = any(level.lower() in str(self.jobs[-1].get('summary', '')).lower() 
                              for level in self.experience_levels)
            if not job_exp_match:
                rating = 2  # Downgrade to partial match if experience doesn't match
        
        return rating

    def save_results(self):
        """Save job results to CSV file in Documents folder"""
        if not self.jobs:
            return
            
        # Filter out jobs with no salary if include_no_salary is False
        # Also filter out jobs that were rated as None (below bottom buffer)
        filtered_jobs = [
            job for job in self.jobs 
            if (job.get('rating') is not None and # Rating is not None
                (self.include_no_salary or job.get('salary_value') is not None))  # Has salary if required
        ]
        
        if not filtered_jobs:
            print("No jobs match the criteria after filtering")
            return
            
        # Get Documents folder path and create filename with current date
        documents_path = os.path.expanduser('~/Documents')
        current_date = datetime.datetime.now().strftime('%Y-%m-%d')
        filename = f'job_results_{current_date}.csv'
        filepath = os.path.join(documents_path, filename)
        
        # Create DataFrame and save to CSV
        df = pd.DataFrame(filtered_jobs)
        df.to_csv(filepath, index=False)
        print(f"\nSaved {len(filtered_jobs)} jobs to: {filepath}")
        
        # Print job ratings summary
        ratings = df['rating'].value_counts().sort_index()
        for rating, count in ratings.items():
            rating_desc = {
                1: "Top tier salary" + (" & matching experience" if self.require_experience else ""),
                2: "Within target range",
                3: "Below target range"
            }.get(rating, "Unknown")
            print(f"Rating {rating} ({rating_desc}): {count}")

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
            # Split by double newlines to preserve paragraph structure
            paragraphs = [p.strip() for p in job_desc.get_text().split('\n\n') if p.strip()]
            # Join paragraphs with proper spacing
            summary = ' '.join(p.replace('\n', ' ').strip() for p in paragraphs)
        else:
            # Try structured sections
            sections = ['Requirements', 'Responsibilities', 'Qualifications', 'Skills', "What You'll Do"]
            section_texts = []
            for section in sections:
                if header := job_soup.find(['h3', 'h4'], string=lambda s: s and section.lower() in s.lower()):
                    if section_div := header.find_next('div'):
                        section_text = section_div.get_text().strip()
                        # Clean up internal spacing
                        section_text = ' '.join(section_text.split())
                        section_texts.append(f"{section}: {section_text}")
            summary = ' '.join(section_texts)
        
        # Clean up text
        summary = summary.encode('ascii', 'ignore').decode('ascii')
        if len(summary) > 1000:
            summary = summary[:997] + "..."
            
        return summary, salary_text

    def scrape_indeed(self):
        print("Starting job scraper...")
        
        try:
            # Format search query
            search_query = self.job_title if self.job_title else ' '.join(self.keywords)
            print(f"Searching Indeed for '{search_query}' jobs...")
            if self.remote_only:
                print("Filtering for remote jobs only")
            elif self.location:
                print(f"Searching in location: {self.location}")
                if self.distance:
                    print(f"Within {self.distance} miles")
                
            self.setup_driver()
            processed_urls = set()
            page = 0
            
            while True:
                # Build the URL with advanced filters and pagination
                base_url = "https://www.indeed.com/jobs"
                params = {
                    'q': search_query,
                    'l': 'Remote' if self.remote_only else (self.location or ''),
                    'sc': '0kf:attr(DSQF7)' if self.remote_only else '',  # Remote jobs filter
                    'radius': self.distance if self.distance else '',  # Distance in miles
                    'start': page * 10,  # Indeed uses multiples of 10 for pagination
                    'vjk': 'all'
                }

                # Add experience level filters
                if self.experience_levels:
                    exp_params = []
                    for level in self.experience_levels:
                        if level == "Entry Level":
                            exp_params.append("explvl(ENTRY_LEVEL)")
                        elif level == "Mid Level":
                            exp_params.append("explvl(MID_LEVEL)")
                        elif level == "Senior Level":
                            exp_params.append("explvl(SENIOR_LEVEL)")
                    if exp_params:
                        params['sc'] = f"{params['sc']},{''.join(exp_params)}"

                # Add education level filter
                if self.education_level:
                    edu_param = ""
                    if self.education_level == "Bachelor's Degree":
                        edu_param = "attr(FCGTU)|attr(HFDVW)"  # Indeed's parameter for Bachelor's
                    elif self.education_level == "Master's Degree":
                        edu_param = "attr(FCGTU)|attr(HFDVW)|attr(QXQQS)"  # Include Master's
                    if edu_param:
                        params['sc'] = f"{params['sc']},{edu_param}"

                url = f"{base_url}?{urllib.parse.urlencode(params)}"
                
                if not self.handle_page_load(url):
                    break
                
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                job_cards = soup.find_all('div', {'class': ['job_seen_beacon', 'jobsearch-ResultsList', 'tapItem']})
                
                if not job_cards:  # No more results
                    break
                    
                if page == 0:  # Only print this for the first page
                    print(f"\nFound {len(job_cards)} job cards on first page")
                
                new_jobs_found = False
                for job in job_cards:
                    try:
                        # Get job URL and check for duplicates
                        if not (job_link := job.find('a', {'class': ['jcs-JobTitle', 'jobTitle']}, href=True)):
                            continue
                        
                        job_url = 'https://www.indeed.com' + job_link['href']
                        if job_url in processed_urls:
                            continue
                        
                        new_jobs_found = True
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
                
                if not new_jobs_found:  # If no new jobs were found on this page
                    break
                    
                page += 1
                if page >= 3:  # Limit to 3 pages (about 45 jobs) to avoid too many requests
                    break
            
            print(f"\nProcessed {len(self.jobs)} jobs from Indeed")
            self.save_results()
            
        finally:
            if self.driver and not self._driver_shared:
                try:
                    self.driver.quit()
                except:
                    pass

    def scrape_linkedin(self):
        """
        Scrape job listings from LinkedIn.
        Scrapes 3 pages of results using URL-based pagination.
        """
        print("Starting LinkedIn job scraper...")
        
        try:
            # Initialize tracking variables
            processed_urls = set()  # Track processed job URLs
            total_jobs_found = 0
            pages_to_scrape = 3
            
            # Only set up driver if not already provided
            if not self.driver or not self.wait:
                self.setup_driver()
            
            # Format search query - combine job title and keywords if both present
            search_terms = []
            if self.job_title:
                search_terms.append(self.job_title)
            if self.keywords:
                if isinstance(self.keywords, str):
                    search_terms.extend(self.keywords.split())
                else:
                    search_terms.extend(self.keywords)
            search_query = ' '.join(search_terms)
            print(f"Searching LinkedIn for '{search_query}' jobs...")
            
            # Base URL and params that stay constant
            base_url = "https://www.linkedin.com/jobs/search"
            base_params = {
                'keywords': search_query,
                'f_AL': 'true',  # All filters
                'sortBy': 'R'  # Sort by relevance
            }

            # Add location parameters
            if self.remote_only:
                base_params['f_WT'] = '2'  # Remote jobs
                base_params['location'] = 'United States'  # Default to US for remote
            elif self.location:
                base_params['location'] = self.location
                if self.distance:
                    base_params['distance'] = str(self.distance)

            # Add experience level filters if specified
            if self.experience_levels:
                exp_params = []
                for level in self.experience_levels:
                    if level.lower() == "entry level":
                        exp_params.append("1")
                    elif level.lower() == "mid level":
                        exp_params.append("2")
                    elif level.lower() == "senior level":
                        exp_params.append("3")
                if exp_params:
                    base_params['f_E'] = ','.join(exp_params)

            # Debug log the parameters
            logging.debug(f"LinkedIn search parameters: {base_params}")

            # Scrape each page
            for page in range(pages_to_scrape):
                logging.debug(f'Processing page {page + 1} of {pages_to_scrape}')
                
                # Add pagination parameter
                params = base_params.copy()
                params['start'] = page * 25  # LinkedIn uses multiples of 25 for pagination
                
                # Construct URL for this page
                url = f"{base_url}?{urllib.parse.urlencode(params)}"
                logging.debug(f'Built LinkedIn URL for page {page + 1}: {url}')
                
                if not self.handle_page_load(url):
                    print(f"Failed to load LinkedIn jobs page {page + 1}")
                    break
                
                try:
                    # Wait for job results container
                    jobs_container = None
                    container_selectors = [
                        "jobs-search-results-list",
                        "jobs-search-results__list",
                        "jobs-search__results-list",
                        "scaffold-layout__list"
                    ]
                    
                    # Try each possible container selector
                    for selector in container_selectors:
                        try:
                            logging.debug(f'Searching for jobs container with selector: {selector}')
                            jobs_container = self.wait.until(
                                EC.presence_of_element_located((By.CLASS_NAME, selector))
                            )
                            if jobs_container:
                                break
                        except:
                            continue
                    
                    if not jobs_container:
                        print(f"Could not find jobs container on page {page + 1}")
                        break
                    
                    # Scroll the container to load all jobs
                    self.driver.execute_script(
                        "arguments[0].scrollTo(0, arguments[0].scrollHeight)", 
                        jobs_container
                    )
                    time.sleep(2)  # Wait for dynamic content to load
                    
                    # Find all job cards
                    job_cards = self.driver.find_elements(By.CSS_SELECTOR, 
                        ".job-card-container, .jobs-search-results__list-item, .job-card-container--clickable"
                    )
                    logging.debug(f'Found {len(job_cards)} job cards on page {page + 1}')
                    
                    if not job_cards:
                        print(f"No job cards found on page {page + 1}")
                        break
                        
                    print(f"Processing {len(job_cards)} jobs from page {page + 1}")
                    
                    # Process each job card
                    for job_card in job_cards:
                        try:
                            # Click the job card and wait for details to load
                            logging.debug('Attempting to click job card')
                            try:
                                job_card.click()
                            except:
                                # If direct click fails, try JavaScript click
                                self.driver.execute_script("arguments[0].click();", job_card)
                            
                            # Wait for job details pane to load
                            logging.debug('Waiting for job details to load')
                            try:
                                self.wait.until(EC.presence_of_element_located((
                                    By.CSS_SELECTOR, 
                                    ".jobs-details__main-content, .jobs-search__job-details"
                                )))
                            except TimeoutException:
                                logging.warning('Timeout waiting for job details pane')
                                continue
                            
                            time.sleep(1)  # Short wait for content to stabilize
                            
                            # Get current job URL and check if already processed
                            job_url = self.driver.current_url
                            if job_url in processed_urls:
                                logging.debug(f'Skipping already processed job: {job_url}')
                                continue
                            
                            processed_urls.add(job_url)
                            
                            # Extract job details
                            logging.debug('Extracting job details')
                            title = job_card.find_element(By.CSS_SELECTOR, 
                                ".job-card-list__title, .jobs-search-results__list-item-title, .job-card-list__title--link"
                            ).text.strip()
                            
                            company = job_card.find_element(By.CSS_SELECTOR,
                                ".job-card-container__company-name, .job-card-container__primary-description, .artdeco-entity-lockup__caption"
                            ).text.strip()
                            
                            logging.debug(f'Processing job: {title} at {company}')
                            
                            # Get job description
                            description = None
                            description_selectors = [
                                ".jobs-description__content",
                                ".jobs-description",
                                ".jobs-details__main-content"
                            ]
                            
                            for selector in description_selectors:
                                try:
                                    description = self.wait.until(EC.presence_of_element_located((
                                        By.CSS_SELECTOR, selector
                                    )))
                                    if description:
                                        break
                                except:
                                    continue
                            
                            if not description:
                                logging.warning('Could not find job description')
                                continue
                            
                            summary = description.text.strip()
                            
                            # Try to find salary information
                            salary_text = None
                            salary_selectors = [
                                "[class*='salary-range']",
                                "[class*='compensation']",
                                ".job-details-jobs-unified-top-card__job-insight"
                            ]
                            
                            for selector in salary_selectors:
                                try:
                                    salary_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                                    salary_text = salary_elem.text.strip()
                                    if salary_text:
                                        break
                                except:
                                    continue
                            
                            salary = self.extract_salary(salary_text)
                            
                            logging.debug(f'Successfully extracted all job details')
                            
                            # Store job data
                            self.jobs.append({
                                'title': title,
                                'company': company,
                                'summary': summary[:500],
                                'salary_text': salary_text or "Not specified",
                                'salary_value': salary,
                                'rating': self.rate_job(salary),
                                'company_rating': None,
                                'source': 'LinkedIn',
                                'url': job_url
                            })
                            
                            total_jobs_found += 1
                            
                        except Exception as e:
                            logging.error(f"Error processing job: {str(e)}")
                            continue
                    
                except TimeoutException:
                    logging.error(f"Timeout on page {page + 1}")
                    continue
                except Exception as e:
                    logging.error(f"Error processing page {page + 1}: {str(e)}")
                    continue
            
            # After processing all pages, save results
            print(f"\nLinkedIn scraping completed. Found {total_jobs_found} jobs across {pages_to_scrape} pages.")
            
            if self.jobs:
                print(f"Saving {len(self.jobs)} jobs to CSV...")
                try:
                    self.save_results()
                    print("Results saved successfully!")
                except Exception as e:
                    print(f"Error saving results: {str(e)}")
            
        except Exception as e:
            print(f"Error in LinkedIn scraper: {str(e)}")
        finally:
            # Only quit the driver if we created it
            if self.driver and not self._driver_shared:
                self.driver.quit()

    def scrape_jobs(self, websites):
        """Scrape jobs from specified websites"""
        try:
            for website in websites:
                if website == 'LinkedIn':
                    self.scrape_linkedin()
                elif website == 'Indeed':
                    self.scrape_indeed()
        finally:
            # Clean up the driver if we haven't already and it's not shared
            if self.driver and not self._driver_shared:
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None
                self.wait = None

if __name__ == '__main__':
    try:
        scraper = JobScraper(
            keywords='business intelligence data analyst Tableau',
            job_title='Business Intelligence Developer',
            salary_range=(90000, 120000),
            resume='path/to/resume',
            remote_only=True,
            include_no_salary=False,
            top_percent=10,
            bottom_percent=10
        )
        scraper.scrape_indeed()
    except Exception as e:
        print(f"Error: {str(e)}")