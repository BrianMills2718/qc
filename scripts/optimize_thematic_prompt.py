"""
Prompt optimization experiment for thematic coding (v2).

A/B tests 3 prompt variants using prompt_eval with dimensional evaluation:
  - current:        Full existing prompt (baseline)
  - concise:        Analytical instructions only (field specs removed, schema handles those)
  - methodological: Braun & Clarke thematic analysis framing

Improvements over v1:
  - Per-dimension scoring (clarity, grounding, coverage, depth)
  - Calibrated rubric with anchor descriptions
  - Multiple diverse inputs (AI workplace, healthcare, education)
  - Cross-vendor judge (claude-sonnet evaluates gpt-5-mini output)
  - Chain-of-thought reasoning from judge

Requires: OPENAI_API_KEY, ANTHROPIC_API_KEY

Usage:
    python scripts/optimize_thematic_prompt.py
"""

from __future__ import annotations

import asyncio

from prompt_eval import (
    Experiment,
    ExperimentInput,
    PromptVariant,
    RubricDimension,
    run_experiment,
    save_result,
)
from prompt_eval.evaluators import llm_judge_dimensional_evaluator
from prompt_eval.stats import compare_variants

from qc_clean.schemas.analysis_schemas import CodeHierarchy

# ---------------------------------------------------------------------------
# Sample interview data
# ---------------------------------------------------------------------------

INTERVIEW_1 = """
Interviewer: Can you tell me about how AI has changed your work?

Jane Smith: Absolutely. We started using AI tools about two years ago, and it
completely transformed our workflow. Before AI, we spent about 60% of our time
on data entry and routine analysis. Now the AI handles most of that, and we
can focus on strategic decision-making.

Interviewer: What concerns do you have about AI in the workplace?

Jane Smith: Privacy is my biggest concern. We're feeding sensitive client data
into these systems, and I'm not always sure where that data ends up. We also
had an incident where the AI made a recommendation based on biased training
data, which could have led to discriminatory outcomes if we hadn't caught it.

Interviewer: How do your colleagues feel about these changes?

Jane Smith: It's mixed. The younger staff love it — they adapted quickly and
see it as an enhancement. But several senior employees feel threatened. One
colleague told me she's worried about becoming obsolete. There's definitely
a generational divide in how people perceive AI at work.
""".strip()

INTERVIEW_2 = """
Interviewer: What has your experience been with AI implementation?

Robert Chen: We took a cautious approach. Rather than replacing existing
processes, we introduced AI as a supplementary tool. Staff can choose to
use it or not. That voluntary adoption model has worked well — about 70%
of the team now uses AI daily, and the resistance we expected never really
materialized.

Interviewer: Have you encountered any challenges?

Robert Chen: The learning curve was steeper than expected. We budgeted one
month for training, but it really took three months before people felt
comfortable. Cost is another factor — the enterprise AI licenses are
expensive, and we're still trying to measure ROI. Also, the AI sometimes
generates plausible-sounding but incorrect analyses, so we always need
human verification.

Interviewer: What advice would you give to other organizations?

Robert Chen: Start small. Pick one specific use case, prove the value, then
expand. Don't try to automate everything at once. And invest heavily in
training — that's where most organizations underinvest.
""".strip()

INTERVIEW_HEALTHCARE = """
Interviewer: How has telehealth changed your experience as a patient?

Maria Torres: It's been a mixed bag honestly. During the pandemic I had no
choice, everything went virtual overnight. For simple things like prescription
refills or follow-ups where the doctor just checks numbers, it's wonderful.
I save two hours of driving and sitting in a waiting room. But for anything
where I actually feel unwell, it feels inadequate.

Interviewer: Can you say more about that inadequacy?

Maria Torres: When I had chest pains last year, I did a telehealth visit first.
The doctor was kind but she couldn't examine me. She kept asking me to describe
the pain and I could tell she was frustrated too. She ended up saying "you
should probably come in." So I drove to the ER anyway. The technology created
an extra step without adding value. Also my mother is 78 and she can barely
use her phone. She missed three appointments because she couldn't figure out
the video link. The equity issue is real — telehealth assumes digital literacy
that many patients don't have.

Interviewer: Has your trust in your healthcare providers changed?

Maria Torres: That's interesting because yes, subtly. I trust my regular
doctor the same — we've had a relationship for ten years. But the specialists
I've only met on screen feel more like consultants than caregivers. There's
something about physical presence that builds trust. My therapist though, she's
actually better on video. I'm more relaxed at home and I open up more easily.
So it really depends on the type of care.
""".strip()

