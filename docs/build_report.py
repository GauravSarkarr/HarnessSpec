"""Build the four-page mid-submission progress report.

The prose cites pilot/results.json. Re-run the pilot before changing a number.
"""

from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "mid_submission_progress_report.pdf"

HTML = """
<h1>HarnessSpec</h1>
<p class="kicker">Mid-submission progress report</p>
<p class="meta">Syed Affan Daimi &middot; M.S. Computer Science, IIIT Hyderabad<br/>
CS6.403 Automated Software Engineering &middot; Monsoon 2026<br/>
5 November 2026 &middot; registered proposal 21 October 2026</p>
<p class="repo">Repository: <a href="https://github.com/GauravSarkarr/HarnessSpec">https://github.com/GauravSarkarr/HarnessSpec</a></p>

<h2>1. What this submission claims</h2>
<p>The registered study has three objectives. O1 defines a typed harness. O2 builds the validator, the runtime, and trace-driven revision. O3 compares four designers on about 60 SWE-bench Verified issues and about 60 SWE-QA questions, with 7B&ndash;30B local models, three seeds, and energy measured beside accuracy. O3 is most of the experimental work. It is not this submission.</p>
<p>The midpoint freezes the artifact O3 will later measure, and it stops before any accuracy claim. Hypotheses H1&ndash;H4 are not estimated. A fixture pilot checks that the compiler and the runtime implement the decisions in the proposal. It is not a benchmark result, and the report does not treat it as one.</p>

<table>
<tr><th>Piece</th><th>Objective</th><th>State at mid-submission</th></tr>
<tr><td>Protocol, eight fields, version 0.1</td><td>O1</td><td>Frozen. Schema and validator agree.</td></tr>
<tr><td>Validator and bounded repair</td><td>O2</td><td>Done. Measured on 15 specs.</td></tr>
<tr><td>Budgets, tool guards, hooks, return gate</td><td>O2</td><td>Done on one scripted workspace.</td></tr>
<tr><td>Trace revision and a spec cache</td><td>O2</td><td>Mechanism only. No break-even number.</td></tr>
<tr><td>Fixed harness A, and the shape of tuple C</td><td>O3 prep</td><td>A runs. C is a partial object, not a model.</td></tr>
<tr><td>Free-text briefs (B) and a live orchestrator</td><td>O3</td><td>Not started.</td></tr>
<tr><td>SWE-bench, SWE-QA, seeds, energy</td><td>O3</td><td>Not started.</td></tr>
</table>

<h2>2. Protocol</h2>
<p>A HarnessSpec is one JSON object. The eight fields from the proposal are below. <span class="mono">spec_version</span> and <span class="mono">task_id</span> are an envelope, not a ninth design choice. The executable check is the validator module. The JSON schema beside it is the interchange file. A unit test fails if their required top-level names diverge.</p>

<table>
<tr><th>Field</th><th>What the compiler requires</th></tr>
<tr><td>goal</td><td>A non-empty statement, and at least one acceptance test whose command is on the runtime allowlist.</td></tr>
<tr><td>context</td><td>Include-paths inside the parent slice. Absolute paths and <span class="mono">..</span> are rejected.</td></tr>
<tr><td>tools</td><td>The name exists on the parent card. Permission rank is read, then write, then exec. Paths stay inside that tool's grant. A grant of <span class="mono">src</span> does not cover <span class="mono">src2</span>.</td></tr>
<tr><td>budgets</td><td>Steps, tokens, and seconds are at least 1 and at most the parent. The token budget covers one token per step.</td></tr>
<tr><td>stop</td><td>Known stop conditions. On exhaustion the harness either stops or escalates.</td></tr>
<tr><td>verification</td><td>Hooks of kind test, lint, or ast. The command must match the kind.</td></tr>
<tr><td>return_contract</td><td>If citations are required, the contract demands at least one.</td></tr>
<tr><td>model</td><td>Tier is 7&ndash;14B or 24&ndash;30B, and that tier is on the parent card.</td></tr>
</table>

<p>The runtime will execute exactly three commands: <span class="mono">unittest</span>, <span class="mono">ast.parse</span>, and <span class="mono">lint.bare-except</span>. Anything else is a validation error. There is no shell. A least-privilege allowlist is only real if the runtime knows the program it is about to run. The benchmark phase will add container-pinned commands for SWE-bench. It will not add a free-form shell string.</p>
<p><span class="mono">examples/valid_spec.json</span> is one harness that passes the validator against <span class="mono">examples/parent.json</span>. It is harness D for the adder used in the pilot.</p>
<table class="keep">
<tr><th>Field</th><th>Value in the example</th></tr>
<tr><td>goal</td><td>Make add return the sum of its arguments. One acceptance test, command unittest.</td></tr>
<tr><td>context</td><td>Include src and tests. Exclude nothing.</td></tr>
<tr><td>tools</td><td>read_file at read, on src and tests. write_file at write, on src only. No exec tool.</td></tr>
<tr><td>budgets</td><td>6 steps, 2000 tokens, 30 seconds. All inside the parent card.</td></tr>
<tr><td>stop</td><td>Stop on acceptance, budget, hook failure, or a rejected return. On exhaustion, escalate. At most one escalation.</td></tr>
<tr><td>verification</td><td>unittest, then ast.parse.</td></tr>
<tr><td>return_contract</td><td>Citations required, test output required, at least one citation.</td></tr>
<tr><td>model</td><td>Tier 7&ndash;14B, name fixture-small. No digest yet. Digests belong to the pinned-model runs.</td></tr>
</table>
<p>Harness A, the fixed generic designer, is the same envelope with every parent tool, the parent's full budget, no hooks, and citations not required. A unit test builds A and D and requires both to validate. The example file is that D harness, written out. A free-text brief is stored and marked not compiled. There is no parser for it.</p>

<h2>3. Compiler measurements</h2>
<p>Every figure in this section is from <span class="mono">pilot/results.json</span>, produced by <span class="mono">pilot/run_pilot.py</span> on Python 3.12.10. The parent card is the one in <span class="mono">examples/parent.json</span>: <span class="mono">read_file</span> (read on <span class="mono">src</span>, <span class="mono">tests</span>, <span class="mono">README.md</span>), <span class="mono">write_file</span> (write on <span class="mono">src</span>), <span class="mono">list_dir</span> (read on the workspace), <span class="mono">run_tests</span> (exec on <span class="mono">tests</span>), 30 steps, 8000 tokens, 120 seconds, both open-weight tiers.</p>
<p>Fifteen hand-written specs were validated, then passed through repair of at most three rounds. Four were valid on the first pass. Seven more were valid after one round. Four were still invalid when repair stopped. The cap is three rounds. None of these cases used the third round: two invalid specs changed nothing on round 1 and stopped, and two changed once, then stopped on round 2 because the spec no longer moved.</p>

<table class="keep">
<tr><th class="c1">Spec</th><th class="c2">Initial</th><th class="c3">Repaired</th><th>What happened</th></tr>
<tr><td>Four well-formed harnesses</td><td>valid</td><td>unchanged</td><td>Left untouched.</td></tr>
<tr><td>Unknown tool, exec on a write tool, budget above the parent, tokens below the step count, tier 70B, extra field, write path outside <span class="mono">src</span></td><td>invalid</td><td>valid, 1 round</td><td>Drop, downgrade, clamp, or delete. Privileges only move down.</td></tr>
<tr><td>Empty acceptance list</td><td>invalid</td><td>still invalid</td><td><span class="mono">goal.acceptance_tests</span> remains. Tests are not invented.</td></tr>
<tr><td>Blank goal statement</td><td>invalid</td><td>still invalid</td><td><span class="mono">goal.empty</span> remains. The statement is not invented.</td></tr>
<tr><td>Include path <span class="mono">../secrets</span></td><td>invalid</td><td>stops at round 2</td><td>The path is deleted. The slice is then empty. A slice is not invented.</td></tr>
<tr><td>AOrchestra-style tuple: instruction, context, tool names, model name</td><td>invalid</td><td>stops at round 2</td><td>Budgets, stop, verification, return contract, and tier are filled with conservative defaults. Repair stops at <span class="mono">schema.missing:goal.acceptance_tests</span>.</td></tr>
</table>

<p>The tuple row is the gap the proposal named against AOrchestra, shown as a property of this compiler. It is not a claim about any model, and it is not an accuracy result. Repair fills the fields that have a safe default, including a strict return contract (citations and test output required) and escalation on exhaustion. It refuses to supply the test the tuple never contained.</p>
<p>Determinism: the unknown-tool spec was validated 100 times. There was one unique verdict, <span class="mono">tool.unknown</span>. The validator does not read a clock or call a model.</p>
<p>This changes how O3 has to be run. Condition C must be scored as the tuple the orchestrator emitted. If the experiment repaired C until it became D, the comparison would collapse. The repair study above is a compiler result. It is not experimental condition C.</p>

<h2>4. Runtime measurements</h2>
<p>The workspace is <span class="mono">fixtures/off_by_one</span>. <span class="mono">src/app.py</span> returns <span class="mono">a + b + 1</span>. <span class="mono">tests/test_app.py</span> expects <span class="mono">a + b</span>. The same scripted actions were submitted to two harnesses. No model chose them. The question is what the runtime accepts, not whether an agent can solve the task.</p>
<p>Harness A is the fixed generic harness: every tool on the parent card, the parent's full budget, no verification hooks, citations not required. Harness D is a full spec: read and write only, a tight step budget where the budget case needs one, <span class="mono">unittest</span> and <span class="mono">ast.parse</span> hooks, and a return contract of at least one citation plus test output. Both validate before the runtime will start. An invalid spec is refused.</p>

<table>
<tr><th>Scripted task</th><th>Harness A</th><th>Harness D</th></tr>
<tr><td>Patch the file, then return &ldquo;the bug is fixed&rdquo; with no citation</td><td>Accepted. Counted as a silent handoff. Hooks: 0.</td><td>Both hooks passed (the patch was real). The return was then rejected. Not a silent handoff.</td></tr>
<tr><td>Three writes, D capped at 2 steps</td><td>All 3 writes applied. No budget violation.</td><td>Third write intercepted. 1 budget violation. 2 steps used. Stop action: escalate.</td></tr>
<tr><td><span class="mono">run_tests</span> as exec</td><td>Applied. The parent card allows it, and A grants it.</td><td>1 tool denial. D's allowlist has no exec tool.</td></tr>
<tr><td>Return a cited claim while the test still fails</td><td>Accepted. Tests were not run.</td><td>Not accepted. <span class="mono">unittest</span> failed. Stop: hook_failed.</td></tr>
<tr><td>Patch the file, then return <span class="mono">src/app.py:2</span> and test output</td><td>Not the contrast of interest. A does not consult the test.</td><td>Both hooks passed. Return accepted. Not a silent handoff.</td></tr>
</table>

<p>Two distinctions matter, and they are easy to blur. On the first row the patch landed under both harnesses, so the test was able to pass. A still accepted a confident summary with no evidence. D refused that summary after the hooks had passed. On the fourth row the workspace was still wrong. A accepted a cited claim without running the test. D ran it and refused the return. On the fifth row D accepted a return only when the test passed and the contract's evidence was present. That is the gate working in both directions.</p>
<p>These are nine scripted runs, one workspace, one seed, and zero model tokens. They do not support H1 or H2. They define the instruments those hypotheses need: a silent-handoff bit, a budget-violation count, a tool-denial count, and a hook failure. H2's comparison is against B and C, which were not run.</p>
<p>Revision was exercised on the two-step harness. The third action was a budget violation. <span class="mono">revise_from_trace</span> raised <span class="mono">max_steps</span> from 2 to 4, inside the parent cap of 30, and left <span class="mono">require_citations</span> true with <span class="mono">min_citations</span> 1. The revised spec still validates. This revision will not raise a tool privilege and will not drop the citation rule. A failed return stays visible to the orchestrator.</p>
<p>The spec cache recorded one miss and one hit for task type <span class="mono">bugfix</span> at tier 7&ndash;14B. The hit returns the stored spec and does not re-enter repair. Hypothesis H4, the break-even count of tasks that amortise a design call, is not estimated. There is no measured design-call cost. The repairer in this snapshot is deterministic and free. Reporting that as a token saving would be false. H1's token comparison has the same gap: the design call is defined to count, and no design call was made.</p>

<h2>5. The four hypotheses, unchanged</h2>
<p>The proposal pre-registered four hypotheses and said a negative result would be reported as one. This submission does not revise them. It records which instrument now exists, and which quantity is still missing. None of the four is a finding.</p>
<table class="keep">
<tr><th>Id</th><th>Registered claim</th><th>Instrument that now exists</th><th>Not available yet</th></tr>
<tr><td>H1</td><td>D stays within 5 points of A on accuracy and uses fewer tokens, design call included.</td><td>A and D can both be executed on a scripted task.</td><td>Accuracy. Model tokens. A design call.</td></tr>
<tr><td>H2</td><td>D has fewer silent handoffs than B and C.</td><td>A silent-handoff bit. On the fixture, A accepts an unsupported summary and D rejects it.</td><td>B, C, and any model-written return.</td></tr>
<tr><td>H3</td><td>Validation plus revision raises first-pass validity, most for a 7&ndash;14B orchestrator.</td><td>Typed errors, a three-round cap, and a validity count on 15 specs.</td><td>An orchestrator. The 15 specs were written by hand.</td></tr>
<tr><td>H4</td><td>Report how many tasks a cached spec must cover before the design call is paid for.</td><td>A cache, with one miss and one hit.</td><td>A non-zero design cost. Break-even is undefined, not zero.</td></tr>
</table>
<p>A negative result, if it comes, will be stated in those terms. If D falls more than 5 points behind A, H1 fails. If silent handoffs are not lower for D than for B and C, H2 fails. If first-pass validity does not rise, H3 fails, including the case where a small model rarely emits an acceptance test. If the design call is never paid back inside the task set, H4 fails and the report will say the break-even was not reached. Repair will not be used to convert any of those outcomes into a pass.</p>

<h2>6. Deviations from the registered plan</h2>
<p>Six choices are narrower than the proposal, and each one is there so the midpoint cannot pretend to be the study.</p>
<p><b>Validator.</b> The check is Python, not a JSON Schema library. The schema file is the published contract. A test locks the required names. Nested rules live in the validator, because that is the program the runtime actually trusts.</p>
<p><b>Clock.</b> Time budgets are read from an injected clock. The pilot uses a fake clock, so a pass is not a race against the machine. A wall clock is in the runtime for a later live run. It was not used for any number above.</p>
<p><b>Hooks.</b> The proposal names tests, linters, and AST checks. All three kinds exist. The commands are an allowlist of three. A spec cannot carry a shell string.</p>
<p><b>Revision policy.</b> The proposal left the edit rule open, beyond &ldquo;trace-driven.&rdquo; This code may raise a step budget up to the parent cap. It will not grant a broader tool, and it will not drop a citation requirement. A trace cannot talk the compiler out of least privilege.</p>
<p><b>Condition B.</b> A free-text brief is stored and flagged as not compiled. A parser would be a hidden designer, so there is not one.</p>
<p><b>Condition C.</b> Repair of a four-field tuple fills budgets and a strict return contract, then stops on the missing test. That repaired object is not condition C. Scoring it as C would erase the contrast. The run condition, later, is the tuple as emitted.</p>

<h2>7. What the repository is for</h2>
<p>The history on <a href="https://github.com/GauravSarkarr/HarnessSpec">github.com/GauravSarkarr/HarnessSpec</a> is the construction of this snapshot, on 5 November 2026, after the proposal of 21 October. It is not a backdated calendar.</p>

<table>
<tr><th>Commit</th><th>What it adds</th></tr>
<tr><td class="mono">5ec1ef5</td><td>Schema 0.1, path rules, parent capability card, the registered proposal PDF.</td></tr>
<tr><td class="mono">e3ea1db</td><td>Validator. Unknown tools, excess privilege, and unaffordable budgets become typed errors.</td></tr>
<tr><td class="mono">47c8a7a</td><td>Repair, capped at three rounds, with no invention of a goal or a test.</td></tr>
<tr><td class="mono">aca97ab</td><td>Runtime, hooks, and the return gate.</td></tr>
<tr><td class="mono">02c1967</td><td>Harness A, the four-field tuple, and conservative trace revision.</td></tr>
<tr><td class="mono">a60e33e</td><td>Fixture pilot. <span class="mono">pilot/results.json</span> is locked by a test that re-runs it.</td></tr>
<tr><td class="mono">aa8204d</td><td>README and <span class="mono">docs/AI_USE.md</span>.</td></tr>
</table>

<p>Reproduce the numbers, from a clean checkout, with no installed packages:</p>
<p class="mono block">PYTHONPATH=src python3 -m unittest discover -s tests -v<br/>
PYTHONPATH=src python3 pilot/run_pilot.py<br/>
PYTHONPATH=src python3 -m harnessspec examples/valid_spec.json examples/parent.json</p>
<p>The test suite re-runs the pilot and fails if <span class="mono">pilot/results.json</span> has drifted.</p>
<p>Every number in this report was taken from that file after a passing run on Python 3.12.10.</p>
<p>AI-tool use, which the proposal said would be logged: Cursor, Grok 4.7, on 5 November 2026, drafted the milestone implementation and this report. The check is the command above. No orchestrator model and no subagent model were called. The log is <span class="mono">docs/AI_USE.md</span>.</p>

<h2>8. Remaining work, in the order it should happen</h2>
<p>The second half is the study that was registered, not a larger version of the fixture.</p>
<p><b>1. A local orchestrator, measured on validity.</b> One 7&ndash;14B model must emit a HarnessSpec. Typed errors go back to it, at most three rounds. The quantities are first-pass validity and rounds used. That is the setup for H3. A small n will be reported as a pilot, not as H3.</p>
<p><b>2. B and C as run conditions.</b> B stays a free-text brief and is not compiled. C stays the four-field tuple, unrevised, so a missing acceptance test is a failed design. D is the full spec plus the validator. Scoring repaired-C as if it were C would erase the contrast in section 3.</p>
<p><b>3. Ten SWE-bench Verified instances</b> through the real edit-and-test loop, before the registered sizes of about 60 and about 60. The point of the ten is to learn which commands the allowlist must grow to. SWE-QA comes after that slice holds.</p>
<p><b>4. Accounting the proposal already fixed.</b> Tokens from the server, design call included. Three seeds. Paired bootstrap intervals. CPU and GPU energy beside every accuracy figure. The cache break-even (H4) waits until a design call has a real token cost.</p>
<p><b>5. Hooks.</b> The three-command allowlist grows to the pinned commands those benchmarks need. It does not become a general shell.</p>

<h2>9. Risks, with what the midpoint changed</h2>
<p>The risks in the proposal still stand. A small orchestrator may write poor specs, and the design call may cost more than the harness saves. Two of them are sharper now.</p>
<p>The compiler will not hide a missing test. If a 7&ndash;14B orchestrator rarely emits an acceptance test, the first-pass validity of D stays low. That is a reportable result. Patching it inside repair would falsify H3.</p>
<p>The fixture hook is <span class="mono">unittest discover</span> inside one workspace. SWE-bench tests are not that command. The runtime can be right on <span class="mono">fixtures/off_by_one</span> and still fail to run the benchmark. That is the main integration risk of the second half, and it is why the next milestone is ten instances rather than the full set.</p>
<p>Nothing here estimates success per kilowatt-hour, or tokens per correct answer. Those columns stay empty until the runs exist.</p>

<h2>10. Where the project stands</h2>
<p>O1 is met: HarnessSpec 0.1 is a typed eight-field protocol with a deterministic compiler. The enforceable half of O2 is met on fixtures: budgets, tool grants, hooks, and the return contract all change what a scripted subagent is allowed to do, and repair will not invent the evidence the protocol exists to demand. O3 has not started. H1&ndash;H4 are not results of this submission. The repository is the protocol, the compiler, the runtime, and the fixture evidence above.</p>
"""

