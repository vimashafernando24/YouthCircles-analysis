# Youth Circles: acceptance protocol and reproducibility record

This document accompanies the ICCDA 2026 paper TN2029, *Youth Circles: From a
Small Mixed-Type Survey to Evidence-Grounded Programme Matching for a National
Youth Agency*. It records every preprocessing rule, clustering setting,
acceptance threshold and audit rule used in the paper, so that each reported
decision can be traced to code in this repository.

Raw survey responses and person-level outputs are confidential and are not
included (see `README.md`). All counts below are aggregates.

Group codes used in the code: **D** = students, **E** = unemployed job-seekers,
**F** = employed youth, **G** = inactive youth.

---

## 1. Cohort construction

Source: `nysc_survey_cleaning_and_transformation.ipynb`,
`outputs/nysc_survey_preprocessing_summary.json`,
`NYSC_all_branches_clustering_final_report.md` (Section 2).

Exclusions applied **in this order**:

| Stage | Removed | Remaining |
|---|---:|---:|
| Raw submissions | – | 481 |
| Test or debugging records | 11 | 470 |
| Age outside 15–35 | 24 | 446 |
| Unrecognised survey path or fewer than 10 answers | 3 | 443 |
| Repeated sessions (latest submission kept) | 51 | 392 |
| Records from earlier survey versions (6 legacy final-branch, 23 entry-branch fallback) | 29 | 363 |
| Employed record without an employment status | 1 | **362** |

Analytical cohort: 191 students, 34 job-seekers, 81 employed, 56 inactive.

Note: `nysc_survey_preprocessing_summary.json` reports quality *flags*
(for example 30 out-of-age, 10 unrecognised path, 14 too few answers). The
flags overlap and must not be summed; the table above applies them in order.

Each respondent was assigned to the group of the last group-specific section in
their survey path. This preserved 31 legitimate path changes and corrected 11
records whose stored path disagreed with their answers. Questions skipped by
design are kept as *not applicable*; outliers were audited, not deleted.

## 2. Encoding and missing data

- Each input has an explicit type: nominal, ordinal or numeric.
- "Do not know" is its own category (dissimilarity 0 to another "do not know",
  1 to any definite answer).
- Refused income makes that component **unavailable** for 29 students (D),
  5 job-seekers (E), 15 employed respondents (F) and 3 inactive respondents
  (G). Unknown/refused parental education is likewise unavailable: father/mother
  counts are D 5/8, E 2/2, F 3/2 and G 5/4. Nothing is imputed.
- Internally inconsistent household counts make both worker-share components
  unavailable for 5 D, 0 E, 5 F and 5 G respondents (15 total).
- Household counts are converted to shares of household size; no composite
  scores are built.
- Student motivation type is ordered intrinsic → identified → introjected →
  external → amotivated/uncertain with equal spacing (a modelling assumption).

## 3. Distance

Gower distance:

    d(i,j) = Σ_p w_ijp δ_ijp / Σ_p w_ijp

δ is 0/1 for nominal items, rank difference ÷ rank range for ordinal items and
range-scaled absolute difference for numeric items. w_ijp = 0 when the item is
unavailable for either respondent (including questions not shown), so skipped
items never count as disagreement. All components are weighted equally.

## 4. Base algorithms, resampling and consensus

| Setting | Value |
|---|---|
| Base algorithm 1 | K-medoids (alternating assignment / medoid update, random starts) |
| Base algorithm 2 | Spectral clustering, Gaussian affinity exp(−d²/2σ²), σ = median positive Gower distance |
| Standard two-algorithm full-data candidate starts | K-medoids 400 (500 in the F inherited-cultural-capital diagnostic); spectral 100 k-means initialisations |
| Candidate-screen subsamples | Standard scripts use 40 or 50 matched 80% subsamples per algorithm; the F inherited-cultural-capital diagnostic uses 100 |
| Candidate-subsample starts | Standard scripts use K-medoids 50 or 60 and spectral 30 |
| Motivation-selection exception | Initial screen: K-medoids 300 full-data starts and 100 subsamples with 40 starts. Six-algorithm comparison: 50 subsamples per configuration; full/subsample fits use K-medoids 300, spectral 50, K-means 200 and Gaussian mixture 30 starts (hierarchical methods have no random starts) |
| Subsamples at chosen k | 100 matched 80% subsamples per algorithm → 200 base partitions; K-medoids 100 starts (80 in the E script), spectral 30 |
| Co-association | C_ij = M_ij / S_ij (times grouped together ÷ times both sampled) |
| Consensus partition | K-medoids on 1 − C, 500 starts |
| Ensemble stability | 200 partitions resampled with replacement 100 times, co-association rebuilt, reclustered (80 starts), ARI vs frozen consensus |
| Random seeds | 20260823–20260827 by analysis family, with documented offsets (see `README.md`) |

