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
import atexit

import argparse
import logging

parser = argparse.ArgumentParser()
parser.add_argument(
    '-d', '--debug', 
    help="Print lots of debugging statements",
    action="store_const", 
    dest="loglevel", 
    const=logging.DEBUG, 
    default=logging.INFO
)
parser.add_argument(
    "-o", "--output", 
    action='store', 
    nargs='?',
    type=argparse.FileType('w'), 
    dest='output',
    help="Directs the output to a name of your choice"
)
parser.add_argument(
    '-v', '--verbose',
    help="Be verbose",
    action="store_const", 
    dest="loglevel", 
    const=logging.DEBUG,
)
args = parser.parse_args()    
logging.basicConfig(filename='logname.txt',
                    filemode='a',
                    format='%(asctime)s,%(msecs)03d %(name)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level= logging.INFO)

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
        self._cleanup_lock = False
        self._is_cleaned_up = False
        self._driver_pid = None

    def __del__(self):
        """Ensure driver is cleaned up when object is deleted, but only if not already cleaned up"""
        if not self._is_cleaned_up:
            self.cleanup_driver()

    def _is_driver_running(self):
        """Check if the Chrome process is still running"""
        if not self._driver_pid:
            return False
        try:
            import psutil
            return psutil.pid_exists(self._driver_pid)
        except (ImportError, Exception):
            return True  # Assume it's running if we can't check

    def _safe_execute_script(self, script):
        """Safely execute a script, handling any potential errors"""
        try:
            return self.driver.execute_script(script)
        except Exception:
            return None

    def _safe_close_windows(self):
        """Safely close all browser windows"""
        try:
            # Try to get window handles
            try:
                handles = self.driver.window_handles
            except Exception:
                handles = []

            # If we have handles, try to close each window
            for handle in handles:
                try:
                    self.driver.switch_to.window(handle)
                    self._safe_execute_script("window.onbeforeunload = null;")
                    self.driver.close()
                except Exception:
                    continue
        except Exception:
            pass

    def _terminate_chrome_process(self):
        """Forcefully terminate the Chrome process if it's still running"""
        if self._driver_pid:
            try:
                import psutil
                process = psutil.Process(self._driver_pid)
                if process.is_running():
                    process.terminate()
                    process.wait(timeout=3)  # Wait for process to terminate
            except (ImportError, psutil.NoSuchProcess, psutil.TimeoutExpired, Exception):
                pass

    def cleanup_driver(self):
        """Clean up the driver instance with enhanced error handling"""
        if self._cleanup_lock or self._is_cleaned_up:
            return
            
        self._cleanup_lock = True
        try:
            if self.driver and not self._driver_shared:
                # Only attempt cleanup if the driver process is still running
                if self._is_driver_running():
                    try:
                        # Try to disable beforeunload event
                        self._safe_execute_script("window.onbeforeunload = null;")
                        
                        # Safely close all windows
                        self._safe_close_windows()
                        
                        # Attempt to quit the driver
                        try:
                            self.driver.quit()
                        except Exception as e:
                            if "invalid session id" not in str(e).lower() and "no such session" not in str(e).lower():
                                print(f"Warning: Error during driver quit: {str(e)}")
                                
                        # Force terminate the process if it's still running
                        self._terminate_chrome_process()
                        
                    except Exception as e:
                        print(f"Warning: Error during cleanup: {str(e)}")
                        # Still try to terminate the process
                        self._terminate_chrome_process()
                
                # Clear the driver reference regardless of cleanup success
                self.driver = None
                self.wait = None
                self._driver_pid = None
                self._is_cleaned_up = True
        finally:
            self._cleanup_lock = False

    def setup_driver(self):
        """Set up undetected ChromeDriver with enhanced process tracking"""
        try:
            if self.driver:
                self.cleanup_driver()
                
            options = uc.ChromeOptions()
            options.add_argument('--start-maximized')
            options.add_argument('--disable-popup-blocking')
            options.add_argument('--disable-notifications')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--no-sandbox')
            # Add arguments to help with cleanup
            options.add_argument('--disable-background-networking')
            options.add_argument('--disable-background-timer-throttling')
            options.add_argument('--disable-backgrounding-occluded-windows')
            options.add_argument('--disable-breakpad')
            options.add_argument('--disable-component-extensions-with-background-pages')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-features=TranslateUI')
            options.add_argument('--disable-ipc-flooding-protection')
            options.add_argument('--disable-renderer-backgrounding')
            options.add_argument('--enable-features=NetworkService,NetworkServiceInProcess')
            options.add_argument('--force-color-profile=srgb')
            options.add_argument('--metrics-recording-only')
            options.add_argument('--no-first-run')
            
            self.driver = uc.Chrome(options=options)
            
            # Store the process ID for later cleanup
            try:
                self._driver_pid = self.driver.service.process.pid
            except Exception:
                try:
                    # Fallback to getting PID from service directly
                    self._driver_pid = self.driver.service.process.pid if self.driver.service.process else None
                except Exception:
                    self._driver_pid = None
                
            self.driver.set_page_load_timeout(30)
            self.wait = WebDriverWait(self.driver, 10)
            self._driver_shared = False
            self._is_cleaned_up = False
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
                r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)[K]?(?:/yr)?\s*-\s*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)[K]?(?:/yr)?(?:\s*(?:a year|annual|annually|/year|per year|/yr|yr))?',
                r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)[K]?(?:\s*(?:a year|annual|annually|/year|per year|/yr|yr))'
            ],
            'hourly': [
                r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)[K]?(?:/hr)?\s*-\s*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)[K]?(?:/hr)?(?:\s*(?:an hour|/hour|per hour|hourly|/hr|hr))?',
                r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)[K]?(?:\s*(?:an hour|/hour|per hour|hourly|/hr|hr))'
            ],
            'monthly': [
                r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)[K]?\s*-\s*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)[K]?(?:\s*(?:a month|monthly|/month|per month))',
                r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)[K]?(?:\s*(?:a month|monthly|/month|per month))'
            ]
        }
        
        text = text.replace('\n', ' ').strip()
        logging.info(f'Extracting salary from: {text}')
        
        def convert_to_number(value_str):
            """Helper function to convert salary string to number"""
            if not value_str:
                return None
            # Remove commas and convert to float
            num = float(value_str.replace(',', ''))
            # If K is in the original text for this number, multiply by 1000
            if 'K' in text[text.find(value_str)-1:text.find(value_str)+len(value_str)+1]:
                num *= 1000
            return num
        
        for period, period_patterns in patterns.items():
            for pattern in period_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    logging.info(f'Pattern matched: {pattern}')
                    logging.info(f'Groups found: {match.groups()}')
                    groups = match.groups()
                    
                    # Convert first number
                    salary1 = convert_to_number(groups[0])
                    
                    # Convert second number if it exists
                    salary2 = convert_to_number(groups[1]) if len(groups) > 1 and groups[1] else None
                    
                    # Calculate final salary
                    if salary2 is not None:
                        salary = (salary1 + salary2) / 2  # Average of range
                    else:
                        salary = salary1  # Single value
                    
                    # Convert to yearly
                    if period == 'hourly':
                        salary *= 40 * 52  # 40-hour week
                    elif period == 'monthly':
                        salary *= 12
                    
                    logging.info(f'Extracted salary: {salary} from {text}')
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
            
        finally:
            if self.driver and not self._driver_shared:
                try:
                    self.driver.quit()
                except:
                    pass

        return self.jobs

    def check_verification_status(self):
        """Check if we're still on a verification page"""
        try:
            current_url = self.driver.current_url
            return any(x in current_url.lower() for x in ['checkpoint', 'verification', 'challenge', 'login'])
        except:
            return True  # Assume we still need verification if we can't check

    def wait_for_verification(self, timeout=600):  # 10 minutes total timeout
        """Wait for user to complete verification manually"""
        print("\nLinkedIn verification required!")
        print("Please complete the verification in the browser window.")
        print("The browser window will stay open until you complete verification.")
        print("- After 5 minutes, you'll be asked if you want to close the window")
        print("- After 10 minutes, the window will close automatically")
        
        start_time = time.time()
        asked_to_close = False
        
        while time.time() - start_time < timeout:
            if not self.check_verification_status():
                print("\nVerification completed successfully!")
                time.sleep(2)  # Wait for page to stabilize
                return True
                
            # After 5 minutes, ask if user wants to close the window
            elapsed_time = time.time() - start_time
            if elapsed_time > 300 and not asked_to_close:  # 5 minutes
                asked_to_close = True
                print("\n5 minutes have passed. Checking if verification is still needed...")
                
                if self.check_verification_status():
                    print("Still waiting for verification...")
                    print(f"You have {int((timeout - elapsed_time)/60)} minutes before automatic closure")
                    
                    # Use GUI messagebox if available
                    try:
                        import tkinter.messagebox as messagebox
                        if messagebox.askyesno("Verification Timeout", 
                            "Would you like to close the browser window now?\n\n"
                            "Select 'No' to continue waiting for verification."):
                            return False
                    except:
                        # Fallback to console input if GUI not available
                        response = input("\nWould you like to close the browser window? (y/n): ")
                        if response.lower().startswith('y'):
                            return False
            
            # Print remaining time every minute after 5 minutes
            elif elapsed_time > 300 and int(elapsed_time) % 60 == 0:
                remaining = int((timeout - elapsed_time)/60)
                print(f"\n{remaining} minutes remaining before automatic closure")
            
            time.sleep(1)
        
        print("\nVerification timeout - closing browser window")
        return False

    def login_to_linkedin(self, email, password):
        """Login to LinkedIn with provided credentials"""
        try:
            # Load the login page
            if not self.handle_page_load("https://www.linkedin.com/login"):
                raise Exception("Failed to load LinkedIn login page")
            
            try:
                # Wait for and find login elements
                email_input = self.wait.until(EC.presence_of_element_located((By.ID, "username")))
                password_input = self.wait.until(EC.presence_of_element_located((By.ID, "password")))
                
                # Enter credentials
                email_input.send_keys(email)
                password_input.send_keys(password)
                password_input.submit()
                
                # Wait a moment for the login request to process
                time.sleep(3)
                
                # Check for verification requests
                verification_selectors = [
                    "//div[contains(@class, 'verification')]",
                    "//div[contains(@class, 'checkpoint')]",
                    "//div[contains(@class, 'challenge')]",
                    "//input[contains(@aria-label, 'verification')]",
                    "//input[contains(@aria-label, 'pin')]",
                    "//div[contains(text(), 'verify')]",
                    "//div[contains(text(), 'Verify')]",
                    "//div[contains(text(), 'verification')]",
                    "//div[contains(text(), 'Verification')]"
                ]
                
                verification_needed = False
                for selector in verification_selectors:
                    try:
                        if self.driver.find_element(By.XPATH, selector):
                            verification_needed = True
                            break
                    except:
                        continue
                
                if verification_needed or self.check_verification_status():
                    print("\nVerification detected. Starting verification process...")
                    if not self.wait_for_verification():
                        raise Exception("Verification process incomplete")
                
                # Check if we're successfully logged in
                if any(x in self.driver.current_url.lower() for x in ['feed', 'mynetwork', 'jobs']):
                    print("Successfully logged in to LinkedIn")
                    return True
                elif self.check_verification_status():
                    raise Exception("Login unsuccessful - still on login/verification page")
                
                # Additional wait for page to stabilize
                time.sleep(2)
                return True
                
            except Exception as e:
                print(f"Error during LinkedIn login: {str(e)}")
                return False
                
        except Exception as e:
            print(f"Error accessing LinkedIn login page: {str(e)}")
            return False

    def scrape_linkedin(self, email=None, password=None):
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
            
            # Login to LinkedIn if credentials provided
            if email and password:
                if not self.login_to_linkedin(email, password):
                    raise Exception("Failed to login to LinkedIn")
                print("Successfully logged in to LinkedIn")
            else:
                print("No LinkedIn credentials provided. Some job details may be limited.")
            
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
                'position': '1',  # Start position
                'pageNum': '0',   # Page number
                'sortBy': 'R',    # Sort by relevance (R = Relevance, DD = Most recent)
                'f_AL': 'false'   # Don't include all filters
            }

            # Add location parameters
            if self.remote_only:
                base_params['f_WT'] = '2'  # Remote jobs
                base_params['geoId'] = '103644278'  # United States
            elif self.location:
                base_params['location'] = self.location
                if self.distance:
                    base_params['distance'] = str(self.distance)

            # Add experience level filters if specified
            if self.experience_levels:
                exp_params = set()  # Use set to avoid duplicates
                # Map GUI selections to LinkedIn experience levels
                level_mapping = {
                    'Entry level': ['1', '2'],     # Internship and Entry level
                    'Mid level': ['3', '4'],       # Associate and Mid-Senior level
                    'Senior level': ['5', '6']     # Director and Executive
                }
                
                for level in self.experience_levels:
                    if level.lower() in [x.lower() for x in level_mapping.keys()]:
                        # Add all corresponding LinkedIn levels
                        exp_params.update(level_mapping[level])
                
                if exp_params:
                    base_params['f_E'] = ','.join(sorted(exp_params))  # Sort for consistency

            # Add education level if specified
            if self.education_level:
                edu_mapping = {
                    "Bachelor's": '4',
                    "Master's": '5',
                    'Doctorate': '6'
                }
                if self.education_level in edu_mapping:
                    base_params['f_ED'] = edu_mapping[self.education_level]

            # Add salary range if specified
            if self.salary_range and self.salary_range[0] > 0:
                min_salary = self.salary_range[0]
                if min_salary >= 40000:  # Only add if reasonable minimum
                    base_params['f_SB2'] = f'{min_salary}'
                if self.salary_range[1] > min_salary:
                    base_params['f_SB3'] = f'{self.salary_range[1]}'

            # Debug log the parameters
            logging.info(f"LinkedIn search parameters: {base_params}")

            # Scrape each page
            for page in range(pages_to_scrape):
                logging.info(f'Processing page {page + 1} of {pages_to_scrape}')
                
                # Add pagination parameter
                params = base_params.copy()
                params['start'] = page * 25  # LinkedIn uses multiples of 25 for pagination
                
                # Construct URL for this page
                url = f"{base_url}?{urllib.parse.urlencode(params)}"
                logging.info(f'Built LinkedIn URL for page {page + 1}: {url}')
                
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
                            logging.info(f'Searching for jobs container with selector: {selector}')
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
                    logging.info(f'Found {len(job_cards)} job cards on page {page + 1}')
                    
                    if not job_cards:
                        print(f"No job cards found on page {page + 1}")
                        break
                        
                    print(f"Processing {len(job_cards)} jobs from page {page + 1}")
                    
                    # Process each job card
                    for job_card in job_cards:
                        try:
                            # Click the job card and wait for details to load
                            logging.info('Attempting to click job card')
                            try:
                                job_card.click()
                            except:
                                # If direct click fails, try JavaScript click
                                self.driver.execute_script("arguments[0].click();", job_card)
                            
                            # Wait for job details pane to load
                            logging.info('Waiting for job details to load')
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
                                logging.info(f'Skipping already processed job: {job_url}')
                                continue
                            
                            processed_urls.add(job_url)
                            
                            # Extract job details
                            logging.info('Extracting job title')
                            title = job_card.find_element(By.CSS_SELECTOR, 
                                ".job-card-list__title, .jobs-search-results__list-item-title, .job-card-list__title--link"
                            ).text.strip()
                            
                            logging.info('Extracting job company')
                            company = job_card.find_element(By.CSS_SELECTOR,
                                ".job-card-container__company-name, .job-card-container__primary-description, .artdeco-entity-lockup__caption"
                            ).text.strip()
                            
                            print(f'Processing job: {title} at {company}')
                            
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
                                    logging.info('Extracting job description')
                                    if description:
                                        logging.info(f'Job description extracted-- {description}')
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
                                ".salary-range",
                                ".compensation",
                                ".job-details-jobs-unified-top-card__job-insight",
                                "div[class*='job-details-preferences-and-skills__pill'][role*='presentation']",
                            ]
                            
                            for selector in salary_selectors:
                                try:
                                    logging.info(f'Attempting to find salary with selector: {selector}')
                                    salary_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                                    salary_text = salary_elem.text.strip()
                                    if salary_text and any(i.isdigit() for i in salary_text):
                                        salary_text = salary_text.split('Matches your job preferences')[0].strip()
                                        logging.info(f'Found salary: {salary_text}')
                                        salary = self.extract_salary(salary_text)
                                        print(f'Found salary: {salary_text}')
                                        break
                                    else:
                                        salary_text = None
                                        continue
                                except:
                                    continue

                            if salary_text is None:
                                logging.warning('Could not find salary. Attempting to use XPATH')
                                try:
                                    logging.info(f'Attempting to find salary with selector: {selector}')
                                    salary_elem = self.driver.find_element_by_xpath('//div[contains(@class, "job-details-preferences-and-skills__pill") and (contains(text(), "yr") or contains(text(), "hr"))]')
                                    salary_text = salary_elem.text.strip()
                                    if salary_text:
                                        logging.info(f'Found salary: {salary_text}')
                                        salary = self.extract_salary(salary_text)
                                        print(f'Found salary: {salary_text}')
                                        break
                                        
                                except NoSuchElementException:
                                        logging.info(f'Attempting to find salary with selector: {selector}')
                                        salary_elem = self.driver.find_element_by_xpath('//p[contains(text(), "Compensation Range") or contains(text(), "/yr") or contains(text(), "/hr") or contains(text(), "per year")]')
                                        salary_text = salary_elem.text.strip()
                                        if salary_text:
                                            logging.info(f'Found salary: {salary_text}')
                                            salary = self.extract_salary(salary_text)
                                            print(f'Found salary: {salary_text}')
                                            break
                                except:
                                    continue
                            
                            logging.info(f'Successfully extracted all job details.')
                            
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
                            
                            logging.info(f'Job {self.jobs[-1]["title"]} rated: {self.jobs[-1]["rating"]}')

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
            
        except Exception as e:
            print(f"Error in LinkedIn scraper: {str(e)}")
            raise
        finally:
            # Don't cleanup driver here - let the GUI handle it
            pass

    def scrape_jobs(self, websites, scraper):
        """Scrape jobs from specified websites"""
        try:
            for website in websites:
                print(f"\nScraping jobs from {website}...")
                if website == 'LinkedIn':
                    scraper.scrape_linkedin(email="your_email", password="your_password") ## your_email, your_password
                elif website == 'Indeed':
                    scraper.scrape_indeed()
        finally:
            # Clean up the driver if we haven't already and it's not shared
            if scraper.driver and not scraper._driver_shared:
                scraper.cleanup_driver()

if __name__ == '__main__':
    import psutil
    scraper = None
    
    def cleanup_at_exit():
        global scraper
        if scraper and not scraper._is_cleaned_up:
            scraper.cleanup_driver()
    
    # Register cleanup function to run at program exit
    atexit.register(cleanup_at_exit)
    
    try:
        scraper = JobScraper(
            keywords='business intelligence Tableau',
            job_title='Business Intelligence Developer',
            salary_range=(100000, 120000),
            resume='path/to/resume',
            remote_only=True,
            top_percent=10,
            bottom_percent=10
        )
        
        scraper.scrape_jobs(['LinkedIn', 'Indeed'], scraper)
            
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if scraper:
            # Ensure immediate cleanup
            scraper.cleanup_driver()
            # Unregister the atexit handler since we've already cleaned up
            atexit.unregister(cleanup_at_exit)