CSS = """
body { font-family: serif; font-size: 9.15pt; line-height: 1.28; color: #1c1c1c; }
h1 { font-family: sans-serif; font-size: 18pt; line-height: 1.05; margin: 0 0 1pt 0; color: #111; }
h2 { font-family: sans-serif; font-size: 10.6pt; line-height: 1.2; margin: 8pt 0 2pt 0; color: #111; }
p { margin: 0 0 4pt 0; }
.kicker { font-family: sans-serif; font-size: 11pt; margin: 0 0 3pt 0; color: #222; }
.meta { font-size: 8.7pt; line-height: 1.3; margin: 0 0 2pt 0; color: #222; }
.repo { font-size: 8.7pt; margin: 1pt 0 2pt 0; }
a { color: #123a73; }
table { width: 100%; border-collapse: collapse; margin: 2pt 0 5pt 0; }
table.keep, div.keep { page-break-inside: avoid; }
th, td { border: 0.4pt solid #8d8d8d; padding: 2pt 3.5pt; vertical-align: top; font-size: 7.85pt; line-height: 1.22; }
th { font-family: sans-serif; background-color: #efefef; font-weight: bold; text-align: left; }
th.c2, th.c3 { width: 16%; }
.mono, td.mono { font-family: monospace; font-size: 8pt; color: #1c1c1c; }
.block { font-family: monospace; font-size: 8pt; line-height: 1.35; margin: 1pt 0 4pt 0; }
b { font-weight: bold; }
"""


