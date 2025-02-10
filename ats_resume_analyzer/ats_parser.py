import os
import re
from typing import Dict, Any
from pdfminer.high_level import extract_text as pdf_extract_text
import docx2txt
from io import StringIO
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from skills_library import (
    TECHNICAL_SKILLS, SOFT_SKILLS, EXPERIENCE_KEYWORDS,
    EDUCATION_KEYWORDS, FORMATTING_GUIDELINES
)

class ATSParser:
    def __init__(self):
        """Initialize the ATS Parser with necessary NLTK data."""
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('punkt')
            nltk.download('stopwords')
        self.stop_words = set(stopwords.words('english'))

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using pdfminer.six for accurate ATS simulation."""
        try:
            return pdf_extract_text(pdf_path)
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return ""

    def extract_text_from_docx(self, docx_path: str) -> str:
        """Extract text from DOCX using docx2txt for accurate ATS simulation."""
        try:
            return docx2txt.process(docx_path)
        except Exception as e:
            print(f"Error extracting text from DOCX: {e}")
            return ""

    def extract_text(self, file_path: str) -> str:
        """Extract text from resume file based on its format."""
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif file_extension == '.docx':
            return self.extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")

    def parse_resume(self, file_path: str) -> Dict[str, Any]:
        """Parse resume using NLP techniques for comprehensive analysis."""
        # Get raw text
        raw_text = self.extract_text(file_path)
        
        # Tokenize text
        sentences = sent_tokenize(raw_text)
        words = word_tokenize(raw_text.lower())
        words = [w for w in words if w not in self.stop_words and w.isalnum()]
        
        # Parse and analyze
        parsed_data = {
            'raw_text': raw_text,
            'sections': self._identify_sections(raw_text),
            'skills': self._extract_skills(raw_text, words),
            'formatting': self._analyze_formatting(raw_text, sentences),
            'readability': self._analyze_readability(sentences, words)
        }
        
        return parsed_data

    def _identify_sections(self, text: str) -> Dict[str, bool]:
        """Identify presence of standard resume sections."""
        text_lower = text.lower()
        sections = {}
        section_locations = {}
        
        for section in FORMATTING_GUIDELINES['section_headers']:
            section_lower = section.lower()
            if section_lower in text_lower:
                sections[section_lower] = True
                # Find the location of the section
                idx = text_lower.find(section_lower)
                section_locations[section_lower] = idx
            else:
                sections[section_lower] = False
        
        return {
            'present': sections,
            'locations': section_locations
        }

    def _extract_skills(self, text: str, words: list) -> Dict[str, list]:
        """Extract skills using keyword matching and NLP."""
        text_lower = text.lower()
        found_skills = {
            'technical': [],
            'soft': [],
            'other': [],
            'locations': {}  # Store where skills are found
        }
        
        # Check technical skills
        for category, skills in TECHNICAL_SKILLS.items():
            for skill in skills:
                skill_lower = skill.lower()
                if skill_lower in text_lower:
                    found_skills['technical'].append(skill)
                    # Find all occurrences of the skill
                    start = 0
                    skill_locations = []
                    while True:
                        idx = text_lower.find(skill_lower, start)
                        if idx == -1:
                            break
                        skill_locations.append(idx)
                        start = idx + 1
                    found_skills['locations'][skill] = skill_locations
        
        # Check soft skills
        for category, skills in SOFT_SKILLS.items():
            for skill in skills:
                skill_lower = skill.lower()
                if skill_lower in text_lower:
                    found_skills['soft'].append(skill)
                    # Find all occurrences of the skill
                    start = 0
                    skill_locations = []
                    while True:
                        idx = text_lower.find(skill_lower, start)
                        if idx == -1:
                            break
                        skill_locations.append(idx)
                        start = idx + 1
                    found_skills['locations'][skill] = skill_locations
        
        return found_skills

    def _analyze_formatting(self, text: str, sentences: list) -> Dict[str, Any]:
        """Analyze resume formatting as typically processed by ATS."""
        lines = text.split('\n')
        
        # Analyze special characters
        special_chars = {}
        for i, char in enumerate(text):
            if not char.isalnum() and not char.isspace():
                context = text[max(0, i-20):min(len(text), i+20)]
                if char not in special_chars:
                    special_chars[char] = []
                special_chars[char].append({
                    'position': i,
                    'context': context.replace('\n', ' ').strip()
                })
        
        # Detect table-like structures
        table_indicators = []
        for i, line in enumerate(lines):
            if '\t' in line or '|' in line or line.count('  ') > 2:
                table_indicators.append({
                    'line_number': i + 1,
                    'content': line.strip(),
                    'type': 'tab_separated' if '\t' in line else 'pipe_separated' if '|' in line else 'space_separated'
                })
        
        # Detect smart quotes and other problematic characters
        smart_quotes = []
        problematic_quotes = ['"', '"', ''', ''', "'"]
        for i, char in enumerate(text):
            if char in problematic_quotes:
                context = text[max(0, i-20):min(len(text), i+20)]
                smart_quotes.append({
                    'position': i,
                    'char': char,
                    'context': context.replace('\n', ' ').strip()
                })
        
        return {
            'total_lines': len(lines),
            'empty_lines': len([l for l in lines if not l.strip()]),
            'avg_line_length': sum(len(l) for l in lines) / len(lines) if lines else 0,
            'special_chars_count': len([c for c in text if not c.isalnum() and not c.isspace()]),
            'special_chars_details': special_chars,
            'has_tables': bool(table_indicators),
            'table_indicators': table_indicators,
            'bullet_points': text.count('•') + text.count('·') + text.count('-'),
            'smart_quotes': smart_quotes,
            'sections': self._identify_sections(text)
        }

    def _analyze_readability(self, sentences: list, words: list) -> Dict[str, float]:
        """Analyze text readability as processed by ATS."""
        if not sentences or not words:
            return {'score': 0.0}
        
        # Analyze sentence length
        sentence_analysis = []
        for sentence in sentences:
            words_in_sentence = len(word_tokenize(sentence))
            if words_in_sentence > 20:  # Flag long sentences
                sentence_analysis.append({
                    'length': words_in_sentence,
                    'text': sentence.strip(),
                    'issue': 'Long sentence'
                })
        
        avg_word_length = sum(len(word) for word in words) / len(words)
        avg_sentence_length = len(words) / len(sentences)
        
        # Simplified readability score (0-100)
        readability_score = 100 - (avg_word_length * 3 + avg_sentence_length * 0.5)
        readability_score = max(0, min(100, readability_score))
        
        return {
            'score': readability_score,
            'avg_word_length': avg_word_length,
            'avg_sentence_length': avg_sentence_length,
            'unique_words': len(set(words)),
            'long_sentences': sentence_analysis
        }

    def get_ats_recommendations(self, parsed_data: Dict[str, Any]) -> Dict[str, list]:
        """Generate ATS-specific recommendations based on parsing results."""
        recommendations = {
            'critical': [],
            'important': [],
            'suggestions': []
        }
        
        # Check formatting
        formatting = parsed_data['formatting']
        if formatting['special_chars_count'] > 50:
            recommendations['critical'].append(
                "High number of special characters detected. Remove special characters and symbols."
            )
        if formatting['has_tables']:
            recommendations['critical'].append(
                "Tables detected. Convert tabular data to bullet points."
            )
        
        # Check sections
        missing_sections = [
            section for section, present in parsed_data['sections']['present'].items()
            if not present and section in ['experience', 'education', 'skills']
        ]
        if missing_sections:
            recommendations['critical'].append(
                f"Missing key sections: {', '.join(missing_sections)}"
            )
        
        # Check skills
        skills = parsed_data['skills']
        if len(skills['technical']) < 5:
            recommendations['important'].append(
                "Add more technical skills relevant to your field"
            )
        if len(skills['soft']) < 3:
            recommendations['important'].append(
                "Include more soft skills and competencies"
            )
        
        # Check readability
        readability = parsed_data['readability']
        if readability['score'] < 60:
            recommendations['important'].append(
                "Improve readability: use shorter sentences and simpler words"
            )
        if readability['avg_sentence_length'] > 25:
            recommendations['suggestions'].append(
                "Consider breaking down long sentences for better readability"
            )
        
        return recommendations
