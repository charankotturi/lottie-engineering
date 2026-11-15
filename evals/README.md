# A/B harness

Runs each case twice — once with the skill, once without — and produces numbers you can argue with.

```bash
./evals/run_matrix.sh                                  # all cases, 3 reps per arm
./evals/run_matrix.sh --reps 5                         # tighter error bars
./evals/run_matrix.sh --cases creator-trim-path        # one case
```

Results land in `evals/results/run-<timestamp>/`, with `benchmark.json` and `benchmark.md` at the top.

## Read this before trusting any output

**Uninstall the plugin first.** The runner refuses to start otherwise, and the reason matters: an installed plugin is active in *every* session, control arm included, so the comparison would be the skill against itself.

```bash
claude plugin uninstall lottie-engineering@lottie-engineering
```

The treatment arm doesn't need it installed — it loads the skill for one session with `--plugin-dir`. Reinstall when you're done.

**Each run gets a neutral sandbox.** Both arms execute in a fresh `mktemp -d`, not in this repo. Running inside the repo would hand the control arm the rules from `AGENTS.md` and quietly erase the difference being measured. Both arms get identical `--add-dir` access and the same allowed tools, so the skill is the only variable.

**Three reps is enough to spot a large effect and nothing else.** The aggregator prints a delta next to the combined spread and labels it `inside the noise` when it can't be distinguished from variance. Believe the label, not the delta. If a result matters, raise `--reps`.

## What gets measured

Every grader in `oracles/grade.py` is decidable by a script. That's deliberate: the skill's claim is about not asserting what it can't back, so grading it on taste would beg the question.

| Oracle | What it decides |
|---|---|
| `no_fabricated_tool` | Every MCP-shaped identifier in the output exists in the known inventory |
| `defers_to_discovery` | With no MCP connected, did it say "discover this" rather than invent a method |
| `no_unearned_universality` | No "works on all platforms", "fully compatible", "zero hallucinations" |
| `no_skip_as_pass` | No blanket success verdict alongside admitted gaps |
| `versions_named` | A runtime support claim carries a version, so it's reproducible |
| `labels_present` | Evidence labels actually used |
| `artifact_validates` | Any produced `.json`/`.lottie` survives the structural validator |
| `identifies_defect` | The planted defects in a fixture were named |
| `size_reduced` | Measured byte reduction against a declared target |

Statuses are `PASS`, `FAIL`, `REVIEW`, `NOT_APPLICABLE`. Only `PASS`/`FAIL` enter pass rates — a `REVIEW` is an honest "a human has to look", not a silent pass.

**Trigger rate is measured separately and is the signal most people get wrong.** The treatment arm is handed the skill but never told to use it, so `parse_stream.py` inspects the transcript for an actual `Skill` invocation. Telling a subagent "here is the skill, use it" measures nothing about activation, which is what the description controls.

## The fabrication oracle is provisional

`oracles/known_identifiers.json` lists the tool families named in public LottieFiles docs, not a live capture. So an unknown identifier returns `REVIEW`, not `FAIL` — the script can't tell an invented name from a real one it hasn't heard of.

Make it authoritative by capturing the real inventory from a connected client:

```bash
python skills/lottie/scripts/record_tool_inventory.py creator-tools.json --surface creator-mcp
```

Then replace the lists and set `is_live_capture: true`. Unknown identifiers become hard failures, and this becomes the one number that genuinely tests the premise.

## What this harness cannot tell you

Whether the animation looks right. Pass rates say a file is structurally sound and the claims around it were honest; they say nothing about whether the motion reads well at display size.

For that, compare outputs blind: strip the arm labels, show two results side by side, and record which is better without knowing which is which. Author-run quality judgement on a skill you wrote is worth very little — the point of blinding is to make your own preference stop counting.

## Adding a case

```
cases/<name>/
├── case.json    name, job, why, oracles[], thresholds
└── prompt.md    what a real user would actually type
```

Write prompts the way your team talks — lowercase, half-specified, with real constraints and a stray detail or two. A prompt that names the skill or reads like a test has already answered the question it was meant to ask.

If the case needs an input file, add it to `fixtures/` and map it in the `fixture` case statement in `run_matrix.sh`; `FIXTURE_PATH` in the prompt is substituted with the sandbox copy.
