import os
from django.conf import settings
from django.template.loader import render_to_string
from weasyprint import HTML, CSS
from weasyprint.fonts import FontConfiguration
import tempfile
from datetime import datetime
from pathlib import Path

class CertificateGenerator:
    """Service to generate PDF certificates"""
    
    TEMPLATE_DIR = Path(settings.BASE_DIR) / 'templates' / 'certificates'
    
    def __init__(self, certificate):
        self.certificate = certificate
    
    def generate_pdf(self):
        """Generate PDF certificate"""
        # Render HTML template
        context = self.get_context_data()
        
        # Use different templates based on certificate template type
        template_name = f"certificate_{self.certificate.template}.html"
        
        # Fallback to default if template doesn't exist
        template_path = self.TEMPLATE_DIR / template_name
        if not template_path.exists():
            template_name = "certificate_default.html"
        
        html_string = render_to_string(f'certificates/{template_name}', context)
        
        # Generate PDF
        pdf_file = self.html_to_pdf(html_string)
        
        return pdf_file
    
    def get_context_data(self):
        """Prepare context data for certificate template"""
        enrollment = self.certificate.enrollment
        course = enrollment.course
        
        return {
            'certificate': self.certificate,
            'enrollment': enrollment,
            'course': course,
            'student': enrollment.user,
            'instructor': course.instructor,
            'issued_date': self.certificate.issued_at.strftime('%B %d, %Y'),
            'completion_date': self.certificate.completion_date.strftime('%B %d, %Y'),
            'year': datetime.now().year,
            'platform_name': 'BTEE eLearning Platform',
            'verification_url': self.certificate.verification_url,
            'certificate_id': self.certificate.certificate_id,
        }
    
    def html_to_pdf(self, html_string):
        """Convert HTML to PDF"""
        font_config = FontConfiguration()
        
        # CSS for PDF styling
        css = CSS(string='''
            @page {
                size: A4 landscape;
                margin: 0;
            }
            body {
                font-family: 'DejaVu Sans', sans-serif;
                margin: 0;
                padding: 0;
            }
            .certificate-container {
                width: 100%;
                height: 100vh;
                position: relative;
            }
        ''', font_config=font_config)
        
        # Generate PDF
        html = HTML(string=html_string)
        pdf_bytes = html.write_pdf(stylesheets=[css], font_config=font_config)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(pdf_bytes)
            return tmp_file.name
    
    def save_pdf_to_certificate(self, pdf_path):
        """Save generated PDF to certificate model"""
        from django.core.files import File
        
        with open(pdf_path, 'rb') as pdf_file:
            file_name = f"{self.certificate.certificate_id}.pdf"
            self.certificate.pdf_file.save(file_name, File(pdf_file))
        
        # Clean up temporary file
        os.unlink(pdf_path)
        self.certificate.save()