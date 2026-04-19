# multiagent_cli eval fixtures

This directory is the ownership point for `subagent-evals` compatibility
fixtures for the current `multiagent_cli` markdown agent pack.

It contains:

- `subagent-evals.config.yaml` — discovery and output config
- `cases/*.yaml` — replay runtime and security cases
- `example-runner.mjs` — minimal local replay runner for fixture-backed cases

The fixtures target the real local agent definitions under:

- `../.claude/agents`

Run them from a `subagent-evals` checkout by pointing the CLI at this
directory:

```bash
node packages/cli/dist/bin/subagent-evals.js eval --cwd /absolute/path/to/multiagent_cli/evals
node packages/cli/dist/bin/subagent-evals.js report --input /absolute/path/to/multiagent_cli/evals/out/results.json --output /absolute/path/to/multiagent_cli/evals/out/report.html
```

These runtime cases are replay fixtures, not live model invocations. They
exist to validate the eval harness against the current `planner`, `coder`,
`reviewer`, `tester`, `gatekeeper`, and `debugger` markdown identities while
the static layer scores the actual prompts in this repo.