INTERVIEW_EDUCATION = """
Interviewer: What was your experience teaching remotely during and after the pandemic?

David Park: The first year was survival mode. I was teaching high school
chemistry and trying to demonstrate lab experiments through a webcam. Half
my students had their cameras off and I had no idea if they were even there.
Engagement plummeted. I went from having lively classroom discussions to
talking into a void.

Interviewer: How did you adapt?

David Park: I had to completely rethink my approach. Shorter lectures, more
breakout rooms, interactive polls. I started using simulation software for
labs which honestly some students preferred to real labs. But the inequity
was devastating — students without reliable internet or quiet study spaces
fell behind dramatically. One student was doing chemistry homework in a car
in a McDonald's parking lot for the wifi. We lost students we never got back.

Interviewer: What about now that you're back in person?

David Park: We kept some of the tools. Recorded lectures for students who
miss class, online submission for homework, simulation labs as supplements.
But there's a tool fatigue issue now. I'm expected to maintain a learning
management system, respond to parent emails, post grades online, use three
different apps for different things. The administrative overhead of educational
technology has grown enormously while my planning time hasn't. And student
wellbeing is a whole other conversation — anxiety and disengagement are way
higher than pre-pandemic. I spend more time being a counselor than a chemistry
teacher some days.
""".strip()

AI_WORKPLACE_INPUT = (
    "--- Interview: interview1.txt ---\n"
    f"{INTERVIEW_1}\n\n"
    "--- Interview: interview2.txt ---\n"
    f"{INTERVIEW_2}"
)

HEALTHCARE_INPUT = (
    "--- Interview: healthcare_patient.txt ---\n"
    f"{INTERVIEW_HEALTHCARE}"
)

EDUCATION_INPUT = (
    "--- Interview: education_teacher.txt ---\n"
    f"{INTERVIEW_EDUCATION}"
)

# ---------------------------------------------------------------------------
# Prompt variants
# ---------------------------------------------------------------------------

CURRENT_PROMPT = """You are a qualitative researcher analyzing interview(s) to discover thematic codes.

ANALYTIC QUESTION: What are the key themes, patterns, and insights in these interviews?

CRITICAL INSTRUCTIONS:
1. Read through ALL interview content comprehensively
2. Distinguish between INTERVIEWER QUESTIONS and INTERVIEWEE RESPONSES — only code the interviewee's statements, not the interviewer's framing questions
3. Create a hierarchical code structure with up to 3 levels
4. Target 10-15 total codes (5-7 top-level themes with selective sub-codes). Merge overlapping themes rather than creating near-duplicates
5. Each code MUST have these fields:
   - id: Unique ID in CAPS_WITH_UNDERSCORES format
   - name: Clear human-readable name
   - description: 2-3 sentences explaining the code
   - semantic_definition: Clear definition of what qualifies for this code
   - parent_id: ID of parent code (null for top-level codes)
   - level: Hierarchy level (0=top, 1=sub, 2=detailed)
   - example_quotes: 1-3 VERBATIM quotes from the INTERVIEWEE (not the interviewer)
   - mention_count: Count how many distinct times this theme is mentioned or referenced across the interview(s). Be precise — count actual mentions, not estimates
   - discovery_confidence: Float 0.0-1.0 using the FULL range:
     * 0.0-0.3: Weakly supported (mentioned once, tangentially)
     * 0.3-0.6: Moderately supported (mentioned a few times, some detail)
     * 0.6-0.8: Strongly supported (discussed substantively, with examples)
     * 0.8-1.0: Very strongly supported (major theme with extensive discussion)
   - reasoning: 1-2 sentences explaining WHY you created this code — what analytical decision led to it, what data pattern you noticed

6. Hierarchy: Level 0 = main themes, Level 1 = sub-themes, Level 2 = detailed codes
7. Codes must be mutually distinct — if two codes would share >50% of their supporting quotes, merge them

INTERVIEW CONTENT:
{input}

Generate a complete hierarchical taxonomy of codes.

ANALYTICAL MEMO: After completing the analysis above, write a brief analytical memo (3-5 sentences) in the "analytical_memo" field recording:
- Key analytical decisions you made and why
- Patterns or surprises that emerged during analysis
- Uncertainties or areas needing further investigation"""

