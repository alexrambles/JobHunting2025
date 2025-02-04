import tkinter as tk
from tkinter import ttk, messagebox
from job_scraper import JobScraper
import time
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import random
import json
import os
from pathlib import Path

class JobScraperGUI:
    def __init__(self, master):
        self.master = master
        master.title("Job Scraper Configuration")
        
        # Settings file path
        self.settings_file = os.path.join(str(Path.home()), '.job_scraper_settings.json')
        
        # Initialize scraper and driver
        self.scraper = JobScraper()
        self.driver = None
        self.wait = None
        
        # Initialize variables
        self.linkedin_email = ""
        self.linkedin_password = ""
        self.settings = {}
        
        # Create menu
        self.menu = tk.Menu(master)
        master.config(menu=self.menu)

        # Add settings menu
        self.settings_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Settings", menu=self.settings_menu)
        self.settings_menu.add_command(label="LinkedIn Login", command=self.open_linkedin_login_window)
        
        # Create main frame
        self.main_frame = ttk.Frame(master, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Load saved settings
        self.load_settings()

        # Create all GUI elements
        self.create_basic_settings()
        self.create_advanced_settings()

        # Apply saved settings after GUI elements are created
        self.apply_saved_settings()

        # Submit Button
        self.submit_button = ttk.Button(self.main_frame, text="Start Scraper", command=self.start_scraper)
        self.submit_button.pack(pady=10)

    def load_settings(self):
        """Load settings from file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    self.settings = json.load(f)
                    self.linkedin_email = self.settings.get('linkedin_email', '')
                    # Don't load password for security
        except Exception as e:
            print(f"Error loading settings: {str(e)}")
            self.settings = {}

    def save_settings(self):
        """Save settings to file"""
        try:
            # Only save settings if GUI elements exist
            settings = {
                'linkedin_email': self.linkedin_email,
            }
            
            # Add basic settings if they exist
            if hasattr(self, 'keywords_entry'):
                settings.update({
                    'keywords': self.keywords_entry.get(),
                    'job_title': self.job_title_entry.get(),
                    'salary_min': self.salary_min_entry.get(),
                    'salary_max': self.salary_max_entry.get(),
                    'include_no_salary': self.include_no_salary_var.get(),
                    'remote_only': self.remote_var.get(),
                    'location': self.location_entry.get(),
                })
            
            # Add advanced settings if they exist
            if hasattr(self, 'distance_entry'):
                settings.update({
                    'distance': self.distance_entry.get(),
                    'experience_levels': {level: var.get() for level, var in self.exp_vars.items()},
                    'education_level': self.edu_var.get(),
                    'top_percent': self.top_percent_entry.get(),
                    'bottom_percent': self.bottom_percent_entry.get(),
                    'require_experience': self.experience_req_var.get(),
                })
            
            # Add website selections if they exist
            if hasattr(self, 'website_vars'):
                settings['selected_websites'] = {site: var.get() for site, var in self.website_vars.items()}
            
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f)
        except Exception as e:
            print(f"Error saving settings: {str(e)}")

    def apply_saved_settings(self):
        """Apply saved settings to GUI elements"""
        if not hasattr(self, 'settings'):
            return
            
        try:
            # Apply basic settings
            if hasattr(self, 'keywords_entry'):
                if 'keywords' in self.settings:
                    self.keywords_entry.delete(0, tk.END)
                    self.keywords_entry.insert(0, self.settings.get('keywords', ''))
                if 'job_title' in self.settings:
                    self.job_title_entry.delete(0, tk.END)
                    self.job_title_entry.insert(0, self.settings.get('job_title', ''))
                if 'salary_min' in self.settings:
                    self.salary_min_entry.delete(0, tk.END)
                    self.salary_min_entry.insert(0, self.settings.get('salary_min', ''))
                if 'salary_max' in self.settings:
                    self.salary_max_entry.delete(0, tk.END)
                    self.salary_max_entry.insert(0, self.settings.get('salary_max', ''))
                if 'include_no_salary' in self.settings:
                    self.include_no_salary_var.set(self.settings.get('include_no_salary', False))
                if 'remote_only' in self.settings:
                    self.remote_var.set(self.settings.get('remote_only', False))
                if 'location' in self.settings:
                    self.location_entry.delete(0, tk.END)
                    self.location_entry.insert(0, self.settings.get('location', ''))
            
            # Apply advanced settings
            if hasattr(self, 'distance_entry'):
                if 'distance' in self.settings:
                    self.distance_entry.delete(0, tk.END)
                    self.distance_entry.insert(0, self.settings.get('distance', ''))
                if 'experience_levels' in self.settings:
                    for level, value in self.settings['experience_levels'].items():
                        if level in self.exp_vars:
                            self.exp_vars[level].set(value)
                if 'education_level' in self.settings:
                    self.edu_var.set(self.settings.get('education_level', ''))
                if 'top_percent' in self.settings:
                    self.top_percent_entry.delete(0, tk.END)
                    self.top_percent_entry.insert(0, self.settings.get('top_percent', ''))
                if 'bottom_percent' in self.settings:
                    self.bottom_percent_entry.delete(0, tk.END)
                    self.bottom_percent_entry.insert(0, self.settings.get('bottom_percent', ''))
                if 'require_experience' in self.settings:
                    self.experience_req_var.set(self.settings.get('require_experience', False))
            
            # Apply website selections
            if hasattr(self, 'website_vars') and 'selected_websites' in self.settings:
                for site, value in self.settings['selected_websites'].items():
                    if site in self.website_vars:
                        self.website_vars[site].set(value)
                        
        except Exception as e:
            print(f"Error applying settings: {str(e)}")

    def create_basic_settings(self):
        # Basic settings frame
        basic_frame = ttk.LabelFrame(self.main_frame, text="Basic Settings", padding="5")
        basic_frame.pack(fill=tk.X, padx=5, pady=5)

        # Keywords
        ttk.Label(basic_frame, text="Keywords (comma-separated):").pack()
        self.keywords_entry = ttk.Entry(basic_frame)
        self.keywords_entry.pack(fill=tk.X)

        # Job Title
        ttk.Label(basic_frame, text="Job Title:").pack()
        self.job_title_entry = ttk.Entry(basic_frame)
        self.job_title_entry.pack(fill=tk.X)

        # Salary Range
        salary_frame = ttk.Frame(basic_frame)
        salary_frame.pack(fill=tk.X, pady=5)
        ttk.Label(salary_frame, text="Salary Range:").pack(side=tk.LEFT)
        self.salary_min_entry = ttk.Entry(salary_frame, width=15)
        self.salary_min_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(salary_frame, text="to").pack(side=tk.LEFT)
        self.salary_max_entry = ttk.Entry(salary_frame, width=15)
        self.salary_max_entry.pack(side=tk.LEFT, padx=5)

        # Include No Salary Toggle
        self.include_no_salary_var = tk.BooleanVar(value=False)
        self.include_no_salary_checkbox = ttk.Checkbutton(
            basic_frame,
            text="Include Jobs Without Specified Salary",
            variable=self.include_no_salary_var
        )
        self.include_no_salary_checkbox.pack(pady=5)

        # Resume Path
        ttk.Label(basic_frame, text="Resume Path:").pack()
        self.resume_entry = ttk.Entry(basic_frame)
        self.resume_entry.pack(fill=tk.X)

        # Remote/Location Toggle
        self.remote_var = tk.BooleanVar(value=True)
        self.remote_checkbox = ttk.Checkbutton(
            basic_frame,
            text="Remote Only",
            variable=self.remote_var,
            command=self.toggle_location
        )
        self.remote_checkbox.pack()

        # Location Entry (initially hidden)
        self.location_frame = ttk.Frame(basic_frame)
        ttk.Label(self.location_frame, text="Location:").pack(side=tk.LEFT)
        self.location_entry = ttk.Entry(self.location_frame)
        self.location_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        if not self.remote_var.get():
            self.location_frame.pack(fill=tk.X, pady=5)

    def create_advanced_settings(self):
        # Advanced settings button
        self.advanced_var = tk.BooleanVar()
        self.advanced_button = ttk.Checkbutton(
            self.main_frame,
            text="Advanced Settings",
            variable=self.advanced_var,
            command=self.toggle_advanced_settings
        )
        self.advanced_button.pack(pady=5)

        # Advanced settings frame
        self.advanced_frame = ttk.LabelFrame(self.main_frame, text="Advanced Settings", padding="5")
        
        # Distance
        distance_frame = ttk.Frame(self.advanced_frame)
        distance_frame.pack(fill=tk.X, pady=5)
        ttk.Label(distance_frame, text="Distance (miles):").pack(side=tk.LEFT)
        self.distance_entry = ttk.Entry(distance_frame, width=10)
        self.distance_entry.pack(side=tk.LEFT, padx=5)

        # Experience Level
        exp_frame = ttk.LabelFrame(self.advanced_frame, text="Experience Level", padding="5")
        exp_frame.pack(fill=tk.X, pady=5)
        
        self.exp_vars = {
            "Entry Level": tk.BooleanVar(),
            "Mid Level": tk.BooleanVar(),
            "Senior Level": tk.BooleanVar()
        }
        
        for level, var in self.exp_vars.items():
            ttk.Checkbutton(exp_frame, text=level, variable=var).pack(anchor=tk.W)

        # Education Level
        edu_frame = ttk.LabelFrame(self.advanced_frame, text="Education Level", padding="5")
        edu_frame.pack(fill=tk.X, pady=5)
        
        self.edu_var = tk.StringVar(value="All Education Levels")
        education_levels = ["All Education Levels", "Bachelor's Degree", "Master's Degree"]
        
        for level in education_levels:
            ttk.Radiobutton(edu_frame, text=level, variable=self.edu_var, value=level).pack(anchor=tk.W)

        # Website Selection
        self.create_website_selection()

        # Rating Settings
        self.create_rating_settings()

        # Initially hide advanced settings
        self.advanced_frame.pack_forget()

    def create_website_selection(self):
        # Website selection frame
        website_frame = ttk.LabelFrame(self.advanced_frame, text="Select Websites", padding="5")
        website_frame.pack(fill=tk.X, padx=5, pady=5)

        self.website_vars = {
            "Indeed": tk.BooleanVar(value=True),
            "LinkedIn": tk.BooleanVar(value=False)
        }

        for site, var in self.website_vars.items():
            ttk.Checkbutton(website_frame, text=site, variable=var).pack(anchor=tk.W)

    def create_rating_settings(self):
        # Rating Settings Frame
        self.rating_frame = ttk.LabelFrame(self.advanced_frame, text="Rating Criteria", padding="5")
        
        # Default Rating Info
        ttk.Label(self.rating_frame, text="Default Rating System:").pack(anchor=tk.W, pady=(5,0))
        ttk.Label(self.rating_frame, text="Rating 1: Salary in top 10% of range").pack(anchor=tk.W)
        ttk.Label(self.rating_frame, text="Rating 2: Salary within specified range").pack(anchor=tk.W)
        ttk.Label(self.rating_frame, text="Rating 3: Salary in bottom 10% of range").pack(anchor=tk.W)
        
        ttk.Separator(self.rating_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        # Custom Percentages
        percentages_frame = ttk.Frame(self.rating_frame)
        percentages_frame.pack(fill=tk.X, pady=5)
        
        # Top Percentage
        top_frame = ttk.Frame(percentages_frame)
        top_frame.pack(fill=tk.X, pady=2)
        ttk.Label(top_frame, text="Top Percentage for Rating 1:").pack(side=tk.LEFT)
        self.top_percent_entry = ttk.Entry(top_frame, width=5)
        self.top_percent_entry.pack(side=tk.LEFT, padx=5)
        self.top_percent_entry.insert(0, "10")
        ttk.Label(top_frame, text="%").pack(side=tk.LEFT)
        
        # Bottom Percentage
        bottom_frame = ttk.Frame(percentages_frame)
        bottom_frame.pack(fill=tk.X, pady=2)
        ttk.Label(bottom_frame, text="Bottom Percentage for Rating 3:").pack(side=tk.LEFT)
        self.bottom_percent_entry = ttk.Entry(bottom_frame, width=5)
        self.bottom_percent_entry.pack(side=tk.LEFT, padx=5)
        self.bottom_percent_entry.insert(0, "10")
        ttk.Label(bottom_frame, text="%").pack(side=tk.LEFT)

        # Experience Requirement
        self.experience_req_var = tk.BooleanVar(value=True)  
        self.experience_req_checkbox = ttk.Checkbutton(
            self.rating_frame,
            text="Must Match Selected Experience Level for High Rating",
            variable=self.experience_req_var
        )
        self.experience_req_checkbox.pack(pady=5)

        self.rating_frame.pack(fill=tk.X, padx=5, pady=5)

    def toggle_advanced_settings(self):
        if self.advanced_var.get():
            self.advanced_frame.pack(fill=tk.X, padx=5, pady=5)
        else:
            self.advanced_frame.pack_forget()

    def toggle_location(self):
        if self.remote_var.get():
            self.location_frame.pack_forget()
            self.location_entry.config(state='disabled')
            self.location_entry.delete(0, tk.END)
        else:
            self.location_frame.pack(fill=tk.X, pady=5)
            self.location_entry.config(state='normal')

    def start_scraper(self):
        try:
            # Get basic settings
            keywords = [k.strip() for k in self.keywords_entry.get().split(",")]
            job_title = self.job_title_entry.get().strip()
            salary_range = (
                int(self.salary_min_entry.get() or 0),
                int(self.salary_max_entry.get() or 0)
            )
            resume = self.resume_entry.get().strip()
            remote_only = self.remote_var.get()
            location = None if remote_only else self.location_entry.get().strip()
            include_no_salary = self.include_no_salary_var.get()

            # Get advanced settings
            distance = int(self.distance_entry.get()) if self.distance_entry.get() else None
            experience_levels = [
                level for level, var in self.exp_vars.items()
                if var.get()
            ]
            education_level = (
                None if self.edu_var.get() == "All Education Levels"
                else self.edu_var.get()
            )

            # Get selected websites
            selected_websites = [site for site, var in self.website_vars.items() if var.get()]

            # Get rating settings
            top_percent = float(self.top_percent_entry.get() or 10)
            bottom_percent = float(self.bottom_percent_entry.get() or 10)
            require_experience = self.experience_req_var.get()

            # Check if LinkedIn credentials are provided if LinkedIn is selected
            if "LinkedIn" in selected_websites:
                if not self.linkedin_email or not self.linkedin_password:
                    messagebox.showerror("Error", "Please enter LinkedIn credentials in Settings > LinkedIn Login")
                    return
                if not self.login_to_linkedin():
                    return

            # Initialize scraper parameters
            self.scraper.keywords = keywords
            self.scraper.job_title = job_title
            self.scraper.salary_range = salary_range
            self.scraper.resume = resume
            self.scraper.remote_only = self.remote_var.get()
            self.scraper.location = location
            self.scraper.distance = distance
            self.scraper.experience_levels = experience_levels
            self.scraper.education_level = education_level
            self.scraper.include_no_salary = self.include_no_salary_var.get()
            self.scraper.top_percent = top_percent
            self.scraper.bottom_percent = bottom_percent
            self.scraper.require_experience = self.experience_req_var.get()
            
            # Share the driver instance if we're already logged in to LinkedIn
            if self.driver and "LinkedIn" in selected_websites:
                self.scraper.driver = self.driver
                self.scraper.wait = self.wait
            
            self.scraper.scrape_jobs(selected_websites)
            messagebox.showinfo("Success", "Job scraping completed successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.wait = None

    def get_job_summary(self, job):
        """Format job details for display"""
        details = []
        
        if job.get('title'):
            details.append(f"<div class='job-title'>{job['title']}</div>")
        
        if job.get('company'):
            details.append(f"<div class='company'>{job['company']}</div>")
        
        if job.get('salary_text'):
            details.append(f"<div class='salary'>{job['salary_text']}</div>")
        
        if job.get('summary'):
            # Clean and format the summary text
            summary = job['summary'].replace('\n', ' ').strip()
            # Replace <br> tags with non-breaking space
            summary = summary.replace('<br>', '&nbsp;')
            details.append(f"<div class='summary'>{summary}</div>")
        
        if job.get('rating'):
            rating_text = {
                1: "High Match",
                2: "Medium Match",
                3: "Low Match"
            }.get(job['rating'], "Unknown")
            details.append(f"<div class='rating'>Rating: {rating_text}</div>")
        
        # Join with newlines and spaces between tags
        return "\n\n".join(details)

    def open_linkedin_login_window(self):
        # Create a new window for LinkedIn login
        login_window = tk.Toplevel(self.master)
        login_window.title("LinkedIn Login")

        # Email Entry
        ttk.Label(login_window, text="Email:").pack(pady=5)
        email_entry = ttk.Entry(login_window)
        email_entry.pack(fill=tk.X, padx=10)
        email_entry.insert(0, self.linkedin_email)  # Pre-fill saved email

        # Password Entry
        ttk.Label(login_window, text="Password:").pack(pady=5)
        password_entry = ttk.Entry(login_window, show="*")
        password_entry.pack(fill=tk.X, padx=10)

        # Save Button
        def save_credentials():
            self.linkedin_email = email_entry.get()
            self.linkedin_password = password_entry.get()
            self.save_settings()
            login_window.destroy()

        ttk.Button(login_window, text="Save", command=save_credentials).pack(pady=10)

    def setup_driver(self):
        """Set up undetected ChromeDriver"""
        try:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None
                self.wait = None

            options = uc.ChromeOptions()
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-extensions')
            
            self.driver = uc.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, 10)
            self.scraper.driver = self.driver
            self.scraper.wait = self.wait
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

    def login_to_linkedin(self):
        try:
            # Set up the driver if not already set up
            if not self.driver or not self.wait:
                self.setup_driver()
            
            # Load the login page
            if not self.handle_page_load("https://www.linkedin.com/login"):
                raise Exception("Failed to load LinkedIn login page")
            
            try:
                # Wait for and find login elements
                email_input = self.wait.until(EC.presence_of_element_located((By.ID, "username")))
                password_input = self.wait.until(EC.presence_of_element_located((By.ID, "password")))
                
                # Enter credentials
                email_input.send_keys(self.linkedin_email)
                password_input.send_keys(self.linkedin_password)
                password_input.submit()
                
                # Wait for login to complete
                self.wait.until(EC.url_changes("https://www.linkedin.com/login"))
                time.sleep(2)  # Additional wait for page to stabilize
                
                return True
            except (TimeoutException, NoSuchElementException) as e:
                raise Exception(f"Login elements not found: {str(e)}")
                
        except Exception as e:
            messagebox.showerror("Login Error", f"Failed to log in to LinkedIn: {str(e)}")
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.wait = None
            return False

if __name__ == '__main__':
    root = tk.Tk()
    gui = JobScraperGUI(root)
    root.mainloop()
