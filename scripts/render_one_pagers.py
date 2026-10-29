"""Render the attached HTML content to separate A4 PDFs (optional WeasyPrint dependency)."""
from pathlib import Path
from weasyprint import HTML,CSS
root=Path(__file__).resolve().parent.parent
for lang in ('en','es'):
 source=root/'one-pagers'/f'{lang}.html'
 target=root/'dist/assets'/f'six7-one-pager-{lang}.pdf'
 HTML(filename=str(source)).write_pdf(target,stylesheets=[CSS(filename=str(root/'one-pagers/print.css'))])
 print(target.name)
