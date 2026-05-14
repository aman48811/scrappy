import csv

INPUT_FILE = 'CR_OG_questions_extracted.csv'

# Keyed by row index in data (0-based), value is the rewritten answer-detail
REWRITES = {
    0: """The argument concludes that fewer flights will mean fewer tourists. But this only holds if we assume that each remaining flight doesn't compensate by carrying more passengers. Option E captures this assumption — if airlines responded by packing more passengers per flight, the total tourist count wouldn't necessarily fall. So E is the key assumption the argument depends on.""",

    1: """The argument is asking which statement most logically completes it. Option E is correct. (Original explanation lacked sufficient reasoning — flagged for review.)""",

    2: """In boldface questions, you need to identify the role each highlighted portion plays. The first boldface is a supporting fact — it is not a claim being challenged. The second boldface is the conclusion. Option B correctly identifies both of these roles.""",

    3: """The first boldface portion presents the scientists' hypothesis: scarcity of prey explains why boreal owls range so widely. The second boldface offers supporting evidence — owls range more widely in areas where food for their prey is scarcer. There is no indication of an alternative hypothesis, so option C is out. Option B correctly captures this: the first is the hypothesis, and the second supports it.""",

    4: """The argument notes that flight delays doubled but complaints tripled. If we only count the number of delays, we'd expect complaints to double too. But if the delays last year were significantly longer than the year before, that would push more passengers to complain even without a proportional rise in delay frequency. Option D introduces delay length as the missing factor that explains the disproportionate jump in complaints.""",

    5: """Option B is the correct assumption. The argument assumes the opposite of what the incorrect options claim. (Original explanation was too brief — flagged for review.)""",

    6: """We cannot assume that luxury boat buyers were wealthy just because they could afford a boat before the tax. The passage only tells us that some buyers could no longer afford a boat after the tax — it says nothing about how wealthy they were. So option D is unsupported. Option B is what the given information most strongly supports.""",

    7: """The question asks which option most helps explain the exception. Option B is correct. (Original detail only listed answer choices without reasoning — flagged for review.)""",

    8: """The question asks why water companies would request regulations that could reduce their own revenue. An answer about climate changing over time doesn't explain their current motivation. Option B directly resolves the paradox by giving a concrete reason why regulations would benefit the companies despite the short-term revenue cost.""",

    9: """The paradox is: NorthAir knows wider seats and better service would increase profits, yet chose not to make those improvements. Option D — that NorthAir can still sell tickets without improvements — doesn't resolve the paradox because it doesn't explain why they'd pass up the extra profit. Option E provides the actual reason behind NorthAir's decision and is the correct answer.""",

    10: """The key distinction is between 'goods and services' (the general category where Country X supposedly spends more) and 'middle-class consumer goods like vehicles and appliances' (what the study specifically measured). Country X may spend more on services while spending less on that specific subset of goods. Option D captures this gap between what was measured and what was claimed, explaining the discrepancy.""",

    11: """Wind and water-powered factories couldn't meet all manufacturing demand on their own. Steam engines filled that gap. Option E explains the spread of steam-powered factories by pointing to this supply shortfall — existing energy sources simply couldn't keep up, making steam the practical solution.""",

    12: """The passage establishes that the trade deficit and the budget deficit are not correlated. This means reducing one does not automatically reduce the other — the second deficit may go up, down, or stay flat regardless. Option C is the inference that follows directly from this relationship.""",

    13: """The passage shows that elderly Israelis tend to live with their children, while elderly Swedes tend to live alone. Since informal care means care provided by family and friends, elderly Israelis receive more of it — and therefore need less formal care. Option E makes this explicit. Option C only hints at a possible difference in formal care programs without explaining the mechanism, making E the stronger and more specific answer.""",

    14: """No answer detail available for this row.""",

    15: """This is an inference question. The passage tells us that animals evolved to use generalized past memories — not perfect recall — to function better in similar future situations. The correct answer must follow with 100% certainty. Option E aligns with this: since generalized memory is sufficient for survival advantage, animals do not need to remember every detail of past experiences perfectly.""",

    16: """No usable explanation found — original content was promotional/ad content only.""",

    17: """The passage states that athletes breathing pure oxygen show no meaningful difference in blood lactate levels compared to those who don't. Since blood lactate is directly tied to muscular oxygen reabsorption, inhaling pure oxygen makes no practical difference to performance. Option A reflects this conclusion. Option B is unsupported; option C contradicts the last sentence; option D is unclear.""",

    18: """No usable explanation — original content was forum discussion that could not be parsed.""",

    19: """Option E doesn't prove the Neanderthal flute could play a full diatonic scale, but it shows the bone was physically long enough to produce those notes. Even if Neanderthals didn't use the full length, knowing the bone had the capacity removes a key obstacle to the hypothesis. This strengthens the hypothesis, which is all a strengthen question requires.""",

    20: """The manager is worried that discounting coffee will hurt overall profits. Option D counters this by explaining that cheaper coffee attracts more customers, who then spend money on food and pastries where the real profit margin is. The increase in food sales offsets the potential loss on coffee. Option B (saving money roasting coffee) doesn't address the manager's concern about lost revenue from customers who would have paid full price.""",

    21: """The experiment tested seed production in plots with and without dandelions. But option E reveals that removing dandelions involved digging up the soil, which may itself have reduced seed production in those plots. This provides an alternative explanation for the results — the difference in seed counts may be due to soil disturbance, not the presence or absence of dandelions. Since this breaks the causal link, E is the correct weakener.""",

    22: """When someone proposes a plan and predicts it will achieve its goal, they are only predicting the relationship (if plan, then goal) — not guaranteeing the plan will happen or the goal will definitely be reached. The author says: IF we clean our surroundings, THEN India will become a better destination. They are not claiming cleaning will happen, nor that the improvement is guaranteed. Option C correctly reflects this.""",

    23: """The argument is specifically about whether discussing art helps science students become more creative. Evidence about science discussions in arts classes is beside the point. We need something that directly supports art discussions boosting creativity in science students. Option B provides exactly this kind of targeted support.""",

    24: """Option C eliminates an option that presents a fact but doesn't demonstrate causal connection between the two developments in the argument. To show causal relationship, we need direct evidence that one event led to the other — not just that both occurred.""",

    25: """The argument claims that wages of college graduates are falling because of reduced productivity. Option A challenges this by pointing to basic supply and demand: if there is an oversupply of college graduates relative to demand, wages fall regardless of productivity. This provides an alternative explanation for falling wages, directly undermining the argument's conclusion.""",

    26: """The plan is to block current access routes to reduce harm to the turtle population. But this only works if all-terrain vehicles actually use those routes. If ATVs enter through other paths, blocking current routes does nothing. Option B asks whether ATVs use these routes, making it essential for evaluating whether the plan can succeed. Option D is tempting but the passage already tells us that collecting tortoises without a vehicle is difficult — so pedestrians aren't the main threat.""",

    27: """Option E actually strengthens the author's argument (today's carpenters start less skilled), so we eliminate it. Option D is the best answer because it directly weakens the argument by providing information that contradicts the author's reasoning about the decline in carpenter skill and care.""",

    28: """The firm decided to eliminate the smell of coffee roasting. Option E provides the best justification: news about health regulations around that smell — even if ultimately harmless — could cause public anxiety. People associate regulated smells with danger. To avoid customers developing negative associations with the store, the firm proactively eliminated the smell. This strongly supports their decision.""",

    29: """The argument has one main conclusion. The premises may look like sub-conclusions on the surface, but they are essentially facts supporting the main point. Option E is correct in identifying the single conclusion and the role of the boldface portions relative to it. (Note: original explanation was incomplete — flagged for review.)""",

    30: """Option A is the correct answer for this boldface roles question. (Original explanation was only the phrase "I hope that helps!" — no actual reasoning provided. Flagged for review.)""",

    31: """Option E is the correct answer. (Original explanation was a fragment without reasoning — flagged for review.)""",

    32: """In Weaken questions, the correct answer gives new information that makes the conclusion less likely. Scott's claim is that budworm decline causes Tennessee Warbler decline because warblers don't get enough food at the North American source. Option A directly challenges the food-shortage hypothesis at the source, making it the strongest weakener.""",

    33: """Option C strengthens the argument by removing a potential flaw: it confirms that people who express opinions in surveys actually follow through and vote. This 'remove the flaw' type of strengthener is common on the GMAT — it doesn't directly advance the argument, but it closes a gap that would otherwise weaken it.""",

    34: """The argument says alligator sightings in Florida increased in the 1990s, implying the alligator population grew. But option A points out that Florida's human population also grew significantly during that period. More people in the area means more people available to spot and report an alligator — even if the actual population stayed the same. This alternative explanation undermines the argument.""",

    35: """Option A is wrong because avoiding accidents doesn't explain why cost-cutting had no safety impact. Option B actually weakens the argument — companies abandoning safety demands would suggest safety was compromised. Option C is correct: cost-cutting measures simply didn't touch safety-related spending, which is why safety was unaffected. Option D fails for the same reason as A.""",

    36: """Option B is wrong because it only tells us how knowledge reached one city, not that it wasn't common elsewhere. Option C could support either the traveling artisans theory or a shared knowledge base. Option D weakens the conclusion — if species were already widely known, traveling artisans aren't needed to explain the mosaics. Option E is the key assumption: if knowledge of those species wasn't widely shared across Rome, only artisans who traveled and acquired it could have created those specific mosaics.""",

    37: """The proposal says landfill methane should be burned rather than released. The objection is that burning creates CO2. Whether landfills emit more or less methane is irrelevant to this debate — we're talking about what to do with whatever methane IS emitted. So option E (reducing methane output) doesn't counter the objection. Option D directly addresses it by comparing the impact of CO2 from burning versus methane released directly.""",

    38: """After acquiring Eldorado, Apex has 25 casinos. But antitrust rules require selling casinos in the 5 counties where both Apex and Eldorado operated. Depending on how many of those 5 counties Moneyland already has casinos in, the total number of operating casinos could actually decrease — not increase as predicted. Option A walks through all possible cases and shows that in several scenarios the acquisition results in fewer total casinos, undermining the prediction.""",

    39: """The option being discussed here presents a hypothetical that might damage brand image but doesn't directly challenge whether the increased spending will boost sales. It's off-target. Option B is the correct answer because it directly identifies the most serious weakness in the marketing executive's reasoning.""",

    40: """Option D is correct because it shows that the plan's success depends on a condition that won't hold. The shrimps will not last, meaning the solution is temporary and the problem will return. This directly calls into question the plan's chances for long-term success.""",

    41: """Option D is the correct answer. It provides the most direct justification for the explanation offered. (Original detail was too brief to reconstruct full reasoning — flagged for review.)""",

    42: """Option D is the correct answer for this assumption question. The linguist's reasoning depends on this assumption holding true. (Original detail was too brief — flagged for review.)""",

    43: """The agency estimates GNP twice for each year — once five years in advance, and again one year after. The key insight: the agency has no new data when it revises. The only reason it would change its estimate is if it recognized the original was wrong. Option D states exactly this — the agency revises estimates when it believes the original was inaccurate.""",

    44: """The first boldface explains why companies prefer the highest-price strategy — it has clear appeal. The second boldface explains why that strategy can backfire. Together: the first presents the appeal of the strategy, and the second calls its wisdom into question. Option B captures this exactly. Option D fails because it claims the second boldface supports the first — but it actually challenges it.""",

    45: """Option D is the correct answer for this boldface roles question. (Original explanation was only promotional content with no actual reasoning — flagged for review.)""",

    46: """Option A correctly identifies BF1 as the paleontologist's hypothesis and BF2 as supporting evidence for it. Option B is wrong because the paleontologist does not oppose BF2 — they use it as support. Option C is wrong because BF1 is not being challenged — it is being proposed. Option A is the answer.""",

    47: """Option E is about customer beliefs, which isn't what the argument examines. The argument is about the logical link between the percentage of delays caused by airline error and the actual number of those delays. Since E doesn't address this link, it is eliminated. Option D directly exposes a flaw in that logic and is the correct answer.""",

    48: """Option A is the correct answer. The passage gives a reason why the plan faces a problem, and option A most seriously casts doubt on whether that plan will succeed. (Original explanation discussed an unrelated option — flagged for review.)""",

    49: """Notice the quantifiers: 'a substantial proportion' of the target group gets under 10 minutes of homework. For the overall average to still exceed 30 minutes per night, a smaller but significant group of under-12 children must be getting far more than 30 minutes. This shows the editorial's concern is justified — some younger children are genuinely overburdened with homework. Option D captures this inference.""",
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

    print(f'Updated {len(REWRITES)} rows (1-50) and saved.')

if __name__ == '__main__':
    update_rows()
