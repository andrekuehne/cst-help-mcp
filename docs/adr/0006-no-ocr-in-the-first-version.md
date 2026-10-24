# No OCR in the first version

The brainstorm planned equation-image OCR (Pix2Text) and OCR for scanned PDFs. The CST 2024 profile showed that 175 help pages already carry TeX source for MathJax, only about 40–100 equations exist as images, and every PDF is born-digital; scanned PDFs are not expected at all. So the build runs no OCR. TeX is kept as written, equation images stay images (marked as not transcribed, viewable by agents), and a PDF without a text layer is a reported failure. This also keeps PyMuPDF (AGPL-3.0), which Pix2Text requires, out of the dependencies.

## Consequences

- PDF tools with built-in OCR must run with it switched off.
- Transcribing equation images can return later as an opt-in enrichment step. Formula recognition inside PDF pages is decided separately.