CONCISE_PROMPT = """You are a qualitative researcher analyzing interviews to discover thematic codes.

ANALYTIC QUESTION: What are the key themes, patterns, and insights in these interviews?

INSTRUCTIONS:
1. Read ALL interview content. Only code INTERVIEWEE statements, not interviewer questions.
2. Create a hierarchical code structure: 5-7 top-level themes with selective sub-codes (10-15 total).
3. Merge overlapping themes — if two codes share >50% of supporting quotes, combine them.
4. Include VERBATIM quotes from interviewees as evidence for each code.
5. Use the FULL confidence range: 0.0-0.3 weak, 0.3-0.6 moderate, 0.6-0.8 strong, 0.8-1.0 very strong.
6. For each code, explain the analytical reasoning behind its creation.
7. Write an analytical memo noting key decisions, surprising patterns, and uncertainties.

INTERVIEW CONTENT:
{input}"""

METHODOLOGICAL_PROMPT = """You are conducting a reflexive thematic analysis following Braun & Clarke (2006, 2019).

Your task: analyze these interviews to develop a thematic codebook.

METHODOLOGICAL FRAMEWORK:
- Phase 1 (Familiarization): Read the entire dataset before coding.
- Phase 2 (Generating codes): Code systematically, attending to both semantic (surface) and latent (underlying) meanings.
- Phase 3 (Constructing themes): Group codes into candidate themes that capture patterned meaning across the dataset.

REFLEXIVE PRINCIPLES:
- Acknowledge your interpretive role — codes reflect your reading of the data, not objective facts.
- Attend to what is NOT said as much as what IS said.
- Look for tensions and contradictions, not just consensus.
- Consider how participants' social positions shape their accounts.

PRACTICAL INSTRUCTIONS:
1. Only code INTERVIEWEE statements, not interviewer questions.
2. Build a hierarchical codebook: 5-7 top-level themes, selective sub-codes, 10-15 codes total.
3. Merge overlapping themes. Each code needs verbatim quotes as evidence.
4. Use the full confidence range (0.0-1.0) based on evidentiary support.
5. Explain the analytical reasoning for each code.
6. Write an analytical memo capturing your reflexive observations, uncertainties, and emergent patterns.

INTERVIEW CONTENT:
{input}"""

# ---------------------------------------------------------------------------
# Calibrated rubric dimensions
# ---------------------------------------------------------------------------

