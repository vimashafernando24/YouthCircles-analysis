# Youth Circles analysis: public reproducibility copy

This folder is a privacy-preserving copy of the analytical code and aggregate
results used in the Youth Circles project. It is intended for method review and
paper reproducibility checks.

## Privacy and data availability

Raw survey responses and person-level derived data are deliberately not
included. Respondents were promised confidentiality. The omitted material
includes raw exports, cleaned row-level datasets, cluster assignments, sampled
validation cases, API recommendation records, call snapshots, environment
files, credentials, and any audit table containing a person identifier or
person-level answer.

Notebook cell outputs have been cleared in this public copy because some saved
outputs displayed individual records. Notebook source code and Markdown
explanations are retained. The original repository was not changed.

Because the confidential input data are absent, the pipeline cannot be run
end-to-end from this folder alone. Researchers with authorised access should
place the private input files at the paths expected by the notebooks and
scripts. Everyone else can inspect the complete analytical logic and verify the
published aggregate summaries under `outputs/`.

## Recommended execution order

Run files from the project root. Notebook and script pairs implement the same
stage or provide a script version suitable for non-interactive execution.

1. `nysc_survey_cleaning_and_transformation.ipynb` cleans the raw survey export,
   applies branch logic, creates analysis-ready variables, and writes the
   private analysis datasets and aggregate preprocessing summaries.
2. `02_branch_d_clustering_experiments.ipynb` evaluates the initial Branch D
   clustering design and candidate cluster counts.
3. `03_branch_d_dimension_engineering.ipynb` constructs and audits the Branch D
   analytical dimensions.
4. `04_branch_d_integrated_transition_profiles.ipynb` combines the retained
   Branch D dimensions into integrated transition profiles.
5. `05_branch_d_motivation_clustering.ipynb` fits the Branch D motivation
   clustering; `06_branch_d_motivation_algorithm_comparison.ipynb` compares
   algorithms; `07_branch_d_motivation_consensus_clustering.ipynb` builds the
   consensus solution.
6. `08_branch_d_economic_resources_clustering.ipynb` fits the Branch D economic
   resources model.
7. `09_branch_d_educational_cultural_capital_clustering.ipynb` and its `.py`
   counterpart fit and validate the Branch D educational and cultural capital
   model.
8. `10_branch_d_transition_planning_clustering.ipynb` and `.py` fit the Branch D
   transition-planning model.
9. `11_branch_d_social_connectedness_clustering.ipynb` and `.py` fit the Branch
   D social-connectedness model.
10. `12_branch_f_employment_security_formality_clustering.ipynb` and `.py` fit
    the Branch F employment-security and formality model.
11. `13_branch_f_variable_dimension_audit.py` audits Branch F variables and the
    proposed dimension structure.
12. `14_global_household_economic_clustering.ipynb` and `.py` fit the shared
    household-economic model.
13. `15_branch_f_earnings_working_time_clustering.ipynb` and `.py` fit the
    earnings and working-time model.
14. `16_branch_f_job_satisfaction_mobility_clustering.ipynb` and `.py` fit the
    job-satisfaction and mobility model.
15. `17_branch_f_qualification_skill_development_clustering.ipynb` and `.py`
    fit the qualification and skill-development model.
16. `18_branch_f_work_motivation_sdt_clustering.ipynb` and `.py` fit the work
    motivation model using the self-determination-theory framing.
17. `19_branch_f_search_pathway_barriers_clustering.ipynb` and `.py` fit the
    search-pathway and barriers model.
18. `20_branch_f_candidate_dimension_discovery.py` performs candidate-dimension
    discovery for Branch F.
19. `21_branch_f_household_economic_resources_clustering.ipynb` and `.py` fit
    the Branch F household-economic model.
20. `22_branch_f_educational_cultural_capital_clustering.ipynb` and `.py` fit
    the Branch F educational and cultural capital model;
    `22_branch_f_open_combinatorial_dimension_search.py` runs the associated
    open dimension search.
21. `23_branch_g_variable_dimension_audit.ipynb` and `.py` audit Branch G
    variables and dimensions.
22. `24_branch_g_household_economic_resources_clustering.ipynb` and `.py` fit
    the Branch G household-economic model.
23. `25_branch_g_psychological_readiness_support_clustering.ipynb` and `.py` fit
    the psychological-readiness and support model.
24. `26_branch_g_inactivity_pathway_future_engagement_clustering.ipynb` and
    `.py` fit the inactivity-pathway and future-engagement model.
25. `27_branch_g_educational_cultural_capital_clustering.ipynb` and `.py` fit
    the Branch G educational and cultural capital model.
26. `28_branch_e_variable_dimension_audit.ipynb` and `.py` audit Branch E
    variables and dimensions.
27. `29_branch_e_all_dimensions_clustering.ipynb` and `.py` fit all retained
    Branch E dimensions.
28. `30_final_cluster_profile_analysis.ipynb` performs the post-cluster profile
    comparisons and writes the final aggregate profile summaries.

The Python and frontend source under `src/rag_prototype/` implements the
profile-aware retrieval and recommendation prototype. Modules containing fixed
real-person validation cases were omitted from this public copy. The retained
audit modules operate on compatible private inputs when those are supplied by
an authorised researcher.

## Main reproducibility settings

The clustering stages set deterministic random-state constants in the range
`20260823` through `20260827`. Individual stages derive repeat-specific seeds by
adding documented offsets to their stage constant. The main assignments are:

- `20260823`: integrated Branch D profiles and the early Branch D motivation,
  comparison, consensus, and economic analyses.
- `20260824`: Branch D educational/cultural analysis, global household model,
  and the principal Branch F clustering analyses.
- `20260825`: Branch D transition planning, Branch F discovery and later
  dimensions, and final profile comparison.
- `20260826`: Branch D social connectedness, Branch G analyses, and Branch E
  all-dimensions clustering.
- `20260827`: Branch F employment-security/formality analysis.

Other important settings, including candidate cluster-count ranges, numbers of
initialisations, stability repetitions, distance functions, and consensus
rules, are defined beside the random-state constants in each notebook or
script and are preserved here verbatim.

## Included saved outputs

Only aggregate or model-level files are included:

- quality-check and quality-audit tables;
- candidate and selected-model metric tables;
- clustering, dimension, preprocessing, and model summaries;
- variable/dimension audit summaries and aggregate response distributions;
- final profile-comparison and programme-relevant profile summaries;
- course-level audit tables; and
- aggregate analytical and validation reports.

No raw data or person-level output is included.
