# The Knowledge Base is a portable artifact, decoupled from where it is built

Conversion and OCR are expensive and may run on a different machine (one with an NVIDIA GPU) from the one that serves agents. A build therefore produces a self-contained, relocatable Knowledge Base: relative paths only, including copies of the original HTML and PDF files it cites. It can be copied to another machine and served without the CST installation, the input folders, or any OCR dependencies. The 2024 help is about 0.7 GB, so carrying the originals is affordable.

## Considered Options

- Referencing the installed CST help or the input folders at serve time: smaller, but ties the Knowledge Base to one machine and breaks silently when the installation changes.
