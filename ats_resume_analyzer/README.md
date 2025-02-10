# ATS Resume Analyzer

This tool analyzes resumes for ATS (Applicant Tracking System) compatibility and provides recommendations for improvement.

## Features

- Analyzes resume content for ATS compatibility
- Supports PDF and DOCX file formats
- Checks for important keywords and skills
- Evaluates formatting and structure
- Provides detailed recommendations for improvement
- Generates an overall ATS compatibility score

## Installation

1. Clone this repository
2. Install the required dependencies:
```bash
pip install -r requirements.txt
```
3. Download the required spaCy model:
```bash
python -m spacy download en_core_web_sm
```

## Usage

Run the script from the command line:
```bash
python resume_analyzer.py
```

When prompted, enter the path to your resume file (PDF or DOCX format).

## Analysis Components

The analyzer evaluates several key aspects:

1. **Keyword Analysis**
   - Technical Skills
   - Soft Skills
   - Education
   - Experience

2. **Formatting Check**
   - Document length
   - Special characters
   - Section headers
   - Overall structure

3. **Recommendations**
   - Keyword optimization
   - Formatting improvements
   - Structure suggestions

## Output

The tool provides:
- Overall ATS compatibility score
- Detailed keyword analysis by category
- Formatting check results
- Specific recommendations for improvement

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.
