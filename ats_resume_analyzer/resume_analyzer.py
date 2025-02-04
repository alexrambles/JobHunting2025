import os
import re
import docx
import PyPDF2
from pathlib import Path
from typing import Dict, List, Tuple
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

class ATSResumeAnalyzer:
    def __init__(self):
        """Initialize the ATS Resume Analyzer with necessary models and data."""
        # Download required NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('punkt')
            nltk.download('stopwords')
        
        # Common ATS keywords and their categories
        self.ats_keywords = {
            'technical_skills': ['python', 'java', 'sql', 'aws', 'docker', 'kubernetes', 'javascript',
                               'react', 'node.js', 'html', 'css', 'git', 'agile', 'scrum'],
            'soft_skills': ['leadership', 'communication', 'teamwork', 'problem-solving',
                           'analytical', 'organization', 'time management', 'collaboration'],
            'education': ['bachelor', 'master', 'phd', 'degree', 'certification', 'diploma'],
            'experience': ['years', 'developed', 'managed', 'implemented', 'led', 'created',
                         'designed', 'improved', 'increased', 'reduced', 'supervised']
        }
        
        # ATS formatting rules
        self.formatting_rules = {
            'min_words': 300,
            'max_words': 700,
            'preferred_fonts': ['Arial', 'Calibri', 'Times New Roman'],
            'forbidden_elements': ['text boxes', 'tables', 'images', 'headers', 'footers']
        }

    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text content from PDF files."""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                return text
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return ""

    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text content from DOCX files."""
        try:
            doc = docx.Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except Exception as e:
            print(f"Error extracting text from DOCX: {e}")
            return ""

    def extract_text(self, file_path: str) -> str:
        """Extract text from PDF or DOCX files."""
        file_extension = Path(file_path).suffix.lower()
        
        if file_extension == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif file_extension == '.docx':
            return self.extract_text_from_docx(file_path)
        else:
            print(f"Unsupported file format: {file_extension}")
            print("Please provide a PDF or DOCX file.")
            return ""

    def preprocess_text(self, text: str) -> str:
        """Preprocess text by removing special characters and converting to lowercase."""
        # Convert to lowercase
        text = text.lower()
        # Remove special characters and extra whitespace
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def analyze_keywords(self, text: str) -> Dict[str, List[str]]:
        """Analyze the presence of important keywords in the resume."""
        text = self.preprocess_text(text)
        found_keywords = {category: [] for category in self.ats_keywords}
        
        # Tokenize the text
        words = word_tokenize(text)
        # Remove stopwords
        stop_words = set(stopwords.words('english'))
        words = [word for word in words if word not in stop_words]
        
        # Create a set of words for faster lookup
        word_set = set(words)
        
        for category, keywords in self.ats_keywords.items():
            for keyword in keywords:
                # Check for both single words and phrases
                if ' ' in keyword:
                    if keyword in text:
                        found_keywords[category].append(keyword)
                elif keyword in word_set:
                    found_keywords[category].append(keyword)
        
        return found_keywords

    def check_formatting(self, text: str) -> Dict[str, bool]:
        """Check if the resume follows ATS formatting guidelines."""
        words = word_tokenize(text)
        word_count = len(words)
        
        formatting_score = {
            'appropriate_length': self.formatting_rules['min_words'] <= word_count <= self.formatting_rules['max_words'],
            'no_special_characters': not bool(re.findall(r'[^\x00-\x7F]+', text)),
            'proper_sections': all(section in text.lower() for section in ['experience', 'education', 'skills'])
        }
        
        return formatting_score

    def calculate_score(self, keyword_analysis: Dict[str, List[str]], formatting_check: Dict[str, bool]) -> Tuple[float, Dict[str, str]]:
        """Calculate overall ATS compatibility score and provide recommendations."""
        score = 0
        recommendations = {}
        
        # Score keywords (60% of total score)
        max_keywords = sum(len(keywords) for keywords in self.ats_keywords.values())
        found_keywords = sum(len(keywords) for keywords in keyword_analysis.values())
        keyword_score = (found_keywords / max_keywords) * 60
        score += keyword_score
        
        # Score formatting (40% of total score)
        format_score = (sum(1 for check in formatting_check.values() if check) / len(formatting_check)) * 40
        score += format_score
        
        # Generate recommendations
        if keyword_score < 45:
            recommendations['keywords'] = "Add more relevant industry keywords and skills"
        if not formatting_check['appropriate_length']:
            recommendations['length'] = "Adjust resume length to be between 300-700 words"
        if not formatting_check['no_special_characters']:
            recommendations['characters'] = "Remove special characters and symbols"
        if not formatting_check['proper_sections']:
            recommendations['sections'] = "Ensure all key sections (Experience, Education, Skills) are clearly labeled"
            
        return score, recommendations

    def analyze_resume(self, file_path: str) -> Dict:
        """Main method to analyze a resume and provide comprehensive feedback."""
        # Extract text from resume
        text = self.extract_text(file_path)
        if not text:
            return {"error": "Could not extract text from resume"}
        
        # Perform analysis
        keyword_analysis = self.analyze_keywords(text)
        formatting_check = self.check_formatting(text)
        score, recommendations = self.calculate_score(keyword_analysis, formatting_check)
        
        return {
            "ats_score": round(score, 2),
            "keyword_analysis": keyword_analysis,
            "formatting_check": formatting_check,
            "recommendations": recommendations
        }

def main():
    """Example usage of the ATS Resume Analyzer."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python resume_analyzer.py <path_to_resume>")
        sys.exit(1)
        
    resume_path = sys.argv[1]
    analyzer = ATSResumeAnalyzer()
    
    if os.path.exists(resume_path):
        results = analyzer.analyze_resume(resume_path)
        
        print("\n=== ATS Resume Analysis Results ===")
        print(f"\nATS Compatibility Score: {results['ats_score']}%")
        
        print("\nKeyword Analysis:")
        for category, keywords in results['keyword_analysis'].items():
            print(f"{category.replace('_', ' ').title()}: {', '.join(keywords) if keywords else 'None found'}")
        
        print("\nFormatting Check:")
        for check, passed in results['formatting_check'].items():
            print(f"{check.replace('_', ' ').title()}: {'[PASS]' if passed else '[FAIL]'}")
        
        print("\nRecommendations:")
        if results['recommendations']:
            for category, recommendation in results['recommendations'].items():
                print(f"- {recommendation}")
        else:
            print("- Your resume appears to be well-optimized for ATS!")
    else:
        print("Error: File not found. Please provide a valid file path.")

if __name__ == "__main__":
    main()
