#!/usr/bin/env bash
# A/B harness for the lottie skill.
#
# Runs each case twice per repetition: once with the skill loaded for that
# session only (--plugin-dir), once without. Both arms get an identical neutral
# working directory and the same --add-dir access, so the skill is the only
# variable.
#
#   ./evals/run_matrix.sh                      # all cases, 3 reps
#   ./evals/run_matrix.sh --reps 5             # more reps, tighter error bars
#   ./evals/run_matrix.sh --cases creator-trim-path,ios-matte-support
#
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPS=3
CASES=""
OUT="$REPO/evals/results/run-$(date +%Y%m%d-%H%M%S)"
MODEL="${EVAL_MODEL:-}"
PERM="${EVAL_PERMISSION_MODE:-acceptEdits}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --reps) REPS="$2"; shift 2 ;;
    --cases) CASES="$2"; shift 2 ;;
    --out) OUT="$2"; shift 2 ;;
    --model) MODEL="$2"; shift 2 ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

# --- Baseline integrity -----------------------------------------------------
# A user- or project-scope install leaks the skill into the control arm, which
# would make every number below a comparison of the skill against itself.
if claude plugin list 2>/dev/null | grep -q "lottie-engineering"; then
  cat >&2 <<'WARN'
REFUSING TO RUN: the lottie-engineering plugin is currently installed.

An installed plugin is active in every session, including the control arm, so
the comparison would be meaningless. Uninstall it for the duration of the run:

    claude plugin uninstall lottie-engineering@lottie-engineering

The treatment arm does not need it installed - it loads the skill per session
with --plugin-dir. Reinstall when you are done benchmarking.

Set EVAL_ALLOW_INSTALLED=1 to override (your numbers will be invalid).
WARN
  [[ "${EVAL_ALLOW_INSTALLED:-0}" == "1" ]] || exit 1
fi

command -v claude >/dev/null || { echo "claude CLI not found on PATH" >&2; exit 1; }

if [[ -n "$CASES" ]]; then
  IFS=',' read -r -a CASE_LIST <<< "$CASES"
else
  CASE_LIST=()
  for d in "$REPO"/evals/cases/*/; do CASE_LIST+=("$(basename "$d")"); done
fi

mkdir -p "$OUT"
echo "repo:   $REPO"
echo "out:    $OUT"
echo "cases:  ${CASE_LIST[*]}"
echo "reps:   $REPS per arm"
echo

run_one() {
  local case_name="$1" arm="$2" rep="$3"
  local case_dir="$REPO/evals/cases/$case_name"
  local run_dir="$OUT/$case_name/$arm/rep-$rep"
  mkdir -p "$run_dir/outputs"

  # Neutral sandbox: no AGENTS.md, no CLAUDE.md, nothing from this repo on disk.
  # Without this the control arm would read the repo's own AGENTS.md rules.
  local work; work="$(mktemp -d "${TMPDIR:-/tmp}/lottie-eval-XXXXXX")"
  mkdir -p "$work/outputs"

  local prompt; prompt="$(cat "$case_dir/prompt.md")"

  # Cases that operate on a file get a private copy inside the sandbox.
  local fixture=""
  case "$case_name" in
    validate-broken-file) fixture="broken-two-defects.json" ;;
    shrink-janky-file)    fixture="bloated-export.json" ;;
  esac
  if [[ -n "$fixture" ]]; then
    cp "$REPO/evals/fixtures/$fixture" "$work/$fixture"
    prompt="${prompt//FIXTURE_PATH/$work/$fixture}"
    python3 - "$case_dir/case.json" "$work/$fixture" <<'PY'
import json,os,sys
cfg_path, fixture = sys.argv[1], sys.argv[2]
cfg = json.load(open(cfg_path))
if "size_reduced" in cfg.get("oracles", []):
    cfg["input_bytes"] = os.path.getsize(fixture)
    json.dump(cfg, open(cfg_path, "w"), indent=2)
PY
  fi

  local -a args=(-p "$prompt"
    --output-format stream-json --verbose
    --permission-mode "$PERM"
    --add-dir "$work" --add-dir "$REPO"
    --allowedTools Read Write Edit Bash Glob Grep Skill)
  [[ -n "$MODEL" ]] && args+=(--model "$MODEL")
  [[ "$arm" == "with_skill" ]] && args+=(--plugin-dir "$REPO")

  ( cd "$work" && claude "${args[@]}" ) > "$run_dir/stream.jsonl" 2>"$run_dir/stderr.txt"
  local rc=$?

  # Anything the run wrote lands in outputs/ for the graders.
  [[ -d "$work/outputs" ]] && cp -R "$work/outputs/." "$run_dir/outputs/" 2>/dev/null
  find "$work" -maxdepth 1 -type f \( -name '*.json' -o -name '*.lottie' \) \
       ! -name "$fixture" -exec cp {} "$run_dir/outputs/" \; 2>/dev/null

  python3 "$REPO/evals/oracles/parse_stream.py" --run "$run_dir" --exit-code "$rc"
  rm -rf "$work"
  printf '  %-24s %-12s rep %s  exit=%s\n' "$case_name" "$arm" "$rep" "$rc"
}

for case_name in "${CASE_LIST[@]}"; do
  for rep in $(seq 1 "$REPS"); do
    for arm in with_skill without_skill; do
      run_one "$case_name" "$arm" "$rep"
    done
  done
done

echo
echo "grading..."
for case_name in "${CASE_LIST[@]}"; do
  for arm in with_skill without_skill; do
    for rep in $(seq 1 "$REPS"); do
      rd="$OUT/$case_name/$arm/rep-$rep"
      [[ -d "$rd" ]] && python3 "$REPO/evals/oracles/grade.py" \
        --case "$REPO/evals/cases/$case_name" --run "$rd"
    done
  done
done

echo
python3 "$REPO/evals/aggregate.py" "$OUT"
echo
echo "full results: $OUT"
