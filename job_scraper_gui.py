import tkinter as tk
from tkinter import ttk, messagebox
from job_scraper import JobScraper

class JobScraperGUI:
    def __init__(self, master):
        self.master = master
        master.title("Job Scraper Configuration")
        
        # Create main frame
        self.main_frame = ttk.Frame(master, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Basic Settings
        self.create_basic_settings()
        
        # Advanced Settings
        self.create_advanced_settings()

        # Submit Button
        self.submit_button = ttk.Button(self.main_frame, text="Start Scraper", command=self.start_scraper)
        self.submit_button.pack(pady=10)

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

        # Rating Settings
        self.create_rating_settings()

        # Initially hide advanced settings
        self.advanced_frame.pack_forget()

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

            # Get rating settings
            top_percent = float(self.top_percent_entry.get() or 10)
            bottom_percent = float(self.bottom_percent_entry.get() or 10)
            require_experience = self.experience_req_var.get()

            # Create JobScraper instance and start scraping
            scraper = JobScraper(
                keywords=keywords,
                job_title=job_title,
                salary_range=salary_range,
                resume=resume,
                remote_only=remote_only,
                location=location,
                distance=distance,
                experience_levels=experience_levels,
                education_level=education_level,
                include_no_salary=include_no_salary,
                top_percent=top_percent,
                bottom_percent=bottom_percent,
                require_experience=require_experience
            )
            scraper.scrape_indeed()
            messagebox.showinfo("Success", "Job scraping completed successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

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

if __name__ == '__main__':
    root = tk.Tk()
    gui = JobScraperGUI(root)
    root.mainloop()
