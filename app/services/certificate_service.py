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

import textwrap

def generate_certificate(
    recipient_name: str,
    event_name: str,
    event_date: str,
    issuer_name: str,
    output_dir: str,
    unique_id: Union[int, str],
    filename_override: Optional[str] = None,
    certificate_title: str = "CERTIFICATE OF PARTICIPATION",
    introduction_text: str = "This certificate is proudly presented to",
    description_text: str = "for successfully participating in",
    presented_by_label: str = "Presented by"
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
        
        # Title (with safe font auto-scaling if title is long)
        title_font_size = 40
        title_max_w = width - 2 * inch
        while title_font_size > 22 and c.stringWidth(certificate_title, "Helvetica-Bold", title_font_size) > title_max_w:
            title_font_size -= 2
        c.setFont("Helvetica-Bold", title_font_size)
        c.drawCentredString(width / 2.0, height - 2.5 * inch, certificate_title)
        
        # Introduction / Subtitle
        intro_font_size = 18
        intro_max_w = width - 2 * inch
        while intro_font_size > 14 and c.stringWidth(introduction_text, "Helvetica", intro_font_size) > intro_max_w:
            intro_font_size -= 1
        c.setFont("Helvetica", intro_font_size)
        c.drawCentredString(width / 2.0, height - 3.5 * inch, introduction_text)
        
        # Recipient Name
        c.setFont("Helvetica-Bold", 30)
        c.setFillColorRGB(0.1, 0.1, 0.5)
        c.drawCentredString(width / 2.0, height - 4.5 * inch, recipient_name)
        
        # Description text (with multiline text wrapping if text is long)
        c.setFillColorRGB(0, 0, 0)
        desc_font_size = 16
        c.setFont("Helvetica", desc_font_size)
        desc_max_w = width - 2.5 * inch
        if c.stringWidth(description_text, "Helvetica", desc_font_size) > desc_max_w:
            avg_char_w = max(c.stringWidth("participating in", "Helvetica", desc_font_size) / 16, 7)
            approx_chars = max(int(desc_max_w / avg_char_w), 25)
            lines = textwrap.wrap(description_text, width=approx_chars)
            total_h = (len(lines) - 1) * (desc_font_size * 1.2)
            curr_y = height - 5.3 * inch + (total_h / 2.0)
            for line in lines:
                c.drawCentredString(width / 2.0, curr_y, line)
                curr_y -= desc_font_size * 1.2
        else:
            c.drawCentredString(width / 2.0, height - 5.3 * inch, description_text)
        
        # Event Name
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(width / 2.0, height - 6.0 * inch, event_name)
        
        # Event Date
        c.setFont("Helvetica", 14)
        c.drawCentredString(width / 2.0, height - 6.5 * inch, f"held on {event_date}")
        
        # Issuer & Presented By Label
        c.setFont("Helvetica-Oblique", 14)
        c.drawCentredString(width / 2.0, 1.5 * inch, presented_by_label)
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(width / 2.0, 1.1 * inch, issuer_name)
        
        c.setLineWidth(0.5)
        c.line(width / 2.0 - 1.5 * inch, 1.8 * inch, width / 2.0 + 1.5 * inch, 1.8 * inch)
        
        c.save()
        return abs_file_path
        
    except Exception as e:
        raise RuntimeError(f"Certificate generation failed: {str(e)}")
