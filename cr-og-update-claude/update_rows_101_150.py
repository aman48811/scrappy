import csv

INPUT_FILE = 'CR_OG_questions_extracted.csv'

REWRITES = {
    100: "Option B is correct. Since all the plants that thrive in metal-rich soil are closely related, they likely share a common trait that enables this. We hypothesize it's histidine. To test this, we'd check whether the other plants in the group also produce histidine. If they do, the hypothesis gains support. Option B points to the most useful way to evaluate the claim.",

    101: "Option D is correct. The first boldface is the environmentalists' conclusion (introduced by 'Thus'). The second boldface is the economist's own conclusion (introduced by 'Consequently'). Option D correctly identifies both: the first is the conclusion the economist is responding to, and the second is the economist's counter-conclusion.",

    102: "Option E is correct. The question asks what would strengthen the prediction. Options about water control or irrelevant facts don't address how the farm can simultaneously boost output and conserve water. Option E provides a mechanism that achieves both goals, making the prediction more plausible.",

    103: "Option E is correct. The shipping clerk's statements constrain when shipments could have been sent. Three building supplies shipments could have gone out on Friday or earlier; the fourth could have gone out any day Monday through Thursday (since all Friday shipments were building supplies). Option E is the only statement that must also be true.",

    104: "Option E is correct. Option A is not a weakener — it describes a past situation where Autoco provided designs, not the new arrangement. Under the new plan, if suppliers make designs themselves, Autoco will need to revise its overall car designs to accommodate them, potentially increasing time and cost. This weakens Autoco's expectation that the new arrangement will reduce both.",

    105: "Option C is correct. The argument's conclusion has nothing to do with wages. Even if wages in Vernland don't rise, assemblers might stay and keep exporting televisions to Borodia — the argument doesn't require wage changes to hold. Option E is irrelevant. Option C is the assumption the argument actually depends on.",

    106: "Option C is correct. The place where employees earned their degrees is irrelevant to the argument. Option C is the key assumption the argument depends on.",

    107: "Option A is correct. The argument requires this assumption for its logic to hold. Without it, the conclusion doesn't follow from the premises. (Original detail was pure promotional content — no reasoning provided. Flagged for review.)",

    108: "Option E is correct. Comput-o-Mart has no basic units — all their products are expensive. So whatever the salesperson recommends will be expensive regardless of the customer's actual needs. This weakens the conclusion that customers can trust the salesperson's recommendation to match their requirements.",

    109: "Option B is correct. The question asks what most logically completes the passage. Option B explains why revenues of exporters in Country X will probably continue to decline. It is the only option that directly completes the passage's reasoning, even if it's not airtight — it just needs to be the most logical completion among the five choices.",

    110: "Option A is correct. The argument is about why prices increased. The option being eliminated is out of context — it doesn't explain the price increase. Option A directly addresses this and provides the strongest justification for the attorney's argument.",

    111: "Option D is correct. The first boldface challenges the consultant's own explanation. This allows us to eliminate option E. Option D is the answer that correctly identifies the roles of both boldface portions in the consultant's reasoning.",

    112: "Option C is correct. Each gas cloud has a unique chemical signature. If two stars share the same composition, it most likely means they formed from the same parent cloud. Option C strengthens the astronomer's argument by confirming that stars inherit the chemical signature of the cloud they form from.",

    113: "Option A is correct. The question asks what would be most useful to evaluate the argument. Knowing what the new technology does tells us only one side of the comparison. The real issue is whether examining the site now vs. later maximizes long-term knowledge. Option A addresses the core trade-off most directly.",

    114: "Option C is correct. (Original detail was pure promotional ad content — no reasoning provided. Flagged for review.)",

    115: "Option C is correct. The detail mentions that more than half of people had never seen a mountain lion before — but it's unclear whether these are the same people who reported a sighting. If the people claiming sightings had no prior reference, their identification becomes unreliable. Option C correctly identifies this as the answer.",

    116: "Option A is correct. Note that the original poster reversed options A and C. At normal temperatures, Tuff performs equally to competitors. At low temperatures, Tuff performs better. The missing piece is confirming there are no other conditions that reduce Tuff's effectiveness below maximum. Option A rules out such factors, strengthening the 'maximum protection' claim.",

    117: "Option A is correct. The argument has nothing to do with non-toxic pesticides. Option A is the correct assumption the argument depends on — it directly supports the conclusion being evaluated.",

    118: "Option E is correct. The argument depends on this assumption. If the population had increased, the argument would still hold. But if the population decreased, the argument could fall apart. However, option B (about population change) is not a required assumption. Option E is the actual assumption needed for the argument's logic to hold.",

    119: "Option D is correct. Options C and E are about copyists' output and timing, but don't tell us when the document was produced or how long it took. Option D is the most relevant piece of evidence that supports the hypothesis about Codex X's production.",

    120: "Option D is correct. Option E discusses only loyal consumers — a subset of unknown size. If only 5% of consumers are loyal, the plan won't be significantly affected. Option D most seriously weakens the prediction by identifying a flaw that affects the broader customer base.",

    121: "Option D is correct. The question asks for an alternative cause for the pattern observed. Option D provides a plausible alternative explanation — one that doesn't involve the cause stated in the passage — which effectively weakens the given explanation.",

    122: "Option B is correct. Option B identifies a serious drawback to the plan. (Original detail had 'Not a drawback' as a dismissal of an option, then just 'B' followed by a signature — no actual reasoning for why B is the drawback. Flagged for review.)",

    123: "Option D is correct. The key word is 'known to have inhabited the area.' There could be other cultures not yet known to researchers from which the Mayans adopted the stone implements. This possibility weakens the conclusion, and option D is correct.",

    124: "Option D is correct. The first statement provides a premise that leads the author to conclude 'natural selection should therefore favor extreme longevity.' Understanding this causal chain is necessary before evaluating the boldface portions. Option D correctly captures the structure of the argument.",

    125: "Option C is correct. Option E is about crops that won't have genetically engineered seeds — the conclusion doesn't address these crops at all, so E is irrelevant. Option C directly weakens the argument by showing that potential cost savings on pesticides could be offset by increased costs elsewhere.",

    126: "Option D is correct. Option E suggests another mechanism for developing keratitis, which slightly weakens rather than strengthens the hypothesis. Option D is the best answer because it directly supports the scientists' hypothesis about what causes keratitis.",

    127: "Option D is correct. The bulk of travel expenses for airplane travelers was likely spent on airfare itself, with non-airfare transportation (car rentals, etc.) being a smaller fraction. The majority of non-airfare travel expenses were likely incurred by the larger group who didn't fly. Option D is the only statement that must be true.",

    128: "Option D is correct. The argument focuses on the addition of large quantities of the virus — naturally present levels fall outside the scope. Option B might seem relevant but misidentifies the objective: we want something that strengthens the use of this virus as a tool to help shellfish, and Option D does that best.",

    129: "Option B is correct. The question is about what most strongly supports the psychologists' interpretation. Options about how payment is made are irrelevant to the psychological interpretation being tested. Option B directly supports the interpretation.",

    130: "Option D is correct. The argument doesn't assume employees won't accept cuts — it's giving advice about what the union should do. The logic doesn't hinge on employee behavior. Option D is the assumption that the argument actually requires.",

    131: "Option C is correct. Option A says maize became popular in Europe — doesn't explain the inconsistency. Option B says there's more niacin in maize — irrelevant since the niacin is in an unabsorbable form. Option C explains why the Americas avoided niacin deficiency — likely due to a preparation method that made niacin absorbable. Option D is irrelevant.",

    132: "Option D is correct. Firms can be selective about which cases they take on contingency — choosing cases they're most likely to win. This means the additional payout from winning can compensate for the cases they decline or lose. Option D directly strengthens the prediction.",

    133: "Option B is correct. The answer being eliminated doesn't help us address the conclusion. Option B is the most important factor to determine in order to evaluate the argument. (Original detail had a signature — stripped.)",

    134: "Option E is correct. If option E is true, then Edmund Spenser with reduced-fee status almost certainly couldn't have had an affluent father. This confirms that reduced fees meant the student came from a less-affluent family — which is exactly the assumption the argument requires. Option E is the correct answer.",

    135: "Option D is correct. The argument notes a 3% drop in the percentage of retirees going to Florida. But if the total number of retirees has grown significantly, the absolute number going to Florida could still be higher than before. For example, 30% of 20,000 is more than 33% of 10,000. This weakens the conclusion that fewer retirees are choosing Florida.",

    136: "Option D is correct. Option E discusses plants other than garlic, which adds nothing to the argument about garlic's diallyl sulfide repelling mosquitoes. We already know diallyl sulfide is in garlic and repels mosquitoes. Option D most directly strengthens the conclusion by adding new, relevant evidence.",

    137: "Option E is correct. (Original placeholder — original content was forum discussion only. Flagged for review.)",

    138: "Option A is correct. The argument depends on the assumption that vending machines would lead to a net increase in soda consumption. If students would buy soda elsewhere anyway, the machines make no difference to health outcomes. Option A is what the argument requires to hold — without it, the conclusion doesn't follow.",

    139: "Option E is correct. Left-handed snails that survive snake attacks go on to reproduce, creating more left-handed snails. Option E strengthens this by showing snakes specifically fail more often when attacking left-handed snails, meaning more left-handed snails survive and reproduce. This supports the argument that asymmetrical jaw evolution drove left-handed snail prevalence.",

    140: "Option D is correct. The comparison in the passage is between competitive swimmers and other competitive athletes. If latent asthma triggered by strenuous activity affected all athletes equally, we'd expect it to show up across all sports — not just swimming. This makes swimming-specific factors more relevant, and Option D is the only answer that accounts for this distinction.",

    141: "Option D is correct. (Original detail was just 'Choice (D) is the best answer' — no reasoning provided. Flagged for review.)",

    142: "Option D is correct. The conclusion is that GFC will increase its net income. Option A (other funding source) tells us nothing new about income. Option B (local vs. non-local workers) is irrelevant to net income. Option D directly addresses the income question and most strengthens the conclusion.",

    143: "Option B is correct. The question asks what Centennial Commercial would most need to know. Option E introduces a comparison to new-construction investment — but Centennial already has an office building and is deciding what to do with it. That comparison is irrelevant. Option B addresses the actual decision at hand.",

    144: "Option B is correct. Without knowing what notes the missing piece of the flute could produce, we can't know if it completed a diatonic scale. The author's statement that the flute could produce a diatonic scale is an opinion, not a fact — because there's no concrete evidence about the missing holes. Option B correctly identifies this role.",

    145: "Option E is correct. The drought caused the drop, and since the drought has ended, the problem will resolve on its own. The plan would therefore serve no purpose — the issue it aims to fix is already correcting itself. This is the most relevant and serious potential weakness.",

    146: "Option C is correct. Acidity may indicate quality, but it is not used to define it. Just as mass number is defined by protons and neutrons (not mass), quality here is defined by a parameter independent of acidity. Acidity is a signal, not the defining criterion. Option C correctly reflects this inference.",

    147: "Option C is correct. Option C hits the identified flaw directly — it addresses the specific vulnerability in Kayla's reply that was identified in the pre-thinking. It is the most targeted and clearly correct answer among the options.",

    148: "Option B is correct. Option D would weaken the argument — if all small businesses are already served by large foreign banks, local bank financing adds no value. Option B most logically completes the argument by filling the gap about what makes local bank financing helpful.",

    149: "Option A is correct. The argument is about whether a fee at the point of disposal will reduce wastage. What matters is whether the fee applies at that specific moment of throwing off. Option A is correct because it directly addresses whether the fee structure achieves the intended behavioral change.",
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

    print(f'Updated {len(REWRITES)} rows (101-150) and saved.')

if __name__ == '__main__':
    update_rows()
