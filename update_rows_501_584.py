import csv

INPUT_FILE = 'CR_OG_questions_extracted.csv'

REWRITES = {
    500: """Answer: A

Norway has banned tobacco advertising since 1975, yet teen smoking there is at least as prevalent as in countries without such bans. This shows that advertising is not the ONLY factor driving teen smoking — other factors (peer pressure, social norms, availability) must also play a role. The example doesn't prove ads have zero effect, only that they aren't the sole cause. A is the best-supported conclusion.""",

    501: """Answer: C

The passage states that when the ratio of inside sales to inside purchases falls below 2:1, a stock price rise is imminent. For MEGA Corp, inside sales/purchases = 1/9, which is far below 2. Applying the stated rule directly, a rise in MEGA stock price is imminent. C follows logically from the given principle.""",

    502: """Answer: C

The passage describes established companies' defensive strategy: rather than innovating, they try to improve what they already have, and in doing so they underestimate the impact of others' innovations. C — a slide rule manufacturer reacted to electronic calculators by trying to make better slide rules — is the clearest illustration of this behavior. They defended their existing product instead of adapting, and were overtaken by the new technology.""",

    503: """Answer: E

The recommendation is to provide smoke hoods to protect passengers from toxic gases during post-accident evacuations. E states that in many accidents, passengers who were physically able to reach emergency exits were nevertheless overcome by toxic gases before they could exit. This shows the gases are a real, lethal threat at the exit point itself — precisely the scenario smoke hoods would address. E most strongly supports the officials' recommendation.""",

    504: """Answer: C

The argument concludes that perceived nuclear threat decreases willingness to save (postpone consumption). The premise is: more testing correlates with more spending; less testing correlates with more saving. The missing link is C — people's PERCEPTION of nuclear threat depends on the amount of testing. Without this connection, the correlation between testing levels and saving behavior doesn't support the conclusion about perceived threat.""",

    505: """Answer: C

Satellite mishaps raised insurance costs, adding pressure to squeeze more performance from existing satellites. The conclusion is that this will cause costs to rise further. C provides the key causal link: greater performance demands lead to more frequent breakdowns. This closes the loop — demanding more from satellites causes more failures, which triggers more insurance claims, driving costs still higher.""",

    506: """Answer: A

The argument: wholesale cotton prices fell, so retail prices will inevitably fall too. A weakens this by noting that the cost of processing raw cotton into cloth has increased. Even if wholesale raw cotton is cheaper, higher processing costs could offset those savings, meaning retailers may not see lower input costs overall. The drop in raw material price doesn't guarantee a drop in retail price if other costs have risen.""",

    507: """Answer: B

Three Lightning-built planes crashed, yet Everett ordered three more from Lightning. Ordinarily, users avoid accident-prone products. B explains the decision: the crashes were due to pilot error, not a flaw in the planes, and the plane's quality resulted in many survivors. The planes demonstrated their value by protecting passengers even when pilots erred. This makes repurchasing them a rational choice.""",

    508: """Answer: B

⚠️ DISCREPANCY: The original explanation cited answer D, but the Answer column shows B.

The experiment showed the artificial sweetener caused lower cognitive performance. The conclusion is that the amino acid constituent of the sweetener causes this effect by raising amino acid levels in the blood. B provides the biological mechanism that makes this plausible: high blood amino acid levels inhibit the synthesis of a substance required for normal brain function. This directly links the sweetener's amino acid to the observed cognitive decline, supporting the conclusion.""",

    509: """Answer: C

The passage states that in open-market countries, domestic oil prices rise whenever international prices rise — regardless of whether the country imports any oil. C is the most supported inference: the domestic oil market in an open-market country is effectively part of the international market. Even if most oil is sold domestically, domestic producers can sell on the world market, so domestic prices track international prices.""",

    510: """Answer: B

The mayor argues the $5/day fee will cause drivers to switch to buses because it exceeds round-trip bus fare. B weakens this by pointing out that parking fees ALREADY make driving considerably more expensive than taking the bus. If people are already paying more to drive and still choosing to drive, adding another $5 fee is unlikely to change their behavior. The fee doesn't change the economic calculation enough to alter choices.""",

    511: """Answer: E

Airlines used to avoid the safest (heaviest) seats to save fuel. This year the safest seat is selling best. The conclusion: airlines now prioritize safety over fuel costs. E undermines this by revealing the safest seat this year weighs LESS than most other seats. If it's both safest AND lightest, airlines might be buying it primarily for its fuel-efficiency — not because safety has become a higher priority. The conclusion about a shift in values is unsupported.""",

    512: """Answer: D

Asthma attacks occur when messenger molecules are activated unnecessarily by harmless triggers like pollen. The plan: develop a medication that prevents receipt of these messenger signals. The critical flaw is D — such a medication cannot distinguish between messages triggered by harmless substances (pollen) and those triggered by genuinely noxious air. Blocking all signals would also prevent the lungs from protecting themselves against actual toxic substances, defeating the purpose.""",

    513: """Answer: E

The study shows top managers use intuition significantly more than lower-level managers. The argument concludes this confirms that intuitive decision-making is a more effective approach. The gap: being a top manager doesn't automatically mean being a more effective decision-maker. The necessary assumption is E — that top managers ARE actually more effective than lower-level managers. Without this, the argument doesn't establish intuition as superior.""",

    514: """Answer: A

Protein drugs like insulin must be injected because stomach digestion destroys them. Nonprotein drugs resist digestion and can be taken orally. The promising research direction is A — coating insulin with compounds whose bonds resist digestion but are broken down by the target cells. This would allow insulin to survive the digestive tract intact and only be released at the intended destination, making oral administration possible.""",

    515: """Answer: B

The original report concludes that most forests in Canada are NOT being damaged by acid rain. Critics want to change this to: most forests don't SHOW VISIBLE SYMPTOMS of damage. B captures the critics' rationale: acid rain could be causing damage that hasn't yet become visible. The original conclusion overstates what the evidence (lack of visible symptoms) actually shows — absence of visible damage is not the same as absence of damage.""",

    516: """Answer: B

The passage presents a tuition prepayment plan where parents pay current rates and the program covers future tuition at public colleges. B gives a reason NOT to participate: if the prepayment money were instead put in an interest-bearing account, the accumulated amount would exceed the future tuition cost. In other words, investing the money would yield better returns than locking it into prepayment, making the program financially disadvantageous.""",

    517: """Answer: C

A Greek statue supposedly from the 6th century BC has a uniform surface finish characteristic of a chemical bath used by forgers to simulate weathering. The conclusion: it's probably a forgery. C weakens this by revealing that this same chemical bath was historically used by legitimate dealers and collectors to clean genuinely ancient sculptures. If authentic pieces were also treated with this bath, a uniform surface doesn't reliably indicate forgery — the statue could be genuine and simply cleaned.""",

    518: """Answer: E

VC-funded start-ups have lower failure rates. The conclusion: source of financing is more important to success than entrepreneur characteristics or strategic planning. E undermines this by revealing that VCs base their funding decisions specifically on entrepreneur characteristics and planning quality. This shows the relationship is backwards causation: VCs select companies that are already likely to succeed. The financing doesn't cause success — strong fundamentals cause both the VC investment and the success.""",

    519: """Answer: E

An eyeglass manufacturer offered a discount if orders exceeded last year's summer quarter by 20%. Many distributors qualified, yet sales didn't improve. E explains the paradox: most qualifying distributors were longtime customers who simply consolidated — making fewer total shopping trips but spending more per trip. Their total annual purchases didn't increase; they just front-loaded orders to hit the 20% threshold. The program attracted no new business.""",

    520: """Answer: D

The artificial sweetener experiment compared experimental group (sweetener) and control group (no sweetener). The experimental group showed lower cognitive abilities afterward. D strengthens the conclusion by confirming the two groups were evenly matched for cognitive abilities BEFORE the experiment. Without this, one could argue the experimental group was already cognitively weaker at the start, not because of the sweetener.""",

    521: """Answer: D

Florida retirement communities have few families with small children, yet children's furniture rental businesses thrive. D resolves the paradox: many elderly residents have visiting grandchildren for several weeks each year. Renting furniture for occasional visits is more practical than buying, explaining the demand for children's furniture rentals in a community with almost no permanent child residents.""",

    522: """Answer: D

Original argument structure: "It is against law X to do Y. But if the US doesn't, other countries will." The logic acknowledges illegality but dismisses it with "someone else would do it anyway." D matches this structure exactly: "It is against the law to burglarize. But someone else certainly would have burglarized that house if the defendant hadn't." Both acknowledge the illegality, then excuse the act by saying others would have done it.""",

    523: """Answer: C

The hiker sees a milepost reading 21 (facing) and 23 (back). She expects the next milepost (1 mile ahead) to be the midpoint (22 facing, 22 back). Instead it reads 20 facing and 24 behind. C explains: the facing number indicates miles REMAINING to the path's end, not miles from the start. If 21+23=44 total miles: she's at mile 23 from start (21 to end). One mile forward: 22 from start, 20 to end. Wait — the milepost actually shows 20 and 24, so total = 44. C is correct — the numbers represent miles to the near end and far end respectively.""",

    524: """Answer: C

Airlines want to install collision-avoidance systems immediately even though they're not fully tested. Pilots refuse to fly planes with untested systems. C explains the pilots' position and the flaw in the airline's reasoning: the likely malfunctions of untested systems will cause even MORE crashes than the systems will prevent. Installing unreliable equipment creates greater danger than the problem it's meant to solve.""",

    525: """Answer: C

A study found common land was in better condition than private land, challenging Hardin's theory that common land is always used less carefully. To evaluate this study properly, C asks the critical question: was the private land comparable in quality to the common land BEFORE either was used for grazing? If private land started in poorer condition, the study's conclusion (that common land is better maintained) is invalid — the difference might reflect initial quality, not usage patterns.""",

    526: """Answer: B

The analyst's chain: HK retains capitalism IF useful to China; useful IF prosperous; prosperous IF no world economic crisis. The inference in B: if HK retains capitalist ways until 1997, China will allow it afterward. This follows because China's decision is driven by ongoing conditions (usefulness/prosperity), not a one-time choice. As long as HK remains prosperous (no world crisis), the chain of reasoning holds and China continues to allow capitalism after the 1997 handover.""",

    527: """Answer: D

Competition normally lowers prices, yet competitive hospital markets have higher surgery costs. D resolves this: many simple, low-cost surgeries can now be done safely in physicians' offices and are no longer performed in hospitals. Hospitals in competitive markets are left performing only serious, complex, expensive cases. The higher average cost reflects the changed case mix, not inefficiency.""",

    528: """Answer: A

Country Z's NHCP receives more funds each year (both absolute and as % of GNP), yet health care standards have declined. A states that the percentage of funds spent on ACTUAL health care increased while administrative costs decreased. If A is true, more money is reaching direct care but quality is still declining — which means the program is spending more efficiently but something else is causing the decline. A undermines the argument that waste or administrative bloat explains the decline.""",

    529: """Answer: D

Food aid to Ryana: aid will depress local food prices → drive local producers out of business → Ryana less able to feed itself. D provides the strongest counter: since Ryana's food market is regulated, donated food won't depress official prices. Furthermore, the government can sell donated food and use the proceeds to support local farmers. D directly neutralizes both mechanisms of harm identified in the argument.""",

    530: """Answer: E

Proposed bylaw: when multiple nominees are needed for one office, each must consent before being told who the other nominees will be — and must be told who the others are BEFORE consenting. E identifies the logical paradox: if there is more than one prospective nominee, no one can be named first without the others already having consented (to be told to the first person). But no one can consent without first being told who the others are. The rule creates a circular dependency that makes any nomination impossible.""",

    531: """Answer: C

The sample includes only companies that have been operating for at least 20 years (since data from 20 years ago is needed). Newer companies — which may tend to have younger CEOs — are excluded. The conclusion that CEOs are older "in general" is drawn from a biased sample that excludes all newer firms. C identifies this sampling limitation, which undermines the generalization.""",

    532: """Answer: E

Only 10% of smokers switch brands per year, yet manufacturers spend 10% of gross receipts on magazine ads. Conclusion: ads aimed at brand-switching didn't justify the expense. E is the best criticism: the 10% switching figure is an industry-wide aggregate. For any specific company, even capturing a fraction of those switchers could represent a huge gain — if one brand steals all the switchers, it could increase its market share by 50%. Industry-level data doesn't reveal whether the ad spend was profitable for any individual manufacturer.""",

    533: """Answer: E

Value = quality/price. Higher value → better competitive position. Therefore raising quality or lowering price increases the likelihood consumers will choose the product. The key assumption is E: consumers' perceptions of quality are based on ACTUAL quality. If consumers judge quality by price (assuming cheaper = lower quality), then lowering the price could paradoxically reduce perceived value and hurt competitive position. E is required to ensure that genuine improvements translate into perceived improvements.""",

    534: """Answer: A

In January, fewer houses were sold but average prices rose sharply. The explanation: A says higher-priced house sales were unaffected because wealthy buyers have fewer constraints. If sales of cheap and mid-priced homes dropped (buyers waiting for lower rates) but expensive home sales held steady, the mix shifted toward expensive homes. Even with stable expensive-home sales, the average price of ALL sold homes rises when the lower-priced portion of the market stalls.""",

    535: """Answer: A

A state sales tax of 7% on consumer goods is regressive because lower-income people pay a higher percentage of their income in this tax than wealthy people do. For this to be true, lower-income people must spend a larger share of their income on taxable consumer goods than wealthy people do (who save or invest a greater proportion). A is the necessary underlying assumption: spending on taxable goods is equal across income levels (in dollar terms), so as income decreases, the tax represents a higher percentage.""",

    536: """Answer: B

Only 10% of smokers switch brands per year, yet manufacturers spend 10% of gross receipts on cigarette advertising. The conclusion: ads aimed at inducing brand-switching didn't justify the expense. B offers the best alternative explanation: advertising isn't aimed at brand-switching at all — its primary purpose is to attract first-time smokers to replace those who quit. If ads successfully recruit new smokers, the spending may be well justified even if brand-switching is minimal.""",

    537: """Answer: E

Low immune-system activity correlates with lower mental health scores. The researcher concludes the immune system protects against mental illness. E undermines this by offering an alternative explanation: high stress first causes mental illness AND then causes decreased immune-system activity. If true, mental illness causes low immune activity (not the reverse), and the observed correlation exists because both are driven by a third factor (stress). The researcher has the causal direction reversed.""",

    538: """Answer: A

Blood banks will screen for NANB hepatitis. The tests disqualify 5% of prospective donors but miss 2/3 of NANB carriers. Therefore roughly 10% of actual donors will still carry NANB. For this calculation to be valid, A must be assumed: donors carrying NANB hepatitis are not, in large numbers, also carrying other infections screened for routinely. If NANB carriers commonly tested positive for other infections, they'd already be disqualified by existing screens — and the 10% figure would be an overestimate.""",

    539: """Answer: D

Bird deaths increased after pesticide sprayings. Manufacturers claimed the increase was due to increased volunteer searching following publicity, not actual increased deaths. D undermines this claim: agricultural workers noticed initial increases in bird deaths BEFORE any publicity existed. If the deaths were noticed before publicity could have generated volunteer observers, the explanation that more observers (not more deaths) caused the increased counts is invalid.""",

    540: """Answer: B

Meteorologists claim an accurate mathematical model would enable precise weather forecasting — but this is an "idle boast immune to evaluation" because any bad forecast would be blamed on an imperfect model. B challenges this by noting that significant gains in model accuracy are accompanied by clear gains in forecast precision. If improvements in models consistently produce measurable improvements in forecasts, then the relationship between model quality and forecast quality IS evaluable and testable — the claim is not immune to evaluation after all.""",

    541: """Answer: A

Researchers hypothesize that westernized Blacks have higher blood pressure due to an interaction between historically limited salt access (causing efficient salt retention) and modern high-salt diets. A states that descendants of peoples from regions where salt was ALWAYS available (Senegal, Gambia) have LOW blood pressure. This supports the hypothesis: those whose ancestors had consistent salt access did not develop hyperefficient salt retention, and thus their blood pressure remains low in a high-salt modern environment.""",

    542: """Answer: C

A copper mining company argues that import quotas are needed to keep copper prices up so they can stay in business. A wire manufacturer counters that higher copper prices from quotas would be harmful to the wire industry. C correctly identifies what the wire manufacturer's response accomplishes: it shows the mining company's proposal would have a negative effect on the mining company's own business — wire manufacturers are customers of the mining company, so harming wire manufacturers ultimately harms copper miners' sales volume.""",

    543: """Answer: B

Continuous fluorescent light helped hamsters with inherited heart disease live 25% longer than those in alternating light/dark conditions. The question asks which real-world problem this research method could best address. B — whether hospital lighting promotes patient recovery — maps directly: the study's method (comparing continuous vs. partial lighting on organisms with inherited disease) is exactly how you'd investigate whether altered lighting conditions affect recovery in vulnerable human patients.""",

    544: """Answer: E

Sales campaigns emphasize user-friendliness, but this is premature and irrelevant because potential buyers are addressing the logically prior question of "whether ___." E completes this correctly: whether they have enough sensible uses for a personal computer to justify the expense. Before caring about ease of use, buyers first need to determine whether they need a computer at all. User-friendliness is irrelevant if the buyer hasn't yet established a reason to own one.""",

    545: """Answer: C

People estimate likelihood based on how often something comes to their attention (salience). Newspapers give prominent coverage to LOCAL crime over crime elsewhere. Therefore, local newspaper readers will overestimate the amount of crime in their own locality RELATIVE to crime in other places. C states this conclusion directly and correctly. Other options introduce unsupported comparisons or go beyond what the argument establishes.""",

    546: """Answer: E

Red Label offered discounts to customers who spent $50+ per trip, and $50+ receipts increased significantly. But E shows the program did NOT attract new high-spending customers. Instead, most of the people now spending $50+ are longtime customers who previously made more frequent small trips but now make fewer, larger trips to hit the discount threshold. Their total spending didn't increase — they just consolidated trips. The apparent success (more large receipts) masks the absence of real revenue growth.""",

    547: """Answer: A

Y was believed to cause Z. A new report suggests X may be the true cause (X precedes both Y and Z). A best supports the new report: in cases where X occurs but Y does NOT, X is still usually followed by Z. This shows X can produce Z without Y being present at all — demonstrating X is sufficient to cause Z independently, supporting the hypothesis that X (not Y) is the real cause.""",

    548: """Answer: B

The "idle boast" argument: any inadequate weather forecast would be blamed on an imperfect model, and meteorologists would always claim the model needs more improvement — making the claim unfalsifiable. B strengthens this by noting that volcanic eruptions and fossil fuel combustion (among other processes) cannot be quantified accurately but significantly affect the atmosphere. This means there will always be unquantifiable factors to blame for forecast failures, confirming the boast is immune to evaluation.""",

    549: """Answer: D

Many early video recorder buyers lost interest in obtaining videos after about 6 months. The passage concludes that once the market is saturated, the video trade will decline. D weakens this by explaining that early buyers are specifically people who are "quick to acquire novelties but also quick to tire of them." This group is not representative of all buyers. Mainstream buyers who adopt later may sustain their interest much longer, so the early adopters' behavior doesn't predict the market's long-term trajectory.""",

    550: """Answer: E

Counties with the most TVs per capita have the lowest incidence of mosquito-borne encephalitis. Researchers conclude people watch more TV, stay indoors more, and get fewer mosquito bites. E strengthens the argument by confirming the key assumption: more TVs per capita actually does translate into more time spent watching TV. Without this link, the correlation between TV ownership and low encephalitis rates doesn't support the behavioral explanation.""",

    551: """Answer: B

New Hampshire Division set a new annual sales record for that division. This seems surprising since it has the smallest market and lowest sales in the company. B identifies the flaw: the record being discussed is specific to New Hampshire's OWN history — it surpassed its own previous best, not any other division's performance. Since the division is competing against its own record, its small size relative to other divisions is irrelevant. Setting a personal best isn't surprising regardless of how small the division is.""",

    552: """Answer: D

Four of the top 20 exporters in 1953 had the same export share in 1984, so they're proposed as models for stable export share. D undermines this: two of those four had much larger shares in 1970, and two had much smaller shares in 1970. Their shares fluctuated significantly through 1970 before returning to 1953 levels by 1984. The path was not stable — it was volatile. Countries following their example might experience the same volatility, not stability.""",

    553: """Answer: C

Standardized (canned/prepackaged) diets produce LESS food waste overall, but a GREATER proportion of fresh produce in food waste. Non-standardized diets produce more food waste overall, but a SMALLER proportion of fresh produce in that waste. C follows directly: households with less standardized diets have a smaller proportion of fresh produce in their food waste. This is a direct logical inference from the two stated relationships.""",

    554: """Answer: E

Quality Circles participants were less satisfied after two years. E says they felt at the START that participation might improve their situation. This is relevant: workers who joined with high hopes and then saw those hopes unfulfilled would naturally feel disappointed and less satisfied. Their initial optimism, met with disappointing results, explains the decrease in satisfaction as a consequence of unmet expectations created by the program itself.""",

    555: """Answer: B

For the city's public transportation to improve under private management, the plan must assume B — that political considerations would not prevent private firms from ensuring revenues cover costs. The whole argument against municipal management is that politics prevents necessary fare hikes and service cuts. If private firms face the same political pressures (e.g., public outcry, regulatory constraints), privatization solves nothing. B is the essential assumption the plan depends on.""",

    556: """Answer: C

Hospital death rate lists were adjusted for patient ages. C provides grounds for objection: very old patients are less likely to survive the same illnesses or surgical procedures as younger patients. The adjustment may account for the proportion of elderly patients, but not for the severity of age-related vulnerability at the most extreme ages. A hospital serving very elderly patients might have a higher death rate not because of poor care but because of the extreme fragility of its patient population — which age-adjustment alone doesn't fully capture.""",

    557: """Answer: B

Argument: government minimum wage prices out teen workers, so a sub-minimum teen wage would reduce teen unemployment. B weakens this by noting that teen unemployment rose even when the minimum wage remained constant. If unemployment increases independent of minimum wage changes, then the minimum wage is not the primary cause of teen unemployment. Reducing it via a sub-minimum wage won't necessarily fix a problem driven by other factors.""",

    558: """Answer: D

Teresa argues manned spaceflight has no future because it can't compete economically. Edward counters with manned spaceflight's safety record. D identifies the flaw in Edward's response: he fails to address Teresa's point because he assumes there is no serious impediment to transporting people into space — but Teresa's point was precisely that there IS a serious impediment: the economic one. Edward's safety statistics don't speak to whether manned spaceflight is cost-competitive.""",

    559: """Answer: A

The advertiser argues: ad revenue lets publishers charge less per copy, so consumers benefit economically. The consumer counters: but consumers pay for ads through higher product prices — so the apparent saving on the copy price is offset by higher prices for advertised products. A correctly identifies the consumer's method: alleging something that, if true, would weaken the advertiser's conclusion (the net economic benefit to consumers is not as claimed).""",

    560: """Answer: B

Child's World succeeded with self-service and computerized inventory for toys. It now plans to apply the same model to children's clothes. The plan assumes B — that personal service by sales personnel is not required for selling children's clothes successfully. For toys, self-service works because shoppers can evaluate products independently. The same model for clothes would fail if customers need help with sizing, fit, or style — making B the key assumption the plan rests on.""",

    561: """Answer: A

The electronic transmittal operators argue the Postal Service would have an unfair advantage (cross-subsidizing electronic services with monopoly profits from first-class mail). For this argument to hold, A must be assumed: if the Postal Service offered electronic transmission, it could not make a profit on first-class mail. Without this assumption, the PS could profit from both services independently, and there would be no cross-subsidy advantage to complain about.""",

    562: """Answer: C

The argument that women entering male-dominated professions will cause prestige to decline uses past examples (teachers, secretaries) to predict the future. C correctly characterizes this as an analogy between past and future — it draws on historical patterns to project what will happen in similar future situations. The argument's strength and weakness both hinge on whether the past cases are truly analogous to the future ones.""",

    563: """Answer: B

Mr. Primm says teaching hospitals wouldn't be profitable without public subsidies. Ms. Nakai counters: the best physicians are attracted to teaching hospitals' complex cases, and they can charge premium prices for this sophisticated care — making such hospitals profitable. The argument depends on B: sophisticated, nonroutine medical care commands a high price. Without this, attracting elite physicians doesn't translate into profitability.""",

    564: """Answer: E

A weapons-smuggling incident occurred in country Y. The argument concludes the government must have known about the weapons because Y is a closed society. The logical assumption is E: in a closed society, the government has knowledge about everything that occurs in the country. Without this general principle, the fact that Y is a closed society doesn't logically imply government knowledge of this specific incident.""",

    565: """Answer: D

The electric-power company built larger, more efficient plants to increase profits while lowering rates — and it worked. They now plan to replace an older plant with one three times the capacity. The plan does NOT require D as an assumption: that safety measures would be the same as those for the replaced plant. Safety measures could be better or different without affecting the financial logic. D is not a necessary assumption because the financial benefits of efficiency and volume don't depend on safety protocols being identical.""",

    566: """Answer: C

The Postal Service electronic transmission scenario: the electronic operators' argument hinges on the PS using monopoly profits from first-class mail to subsidize electronic services. For this concern to be coherent, C must be true — the electronic transmittal operators must believe the PS actually makes a profit on first-class mail. If they didn't believe this, the entire "unfair advantage from cross-subsidization" argument collapses. C must be assumed for their argument to make sense.""",

    567: """Answer: A

The argument: banning cigarette ads won't reduce teen smoking because teens already know cigarettes exist and don't need ads for that information. A weakens this by pointing out that ads do more than convey information — seeing or hearing an advertisement tends to increase people's desire for the product. If ads increase desire (not just awareness), then banning them could reduce the appeal of smoking, even among teens who already know cigarettes exist.""",

    568: """Answer: A

Mr. Lawson argues: national family policy (paid parental leave + daycare) → reduces employee stress → improves employee productivity. The gap between reduced stress and improved productivity requires a bridge. A provides it: high stress can cause unhappiness and poor family adjustment. The reasoning chain becomes: policy → less stress → more stable, happier family life → employees function better at work → improved productivity. A links the stress reduction to concrete outcomes that enable better work performance.""",

    569: """Answer: B

A fixed-rate sales tax is regressive — poor people pay a higher percentage of income. For this to be true, B must be inferable: poor people spend a larger proportion of their income on purchases of taxable consumer goods than wealthy people do. Wealthy people save and invest more of their income, so less of their total income is exposed to the sales tax. This spending disparity is what causes the tax to be regressive.""",

    570: """Answer: D

Blood bank NANB screening: tests disqualify 5% of prospective donors but miss 2/3 of NANB carriers. Therefore ~10% of actual donors still carry NANB. D is the logical consequence: blood supplies available from blood banks will go down. Since 5% of prospective donors are now disqualified, the pool of eligible donors shrinks. Even if demand remains constant, fewer eligible donors means less blood available.""",

    571: """Answer: C

The cloning/tissue-culture techniques allow identical plants to be mass-produced. C is the EXCEPTION — not a benefit to farmers but a drawback: plant diseases and pests spread more rapidly among genetically uniform plants than among genetically diverse ones. All other choices (A, B, D, E) describe genuine benefits: faster development of superior strains, uniform growth rates, easier mechanical harvesting, and easier introduction of special traits.""",

    572: """Answer: E

The argument uses historical precedent to predict the future: as women entered teaching, banking, and secretarial work, those professions lost pay and prestige; therefore the same will happen in accounting, law, and medicine. E weakens this by noting that the economic and sociological forces governing today's high-status professions are significantly different from those that governed the past examples. If the underlying conditions differ, the historical analogy doesn't hold, and the prediction may be wrong.""",

    573: """Answer: A

Psychological research found football and hockey players move to hostility more quickly than swimmers. Researchers concluded that contact sports encourage hostility. The alternative explanation is that hostile people self-select into contact sports. A strengthens the researchers' conclusion by showing the change happened DURING the season (not pre-existing): players became more hostile during the season and remained so — while swimmers showed no increase. This timing pattern supports causation (sport → hostility) over selection.""",

    574: """Answer: C

Pepper production has been below world sales for three years, causing prices to soar. Growers who switched from pepper to cocoa are now implied to regret their decision. C supports this: if those growers hadn't switched, pepper supplies would not be as low as they are. Their exit contributed to the supply shortage — and by extension, they missed out on the windfall from the high pepper prices their own departure helped create.""",

    575: """Answer: E

Stronger patent laws → encourage manufacturer investment in new products → frequently increase productivity. E states the conclusion most directly supported: stronger patent laws would stimulate improvements in productivity for many manufacturers. This follows as a logical chain from the two given premises — it's a valid conclusion, not a new assumption or an unsupported prediction beyond what the argument establishes.""",

    576: """Answer: D

Pepper production has been below sales for three years. D is a direct logical inference: surplus stocks of pepper have been reduced. If production falls short of sales year after year, the gap must be covered by drawing down existing stockpiles. After three years of this, surplus stocks must have been significantly depleted. D follows necessarily from the supply-demand imbalance described.""",

    577: """Answer: E

Amusement parks use live shows deliberately to manage crowd flow. Lunchtime shows relieve restaurant pressure; evening shows serve a different purpose. E correctly completes the passage: evening shows encourage visitors to stay late in order to utilize restaurants at optimal levels for as much of the day as possible. The goal is keeping restaurants steadily busy throughout the day — lunchtime shows spread peak demand, while evening shows extend the dining window into the evening.""",

    578: """Answer: E

Researchers use computer analysis to find hidden layers under paintings, claiming mountainous scenery was once in the Mona Lisa. Skeptics argue that earlier X-ray analysis found nothing unusual, undermining the new claims. E explains why the skeptics' argument fails: X-ray analysis is capable of detecting only lead-based white pigments in subsurface layers. If the hidden scenery was painted with other pigments, X-rays would miss it entirely — the absence of X-ray evidence doesn't mean nothing is hidden.""",

    579: """Answer: A

Archaeologists believe the siege happened at the lower layer, but type 3 pottery (from AFTER the siege period) was found at the bottom of the middle layer. A weakens the evidence for the lower layer by introducing an alternative explanation: gerbils dig large burrows, and objects can fall into these burrows from upper layers when they collapse. This means later-period pottery (type 3) could have migrated downward through gerbil burrows, undermining the stratigraphic integrity of the layers.""",

    580: """Answer: C

The middle layer has type 3 pottery (from AFTER the siege period) at its very bottom. This means the middle layer's earliest deposits already contain post-siege era artifacts. C is the supported conclusion: the middle layer does not represent the siege period. Since siege-era events predate the type 3 pottery, and type 3 appears at the bottom of the middle layer, the siege must have occurred before the middle layer was deposited.""",

    581: """Answer: C

Ross says Company X's profitability since privatization proves businesses fare better under private ownership. Julia counters: X has been profitable since the appointment of a first-class manager, not since privatization per se. C identifies the flaw in Ross's reasoning: he leaves open the possibility that the cause he cites (privatization) came AFTER the effect he attributes to it (profitability). If the manager was the real cause, and was appointed after privatization, then privatization preceded the manager but the manager — not privatization — drove the profit.""",

    582: """Answer: D

Financial Forecaster ad: "One-third of subscribers are millionaires, over half are in top management. Shouldn't you subscribe?" A non-millionaire/non-manager would subscribe only if they drew conclusion D: that subscribing to Financial Forecaster helped those subscribers BECOME millionaires or top managers. This is the key questionable inference the ad invites — conflating correlation (successful people subscribe) with causation (subscribing made them successful). Without D, the ad gives no reason for an ordinary person to subscribe.""",

    583: """Answer: D

A realtor calculated that a family with Millington's median income ($28,000) could afford the median-priced house ($77,000) based on an 11.2% mortgage rate and a rule that a family can spend up to 25% of annual income on housing. D says the actual mortgage rate was only 10%, not 11.2%. A lower interest rate means lower monthly payments, making the house even MORE affordable than the realtor calculated — which supports, rather than undermines, the conclusion. D does not call the calculation into question.""",
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
    print(f'Updated {len(REWRITES)} rows (501-584) and saved.')

if __name__ == '__main__':
    update_rows()
