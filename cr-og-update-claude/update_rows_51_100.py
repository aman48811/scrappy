import csv

INPUT_FILE = 'CR_OG_questions_extracted.csv'

REWRITES = {
    50: "The plan aims to expose the opposition's domestic policies as harmful to middle-class voters. If option A is true — that such voters can be persuaded — it actually helps the plan succeed, not hinders it. So this option strengthens rather than weakens. Option A is the correct answer because it identifies what would most strongly suggest the plan could work.",

    51: "Option E is wrong because the second boldface simply states the strategy companies adopt (charging maximum price), not an intended outcome. The intended outcome would be earning large profits — but the statement doesn't say that. Since the second half of E misidentifies the role of that boldface portion, E is eliminated. Option C correctly identifies both boldface roles.",

    52: "The passage describes Groucho Marx's comic style and links it to a 16th-century tradition. The actor who played harlequin in La Finestrina reminded viewers of Marx — but that doesn't mean Marx performed in that play. We can infer the style connects across centuries, but not specific biographical details about Marx. Option D is the most logical conclusion supported by the passage.",

    53: "The first boldface introduces the established fact that more whiplash reports occur in countries with insurance coverage. The second boldface offers an alternative explanation for that fact — people report injuries more readily when insured, not because more injuries occur. Option D correctly captures this: the first is a fact the argument seeks to explain, and the second is an alternative explanation offered to support the author's conclusion.",

    54: "The first boldface is a position that might appear to support the opposing view, but it actually contains a flaw that the author will exploit. The second boldface is the author's counter — pointing out what the first boldface fails to account for. Option A correctly captures this relationship.",

    55: "The poll said voters cared most about pollution, yet they voted for other candidates. Option E suggests the poll was inaccurate — but we need a reason why the result could differ even if the poll was accurate. Option D does exactly this: voters may genuinely care most about pollution yet vote for candidates based on other criteria. This reconciles the poll result with the election outcome.",

    56: "Option D is correct. Therese doesn't simply disagree with Mansour — she challenges the assumption behind his proposal by suggesting the existing strategy may already be the better course. This is a reversal of the burden of proof: rather than saying his plan is bad, she implies the default (doing nothing) hasn't been shown to be worse. Option D captures this method of response.",

    57: "Option C is correct. (Original detail was 'Out of scope C' with only a signature — no reasoning provided. Flagged for review.)",

    58: "Option D is correct. (Original detail was only 'I hope that helps!' — no reasoning provided. Flagged for review.)",

    59: "The argument concludes that insincerity in government shows the government is functioning well. Option A weakens this by pointing out that the conclusion conflates correlation with causation — just because a functioning government might display insincerity doesn't mean insincerity proves functioning. The analogy: a 760 GMAT score doesn't guarantee Harvard admission, so Harvard admission can't be 'shown' purely by a 760 score.",

    60: "This is a weaken question. Option B is correct. The community members' analysis shows that the key flaw lies in the study's methodology — specifically, that participants were self-selected based on willingness to use meditation, which introduces bias. This undermines the argument that meditation works for the general population of high-blood-pressure patients.",

    61: "Option E is correct. For inference questions on the duckbill dinosaur, the key is finding a conclusion that must be true within the passage's parameters. Option E follows logically — if the duckbill's tail was more fragile and its predators were larger, tail injuries during predator encounters would be more likely, explaining the damage observed. This is the most strongly supported inference.",

    62: "Option A is correct. The highway officials argue ECC is economically viable despite higher construction costs. Option A directly supports this by providing a specific reason why ECC's total cost over time is lower — eliminating the taxpayer's objection that higher upfront costs make it unviable.",

    63: "Option C is correct. The birds choose lower-calorie berries over insects during migration. Option E only tells us birds avoid some high-calorie berries — it doesn't explain the preference for lower-calorie options. Option C provides the actual explanation for why lower-calorie berries are preferred.",

    64: "Option E is correct. None of the other options address the specific point about defining generic concepts using concrete examples. Option E aligns directly with what the passage describes and most logically completes the argument.",

    65: "Option B is the correct assumption. Using the negation test: if no one buys DVDs under the new plan, the plan achieves nothing. A negated option B completely destroys the argument, which confirms it is a necessary assumption. Options that don't destroy the argument when negated are not necessary assumptions.",

    66: "Option B is correct. The question asks what provides the strongest support for the director's position. While option B only offers modest support, it is the only option that provides any support at all — the other four options provide none. On GMAT, the task is to pick the best available answer, not a perfect one.",

    67: "Option A is correct. The argument doesn't state that every mine with increased output also had increased productivity — it only describes a specific instance. Inferring a universal rule from one specific case is not supported by the data provided.",

    68: "Option B is correct for this boldface roles question. The first boldface states the content of the conclusion (what the conclusion says), and the second boldface provides a premise that supports arriving at that conclusion. Option B accurately captures both roles.",

    69: "Option E is correct. (Original detail was only 'Answer: E' — no reasoning provided. Flagged for review.)",

    70: "Option E is correct. This answer choice explains how, even with the plastic bag tax in place, bag usage would remain unchanged — because the group of users in question would not reduce consumption regardless of the cost. This explains the environmental groups' opposition to a measure that appears effective on paper but fails in practice.",

    71: "Option A is correct. The argument is about whether the conclusion logically follows. Option A clarifies that even though the absolute number may look large, what matters for the argument is proportional comparison. The relative comparisons — not the specific numbers — are what determine whether the conclusion holds.",

    72: "Option A is correct. The question is whether younger children considered intent when assigning punishment. What other factors they considered is irrelevant — the argument only hinges on whether intent was one factor they used.",

    73: "Option A is correct. The argument depends on the assumption that a smaller percentage of older drivers are involved in serious accidents — not just a smaller absolute number. Even if more older drivers are involved in absolute terms, if the percentage is lower, the argument still holds. Option A must be assumed for the conclusion to stand.",

    74: "Option E is correct. The investors buying plants and running them long-term would not constitute 'opportunistically exploiting a currency fall.' But if investors intended to buy low, hold, and resell once prices recover, that would be exploiting the currency dip for profit. Option E casts doubt on whether the explanation given adequately accounts for this alternative motive.",

    75: "Option C is correct. Option D is irrelevant because the argument doesn't depend on other potential factors for oxygen absorption. Option E is irrelevant because the argument is about oxygen, not water. Option C directly supports the conclusion that SuperOXY won't increase oxygen absorption by providing a mechanism that explains why it doesn't work.",

    76: "Option B is correct. The politicians' plan assumes that what worked during a period of natural currency weakness will also work when the currency is weakened intentionally. Option B attacks this assumption by pointing out that manufacturers responded differently to the natural weakening — the same effect cannot be assumed for a deliberate policy action.",

    77: "Option B is correct. The argument depends on the assumption that government research is actually capable of producing useful improvements. Without this, the entire proposal collapses. Option A doesn't need to be assumed — the argument only requires that the government can help, not that it is the only party responsible.",

    78: "Option D is correct. (Original detail was only 'Answer (D)' — no reasoning provided. Flagged for review.)",

    79: "Option D is correct. The 'answer' given in the original detail was a lecture about study habits with no actual reasoning. The consultant responds to the lawmaker's argument by pointing out a key distinction the lawmaker overlooked — Option D identifies this method of response correctly.",

    80: "Option C is correct. The question asks what would be most important to determine whether the seismic stations will succeed. Option C is correct because the argument focuses specifically on tidal waves caused by earthquakes — any other disaster type is outside the scope of the argument.",

    81: "Option D is correct. Even if sales of the vegetarian sandwich don't increase, having it on the menu can attract groups who would otherwise avoid the restaurant entirely. This introduces a benefit beyond the sandwich's own sales, giving a valid reason to keep it on the menu despite the sales prediction. Option D weakens the argument for removing it.",

    82: "Option D is correct. The key is finding something that weakens the conclusion that humans could not have migrated during a certain period. Option D provides evidence that directly contradicts a necessary condition for the conclusion, making it the correct weakener.",

    83: "Option B is correct. The argument predicts SpendLess will gain customers after competing discount stores close. Option B weakens this by suggesting the vacated storefronts won't stay empty — new competitors will fill them, so SpendLess may not see the expected customer increase.",

    84: "Option C is correct. With fewer companies competing for recyclable plastics, the cost of raw materials falls. This lowers production costs for the company, which strengthens its competitive position. The 'I hope that helps!' in the original was not reasoning.",

    85: "Option C is correct. Option E is wrong because it doesn't explain why veterinarians rejected the offer — the question asks specifically about their reaction. Option C provides a direct reason for their reluctance.",

    86: "Option E is correct. The village was on the border between two countries, meaning it likely saw significant trade activity. A trade contract found there is more plausible than option E (people who spent their childhood deep within one country), because border locations naturally attract trade documents. Option E would be the stronger evidence of migration from the interior.",

    87: "Option C is correct. Option C is vague — it doesn't tell us the number of residents without false alarms, and it can't guarantee false alarms won't recur. This uncertainty means it doesn't confirm the measure works. Option C most directly casts doubt on whether the measure successfully enabled what it was designed to do.",

    88: "Option E is correct. The 'twin goals' are giving hunters income and ensuring manatee survival. Option A only threatens the income goal — if tourists don't want to see manatees, the tour income falls, but manatees might still survive. Option E undermines both goals simultaneously, making it the strongest answer.",

    89: "Option C is correct. ⚠️ DISCREPANCY: Original detail says 'I choose D' but the answer is C. The reasoning provided appears to argue for a different option. The original explanation seems to favor D but the correct answer is C. Flagged for manual review.",

    90: "Option D is correct. The scholar's hypothesis depends on the assumption that Roman numerals were actually used in 15th-century England. Without this, the hypothesis doesn't apply. Option C requires an additional assumption about why the specific writers used Roman numerals despite most writers not doing so — that extra step makes it weaker than Option D.",

    91: "Option C is correct. The professor doesn't directly challenge the connection between the biologist's premises and conclusion. Instead, the professor introduces additional evidence that attacks a premise, which indirectly undermines the conclusion. Option C correctly describes this method.",

    92: "Option E is correct. This is a Conclusion question — find the choice most strongly supported by the passage. A Conclusion question differs from an Inference question: instead of finding what must be true, we find the statement the passage best supports as a conclusion. Option E is most strongly supported by the evidence given.",

    93: "Option C is correct. Option E is tempting because it raises the possibility of non-European artistic influence on El Greco — but this doesn't eliminate the astigmatism explanation. It simply adds another possible explanation. Option C is the only remaining answer and correctly accounts for the argument's logic.",

    94: "Option E is correct. The question involves a safety context where passengers may need to break windows. Normal glass breaks more easily, which is an advantage in emergencies. Laminated glass, while harder to break for security, becomes a disadvantage when passengers need to escape. Option E identifies this trade-off.",

    95: "Option C is correct. The argument needs a reason why cocoa product prices will continue rising. Option C provides a direct link: if supply remains constrained and demand stays strong, prices will keep going up. Options that discuss processing capacity without addressing bean supply don't solve this.",

    96: "Option E is correct. The conclusion is that you will not suffer an allergic reaction from sulfites specifically — not that you won't suffer any allergic reaction. Even if other substances cause reactions, that doesn't contradict this conclusion. So the argument does not need to assume those other substances don't exist. Option E is the actual assumption the argument depends on.",

    97: "Option D is correct. Option D strengthens the argument by providing a second mechanism through which eco-cement reduces atmospheric CO2. Even though the reasoning about 'burning vs. using' fossil fuels introduces slight ambiguity, Option D still strengthens the argument more than any other available choice.",

    98: "Option E is correct. The experts say the plan won't achieve its goals. This is effectively a 'weaken the unstated conclusion' question. Option E shows that even if the nearby airport attracts 20% of passengers, the target airport won't actually benefit — because those redirected passengers would have used the target airport anyway, meaning no net reduction in congestion.",

    99: "Option A is correct. The argument concerns newly proposed incinerators. Option A weakens the conclusion by pointing out that the proposed designs have no additional safeguards beyond what the two existing incinerators already have — the same designs that experienced the dangerous leaks. This directly undermines the claim that the new incinerators would be safe.",
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

    print(f'Updated {len(REWRITES)} rows (51-100) and saved.')

if __name__ == '__main__':
    update_rows()
