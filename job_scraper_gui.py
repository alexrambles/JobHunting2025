import tkinter as tk
from tkinter import messagebox
from job_scraper import JobScraper

class JobScraperGUI:
    def __init__(self, master):
        self.master = master
        master.title("Job Scraper Configuration")

        # Keywords
        self.keywords_label = tk.Label(master, text="Keywords (comma separated):")
        self.keywords_label.pack()
        self.keywords_entry = tk.Entry(master)
        self.keywords_entry.pack()

        # Job Title
        self.job_title_label = tk.Label(master, text="Job Title:")
        self.job_title_label.pack()
        self.job_title_entry = tk.Entry(master)
        self.job_title_entry.pack()

        # Salary Range
        self.salary_label = tk.Label(master, text="Salary Range (min, max):")
        self.salary_label.pack()
        self.salary_min_entry = tk.Entry(master)
        self.salary_min_entry.pack()
        self.salary_max_entry = tk.Entry(master)
        self.salary_max_entry.pack()

        # Resume
        self.resume_label = tk.Label(master, text="Resume File Path:")
        self.resume_label.pack()
        self.resume_entry = tk.Entry(master)
        self.resume_entry.pack()

        # Remote Only and Location Frame
        self.location_frame = tk.Frame(master)
        self.location_frame.pack(pady=10)

        # Remote Only
        self.remote_var = tk.BooleanVar()
        self.remote_checkbox = tk.Checkbutton(
            self.location_frame, 
            text="Remote Only", 
            variable=self.remote_var,
            command=self.toggle_location
        )
        self.remote_checkbox.pack(side=tk.LEFT, padx=5)

        # Location
        self.location_label = tk.Label(self.location_frame, text="Location:")
        self.location_label.pack(side=tk.LEFT, padx=5)
        self.location_entry = tk.Entry(self.location_frame)
        self.location_entry.pack(side=tk.LEFT, padx=5)
        
        # Set initial state
        self.remote_var.set(True)  # Default to remote
        self.toggle_location()  # Initial toggle

        # Submit Button
        self.submit_button = tk.Button(master, text="Start Scraper", command=self.start_scraper)
        self.submit_button.pack(pady=10)

    def toggle_location(self):
        if self.remote_var.get():
            self.location_entry.config(state='disabled')
            self.location_entry.delete(0, tk.END)
        else:
            self.location_entry.config(state='normal')

    def start_scraper(self):
        try:
            keywords = [k.strip() for k in self.keywords_entry.get().split(",")]
            job_title = self.job_title_entry.get().strip()
            salary_range = (int(self.salary_min_entry.get()), int(self.salary_max_entry.get()))
            resume = self.resume_entry.get().strip()
            remote_only = self.remote_var.get()
            location = None if remote_only else self.location_entry.get().strip()

            # Create JobScraper instance and start scraping
            scraper = JobScraper(
                keywords=keywords, 
                job_title=job_title, 
                salary_range=salary_range, 
                resume=resume, 
                remote_only=remote_only,
                location=location
            )
            scraper.scrape_indeed()
            messagebox.showinfo("Success", "Job scraping completed successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

if __name__ == '__main__':
    root = tk.Tk()
    gui = JobScraperGUI(root)
    root.mainloop()
