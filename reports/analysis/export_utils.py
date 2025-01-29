# export_utils.py
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from PIL import Image
import io
import base64
from dataclasses import dataclass
from typing import List
from jinja2 import Template
import pdfkit
from datetime import datetime

@dataclass
class ComponentExport:
    """Class to hold component export information"""
    title: str
    content: str
    order: int = 0

class PDFExporter:
    def __init__(self):
        self._components: List[ComponentExport] = []
    
    def plotly_to_html(self, fig) -> str:
        """Convert Plotly figure to static HTML image"""
        # Convert plotly figure to static image bytes
        img_bytes = fig.to_image(format="png", scale=2)
        
        # Convert bytes to base64 string
        img_base64 = base64.b64encode(img_bytes).decode()
        
        # Return HTML img tag with embedded base64 image
        return f'<img src="data:image/png;base64,{img_base64}" style="width: 100%; max-width: 800px;">'
    
    def register_component(self, title: str, content: str, order: int = 0):
        """Register a component for PDF export"""
        self._components.append(ComponentExport(title=title, content=content, order=order))
    
    def register_plotly_component(self, title: str, fig, description: str = "", order: int = 0):
        """Register a Plotly figure with optional description"""
        # Convert Plotly figure to static HTML image
        fig_html = self.plotly_to_html(fig)
        
        # Combine description and figure
        content = f"""
        <div class="chart-container">
            {description}
            {fig_html}
        </div>
        """
        
        self.register_component(title, content, order)
    
    def clear_components(self):
        """Clear all registered components"""
        self._components = []
    
    def create_pdf(self, filename: str = "output.pdf") -> bool:
        """Generate PDF from all registered components"""
        sorted_components = sorted(self._components, key=lambda x: x.order)
        
        combined_content = "\n\n".join([
            f'<div class="section">\n<h2>{comp.title}</h2>\n{comp.content}\n</div>'
            for comp in sorted_components
        ])
        
        return self._generate_pdf(combined_content, filename)
    
    def _generate_pdf(self, content: str, filename: str) -> bool:
        """Convert HTML content to PDF"""
        html_template = Template("""
        <!DOCTYPE html>
        <html>
            <head>
                <style>
                    body { 
                        font-family: Arial, sans-serif; 
                        margin: 40px;
                        line-height: 1.6;
                    }
                    .header { 
                        text-align: center; 
                        margin-bottom: 30px;
                    }
                    .section {
                        margin-bottom: 40px;
                    }
                    .chart-container {
                        margin: 20px 0;
                    }
                    .chart-container img {
                        display: block;
                        margin: 20px auto;
                        max-width: 100%;
                    }
                    table { 
                        width: 100%; 
                        border-collapse: collapse; 
                        margin: 20px 0;
                    }
                    th, td { 
                        border: 1px solid #ddd; 
                        padding: 8px; 
                        text-align: left;
                    }
                    th { background-color: #f5f5f5; }
                    .footer { 
                        text-align: center; 
                        margin-top: 50px; 
                        font-size: 12px;
                        color: #666;
                    }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Dashboard Report</h1>
                    <p>Generated on: {{date}}</p>
                </div>
                <div class="content">
                    {{content}}
                </div>
                <div class="footer">
                    Generated using Streamlit
                </div>
            </body>
        </html>
        """)
        
        html_content = html_template.render(
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            content=content
        )
        
        try:
            pdfkit.from_string(html_content, filename)
            return True
        except Exception as e:
            st.error(f"Error generating PDF: {str(e)}")
            return False

# Initialize global PDF exporter
if 'pdf_exporter' not in st.session_state:
    st.session_state.pdf_exporter = PDFExporter()
