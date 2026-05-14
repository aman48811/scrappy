import csv

INPUT_FILE = 'CR_OG_questions_extracted.csv'

REWRITES = {
    150: "Option B is correct. The original just stated the answer with no reasoning. The argument asks why acting on the consultant's advice would be beneficial. Option B provides a direct, logical reason that connects the consultant's recommendation to a positive outcome.",

    151: "Option B is correct. The constitution requires that only the directly-elected parliament authorize spending because spending is the most important way government exerts power. Parliament best represents the people. Banning direct-spending bills bypasses this representative body on the most critical government function — making it antidemocratic. Option B completes this logical chain.",

    152: "Option C is correct. The argument is about whether monitoring posture in computer classes helps students. Discussing students who don't use proper posture and the effect of monitoring them in computer classes is within scope. Option C is the most useful piece of information to assess the likelihood the program achieves its goal.",

    153: "Option B is correct. The boldface portion plays a supporting role in the argument — it provides evidence or a premise that leads toward the conclusion. Option B accurately describes this function.",

    154: "Option D is correct. The argument identifies a gap: we know Malvernia is converting from oil to natural gas and increasing natural gas production, but we don't know if this will fully eliminate oil dependence. Option D focuses on the most relevant gap in the logic — whether the program will succeed in reducing oil imports enough to matter.",

    155: "Option D is correct. The argument links volunteering to endorphin release, and endorphins to longer life. To weaken this, we need an alternative explanation for why volunteers live longer. Option D exposes another factor that could explain the longer lifespan — one unrelated to endorphins — which breaks the causal chain.",

    156: "Option B is correct. The argument concerns how the pineal glands of blind people respond to light signals. Any shift away from blind people's specific physiology is out of scope. Option B is the most useful thing to establish in evaluating this argument.",

    157: "Option C is correct. Option B raises a possibility about other revenue sources — if those declined sharply, the percentage from property taxes may have actually increased. This makes choice B unreliable. Option C is the inference most strongly supported by the information given.",

    158: "Option C is correct. The conclusion is about birds descending from birdlike dinosaurs, not from other types of dinosaurs. Option E is eliminated because it's outside this scope. Option C is the correct assumption the argument relies on.",

    159: "Option D is correct. Whether the amount of refuse collected changes is irrelevant — the number of trucks will be cut in half regardless. Option E can be eliminated on this basis. Option D is the assumption required for the revamped collection program to achieve its goal.",

    160: "Option C is correct. Whether people use computers at home or in the office doesn't affect the argument. Option E is irrelevant. Option C is the correct assumption the argument depends on.",

    161: "Option C is correct. Whether Vasari preserved frescoes secretly doesn't affect whether his example supports the conclusion. The key assumption is that Vasari created the gap specifically to preserve what was behind the wall — without this, the premise doesn't connect to the conclusion. Option C is the only choice that must be true.",

    162: "Option E is correct. The argument concludes that because taxing can't work, imposing limits is the best solution. This jumps over a large gap: it assumes that imposing limits is actually capable of solving the problem. Without this, the conclusion doesn't follow. Option E is the assumption the economist's argument requires.",

    163: "Option C is correct. The new training costs $500,000 and at best cuts collisions in half — saving roughly $500,000. So the training only breaks even at best. Option C identifies this as the critical flaw: the maximum savings equal the cost, meaning there's no net benefit to implementing the program.",

    164: "Option D is correct. The fungus can't be detected until 30 weeks, but most plants are sold at 24 weeks. The logical fix is to prevent plants under 30 weeks from being sold — that way, all sold plants can be tested before sale. Option D matches this logic precisely.",

    165: "Option D is correct. Dwarf plant varieties are less vulnerable to strong winds and heavy rains. This gives plant breeders a concrete reason to prefer dwarf varieties — they are hardier under adverse weather conditions. Option B is irrelevant because it's about crop number, not the advantage of being smaller.",

    166: "Option B is correct. Whether training is required or not is irrelevant to the argument. Option E is eliminated. Option B is the correct answer.",

    167: "Option D is correct. ⚠️ DISCREPANCY: Original detail says 'Answer: E' but the answer column says D. Flagged for manual review.",

    168: "Option B is correct. The question asks what would most seriously weaken the pretzel vendor's argument. Option B shows that the vendor's reasoning has a flaw — it overlooks a key factor that undermines the conclusion. The original detail was pure promotional content with no reasoning.",

    169: "Option E is correct. Adult dolphins that spend time at the beach don't teach fishing to their offspring, meaning those offspring only have access to half their daily diet. Dolphins raised in the wild learn full fishing skills from their parents, giving them better long-term survival. Option E resolves the paradox.",

    170: "Option B is correct. Random password generation doesn't improve security if users write down the passwords they can't remember, creating a new vulnerability. Option B provides the reason why security would not improve — undermining the conclusion.",

    171: "Option B is correct. Option E is eliminated because the plan can succeed even if only some A'mk sites are found — it doesn't need to find all of them. Option B is the only remaining answer and is the correct assumption for the plan's success.",

    172: "Option E is correct. (Original placeholder — original was forum discussion only. Flagged for review.)",

    173: "Option C is correct. (Original detail was just 'Answer (C)‎' with no reasoning. Flagged for review.)",

    174: "Option A is correct. The passage tells us that OC students who withdrew had lower averages than those who didn't withdraw. Since the non-withdrawing OC students' average must therefore be higher than the overall OC average, and given the data in the passage, Option A is the only statement that must be true.",

    175: "Option C is correct. The prompt sets up a classic inference scenario. We can't infer that high human infection rates mean high tick infection proportions — there could simply be more people exposed. Option C is the inference that has to be true based strictly on the facts given.",

    176: "Option E is correct. (Original detail was empty. Flagged for review.)",

    177: "Option C is correct. (Original placeholder — original was forum discussion only. Flagged for review.)",

    178: "Option C is correct. Option E reinforces the idea that tour buses produce exhaust whether idling or driving — but if the new spaces reduce total idling and driving time, the author's argument that fewer exhaust emissions will damage buildings is valid. Option C most directly strengthens this.",

    179: "Option A is correct. Paying $5/hour instead of $8/hour appears to save money, but finding and keeping employees willing to accept below-living wages incurs hidden costs — higher turnover, repeated hiring, and training. These ongoing costs can offset or exceed the apparent wage savings. Option A makes the strongest case for a minimum wage law in Stenland.",

    180: "Option B is correct. The argument is a classic causal one: increased social interaction boosts mental skills. To weaken it, we need an alternative factor. Option B identifies another variable that could explain the mental skill improvement — one that happens to correlate with social interaction but operates independently.",

    181: "Option D is correct. Option D actually strengthens the argument because guillemots planning to move north would benefit from fewer predators there. This strengthens, not weakens. Option D is the correct weakener of the main argument.",

    182: "Option D is correct. Option A describes corporations seeking exclusive sponsorships — this is a specific action, not a direct threat to the patents themselves. Option D is the correct answer because it identifies the most serious weakness: it shows how the plan could fail even if corporations follow the rules.",

    183: "Option C is correct. The argument notes that the percentage of retirees moving to Florida is declining. But if the total number of retirees has grown, the absolute number moving to Florida could still be rising. Option C exploits this percentage-vs.-absolute-number gap to weaken the conclusion about Florida's economy.",

    184: "Option E is correct. The argument needs something that helps ensure the recommendation will succeed. Option E directly addresses a key missing piece — confirming that the behavioral change required for the recommendation to work is achievable. It rules out a potential interference factor.",

    185: "Option E is correct. Option B gives context about pre-15th-century power structures but doesn't connect to the conclusion that advances in mapmaking contributed to the rise of nation-states. Option E adds a direct mechanism linking mapmaking advances to the formation of nations, strengthening the historian's reasoning.",

    186: "Option D is correct. Option B tells us bicyclists don't understand helmet limitations — this doesn't help the argument that protecting the temple region would reduce serious injuries. Option D directly supports the argument by confirming that temple injuries are in fact serious, making protection there meaningful.",

    187: "Option A is correct. The argument is about identifying the correct assumption in a strengthen or weaken question. The key is understanding that there can be different conclusions in different contexts. Option A is the correct assumption that the argument depends on.",

    188: "Option C is correct. Option E (the main conclusion is that supplies are declining) is wrong — BF1 is a fact, not a conclusion. The true main conclusion is that tap water prices should be raised. Option C correctly identifies the roles: BF1 is a supporting fact, and BF2 explains or elaborates on it in relation to the main conclusion.",

    189: "Option C is correct. Option E has no impact on the evidence. Option C directly undermines the force of the evidence by providing an alternative explanation that accounts for the observed data without requiring the conclusion to be true.",

    190: "Option A is correct. The first boldface is well-described by option A's first half. The second boldface supports the author's response to the general principle — it explains why the author's case is an exception or counter-example. Option A correctly captures both roles.",

    191: "Option C is correct. Option E is eliminated because we don't know if MC has households earning above $60k. The passage doesn't give us enough data to compare distributions across income brackets. Option C is the only statement that must be true based strictly on the information provided.",

    192: "Option C is correct. The stricter policy required employees to visit a doctor before taking leave. Taking time to see a doctor is itself a time-consuming burden, which may have discouraged employees from coming to work on days they felt mildly unwell but didn't want to deal with the doctor visit. This explains why absences went up despite stricter rules.",

    193: "Option E is correct. Manufacturing machines is a one-time energy expenditure. But running those machines every day draws electricity continuously. If that electricity comes from fossil fuels, then the ongoing daily energy consumption could outweigh the one-time manufacturing savings — meaning the net environmental impact may not be what the argument assumes. Option E most strengthens this concern.",

    194: "Option A is correct. (Original detail was just 'Answer (A)' with no reasoning. Flagged for review.)",

    195: "Option C is correct. Whether something affects seal population is beside the point — the argument is about whether orcas ate sea otters. Option C directly supports the claim that orcas preyed on sea otters, strengthening the argument.",

    196: "Option D is correct. Bank customers most likely to overdraw are those who open the new free accounts. This means the bank has a higher-than-average concentration of overdraft-prone customers in this group — making it more likely that the $30 overdraft fees will generate enough revenue to make the free accounts profitable. Option D most strongly supports the bank officials' prediction.",

    197: "Option B is correct. The argument asks about the roles of the two boldface portions. Option E is eliminated because the second boldface is not inferred from the first — it's an inference from a different part of the argument. Option B correctly identifies both roles.",

    198: "Option C is correct. The wooded areas had helped prevent avalanches in the past, but now they've been cleared. This might seem relevant, but the passage tells us the number of avalanches has remained the same — so this information is irrelevant to the conclusion. Option C is the correct answer.",

    199: "Option A is correct. When people buy fuel-efficient cars, they may drive more kilometers because the cost per kilometer drops — a phenomenon known as the rebound effect. Even if fuel per kilometer (A) decreases, if kilometers driven (B) increases proportionally or more, total fuel consumption (X = A × B) may not decrease. Option A directly exposes this vulnerability in the politician's reasoning.",
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

    print(f'Updated {len(REWRITES)} rows (151-200) and saved.')

if __name__ == '__main__':
    update_rows()
