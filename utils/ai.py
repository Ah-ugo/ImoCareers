# ai.py
import google.generativeai as genai
import os
from dotenv import load_dotenv
from typing import Dict
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from io import BytesIO

load_dotenv()


class AIHelper:
    def __init__(self):
        genai.configure(api_key=os.getenv("GOOGLE_AI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.styles = getSampleStyleSheet()
        self._configure_styles()

    def _configure_styles(self):
        """Modify existing styles instead of adding new ones"""
        # Modify existing BodyText style
        body_style = self.styles['BodyText']
        body_style.spaceBefore = 6
        body_style.spaceAfter = 6

        # Create new style if it doesn't exist
        if 'Header1' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='Header1',
                parent=self.styles['Heading1'],
                fontSize=18,
                leading=22,
                spaceAfter=12
            ))

    def generate_cover_letter(self, job: Dict, user: Dict, cv: Dict) -> str:
        """
        Generates a cover letter using Google AI
        """
        prompt = f"""
        Generate a professional cover letter for {user['name']} applying to 
        {job['title']} at {job['company']}.

        Job Description:
        {job.get('description', '')[:2000]}

        Applicant Profile:
        - Skills: {', '.join(cv.get('skills', []))}
        - Experience: {len(cv.get('experience', []))} positions
        - Education: {len(cv.get('education', []))} degrees
        {f"- Summary: {cv.get('summary', '')}" if cv.get('summary') else ""}

        Requirements:
        1. Match key skills to job requirements
        2. Highlight relevant experience
        3. Professional tone with 3-4 paragraphs
        4. Proper business letter format
        """

        try:
            response = self.model.generate_content(prompt)
            if not response.text:
                raise ValueError("Empty response from AI")
            return response.text
        except Exception as e:
            print(f"Cover letter error: {str(e)}")
            raise Exception("Failed to generate cover letter")

    def generate_cv_pdf(self, user_data: Dict, cv_data: Dict) -> bytes:
        """
        Generates PDF CV using ReportLab
        Returns PDF bytes
        """
        try:
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []

            # Header Section
            elements.append(Paragraph(user_data['name'], self.styles['Header1']))
            elements.append(Paragraph(user_data.get('email', ''), self.styles['BodyText']))
            elements.append(Spacer(1, 24))

            # Summary Section
            if cv_data.get('summary'):
                elements.append(Paragraph("Professional Summary", self.styles['Heading2']))
                elements.append(Paragraph(cv_data['summary'], self.styles['BodyText']))
                elements.append(Spacer(1, 12))

            # Skills Section
            elements.append(Paragraph("Technical Skills", self.styles['Heading2']))
            skills_table = Table([[", ".join(cv_data.get('skills', []))]],
                                 style=[('ALIGN', (0, 0), (-1, -1), 'LEFT')])
            elements.append(skills_table)
            elements.append(Spacer(1, 16))

            # Experience Section
            elements.append(Paragraph("Professional Experience", self.styles['Heading2']))
            for exp in cv_data.get('experience', []):
                date_str = self._format_date_range(exp.get('start_date'), exp.get('end_date'))
                elements.append(Paragraph(
                    f"{exp.get('position', '')} at {exp.get('company', '')}",
                    self.styles['BodyText']
                ))
                elements.append(Paragraph(
                    date_str,
                    self.styles['Italic']
                ))
                elements.append(Paragraph(
                    exp.get('description', ''),
                    self.styles['BodyText']
                ))
                elements.append(Spacer(1, 8))

            # Education Section
            elements.append(Paragraph("Education", self.styles['Heading2']))
            for edu in cv_data.get('education', []):
                date_str = self._format_date_range(edu.get('start_date'), edu.get('end_date'))
                elements.append(Paragraph(
                    f"{edu.get('degree', '')} in {edu.get('field', '')}",
                    self.styles['BodyText']
                ))
                elements.append(Paragraph(
                    f"{edu.get('school', '')} - {date_str}",
                    self.styles['Italic']
                ))
                elements.append(Spacer(1, 8))

            doc.build(elements)
            pdf_bytes = buffer.getvalue()
            buffer.close()
            return pdf_bytes

        except Exception as e:
            print(f"PDF generation error: {str(e)}")
            raise Exception("Failed to generate PDF")

    def _format_date_range(self, start_date, end_date=None) -> str:
        """Formats date range for CV display"""
        try:
            start = start_date.strftime('%b %Y') if isinstance(start_date, datetime) else 'N/A'
            end = end_date.strftime('%b %Y') if end_date else 'Present'
            return f"{start} - {end}"
        except Exception:
            return "Date information unavailable"


# Singleton instance
ai_helper = AIHelper()