DIMENSIONS = [
    RubricDimension(
        name="code_clarity",
        description="Are code names specific and descriptive? Do descriptions clearly define what data belongs under each code? Are codes mutually exclusive?",
        weight=1.0,
        anchors={
            "low": "Codes have vague names like 'Theme 1' or 'General Issues'. Descriptions are one word or missing. Multiple codes cover the same data.",
            "mid": "Most codes have descriptive names. Descriptions exist but some are thin. Minor overlap between 1-2 codes.",
            "high": "Every code has a specific, informative name. Descriptions clearly delineate boundaries. No significant overlap between codes.",
        },
    ),
    RubricDimension(
        name="grounding",
        description="Is each code supported by verbatim quotes? Are quotes relevant and illustrative? Do mention_counts reflect actual data frequency?",
        weight=1.0,
        anchors={
            "low": "Few or no verbatim quotes. Quotes are paraphrased or from interviewer. Mention counts are round numbers (5, 10) suggesting estimation.",
            "mid": "Most codes have quotes but some are vague or tangential. Mention counts are roughly plausible.",
            "high": "Every code has 1-3 precise verbatim quotes from interviewees. Mention counts match actual data frequency.",
        },
    ),
    RubricDimension(
        name="coverage",
        description="Do codes capture the major themes? Are important patterns missing? Is hierarchy meaningful?",
        weight=1.0,
        anchors={
            "low": "Major themes missing (e.g., ignores privacy or adoption challenges). All codes at one level. Fewer than 5 codes.",
            "mid": "Most major themes captured. Hierarchy exists but some subcodes are unnecessary or misplaced. 8-12 codes.",
            "high": "All significant themes covered. Hierarchy adds analytical value (subcodes refine parent themes). 10-15 codes with good breadth/depth balance.",
        },
    ),
    RubricDimension(
        name="analytical_depth",
        description="Do codes reveal latent patterns beyond surface content? Is there evidence of interpretive work? Are analytical memos insightful?",
        weight=1.0,
        anchors={
            "low": "Codes are purely descriptive labels of manifest content ('mentioned AI'). No interpretation. Memo is generic or missing.",
            "mid": "Some codes capture underlying dynamics (e.g., 'power shift'). Memo notes a few patterns. Limited reflexivity.",
            "high": "Codes identify latent tensions, contradictions, or dynamics not explicitly stated. Memo reflects on analytical decisions and emergent patterns with genuine insight.",
        },
    ),
]

# ---------------------------------------------------------------------------
# Experiment definition
# ---------------------------------------------------------------------------

CODING_MODEL = "gpt-5-mini"
JUDGE_MODEL = "gemini/gemini-2.0-flash"


def build_experiment() -> Experiment:
    def make_variant(name: str, prompt: str) -> PromptVariant:
        return PromptVariant(
            name=name,
            messages=[{"role": "user", "content": prompt}],
            model=CODING_MODEL,
            kwargs={"timeout": 120},
        )

    return Experiment(
        name="thematic_coding_prompt_v2",
        variants=[
            make_variant("current", CURRENT_PROMPT),
            make_variant("concise", CONCISE_PROMPT),
            make_variant("methodological", METHODOLOGICAL_PROMPT),
        ],
        inputs=[
            ExperimentInput(id="ai_workplace", content=AI_WORKPLACE_INPUT),
            ExperimentInput(id="healthcare", content=HEALTHCARE_INPUT),
            ExperimentInput(id="education", content=EDUCATION_INPUT),
        ],
        n_runs=3,
        response_model=CodeHierarchy,
    )


