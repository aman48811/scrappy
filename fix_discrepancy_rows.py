import csv

INPUT_FILE = 'CR_OG_questions_extracted.csv'

REWRITES = {
    # No=96, ANS=C
    95: """Answer: C

Cocoa prices are rising due to supply shortages (bad weather in Brazil and West Africa) and stronger demand in Europe and North America. Analysts predict prices will continue rising.

C strengthens this: new cocoa trees take 5–6 years before they bear fruit. Even if farmers respond to high prices by planting more trees now, supply cannot increase for at least 5–6 years. The shortage is structural and cannot be corrected quickly, so the upward price pressure will persist into the near future.""",

    # No=113, ANS=C
    112: """Answer: C

The astronomer's argument: each parent cloud has a unique, homogeneous chemical composition, and stars form from these clouds. Therefore, two stars with the same chemical composition must have originated from the same cloud.

The critical gap in this reasoning is whether stars actually retain the composition of their parent cloud after forming. C directly closes this gap: whenever a star forms, it inherits the chemical composition of its parent cloud. Without this link, identical compositions in two stars wouldn't prove they came from the same cloud.""",

    # No=135, ANS=E
    134: """Answer: E

The argument: Edmund attended the Merchant Tailors' School at a reduced fee → he came from a less affluent family → John Spenser (the least affluent of the three Guild members named Spenser) was likely his father.

This reasoning only works if reduced fees specifically signal financial need. E provides the necessary assumption: the school did NOT reduce fees for children of the more affluent Guild members. If affluent members' children also received reduced fees (as a perk), then Edmund's reduced fee wouldn't point to a less wealthy father. E ensures reduced fees = less affluent background.""",

    # No=168, ANS=D
    167: """Answer: D

New safety features (seat belts, power steering) were mandated in 1966, and one-seventh of cars were replaced with new safe cars. Yet collisions and injuries didn't decline. D explains why: owners of the new cars, feeling protected by the safety features, drove less cautiously than before. This behavioral offset (risk compensation) neutralized the safety benefits — the safety technology reduced harm per collision but drivers' recklessness increased the number of collisions.""",

    # No=246 — Non-CR
    245: """⚠️ NON-CR QUESTION: This appears to be a dropdown/multi-select data interpretation question, not a standard Critical Reasoning question. The answer options (A–E) are empty. Requires manual review.""",

    # No=260 — Non-CR
    259: """⚠️ NON-CR QUESTION: This appears to be a multi-select data sufficiency question involving a library database and page calculations, not a standard Critical Reasoning question. The answer options (A–E) are empty. Requires manual review.""",

    # No=278 — Non-CR
    277: """⚠️ NON-CR QUESTION: This appears to be part of a multi-part table/design problem about a business school building, not a standard Critical Reasoning question. The question text and options are incomplete. Requires manual review.""",

    # No=279 — Non-CR
    278: """⚠️ NON-CR QUESTION: This appears to be part of a multi-part table/design problem about a business school building, not a standard Critical Reasoning question. The question text and options are incomplete. Requires manual review.""",

    # No=280 — Non-CR
    279: """⚠️ NON-CR QUESTION: This appears to be part of a multi-part table/design problem about a business school building, not a standard Critical Reasoning question. The question text and options are incomplete. Requires manual review.""",

    # No=333, ANS=C
    332: """Answer: C

The argument: the only cyclists who want innovation and will pay for it are racers → innovation is limited by what race authorities accept as standard for competition.

This conclusion requires C as an assumption: bicycle racers do not generate strong demand for innovations that fall OUTSIDE what is officially recognized as competition-standard. If racers demanded non-standard innovations too, manufacturers would have reason to innovate beyond race rules. C ensures that racer demand and race-authority standards are perfectly aligned — meaning race rules fully define the ceiling of innovation demand.""",

    # No=351, ANS=E
    350: """Answer: E

The board proposes a physics curriculum focused on visual image production and analysis to make the subject more relevant and attract more students.

E provides the strongest support: in today's world, the production and analysis of visual images is of major importance in communications, business, and recreation. If visual images are genuinely central to modern life, students will recognize the curriculum as directly useful and relevant — which is precisely the gap the original curriculum failed to fill. E confirms that the new focus addresses what students actually care about.""",

    # No=388, ANS=E
    387: """Answer: E

The recommendation is to use the test with the LOWEST proportion of false positive results to detect pironoma most accurately.

A concern with this recommendation: maybe the test with fewer false positives compensates by having more false negatives (missing actual disease cases). E eliminates this concern: all laboratory tests to detect pironoma have the SAME proportion of false negative results. Since false negatives are equal across all tests, the only meaningful difference between tests is their false positive rates. Minimizing false positives therefore maximizes overall accuracy.""",

    # No=412, ANS=A
    411: """Answer: A

After the dam reduced the river's annual temperature range from 50°F to 6°F, all eight native fish species stopped reproducing adequately. Scientists hypothesize that sharply rising temperatures signal fish to begin their reproductive cycle.

A strongly supports this: the native fish species are still able to reproduce — but only in side streams where the annual temperature range remains approximately 50°F. The dam narrowed the main river's temperature range but not the side streams'. Fish reproduce where the large temperature swings still occur and fail to reproduce where the swings have been eliminated. This is direct evidence that temperature change is the reproductive trigger.""",

    # No=431, ANS=C
    430: """Answer: C

Solar power became more cost-efficient over the last decade (lower equipment costs, better technology). Yet the economic viability threshold — the oil price at which new solar plants become more economical than new oil-fired plants — remained unchanged at $35/barrel.

C explains why: technological changes have also increased the efficiency of oil-fired power plants. As solar improved, oil plants improved too, maintaining the same competitive gap. The threshold didn't drop because both sides of the comparison moved in parallel — solar got cheaper, but so did oil-based power generation.""",

    # No=509, ANS=B
    508: """Answer: B

An experiment found that large consumption of an artificial sweetener caused lower cognitive abilities in the experimental group. The effect was attributed to an amino acid that is one of the sweetener's main constituents.

The question asks how the sweetener might produce this cognitive effect. B explains the mechanism: a high level of the amino acid in the blood inhibits the synthesis of a substance required for normal brain functioning. This provides the complete causal chain: sweetener → elevated blood amino acid → blocked synthesis of brain-essential substance → reduced cognitive performance.""",
}

def update_rows():
    with open(INPUT_FILE, encoding='utf-8-sig', errors='replace', newline='') as f:
        rows = list(csv.reader(f))
    header = rows[0]
    data = rows[1:]
    detail_idx = header.index('answer-detail')
    answer_by_idx = header.index('answer-by')
    for row_idx, new_detail in REWRITES.items():
        data[row_idx][detail_idx] = new_detail.strip()
        data[row_idx][answer_by_idx] = 'Claude'
    with open(INPUT_FILE, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(data)
    print(f'Fixed {len(REWRITES)} discrepancy rows and saved.')

if __name__ == '__main__':
    update_rows()
