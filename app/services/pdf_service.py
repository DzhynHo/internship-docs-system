"""
PDF Generator Service - konwersja formularzy na PDF.
"""

from weasyprint import HTML, CSS
from flask import render_template, current_app
from io import BytesIO
import os


def generate_pdf_from_html(html_content, filename="document.pdf"):
    """
    Generowanie PDF z zawartości HTML.
    
    Args:
        html_content: HTML jako string
        filename: Nazwa pliku do zapisania
    
    Returns:
        BytesIO object lub ścieżka pliku
    """
    try:
        html_obj = HTML(string=html_content)
        pdf_bytes = html_obj.write_pdf()
        return pdf_bytes
    except Exception as e:
        print(f"[PDF Generator] Error: {e}")
        return None


def generate_attachment_1_pdf(document_data):
    """Generowanie PDF - Porozumienie (Załącznik 1)."""
    
    html = render_template(
        'pdf/attachment_1.html',
        data=document_data
    )
    
    return generate_pdf_from_html(html, "Porozumienie.pdf")


def generate_attachment_3_pdf(document_data):
    """Generowanie PDF - Karta Praktyki (Załącznik 3)."""
    
    html = render_template(
        'pdf/attachment_3.html',
        data=document_data
    )
    
    return generate_pdf_from_html(html, "Karta_Praktyki.pdf")


def generate_attachment_6_pdf(diary_entries, internship_data):
    """Generowanie PDF - Dziennik Praktyki (Załącznik 6)."""
    
    html = render_template(
        'pdf/attachment_6.html',
        entries=diary_entries,
        internship=internship_data
    )
    
    return generate_pdf_from_html(html, "Dziennik_Praktyki.pdf")


def generate_attachment_7_pdf(document_data, internship_data):
    """Generowanie PDF - Sprawozdanie (Załącznik 7)."""
    
    html = render_template(
        'pdf/attachment_7.html',
        data=document_data,
        internship=internship_data
    )
    
    return generate_pdf_from_html(html, "Sprawozdanie.pdf")


def generate_protocol_pdf(internship_data, approval_data):
    """Generowanie PDF - Protokół Egzaminu (Załącznik 8) - tylko dla Dyrekcji."""
    
    html = render_template(
        'pdf/attachment_8.html',
        internship=internship_data,
        approval=approval_data
    )
    
    return generate_pdf_from_html(html, "Protokol_Egzaminu.pdf")


def generate_confirmation_report_pdf(internship_data, learning_outcomes):
    """Generowanie PDF - Potwierdzenie Uzyskania Efektów (Załącznik 4a)."""
    
    html = render_template(
        'pdf/attachment_4a.html',
        internship=internship_data,
        outcomes=learning_outcomes
    )
    
    return generate_pdf_from_html(html, "Potwierdzenie_Efektow.pdf")
