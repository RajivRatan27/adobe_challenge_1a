# round1a_implementation.py

import fitz  # PyMuPDF
import os
import json
import time
import re
from collections import Counter
import operator

# --- Configuration ---
INPUT_DIR = "input"
OUTPUT_DIR = "output"
MAX_TIME_PER_FILE = 10  # seconds

# --- V6 ADVANCED DE-SCRAMBLING PIPELINE (NEW) ---

def deduplicate_characters(text):
    """Stage 1: Fixes stuttering characters like 'Reeeequest' -> 'Request'."""
    return re.sub(r'(.)\1+', r'\1', text)

def reduce_word_repetitions(text):
    """Stage 2: Fixes echoing words like 'fquest fquest' -> 'fquest'."""
    words = text.split()
    if not words: return ""
    cleaned_words = [words[0]]
    for i in range(1, len(words)):
        if words[i] != words[i-1]:
            cleaned_words.append(words[i])
    return " ".join(cleaned_words)

def fix_overlapping_stutter(text):
    """Stage 3: Fixes complex overlapping stutters like 'Proposaloposal' -> 'Proposal'."""
    words = text.split()
    fixed_words = []
    for word in words:
        if len(word) < 4:
            fixed_words.append(word)
            continue
        
        best_prefix = word
        for i in range(len(word) // 2, 0, -1):
            prefix = word[:i]
            remainder = word[i:]
            if prefix.endswith(remainder) or remainder == prefix:
                best_prefix = prefix
                break
        fixed_words.append(best_prefix)
    return " ".join(fixed_words)

def descramble_complex_title(text):
    """Runs the full, multi-stage decontamination pipeline."""
    # This pipeline is designed to be robust against complex scrambling.
    text = deduplicate_characters(text)
    text = reduce_word_repetitions(text)
    text = fix_overlapping_stutter(text)
    # A final pass to clean up any remaining simple echoes.
    text = reduce_word_repetitions(text)
    return text

# --- CORE HELPER FUNCTIONS (MODIFIED) ---

def find_content_start_page(doc):
    toc = doc.get_toc()
    if toc:
        first_content_page_num = toc[0][2] - 1
        return max(0, min(first_content_page_num, 10))
    return 0

def clean_and_validate_title(text):
    """This function is now upgraded to use the advanced pipeline."""
    if not text: return None
    
    # MODIFICATION: Calling the new advanced pipeline instead of the old function.
    text = descramble_complex_title(text)
    
    # The rest of the function remains the same.
    text = re.sub(r'\.(pdf|docx?|pptx?|xlsx?|cdr|doc|txt)$', '', text, flags=re.IGNORECASE)
    text = "".join(char for char in text if char.isprintable())
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) > 2 and re.search(r'\w', text, re.UNICODE): return text
    return None

# --- ALL OTHER FUNCTIONS REMAIN EXACTLY AS YOU PROVIDED ---

def get_document_title(doc):
    metadata_title = clean_and_validate_title(doc.metadata.get('title'))
    page = doc[0]
    page_width, page_height = page.rect.width, page.rect.height
    best_candidate = {"text": "", "score": 0}
    blocks = page.get_text("dict")["blocks"]
    for block in blocks:
        if block['type'] == 0:
            block_text = "".join(span['text'] for line in block['lines'] for span in line['spans']).strip()
            if not block_text: continue
            score = 0
            rep_span = block['lines'][0]['spans'][0]
            score += rep_span['size'] * 1.5
            if rep_span['flags'] & 2**4: score += 10
            if block['bbox'][1] < page_height * 0.35: score += 10
            block_center = (block['bbox'][0] + block['bbox'][2]) / 2
            score += max(0, 10 - (abs((page_width / 2) - block_center) / page_width * 20))
            if block_text.endswith('.'): score -= 10
            if score > best_candidate['score']:
                best_candidate['score'], best_candidate['text'] = score, block_text
    
    # The heuristic title is now cleaned by the new, powerful function
    heuristic_title = clean_and_validate_title(best_candidate['text'])
    
    if heuristic_title and best_candidate['score'] > 25: return heuristic_title
    elif metadata_title: return metadata_title
    elif heuristic_title: return heuristic_title
    else: return "Untitled Document"

def extract_outline_from_toc(doc):
    toc = doc.get_toc()
    if not toc: return None
    outline = [{"level": f"H{min(level, 3)}", "text": text.strip(), "page": page} for level, text, page in toc]
    return outline if outline else None

