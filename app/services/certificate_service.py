import os
import re
from typing import Union, Optional
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch
from typing import Union

def get_safe_filename(name: str) -> str:
    """Convert a string into a safe file name, preventing path traversal."""
    safe_name = re.sub(r'[^\w\s-]', '_', name)
    safe_name = safe_name.replace(' ', '_')
    if not safe_name:
        safe_name = "recipient"
    # Ensure sequential underscores are reduced
    safe_name = re.sub(r'_+', '_', safe_name)
    return f"{safe_name.strip('_')}"

def generate_certificate(
    recipient_name: str,
    event_name: str,
    event_date: str,
    issuer_name: str,
    output_dir: str,
    unique_id: Union[int, str],
    filename_override: Optional[str] = None
) -> str:
    """
    Generates a PDF certificate and returns the absolute file path.
    """
    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        if filename_override:
            # Safely extract basename to strictly prevent path traversal issues out of the box
            filename = os.path.basename(filename_override)
            if not filename.endswith('.pdf'):
                filename += '.pdf'
        else:
            safe_name = get_safe_filename(recipient_name)
            filename = f"{safe_name}_{unique_id}.pdf"
            
        file_path = os.path.join(output_dir, filename)
        
        abs_output_dir = os.path.abspath(output_dir)
        abs_file_path = os.path.abspath(file_path)
        
        if not abs_file_path.startswith(abs_output_dir):
            raise ValueError("Invalid file path prevented")
            
        # Generate the PDF
        c = canvas.Canvas(abs_file_path, pagesize=landscape(A4))
        width, height = landscape(A4)
        
        # Border
        c.setStrokeColorRGB(0.2, 0.2, 0.4)
        c.setLineWidth(5)
        c.rect(0.5 * inch, 0.5 * inch, width - 1 * inch, height - 1 * inch, stroke=1, fill=0)
        
        c.setLineWidth(1)
        c.rect(0.6 * inch, 0.6 * inch, width - 1.2 * inch, height - 1.2 * inch, stroke=1, fill=0)
        
        # Title
        c.setFont("Helvetica-Bold", 40)
        c.drawCentredString(width / 2.0, height - 2.5 * inch, "CERTIFICATE OF PARTICIPATION")
        
        # Subtitle
        c.setFont("Helvetica", 18)
        c.drawCentredString(width / 2.0, height - 3.5 * inch, "This certificate is proudly presented to")
        
        # Recipient Name
        c.setFont("Helvetica-Bold", 30)
        c.setFillColorRGB(0.1, 0.1, 0.5)
        c.drawCentredString(width / 2.0, height - 4.5 * inch, recipient_name)
        
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica", 16)
        c.drawCentredString(width / 2.0, height - 5.3 * inch, "for successfully participating in")
        
        # Event Name
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(width / 2.0, height - 6.0 * inch, event_name)
        
        # Event Date
        c.setFont("Helvetica", 14)
        c.drawCentredString(width / 2.0, height - 6.5 * inch, f"held on {event_date}")
        
        # Issuer
        c.setFont("Helvetica-Oblique", 14)
        c.drawCentredString(width / 2.0, 1.5 * inch, "Presented by")
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(width / 2.0, 1.1 * inch, issuer_name)
        
        c.setLineWidth(0.5)
        c.line(width / 2.0 - 1.5 * inch, 1.8 * inch, width / 2.0 + 1.5 * inch, 1.8 * inch)
        
        c.save()
        return abs_file_path
        
    except Exception as e:
        raise RuntimeError(f"Certificate generation failed: {str(e)}")