## 5. Choosing the number of profiles k

| Group / dimension | Candidate k |
|---|---|
| Students: economic, educational trajectory, transition planning, social connectedness; global household model | 2–5 |
| Students: study motivation | fixed at 3 (after an earlier six-algorithm comparison over k = 2–6) |
| Employed and inactive youth | 2–4 |
| Job-seekers | 2 only (34 respondents cannot form three profiles of ≥ 15) |

Rule: discard any k that gives a profile with fewer than 15 members in either
base algorithm; rank the remainder by mean silhouette and by subsample stability
(40 or 50 matched 80% subsamples in the standard scripts; 100 in the F
inherited-cultural-capital diagnostic); average the two ranks; break ties in
favour of fewer profiles. The motivation analyses use the separate settings in
§4. The global household diagnostic used a minimum profile size of 25.

## 6. Three-tier acceptance framework

| Tier | Check | Rule | Source of threshold |
|---|---|---|---|
| Required | Profile size | Every profile ≥ 15 in the 26 group-dimension models; the separate global household diagnostic used ≥ 25 | Set for this study |
| Required | Separation | Gower silhouette ≥ 0.25 | Kaufman & Rousseeuw |
| Required | Ensemble stability | Mean ARI ≥ 0.80 over 100 ensemble resamples | Steinley ("good") |
| Required | Algorithm agreement | ARI ≥ 0.60 with each full-data base solution | Below Steinley's moderate band; all retained ≥ 0.712 |
| Diagnostic | Low confidence | ≤ 20% of members with individual silhouette < 0.10 | Set for this study |
| Diagnostic | Ambiguity | ≤ 20% of members with co-association < 0.70 or margin < 0.20 | Set for this study |
| Diagnostic | PAC | Share of pairs with 0.10 < C < 0.90. Some earlier D/F scripts used ≤ 0.20 as a caution; later E/G scripts report PAC descriptively without an absolute cutoff | Şenbabaoğlu et al.; script-specific policy |
| Review | Single item | Max ARI with any single input item < 0.90 | Steinley ("excellent") |
| Review | Leave one item out | ARI after removing each item; reviewed, no fixed cut-off (see §8) | – |
| Review | Encoding | Robust to reasonable alternative encodings (e.g. job-seeker E2: raw vs log counts, ARI ≥ 0.60) | – |
| Review | Permutation | p < 0.05 against 100 shuffled datasets | Conventional |
| Review | Meaning | Coherent, non-stigmatising, programme-relevant | – |

### How the checks apply by group (as implemented in code)

| Check | Students (D) | Job-seekers (E) | Employed (F) | Inactive (G) |
|---|---|---|---|---|
| Required tier | Automatic | Automatic | Automatic | Automatic |
| Diagnostics | Caution only | **Automatic (required)** | Caution only | Caution only |
| Single item < 0.90 | Review | **Automatic** | Review; automatic in the household and inherited-capital scripts | **Automatic** |
| Permutation p < 0.05 | Not run | **Automatic** | Run for two rejected models only | **Automatic** |
| PAC ≤ 0.20 | Caution only | Reported, no cut-off | Caution in some earlier scripts; later scripts report it only | Reported, no cut-off |
| Leave one item out | Review | Rule in §8 | Review | Review |

