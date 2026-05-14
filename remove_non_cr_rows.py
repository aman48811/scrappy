import csv

INPUT_FILE = 'CR_OG_questions_extracted.csv'

REMOVE_NOS = {246, 260, 278, 279, 280}

def remove_and_renumber():
    with open(INPUT_FILE, encoding='utf-8-sig', errors='replace', newline='') as f:
        rows = list(csv.reader(f))
    header = rows[0]
    data = rows[1:]
    no_idx = header.index('No')

    filtered = [row for row in data if row[no_idx] not in {str(n) for n in REMOVE_NOS}]

    for i, row in enumerate(filtered, start=1):
        row[no_idx] = str(i)

    with open(INPUT_FILE, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(filtered)

    print(f'Removed {len(data) - len(filtered)} rows. Remaining: {len(filtered)}. No column renumbered 1–{len(filtered)}.')

if __name__ == '__main__':
    remove_and_renumber()
