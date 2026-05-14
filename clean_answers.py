import csv
import re
import os

INPUT_FILE = 'CR_OG_questions_extracted.csv'
BATCH_SIZE = 50
MY_NAME = 'Claude'

GARBAGE_LINES = [
    r'^\s*show more\s*$',
    r'^\s*please\s+(hit|give)\s+kudos.*$',
    r'^\s*kudos.*$',
    r'^\s*\+1\s*kudos.*$',
    r'^\s*responding to a pm.*$',
    r'^\s*rgds,?\s*$',
    r'^\s*thanks[!.,]?\s*$',
    r'^\s*hope (that |this )?helps.*$',
    r'^\s*sent from.*$',
    r'^\s*_+\s*$',
    r'^\s*-+\s*$',
    r'https?://\S+',
    r'^\s*\[.*?\]\s*$',
    r'^\s*Quote:\s*$',
]

GARBAGE_PATTERNS = [re.compile(p, re.IGNORECASE) for p in GARBAGE_LINES]

# Patterns that mark the START of a tutor/promo signature block at the end
SIGNATURE_TRIGGERS = [
    re.compile(r'start free with', re.IGNORECASE),
    re.compile(r'signature\s+read more', re.IGNORECASE),
    re.compile(r'gmat/gre(/ea)?\s+tutors?', re.IGNORECASE),
    re.compile(r'free trial:', re.IGNORECASE),
    re.compile(r'youtube channel:', re.IGNORECASE),
    re.compile(r'get \d+ ai-powered', re.IGNORECASE),
    re.compile(r'anaprep\.com', re.IGNORECASE),
    re.compile(r'gmatninja\.com', re.IGNORECASE),
    re.compile(r'e-gmat\.com', re.IGNORECASE),
    re.compile(r'magoosh\.com', re.IGNORECASE),
    re.compile(r'^\s*(RC|CR|SC|verbal|quant)\s*\|\s*(RC|CR|SC|verbal|quant)', re.IGNORECASE),
    re.compile(r'gmatinsight', re.IGNORECASE),
    re.compile(r'tutor.*admission consultant', re.IGNORECASE),
    re.compile(r'our recent scores:', re.IGNORECASE),
]


def strip_signature(lines):
    """Remove trailing signature/promo block from lines list."""
    for i, line in enumerate(lines):
        for trigger in SIGNATURE_TRIGGERS:
            if trigger.search(line):
                # Cut everything from this line onward
                return lines[:i]
    return lines


def looks_like_username(line):
    """First line is a username if it has no spaces and is short, or is a known pattern."""
    stripped = line.strip()
    if not stripped:
        return False
    # Single word, no spaces — likely a username/handle
    if ' ' not in stripped and len(stripped) < 40:
        return True
    # Numeric ID (like "282552")
    if stripped.isdigit():
        return True
    return False


def is_garbage_line(line):
    for pat in GARBAGE_PATTERNS:
        if pat.search(line):
            return True
    return False


def clean_detail(text, question_text=''):
    if not text or not text.strip():
        return text

    lines = text.split('\n')

    # Remove username from first line
    if lines and looks_like_username(lines[0]):
        lines = lines[1:]

    # If there's a "Show more" in the first ~10 lines, the real answer starts after it
    show_more_pos = None
    for i, line in enumerate(lines[:15]):
        if re.match(r'^\s*show more\s*$', line, re.IGNORECASE):
            show_more_pos = i
            break

    if show_more_pos is not None:
        lines = lines[show_more_pos + 1:]

    # Remove repeated question text block at the start
    # (if early lines contain a lot of the question text, skip them)
    if question_text:
        q_words = set(question_text.lower().split())
        skip_until = 0
        for i, line in enumerate(lines[:20]):
            line_words = set(line.lower().split())
            if len(line_words) > 4 and len(line_words & q_words) / max(len(line_words), 1) > 0.6:
                skip_until = i + 1
        if skip_until > 0:
            lines = lines[skip_until:]

    # Strip signature/promo block from the end
    lines = strip_signature(lines)

    # Remove all garbage lines
    cleaned = []
    for line in lines:
        if is_garbage_line(line):
            continue
        cleaned.append(line)

    # Remove leading/trailing blank lines
    while cleaned and not cleaned[0].strip():
        cleaned.pop(0)
    while cleaned and not cleaned[-1].strip():
        cleaned.pop()

    # Collapse multiple consecutive blank lines into one
    result = []
    prev_blank = False
    for line in cleaned:
        is_blank = not line.strip()
        if is_blank and prev_blank:
            continue
        result.append(line)
        prev_blank = is_blank

    return '\n'.join(result).strip()


def process_csv():
    with open(INPUT_FILE, encoding='utf-8-sig', errors='replace', newline='') as f:
        rows = list(csv.reader(f))

    header = rows[0]
    data = rows[1:]

    detail_idx = header.index('answer-detail')
    answer_by_idx = header.index('answer-by')
    question_idx = header.index('Question + Text')

    total = len(data)
    print(f'Total data rows: {total}')

    for batch_start in range(0, total, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, total)
        print(f'\nProcessing rows {batch_start + 1} to {batch_end}...')

        for i in range(batch_start, batch_end):
            row = data[i]
            original = row[detail_idx]
            question = row[question_idx] if question_idx < len(row) else ''
            cleaned = clean_detail(original, question)

            if not cleaned.strip() and original.strip():
                # Cleaning removed everything — keep a note
                cleaned = '[Answer detail could not be parsed — original content was forum discussion only]'

            data[i][detail_idx] = cleaned
            data[i][answer_by_idx] = MY_NAME

        # Checkpoint save after each batch
        with open(INPUT_FILE, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(data)

        print(f'  Saved checkpoint after row {batch_end}.')

    print(f'\nDone. All {total} rows processed and saved to {INPUT_FILE}')


if __name__ == '__main__':
    process_csv()
