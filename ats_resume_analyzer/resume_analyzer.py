import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from ats_parser import ATSParser
from skills_library import (
    TECHNICAL_SKILLS, SOFT_SKILLS, EXPERIENCE_KEYWORDS,
    EDUCATION_KEYWORDS, FORMATTING_GUIDELINES
)

class ATSResumeAnalyzer:
    def __init__(self):
        """Initialize the ATS Resume Analyzer with ATS parser."""
        self.parser = ATSParser()

    def analyze_resume(self, file_path: str) -> Dict[str, Any]:
        """Analyze resume using ATS simulation techniques."""
        # Parse resume using multiple ATS simulation techniques
        parsed_data = self.parser.parse_resume(file_path)
        
        # Calculate ATS compatibility score
        ats_score = self._calculate_ats_score(parsed_data)
        
        # Get recommendations
        recommendations = self.parser.get_ats_recommendations(parsed_data)
        
        # Combine results
        analysis_results = {
            'ats_score': ats_score,
            'parsed_data': parsed_data,
            'recommendations': recommendations
        }
        
        # Save detailed report
        self._save_detailed_report(analysis_results)
        
        return analysis_results

    def _calculate_ats_score(self, parsed_data: Dict[str, Any]) -> float:
        """Calculate ATS compatibility score based on parsed data."""
        score = 0.0
        
        # Skills score (30%)
        max_skills = 20  # Expected number of relevant skills
        found_skills = len(parsed_data['skills']['technical']) + len(parsed_data['skills']['soft'])
        skills_score = min(found_skills / max_skills * 30, 30)
        score += skills_score
        
        # Formatting score (25%)
        formatting = parsed_data['formatting']
        formatting_score = 25
        if formatting['special_chars_count'] > 50:
            formatting_score -= 10
        if formatting['has_tables']:
            formatting_score -= 10
        if formatting['empty_lines'] / formatting['total_lines'] > 0.3:
            formatting_score -= 5
        score += max(0, formatting_score)
        
        # Section completeness score (25%)
        required_sections = ['experience', 'education', 'skills']
        section_score = sum(1 for section in required_sections 
                          if parsed_data['formatting']['sections']['present'].get(section, False)) / len(required_sections) * 25
        score += section_score
        
        # Readability score (20%)
        readability_score = parsed_data['readability']['score'] * 0.2
        score += readability_score
        
        return round(score, 2)

    def _save_detailed_report(self, analysis_results: Dict[str, Any]) -> None:
        """Save detailed analysis report to user's documents folder."""
        # Get user's documents folder
        docs_folder = str(Path.home() / "Documents")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_folder = os.path.join(docs_folder, "ATS_Analysis_Reports")
        os.makedirs(report_folder, exist_ok=True)
        
        # Create report filename
        report_file = os.path.join(report_folder, f"ats_analysis_{timestamp}.txt")
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=== ATS Resume Analysis Report ===\n\n")
            
            # Overall Score
            f.write(f"ATS Compatibility Score: {analysis_results['ats_score']}%\n\n")
            
            # Executive Summary
            f.write("=== Executive Summary ===\n")
            f.write("Strengths:\n")
            skills = analysis_results['parsed_data']['skills']
            f.write(f"1. Technical Skills Coverage: {len(skills['technical'])} skills detected\n")
            formatting = analysis_results['parsed_data']['formatting']
            f.write(f"2. Bullet Points Usage: {formatting['bullet_points']} bullet points found\n")
            
            f.write("\nAreas for Improvement:\n")
            if formatting['special_chars_count'] > 50:
                f.write("1. Special Characters: Too many non-standard characters detected\n")
            if formatting['has_tables']:
                f.write("2. Table Formatting: Tables detected (not ATS-friendly)\n")
            if len(skills['soft']) < 3:
                f.write("3. Soft Skills: Limited soft skills detected\n")
            
            # Skills Analysis
            f.write("\n=== Skills Analysis ===\n")
            f.write("\nTechnical Skills:\n")
            for skill in skills['technical']:
                locations = skills['locations'].get(skill, [])
                if locations:
                    context = analysis_results['parsed_data']['raw_text'][max(0, locations[0]-30):min(len(analysis_results['parsed_data']['raw_text']), locations[0]+30)]
                    f.write(f"- {skill} (Found in context: '...{context.strip()}...')\n")
                else:
                    f.write(f"- {skill}\n")
            
            f.write("\nSoft Skills:\n")
            if skills['soft']:
                for skill in skills['soft']:
                    locations = skills['locations'].get(skill, [])
                    if locations:
                        context = analysis_results['parsed_data']['raw_text'][max(0, locations[0]-30):min(len(analysis_results['parsed_data']['raw_text']), locations[0]+30)]
                        f.write(f"- {skill} (Found in context: '...{context.strip()}...')\n")
                    else:
                        f.write(f"- {skill}\n")
            else:
                f.write("- No soft skills detected\n")
            
            # Formatting Analysis
            f.write("\n=== Formatting Analysis ===\n")
            f.write(f"- Special Characters: {formatting['special_chars_count']}\n")
            
            if formatting['special_chars_details']:
                f.write("\nDetailed Special Characters Found:\n")
                for char, occurrences in formatting['special_chars_details'].items():
                    f.write(f"- '{char}' ({len(occurrences)} times)\n")
                    # Show first occurrence context
                    f.write(f"  Example: ...{occurrences[0]['context']}...\n")
            
            if formatting['table_indicators']:
                f.write("\nTable-like Structures Found:\n")
                for table in formatting['table_indicators']:
                    f.write(f"- Line {table['line_number']}: {table['content']}\n")
            
            if formatting['smart_quotes']:
                f.write("\nSmart Quotes Found:\n")
                for quote in formatting['smart_quotes']:
                    f.write(f"- '{quote['char']}' in context: ...{quote['context']}...\n")
            
            # Readability Analysis
            f.write("\n=== Readability Analysis ===\n")
            readability = analysis_results['parsed_data']['readability']
            f.write(f"- Readability Score: {readability['score']:.2f}/100\n")
            f.write(f"- Average Word Length: {readability['avg_word_length']:.2f}\n")
            f.write(f"- Average Sentence Length: {readability['avg_sentence_length']:.2f}\n")
            
            if readability['long_sentences']:
                f.write("\nLong Sentences Found:\n")
                for sentence in readability['long_sentences']:
                    f.write(f"- {sentence['length']} words: {sentence['text']}\n")
            
            # Recommendations
            f.write("\n=== Recommendations ===\n")
            recs = analysis_results['recommendations']
            if recs['critical']:
                f.write("\nCritical Issues:\n")
                f.write("- " + "\n- ".join(recs['critical']) + "\n")
            if recs['important']:
                f.write("\nImportant Improvements:\n")
                f.write("- " + "\n- ".join(recs['important']) + "\n")
            if recs['suggestions']:
                f.write("\nSuggestions:\n")
                f.write("- " + "\n- ".join(recs['suggestions']) + "\n")
            
            # Specific Action Items
            f.write("\n=== Specific Action Items ===\n")
            f.write("1. Format Changes:\n")
            f.write("   - Replace any tables with bulleted lists\n")
            f.write("   - Use standard bullet points (• or -) consistently\n")
            f.write("   - Remove special characters like em dashes (—), arrows (→), or other symbols\n")
            f.write("   - Use standard quotation marks (\") instead of smart quotes\n")
            
            f.write("\n2. Content Structure:\n")
            f.write("   - Break long sentences into shorter, clearer statements\n")
            f.write("   - Add a dedicated \"Skills\" section with both technical and soft skills\n")
            f.write("   - Use more action verbs at the beginning of bullet points\n")
            
            f.write("\n3. Skills Enhancement:\n")
            f.write("   - Add relevant soft skills throughout your experience descriptions\n")
            f.write("   - Quantify achievements where possible\n")
            f.write("   - Use industry-standard terminology\n")
            
            f.write("\n=== Additional Notes ===\n")
            f.write("* This analysis simulates how your resume might be processed by ATS systems.\n")
            f.write("* Different ATS systems may process your resume differently.\n")
            f.write("* Focus on addressing critical issues first, then important improvements.\n")
            f.write("* Always tailor your resume for specific job descriptions.\n")
        
        print(f"\nDetailed analysis report saved to: {report_file}")

def main():
    """Main function to run the resume analyzer."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python resume_analyzer.py <path_to_resume>")
        sys.exit(1)
        
    resume_path = sys.argv[1]
    if not os.path.exists(resume_path):
        print("Error: File not found. Please provide a valid file path.")
        sys.exit(1)
        
    analyzer = ATSResumeAnalyzer()
    
    try:
        results = analyzer.analyze_resume(resume_path)
        
        print("\n=== ATS Resume Analysis Results ===")
        print(f"\nATS Compatibility Score: {results['ats_score']}%")
        
        print("\nKey Findings:")
        skills = results['parsed_data']['skills']
        print(f"- Technical Skills Found: {len(skills['technical'])}")
        print(f"- Soft Skills Found: {len(skills['soft'])}")
        
        print("\nCritical Issues:")
        for rec in results['recommendations']['critical']:
            print(f"- {rec}")
            
        print("\nSee the detailed report in your Documents folder for complete analysis and recommendations.")
        
    except Exception as e:
        print(f"Error analyzing resume: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