def extract_outline_by_heuristics(doc, start_page_num, time_limit):
    start_time = time.time()
    outline = []
    HEADING_SCORE_THRESHOLD = 15
    for page_num in range(start_page_num, len(doc)):
        if time.time() - start_time > time_limit: break
        page_heading_candidates = []
        for block in doc[page_num].get_text("dict")["blocks"]:
            if block['type'] == 0 and len(block['lines']) == 1:
                line = block['lines'][0]
                full_line_text = "".join(s['text'] for s in line['spans']).strip()
                if not full_line_text: continue
                score = 0
                span = line['spans'][0]
                font_size = round(span['size'])
                score += font_size
                if span['flags'] & 2**4: score += 5
                word_count = len(full_line_text.split())
                if word_count < 15: score += (15 - word_count)
                else: score -= 20
                if full_line_text.endswith('.'): score -= 10
                if re.match(r'^[A-Z\d]+[\.\)]', full_line_text): score += 5
                if score >= HEADING_SCORE_THRESHOLD:
                    page_heading_candidates.append({"text": full_line_text, "size": font_size, "page": page_num + 1})
        if page_heading_candidates:
            unique_heading_sizes = sorted(list(set(c['size'] for c in page_heading_candidates)), reverse=True)
            size_to_level_map = {size: f"H{i+1}" for i, size in enumerate(unique_heading_sizes[:3])}
            for candidate in page_heading_candidates:
                if candidate['size'] in size_to_level_map:
                    outline.append({"level": size_to_level_map[candidate['size']], "text": candidate['text'], "page": candidate['page']})
    return outline if outline else None

def extract_outline_by_regex(doc, start_page_num, time_limit):
    start_time = time.time()
    outline = []
    pattern = re.compile(r"^\s*(?:(?:Chapter|Section)\s+)?(\d{1,2}(?:\.\d{1,2}){0,2})\s*[:.\-]?\s+(.+)")
    for page_num in range(start_page_num, len(doc)):
        if time.time() - start_time > time_limit: break
        for line in doc[page_num].get_text("text").splitlines():
            match = pattern.match(line.strip())
            if match:
                numbering, text_content = match.group(1), match.group(2).strip()
                if text_content and re.search(r'\w', text_content, re.UNICODE):
                    level = numbering.count('.') + 1
                    if level <= 3: outline.append({"level": f"H{level}", "text": text_content, "page": page_num + 1})
    return outline if outline else None

def process_pdf(pdf_path):
    start_time = time.time()
    filename = os.path.basename(pdf_path)
    print(f"Processing {filename}...")
    try: doc = fitz.open(pdf_path)
    except Exception as e: print(f"  Error opening or parsing {filename}: {e}"); return

    title = get_document_title(doc)
    start_page_num = find_content_start_page(doc)
    if start_page_num > 0: print(f"  Info: Main content detected to start on page {start_page_num + 1}.")

    outline = extract_outline_from_toc(doc)
    if outline: print(f"  Success: Extracted outline using native TOC.")
    
    if not outline:
        time_left = MAX_TIME_PER_FILE - (time.time() - start_time)
        outline = extract_outline_by_heuristics(doc, start_page_num, time_left)
        if outline: print("  Success: Extracted outline using V3 Scoring Engine.")

    if not outline:
        time_left = MAX_TIME_PER_FILE - (time.time() - start_time)
        outline = extract_outline_by_regex(doc, start_page_num, time_left)
        if outline: print("  Success: Extracted outline using language-agnostic regex.")

    if not outline: print("  Failed: Could not extract a meaningful outline."); outline = []
        
    output_data = {"title": title, "outline": outline}
    output_path = os.path.join(OUTPUT_DIR, os.path.splitext(filename)[0] + ".json")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    doc.close()
    print(f"  Finished in {time.time() - start_time:.2f}s. Title found: '{title}'. Output saved to {output_path}")

def main():
    print("--- docker: PDF Outline Extractor ---")
    if not os.path.exists(INPUT_DIR): os.makedirs(INPUT_DIR)
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
    pdf_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(".pdf")]
    if not pdf_files: print(f"No PDF files found in '{INPUT_DIR}'."); return
    for pdf_file in pdf_files: process_pdf(os.path.join(INPUT_DIR, pdf_file))
    print("\n--- All files processed. ---")

if __name__ == "__main__":
    main()