def build() -> int:
    story = pymupdf.Story(html=HTML, user_css=CSS)
    writer = pymupdf.DocumentWriter(str(OUT))
    page = pymupdf.paper_rect("a4")
    body = pymupdf.Rect(40, 34, page.width - 40, page.height - 38)
    more = 1
    while more:
        device = writer.begin_page(page)
        more, _ = story.place(body)
        story.draw(device)
        writer.end_page()
    writer.close()

    doc = pymupdf.open(OUT)
    total = doc.page_count
    for index, sheet in enumerate(doc, start=1):
        footer = f"CS6.403 AutoSE  ·  HarnessSpec mid-submission  ·  5 November 2026  ·  {index} / {total}"
        sheet.insert_text(
            pymupdf.Point(40, page.height - 22),
            footer,
            fontsize=7.5,
            fontname="tiro",
            color=(0.25, 0.25, 0.25),
        )
        if index > 1:
            sheet.insert_text(
                pymupdf.Point(40, 20),
                "HarnessSpec  ·  mid-submission progress report",
                fontsize=8,
                fontname="tiro",
                color=(0.2, 0.2, 0.2),
            )
        sheet.draw_line(
            pymupdf.Point(40, 28),
            pymupdf.Point(page.width - 40, 28),
            color=(0.15, 0.15, 0.15),
            width=0.6,
        )
    doc.saveIncr()
    doc.close()
    return total


if __name__ == "__main__":
    print(f"{build()} pages -> {OUT}")