Code: `quality_checks` / `checks` blocks in each clustering script, e.g.
`09_branch_d_educational_cultural_capital_clustering.py` (lines 832–875),
`29_branch_e_all_dimensions_clustering.py` (lines 581–606),
`12_branch_f_employment_security_formality_clustering.py` (lines 731–742),
`21_branch_f_household_economic_resources_clustering.py` (lines 700–711),
`24_branch_g_household_economic_resources_clustering.py` (lines 701–712) and
`26_branch_g_inactivity_pathway_future_engagement_clustering.py` (lines 637–649).

### 6a. Single-question check for student and employed models

- For students and employed youth, the single-question check was a review item,
  and the original scripts did not compute a single-question ARI for the four
  retained models in those groups.
- On 27 November 2026 it was computed post hoc on the frozen consensus labels,
  without re-clustering, using the same procedure as the automatic check in
  `21_branch_f_household_economic_resources_clustering.py`: single-feature
  Gower distance, K-medoids at the model's k, 300 starts, seed = model base seed
  + 91000 + zero-based feature index, and ARI against the frozen labels.

| Retained model | Maximum single-feature ARI | Feature | Below 0.90 |
|---|---:|---|---|
| Student study motivation | 0.343 | `study_motivation_type` | Yes |
| Student economic position | 0.751 | `education_funding_source` | Yes |
| Student educational trajectory | 0.527 | `worked_while_studying` | Yes |
| Employed employment security and formality | 0.329 | `job_security_12months` | Yes |

- Comparing the raw categories of `education_funding_source` with the
  economic-position labels gives ARI 0.823, also below 0.90. The profiles
  therefore partly reflect how education is funded and are interpreted as
  relative household position.
- Reproducibility files: [script](outputs/single_item_check_2026-11-27/run_single_item_check.py)
  and [aggregate CSV](outputs/single_item_check_2026-11-27/single_feature_ari.csv).

## 7. Permutation test

Each input column is shuffled independently; the K-medoids search is repeated;
the statistic is the silhouette of size-eligible solutions;
p = (1 + number of null statistics ≥ observed) / (1 + number of valid null runs).
Null runs with no size-eligible solution are discarded, so the test is
conditional, and the p-values do not control error across all 26 dimensions.
100 repetitions per model.

| Retained model | Valid null runs | p |
|---|---:|---:|
| Job-seekers: learning orientation | 100 | 0.040 |
| Inactive: economic role | 84 | 0.012 |
| Inactive: future engagement | 92 | 0.011 |

## 8. Job-seeker leave-one-out rule

In `29_branch_e_all_dimensions_clustering.py`, a model that passes every
automatic check but has minimum leave-one-item-out ARI < 0.10 is labelled
`retain_cautiously_feature_dependent`. Only the learning-orientation model met
this condition (leave-one-out ARI 0.039), so it is reported as **provisional**.

Timing: the rule first appears in commit `091e76c` (2026-08-29 23:56 +05:30);
the job-seeker outputs were first committed in `182299e` (2026-08-31 14:27 +05:30),
the direct child commit. Git cannot show whether results existed uncommitted
earlier.

## 9. Outcomes of all 26 candidate dimensions

7 retained, 14 rejected, 2 excluded, 3 not run.
Of the 14 rejections: 8 hinged on one question (5 single-item reproduction,
3 leave-one-out dependence) and 6 had no acceptable solution.