def format_codebook(output: object) -> str:
    """Format CodeHierarchy for the LLM judge."""
    if hasattr(output, "model_dump_json"):
        return output.model_dump_json(indent=2)
    return str(output)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    experiment = build_experiment()
    evaluator = llm_judge_dimensional_evaluator(
        dimensions=DIMENSIONS,
        judge_models=[JUDGE_MODEL],
        output_formatter=format_codebook,
    )

    n_coding = len(experiment.variants) * len(experiment.inputs) * experiment.n_runs
    n_judge = n_coding
    print(f"Running experiment: {experiment.name}")
    print(f"  Variants: {[v.name for v in experiment.variants]}")
    print(f"  Inputs: {[i.id for i in experiment.inputs]}")
    print(f"  Runs per variant per input: {experiment.n_runs}")
    print(f"  Total calls: {n_coding} coding ({CODING_MODEL}) + {n_judge} judge ({JUDGE_MODEL})")
    print()

    result = await run_experiment(experiment, evaluator)

    # Print per-variant summary with dimension breakdown
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    dim_names = [d.name for d in DIMENSIONS]
    header = f"  {'variant':20s}  {'overall':>8s}"
    for d in dim_names:
        header += f"  {d:>16s}"
    header += f"  {'cost':>8s}  {'errors':>6s}"
    print(header)
    print("  " + "-" * (len(header) - 2))

    for name, summary in result.summary.items():
        mean = summary.mean_score if summary.mean_score is not None else 0.0
        std = summary.std_score if summary.std_score is not None else 0.0
        line = f"  {name:20s}  {mean:>7.3f}±"
        line_std = f"{std:.2f}"
        line = f"  {name:20s}  {mean:.3f}±{std:.2f}"

        if summary.dimension_means:
            for d in dim_names:
                val = summary.dimension_means.get(d, 0.0)
                line += f"  {val:>16.3f}"
        else:
            for d in dim_names:
                line += f"  {'n/a':>16s}"

        line += f"  ${summary.mean_cost:.4f}  {summary.n_errors:>6d}"
        print(line)
    print()

    # Pairwise comparisons (overall)
    variant_names = [v.name for v in experiment.variants]
    print("PAIRWISE COMPARISONS (overall)")
    print("-" * 70)
    for i, a in enumerate(variant_names):
        for b in variant_names[i + 1:]:
            cmp = compare_variants(result, a, b)
            sig = "SIGNIFICANT" if cmp.significant else "not significant"
            print(f"  {a} vs {b}: diff={cmp.difference:+.3f}  "
                  f"CI=[{cmp.ci_lower:+.3f}, {cmp.ci_upper:+.3f}]  {sig}")
    print()

    # Per-dimension pairwise comparisons
    print("PAIRWISE COMPARISONS (per dimension)")
    print("-" * 70)
    for dim in dim_names:
        print(f"  [{dim}]")
        for i, a in enumerate(variant_names):
            for b in variant_names[i + 1:]:
                try:
                    cmp = compare_variants(result, a, b, dimension=dim)
                    sig = "SIG" if cmp.significant else "n.s."
                    print(f"    {a} vs {b}: diff={cmp.difference:+.3f}  "
                          f"CI=[{cmp.ci_lower:+.3f}, {cmp.ci_upper:+.3f}]  {sig}")
                except ValueError as e:
                    print(f"    {a} vs {b}: {e}")
    print()

    # Save
    path = save_result(result)
    print(f"Results saved to: {path}")

    # Print trial details with dimension scores
    print()
    print("TRIAL DETAILS")
    print("-" * 70)
    for trial in result.trials:
        score_str = f"{trial.score:.3f}" if trial.score is not None else "ERROR"
        error_str = f"  error={trial.error}" if trial.error else ""
        dim_str = ""
        if trial.dimension_scores:
            parts = [f"{k}={v:.2f}" for k, v in trial.dimension_scores.items()]
            dim_str = f"  [{', '.join(parts)}]"
        print(f"  {trial.variant_name:20s}  {trial.input_id:20s}  "
              f"score={score_str}{dim_str}{error_str}")

    # Print judge reasoning for first trial of each variant (sample)
    print()
    print("SAMPLE JUDGE REASONING")
    print("-" * 70)
    seen_variants: set[str] = set()
    for trial in result.trials:
        if trial.variant_name not in seen_variants and trial.reasoning:
            seen_variants.add(trial.variant_name)
            print(f"\n  [{trial.variant_name} / {trial.input_id}]")
            # Truncate reasoning to first 500 chars for readability
            reasoning = trial.reasoning[:500]
            if len(trial.reasoning) > 500:
                reasoning += "..."
            for line in reasoning.split("\n"):
                print(f"    {line}")

    # Summary
    best_name = max(result.summary, key=lambda n: result.summary[n].mean_score or 0.0)
    best_score = result.summary[best_name].mean_score or 0.0
    print()
    print(f"Best variant: {best_name} (mean={best_score:.3f})")

    all_significant = True
    for name in variant_names:
        if name == best_name:
            continue
        cmp = compare_variants(result, best_name, name)
        if not cmp.significant:
            all_significant = False
            break

    if all_significant:
        print(f"  -> {best_name} is significantly better than all others.")
        print(f"  -> Consider updating thematic_coding.py with this prompt.")
    else:
        print("  -> No variant is significantly better than all others.")
        print("  -> Inspect per-dimension scores to identify specific strengths.")


if __name__ == "__main__":
    asyncio.run(main())
