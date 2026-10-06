import os
import hashlib
import io
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
import qrcode
from PIL import Image, ImageDraw, ImageFont, ImageOps

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Rect, Circle, String as RLString, Group

from app.config import settings

def compute_verification_hash(cert_id: str, email: str, event_name: str) -> str:
    raw = f"{cert_id}:{email}:{event_name}:{settings.PROJECT_NAME}"
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()

def create_qr_code_image(data: str) -> Image.Image:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1E293B", back_color="#FFFFFF").convert("RGB")
    return img

class CertificateGenerator:
    """
    Handles PDF and PNG certificate generation with multiple design themes,
    QR code embedding, verification hashing, and custom attribute rendering.
    """

    @staticmethod
    def generate(
        cert_id: str,
        recipient_name: str,
        recipient_email: str,
        event_name: str,
        issuer_name: str = "Organization",
        issuer_title: str = "Authorized Signatory",
        issue_date: str = "2026-10-06",
        template_style: str = "classic",
        custom_attributes: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, str, str]:
        """
        Generates both PDF and PNG certificates for a recipient.
        Returns: (pdf_path, png_path, verification_hash)
        """
        verification_hash = compute_verification_hash(cert_id, recipient_email, event_name)
        verification_url = f"{settings.BASE_URL}/api/v1/certificates/verify/{cert_id}"
        
        pdf_filename = f"{cert_id}.pdf"
        png_filename = f"{cert_id}.png"
        
        pdf_path = settings.STORAGE_DIR / pdf_filename
        png_path = settings.STORAGE_DIR / png_filename

        # Generate QR Code image
        qr_img = create_qr_code_image(verification_url)
        
        # Save temp QR code file for ReportLab
        qr_temp_path = settings.STORAGE_DIR / f"temp_qr_{cert_id}.png"
        qr_img.save(qr_temp_path)

        try:
            # 1. Generate PDF
            CertificateGenerator._generate_pdf(
                output_path=str(pdf_path),
                cert_id=cert_id,
                recipient_name=recipient_name,
                event_name=event_name,
                issuer_name=issuer_name,
                issuer_title=issuer_title,
                issue_date=issue_date,
                template_style=template_style,
                custom_attributes=custom_attributes,
                qr_temp_path=str(qr_temp_path),
                verification_hash=verification_hash
            )

            # 2. Generate PNG Preview
            CertificateGenerator._generate_png(
                output_path=str(png_path),
                cert_id=cert_id,
                recipient_name=recipient_name,
                event_name=event_name,
                issuer_name=issuer_name,
                issuer_title=issuer_title,
                issue_date=issue_date,
                template_style=template_style,
                custom_attributes=custom_attributes,
                qr_img=qr_img,
                verification_hash=verification_hash
            )
        finally:
            if qr_temp_path.exists():
                os.remove(qr_temp_path)

        return str(pdf_path), str(png_path), verification_hash

    @staticmethod
    def _generate_pdf(
        output_path: str,
        cert_id: str,
        recipient_name: str,
        event_name: str,
        issuer_name: str,
        issuer_title: str,
        issue_date: str,
        template_style: str,
        custom_attributes: Optional[Dict[str, Any]],
        qr_temp_path: str,
        verification_hash: str
    ):
        width, height = landscape(A4) # 841.89 x 595.27 pt
        c = canvas.Canvas(output_path, pagesize=(width, height))

        # Color schemes based on style
        if template_style == "modern":
            primary_color = colors.HexColor("#0D9488")  # Teal
            secondary_color = colors.HexColor("#0F172A") # Dark slate
            accent_color = colors.HexColor("#F59E0B")    # Amber
            bg_accent = colors.HexColor("#F0FDFA")
        elif template_style == "elegant":
            primary_color = colors.HexColor("#7C3AED")  # Purple
            secondary_color = colors.HexColor("#18181B") # Dark Zinc
            accent_color = colors.HexColor("#D97706")    # Gold
            bg_accent = colors.HexColor("#FAF5FF")
        else: # classic
            primary_color = colors.HexColor("#1E3A8A")  # Deep Navy
            secondary_color = colors.HexColor("#111827") # Dark Gray
            accent_color = colors.HexColor("#D97706")    # Gold
            bg_accent = colors.HexColor("#F8FAFC")

        # Background tint
        c.setFillColor(bg_accent)
        c.rect(0, 0, width, height, fill=1, stroke=0)

        # Outer Decorative Border
        c.setStrokeColor(primary_color)
        c.setLineWidth(4)
        c.rect(20, 20, width - 40, height - 40)

        # Inner Gold Border
        c.setStrokeColor(accent_color)
        c.setLineWidth(1.5)
        c.rect(26, 26, width - 52, height - 52)

        # Corner Ornaments
        c.setFillColor(accent_color)
        c.rect(18, height - 30, 12, 12, fill=1, stroke=0)
        c.rect(width - 30, height - 30, 12, 12, fill=1, stroke=0)
        c.rect(18, 18, 12, 12, fill=1, stroke=0)
        c.rect(width - 30, 18, 12, 12, fill=1, stroke=0)

        # Header Badge Seal
        seal_x = width / 2
        seal_y = height - 85
        c.setFillColor(accent_color)
        c.circle(seal_x, seal_y, 22, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(seal_x, seal_y - 4, "★")

        # Title: CERTIFICATE OF ACHIEVEMENT
        c.setFillColor(primary_color)
        c.setFont("Helvetica-Bold", 28)
        c.drawCentredString(width / 2, height - 135, "CERTIFICATE OF ACHIEVEMENT")

        # Subtitle
        c.setFillColor(colors.HexColor("#64748B"))
        c.setFont("Helvetica", 12)
        c.drawCentredString(width / 2, height - 165, "THIS IS PROUDLY PRESENTED TO")

        # Recipient Name
        c.setFillColor(secondary_color)
        c.setFont("Helvetica-Bold", 32)
        c.drawCentredString(width / 2, height - 215, recipient_name.upper())

        # Underline accent for recipient name
        c.setStrokeColor(accent_color)
        c.setLineWidth(2)
        c.line(width / 2 - 150, height - 225, width / 2 + 150, height - 225)

        # Description text
        c.setFillColor(colors.HexColor("#334155"))
        c.setFont("Helvetica", 14)
        c.drawCentredString(width / 2, height - 265, "for successfully completing the course/event program")

        # Event Name
        c.setFillColor(primary_color)
        c.setFont("Helvetica-Bold", 22)
        c.drawCentredString(width / 2, height - 305, event_name)

        # Custom Attributes (if present)
        current_y = height - 335
        if custom_attributes:
            attr_strs = [f"{k.replace('_', ' ').title()}: {v}" for k, v in custom_attributes.items()]
            attr_text = " • ".join(attr_strs)
            c.setFillColor(colors.HexColor("#475569"))
            c.setFont("Helvetica-Oblique", 11)
            c.drawCentredString(width / 2, current_y, attr_text)
            current_y -= 25

        # Signatures & Footer Section
        sig_y = 110
        # Left: Date & Certificate ID
        c.setFillColor(colors.HexColor("#334155"))
        c.setFont("Helvetica-Bold", 10)
        c.drawString(60, sig_y + 35, f"Date: {issue_date}")
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor("#64748B"))
        c.drawString(60, sig_y + 20, f"Certificate ID: {cert_id}")
        c.drawString(60, sig_y + 5, f"Verify Code: {verification_hash[:16]}...")

        # Center: QR Code
        if os.path.exists(qr_temp_path):
            c.drawImage(qr_temp_path, width / 2 - 35, sig_y - 15, width=70, height=70)
            c.setFont("Helvetica", 8)
            c.setFillColor(colors.HexColor("#64748B"))
            c.drawCentredString(width / 2, sig_y - 25, "Scan to Verify")

        # Right: Issuer Signature
        right_x = width - 200
        c.setStrokeColor(colors.HexColor("#94A3B8"))
        c.setLineWidth(1)
        c.line(right_x, sig_y + 30, right_x + 140, sig_y + 30)
        c.setFillColor(secondary_color)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(right_x, sig_y + 15, issuer_name)
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor("#64748B"))
        c.drawString(right_x, sig_y, issuer_title)

        c.showPage()
        c.save()

    @staticmethod
    def _generate_png(
        output_path: str,
        cert_id: str,
        recipient_name: str,
        event_name: str,
        issuer_name: str,
        issuer_title: str,
        issue_date: str,
        template_style: str,
        custom_attributes: Optional[Dict[str, Any]],
        qr_img: Image.Image,
        verification_hash: str
    ):
        # 1600 x 1131 resolution (1.414 aspect ratio matching A4 landscape)
        img_width, img_height = 1600, 1131
        
        if template_style == "modern":
            bg_color = (240, 253, 250)    # #F0FDFA
            primary_color = (13, 148, 136) # #0D9488
            secondary_color = (15, 23, 42) # #0F172A
            accent_color = (245, 158, 11)  # #F59E0B
        elif template_style == "elegant":
            bg_color = (250, 245, 255)    # #FAF5FF
            primary_color = (124, 58, 237) # #7C3AED
            secondary_color = (24, 24, 27) # #18181B
            accent_color = (217, 119, 6)   # #D97706
        else: # classic
            bg_color = (248, 250, 252)    # #F8FAFC
            primary_color = (30, 58, 138)  # #1E3A8A
            secondary_color = (17, 24, 39) # #111827
            accent_color = (217, 119, 6)   # #D97706

        img = Image.new("RGB", (img_width, img_height), bg_color)
        draw = ImageDraw.Draw(img)

        # Outer Frame
        draw.rectangle([40, 40, img_width - 40, img_height - 40], outline=primary_color, width=8)
        draw.rectangle([52, 52, img_width - 52, img_height - 52], outline=accent_color, width=3)

        # Corner Gold Rectangles
        corner_sz = 24
        draw.rectangle([36, 36, 36 + corner_sz, 36 + corner_sz], fill=accent_color)
        draw.rectangle([img_width - 36 - corner_sz, 36, img_width - 36, 36 + corner_sz], fill=accent_color)
        draw.rectangle([36, img_height - 36 - corner_sz, 36 + corner_sz, img_height - 36], fill=accent_color)
        draw.rectangle([img_width - 36 - corner_sz, img_height - 36 - corner_sz, img_width - 36, img_height - 36], fill=accent_color)

        # Load fonts (fallback to PIL default if truetype not found)
        try:
            title_font = ImageFont.truetype("arial.ttf", 54)
            subtitle_font = ImageFont.truetype("arial.ttf", 24)
            name_font = ImageFont.truetype("arialbd.ttf", 64)
            body_font = ImageFont.truetype("arial.ttf", 28)
            event_font = ImageFont.truetype("arialbd.ttf", 44)
            attr_font = ImageFont.truetype("ariali.ttf", 22)
            meta_font = ImageFont.truetype("arial.ttf", 20)
            meta_bold = ImageFont.truetype("arialbd.ttf", 22)
        except IOError:
            title_font = subtitle_font = name_font = body_font = event_font = attr_font = meta_font = meta_bold = ImageFont.load_default()

        # Helper to draw centered text
        def draw_centered(text: str, y: int, font: ImageFont.ImageFont, color: Tuple[int, int, int]):
            bbox = draw.textbbox((0, 0), text, font=font)
            w = bbox[2] - bbox[0]
            draw.text(((img_width - w) / 2, y), text, font=font, fill=color)

        # Draw Star Emblem Circle
        seal_cx, seal_cy = img_width // 2, 160
        draw.ellipse([seal_cx - 40, seal_cy - 40, seal_cx + 40, seal_cy + 40], fill=accent_color)
        draw_centered("★", seal_cy - 22, title_font, (255, 255, 255))

        # Title
        draw_centered("CERTIFICATE OF ACHIEVEMENT", 250, title_font, primary_color)
        draw_centered("THIS IS PROUDLY PRESENTED TO", 330, subtitle_font, (100, 116, 139))

        # Recipient Name
        draw_centered(recipient_name.upper(), 410, name_font, secondary_color)

        # Line under name
        name_bbox = draw.textbbox((0, 0), recipient_name.upper(), font=name_font)
        name_w = name_bbox[2] - name_bbox[0]
        line_half = max(250, name_w // 2 + 40)
        draw.line([(img_width // 2 - line_half, 500), (img_width // 2 + line_half, 500)], fill=accent_color, width=4)

        # Description & Event Name
        draw_centered("for successfully completing the course/event program", 550, body_font, (51, 65, 85))
        draw_centered(event_name, 620, event_font, primary_color)

        # Custom Attributes
        if custom_attributes:
            attr_strs = [f"{k.replace('_', ' ').title()}: {v}" for k, v in custom_attributes.items()]
            attr_text = " • ".join(attr_strs)
            draw_centered(attr_text, 700, attr_font, (71, 85, 105))

        # Footer / Signature / QR Code
        footer_y = 860
        # Left Details
        draw.text((120, footer_y), f"Date: {issue_date}", font=meta_bold, fill=(51, 65, 85))
        draw.text((120, footer_y + 35), f"Certificate ID: {cert_id}", font=meta_font, fill=(100, 116, 139))
        draw.text((120, footer_y + 65), f"Verify Code: {verification_hash[:16]}...", font=meta_font, fill=(100, 116, 139))

        # Center QR Code
        resized_qr = qr_img.resize((140, 140))
        img.paste(resized_qr, (img_width // 2 - 70, footer_y - 20))
        draw_centered("Scan to Verify", footer_y + 130, meta_font, (100, 116, 139))

        # Right Signature Line
        right_x = img_width - 450
        draw.line([(right_x, footer_y + 40), (right_x + 320, footer_y + 40)], fill=(148, 163, 184), width=2)
        draw.text((right_x, footer_y + 50), issuer_name, font=meta_bold, fill=secondary_color)
        draw.text((right_x, footer_y + 80), issuer_title, font=meta_font, fill=(100, 116, 139))

        img.save(output_path, format="PNG")
