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

        # Rating Settings
        self.create_rating_settings()

        # Submit Button
        self.submit_button = ttk.Button(self.main_frame, text="Start Scraper", command=self.start_scraper)
        self.submit_button.pack(pady=10)

    def create_basic_settings(self):
        # Basic settings frame
        basic_frame = ttk.LabelFrame(self.main_frame, text="Basic Settings", padding="5")
        basic_frame.pack(fill=tk.X, padx=5, pady=5)

        # Keywords
        ttk.Label(basic_frame, text="Keywords (comma separated):").pack()
        self.keywords_entry = ttk.Entry(basic_frame)
        self.keywords_entry.pack(fill=tk.X)

        # Job Title
        ttk.Label(basic_frame, text="Job Title:").pack()
        self.job_title_entry = ttk.Entry(basic_frame)
        self.job_title_entry.pack(fill=tk.X)

        # Salary Range
        salary_frame = ttk.Frame(basic_frame)
        salary_frame.pack(fill=tk.X)
        ttk.Label(salary_frame, text="Salary Range:").pack()
        self.salary_min_entry = ttk.Entry(salary_frame, width=15)
        self.salary_min_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(salary_frame, text="to").pack(side=tk.LEFT)
        self.salary_max_entry = ttk.Entry(salary_frame, width=15)
        self.salary_max_entry.pack(side=tk.LEFT, padx=5)

        # Resume
        ttk.Label(basic_frame, text="Resume File Path:").pack()
        self.resume_entry = ttk.Entry(basic_frame)
        self.resume_entry.pack(fill=tk.X)

        # Location Settings
        location_frame = ttk.Frame(basic_frame)
        location_frame.pack(fill=tk.X, pady=5)
        
        # Remote Only
        self.remote_var = tk.BooleanVar(value=True)
        self.remote_checkbox = ttk.Checkbutton(
            location_frame, 
            text="Remote Only", 
            variable=self.remote_var,
            command=self.toggle_location
        )
        self.remote_checkbox.pack(side=tk.LEFT)

        # Location
        self.location_entry = ttk.Entry(location_frame)
        self.location_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.toggle_location()  # Initial state

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

        # Initially hide advanced settings
        self.advanced_frame.pack_forget()

    def create_rating_settings(self):
        # Rating settings frame
        rating_frame = ttk.LabelFrame(self.main_frame, text="Rating Settings", padding="5")
        rating_frame.pack(fill=tk.X, padx=5, pady=5)

        # Salary Threshold
        ttk.Label(rating_frame, text="Salary Threshold for High Rating:").pack()
        self.salary_threshold_entry = ttk.Entry(rating_frame)
        self.salary_threshold_entry.pack(fill=tk.X)

        # Experience Requirement
        self.experience_req_var = tk.BooleanVar()
        self.experience_req_checkbox = ttk.Checkbutton(
            rating_frame,
            text="Require Specific Experience Level for High Rating",
            variable=self.experience_req_var
        )
        self.experience_req_checkbox.pack()

        # Add other rating criteria as needed

    def toggle_advanced_settings(self):
        if self.advanced_var.get():
            self.advanced_frame.pack(fill=tk.X, padx=5, pady=5)
        else:
            self.advanced_frame.pack_forget()

    def toggle_location(self):
        if self.remote_var.get():
            self.location_entry.config(state='disabled')
            self.location_entry.delete(0, tk.END)
        else:
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
            salary_threshold = int(self.salary_threshold_entry.get() or 0)
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
                salary_threshold=salary_threshold,
                require_experience=require_experience
            )
            scraper.scrape_indeed()
            messagebox.showinfo("Success", "Job scraping completed successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

if __name__ == '__main__':
    root = tk.Tk()
    gui = JobScraperGUI(root)
    root.mainloop()