| Group | Candidate dimension | Outcome | Main reason / evidence |
|---|---|---|---|
| Students | Motivation and study experience | Retained (caution) | Silhouette 0.350; bootstrap ARI 0.981; source ARIs 0.968/0.712; 7/8 checks |
| Students | Economic resources and household pressure | Retained (caution) | Silhouette 0.436; bootstrap ARI 0.986; source ARIs 0.849/0.796; PAC 0.422; 7/8 checks |
| Students | Educational trajectory and cultural capital | Retained (assignment caution) | Silhouette 0.427; bootstrap ARI 0.963; source ARIs 0.776/0.934; 8/8 checks; nearest-medoid validation needs review (§10) |
| Students | Transition planning and direction | Rejected | No acceptable solution (silhouette 0.245, spectral ARI 0.137, PAC 0.751; 5/8 checks) |
| Students | Social connectedness and support pathways | Excluded | Reused a question of the motivation model (silhouette 0.496, source ARIs 1.000/1.000) |
| Job-seekers | Job-search readiness and support | Rejected | No acceptable solution (source-method minimum 11, spectral ARI 0.403, p = 0.050) |
| Job-seekers | Search intensity and exposure | Rejected | Exactly reproduced searched-in-past-four-weeks item; profiles 26/8; p = 0.500 |
| Job-seekers | Economic urgency and acceptance | Rejected | Exactly reproduced minimum-wage item; profiles 28/6 |
| Job-seekers | Education usefulness and further learning | Retained (provisional) | Silhouette 0.567; bootstrap ARI 0.953; source ARIs 0.882/1.000; p = 0.040; leave-one-out ARI 0.039 (§8) |
| Job-seekers | Household resources and dependency | Rejected | Profiles 22/12; source ARIs 0.484/0.484; 38.2% ambiguous; p = 0.583 |
| Job-seekers | Inherited cultural capital | Rejected | Exactly reproduced work-while-studying item; profiles 24/10 |
| Job-seekers | Job-search social capital | Not run | Scope decision |
| Employed | Household resources and responsibility | Rejected | Income-source dominated; leave-source-out ARI −0.036; structural-only ARI 0.000; p = 0.059 |
| Employed | Inherited cultural capital | Rejected | No candidate met the cross-algorithm size rule; p = 0.683 |
| Employed | Employment security and formality | Retained (caution) | Silhouette 0.368; bootstrap ARI 0.953; source ARIs 0.854/0.950; PAC 0.427; 7/8 checks |
| Employed | Earnings and working-time adequacy | Excluded | Statistically stable (silhouette 0.525) but controlled by one preference item; profiles 51/30 |
| Employed | Satisfaction and mobility intention | Rejected | Leave-one-out ARI −0.007; PAC 0.519; profiles 34/47 |
| Employed | Qualification use and skill development | Rejected | Exactly reproduced received-training item; profiles 65/16; leave-item-out ARI 0.014 |
| Employed | Professional social capital | Not run | Scope decision |
| Employed | Work motivation and psychological needs | Rejected | No k = 2–4 met the cross-algorithm size rule; spectral ARI 0.330 |
| Employed | Search pathway and barriers | Rejected | Silhouette 0.165; ensemble ARI 0.532; spectral ARI 0.038; 35.8% low confidence |
| Inactive | Household resources (economic role) | Retained | Silhouette 0.372; bootstrap ARI 1.000; source ARIs 0.854/0.718; p = 0.012; 9/9 checks |
| Inactive | Inherited cultural capital | Rejected | Exactly reproduced work-while-studying item; profiles 38/18; p = 0.230 |
| Inactive | Inactivity pathway and future engagement | Retained | Silhouette 0.413; bootstrap ARI 1.000; source ARIs 0.928/1.000; p = 0.011; 10/10 checks |
| Inactive | Psychological readiness and support | Rejected | Profile sizes 45/11; K-medoids ARI 0.590; leave-one-out ARI −0.017 |
| Inactive | Labour-market social connection | Not run | Scope decision |

## 10. Describing profiles and placing new members

- The saved comparison table has 270 model–question comparison rows covering
  115 distinct questions not used to form the model being tested: chi-square or
  Fisher tests (categorical), Mann–Whitney or Kruskal–Wallis (ordered/numeric).
- Effect sizes: bias-corrected Cramér's V for categorical comparisons,
  absolute rank-biserial correlation for two-profile ordered/numeric comparisons,
  and epsilon-squared for ordered/numeric comparisons with more than two profiles.
- Benjamini–Hochberg false-discovery-rate control **within each model**
  (30–58 comparisons per model).
- Reassignment: every respondent reassigned to the nearest profile medoid in
  Gower space. A model is safe only if accuracy ≥ 0.95, balanced accuracy
  ≥ 0.90, macro F1 ≥ 0.90, ARI ≥ 0.80 and mismatches ≤ 5%.

