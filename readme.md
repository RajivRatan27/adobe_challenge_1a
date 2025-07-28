# DocStructureX - Intelligent PDF Outline & Title Extractor

![Version](https://img.shields.io/badge/Version-10.0-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Build](https://img.shields.io/badge/Build-Docker-blueviolet.svg)

DocStructureX is a production-ready, intelligent tool designed to extract structured outlines and accurate titles from PDF documents. It transforms raw PDFs into a clean, hierarchical JSON format, identifying the document's title and section headings (H1, H2, H3).

This solution was iteratively engineered to overcome real-world challenges, including malformed titles, multi-line headers, boilerplate noise, and complex document layouts, making it a highly robust and reliable tool for document understanding.

## Key Features

-   **Intelligent Title Extraction:** Uses a V10 Hybrid Engine that combines multiple strategies to correctly identify both simple and complex multi-part titles.
-   **Advanced Text De-Scrambling:** Includes a powerful, multi-stage pipeline to algorithmically fix common PDF text corruption issues like "stuttering" (`Reeequest`), "echoes" (`fquest fquest`), and complex overlapping text (`Proposaloposal`).
-   **Robust Heuristic Outline Extraction:** Employs a page-by-page contextual scoring engine to identify headings based on font size and style, while intelligently filtering out footers, headers, and other boilerplate text.
-   **Language Agnostic:** Built to be Unicode-first, with logic that works seamlessly on documents in multiple languages.
-   **Fully Offline & Portable Build:** The repository includes all dependencies as pre-downloaded "wheels", allowing the Docker image to be built and run in a completely air-gapped environment.
-   **Clean & Standardized Output:** Generates human-readable and machine-friendly JSON, perfect for downstream processing, semantic search, or knowledge graph creation.

## How It Works: The V10 Architecture

DocStructureX uses a sophisticated, multi-strategy approach to ensure accuracy and resilience.

1.  **Title Extraction:**
    -   **Base Title Identification:** First, it finds the single text block with the highest visual score (font size, boldness) to reliably capture the main title.
    -   **Conditional Combination:** It then identifies the first "H1" on the page and, if its text is not already part of the base title, logically appends it. This correctly assembles compound titles without corrupting simple ones.
    -   **De-Scrambling Pipeline:** The selected title is passed through an advanced pipeline to fix any text corruption artifacts.

2.  **Outline Extraction:**
    -   **Page-by-Page Analysis:** The tool iterates through every page to establish a local context, preventing inconsistencies from affecting results.
    -   **Universal Scoring & Boilerplate Filtering:** Every line is scored based on positive attributes (large font, short word count) and negative attributes (ends with a period, located in header/footer area). Common boilerplate text is automatically disqualified.
    -   **Dynamic Hierarchy:** Headings are assigned H1/H2/H3 levels based on their relative font sizes *on that page*, making the system highly adaptive.

## Project Structure

```
DocStructureX/
├── input/                  # Place your input PDFs here
├── output/                 # Generated JSON outlines appear here
├── wheels/                 # Pre-downloaded Python packages for offline build
├── round1a_implementation.py  # The core V10 engine logic
├── requirements.txt        # List of Python dependencies
├── Dockerfile              # Instructions to build the Docker image
└── README.md               # This file
```

---

## Execution Guide

This project is fully containerized with Docker for maximum portability and ease of use.

### Prerequisites

-   [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.
-   You have cloned this repository.

### Step 1: Place Your PDFs

Copy or move the PDF files you want to process into the `input/` directory at the root of the project.

### Step 2: Build the Docker Image

This solution is designed for a **fully offline build**. The repository already contains all necessary Python packages in the `wheels/` folder. The `Dockerfile` is pre-configured to use this local cache, so no internet connection is required during the build process.

Open a terminal in the project root and run:

```bash
docker build --platform linux/amd64 -t adobechallenge1a:latest .
```
*(Note: The first time you run this, Docker may need to download the base `python:3.10` image if you don't have it cached locally. Subsequent builds will be completely offline.)*

### Step 3: Run the Container

Execute the following command to process the PDFs from your `input` folder and save the results to your `output` folder.

```bash
docker run --rm \
    -v "$(pwd)/input:/app/input" \
    -v "$(pwd)/output:/app/output" \
    --network none \
    adobechallenge1a:latest
```
### Step 4: Check the Output

The extracted JSON files, one for each input PDF, will now be available in the `output/` directory.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
