#!/usr/bin/env bash
# Read agent output on stdin. Extract the first ```json ... ``` block.
# Write to .multiagent_cli/run/plan.json. Echo the batch schedule.
# Requires: jq.
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
RUN_DIR="$REPO_ROOT/.multiagent_cli/run"
mkdir -p "$RUN_DIR"

INPUT="$(cat)"

JSON_BODY="$(printf '%s' "$INPUT" | awk '
  /```json/ { flag=1; next }
  /```/     { if (flag) { flag=0; exit } }
  flag      { print }
')"

if [ -z "$JSON_BODY" ]; then
  # Fallback: treat entire stdin as JSON.
  JSON_BODY="$INPUT"
fi

echo "$JSON_BODY" | jq '.' > "$RUN_DIR/plan.json" || {
  echo "ERROR: plan JSON parse failed" >&2
  echo "$JSON_BODY" >&2
  exit 1
}

# Emit batch schedule: groups by parallel_group honoring depends_on.
jq '
  reduce (.subtasks // [])[] as $task (
    {batches: [], done: []};
    . as $state
    | ($task.parallel_group // $task.id) as $group
    | [($task.depends_on // [])[] | select(($state.done | index(.)) == null)] as $blocked
    | if ($blocked | length) > 0 then
        .batches += [[$task]]
        | .done += [$task.id]
      else
        (.batches | length) as $batch_count
        | if $batch_count == 0 then
            .batches = [[$task]]
          else
            (.batches[$batch_count - 1] | map(.parallel_group // .id) | unique) as $last_groups
            | if ($last_groups | length) == 1 and $last_groups[0] == $group then
                .batches[$batch_count - 1] += [$task]
              else
                .batches += [[$task]]
              end
          end
        | .done += [$task.id]
      end
  )
  | .batches
' "$RUN_DIR/plan.json" > "$RUN_DIR/batches.json"

echo "$RUN_DIR/batches.json"