| Model | Accuracy | Balanced accuracy | Macro F1 | ARI | Mismatches | Result |
|---|---:|---:|---:|---:|---:|---|
| Student motivation | 0.958 | 0.964 | 0.955 | 0.886 | 4.2% | Safe |
| Student economic resources | 0.990 | 0.985 | 0.985 | 0.955 | 1.0% | Safe |
| Student educational trajectory | 0.906 | 0.925 | 0.886 | 0.776 | 9.4% | Needs review |
| Job-seeker learning orientation | 0.971 | 0.972 | 0.971 | 0.882 | 2.9% | Safe |
| Employed employment security | 0.988 | 0.990 | 0.987 | 0.950 | 1.2% | Safe |
| Inactive economic role | 0.964 | 0.954 | 0.954 | 0.854 | 3.6% | Safe |
| Inactive future engagement | 0.875 | 0.833 | 0.855 | 0.550 | 12.5% | Needs review |

- Code: `30_final_cluster_profile_analysis.ipynb`,
  `outputs/fixed_medoid_assignment_validation/`.

## 11. Recommendation audits

Scripts (in `src/rag_prototype/`):

- `grounding_audit_v2.py`: course facts and cited member/profile evidence must be
  found in the course record and evidence pack; unsupported eligibility claims fail.
- `evidence_category_discipline_audit.py`: each cited answer must be used in the
  role its evidence-policy category allows (e.g. opinion questions are not preferences).
- `evidence_hierarchy_audit.py`: the member's own answers must outrank profile
  context; checks profile overreach, affordability claims and catalogue-gap disclosure.

Each returns PASS, PASS WITH CAUTION or FAIL. Cautions and failures were checked
by hand. The audits were designed by the author and cross-checked with AI coding
assistants; no independent human reviewer was involved.

Members were real survey respondents chosen by hand to cover groups, sectors and
strengths of evidence. Ranking model: `gpt-5-mini`, hard-coded and verified
before each call (`env_config.py`), low reasoning effort, provider-default
temperature, so re-runs can differ in wording. All batches below used the
earlier pipeline with BM25 text retrieval over the 84-course corpus; the
deployed officer dashboard selects courses by sector instead.

| Batch | People | Model | Recommendations | Declines | Grounding P/C/F | Category P/C/F | Hierarchy P/C/F |
|---|---:|---|---:|---:|---|---|---|
| v1 (first run) | 10 | gpt-4o-mini (environment setting had silently changed) | 4 | 8 | 11/0/**1** | 18/0/0 | – |
| v2 (new model, rebalanced prompt) | same 10 | gpt-5-mini | 35 | 0 | 32/3/0 | 95/6/**4** | – |
| v3 (category prompt fix) | same 10 | gpt-5-mini | 30 | 2 | 29/3/0 | 72/1/0 | – |
| 30-person validation | 30 (11 D, 5 E, 8 F, 6 G) | gpt-5-mini | 102 | 4 | 92/14/0 | 243/3/0 | not run |
| Targeted, initial | 10 of the 30 | gpt-5-mini | 33 | 1 | 29/5/0 | 77/2/0 | 41/0/2 |
| Targeted, final (post-fix) | same 10 | gpt-5-mini | **34** | 1 | 32/3/0 | 75/1/0 | 44/0/0 |

P/C/F counts are audited items (citations or checks), not recommendations.
The v1 grounding count is from the saved extended re-audit of its four
recommendations and eight declines. The v1 and v2 category counts are the
model-specific subsets of the combined saved category-audit CSV.
Targeted-initial counts are after the documented deterministic re-audits; the
original report recorded 29/4/1, 76/2/1 and 41/1/1.

**Correction.** Earlier narrative reports gave 36 and 39 recommendations for the
two targeted runs. Counting the saved output files gives **33 and 34**; the paper
uses 34. (The 44 in one report is the number of hierarchy-audit rows, not
recommendations.)

Per-person selection lists, inputs and audit outputs are withheld because they
contain respondents' answers.
