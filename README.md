# Job Scraper

## Overview
This project is a job scraper designed to search for job listings on Indeed, focusing on remote positions and allowing users to specify various search parameters.

## Features
- **Basic Settings**:
  - Keywords (comma-separated)
  - Job Title
  - Salary Range (minimum and maximum)
  - Resume File Path
  - Remote Only toggle with location input

- **Advanced Settings**:
  - Distance in miles from the specified location
  - Experience Levels (Entry Level, Mid Level, Senior Level)
  - Education Requirements (All Education Levels, Bachelor's Degree, Master's Degree)

- **Pagination Support**: Fetches multiple pages of job listings (up to 3 pages, approximately 45 jobs).
- **Results Saving**: Saves job results to the user's Documents folder with a date-based filename (e.g., `job_results_YYYY-MM-DD.csv`).

## Usage Instructions
### Setup
1. Clone the repository or download the project files.
2. Install the required dependencies:
   ```bash
   pip install pandas beautifulsoup4 undetected-chromedriver fake-useragent
   ```

### Running the Script
To run the GUI version of the job scraper:
```bash
python job_scraper_gui.py
```

To run the scraper directly:
```bash
python job_scraper.py
```

## Functions
- **`JobScraper` Class**: Handles the job scraping logic.
  - **`__init__`**: Initializes the scraper with parameters such as keywords, job title, salary range, resume, remote settings, location, distance, experience levels, and education level.
  - **`scrape_indeed`**: Main method to perform the scraping from Indeed, handling pagination and filtering based on user input.
  - **`save_results`**: Saves the scraped job listings to a CSV file in the user's Documents folder.
  - **`extract_job_details`**: Extracts detailed job information from a job listing page.
  - **`extract_salary`**: Parses and returns the salary information from job listings.
  - **`rate_job`**: Rates the job based on salary and other criteria.

## License
This project is licensed under the GPL GNU General Public License v3.
