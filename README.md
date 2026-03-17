# watchdog-ai

Runtime verification for AI-built systems. Catch silent failures, contradictions, and stale data before they cost you.

## The Problem

AI writes code fast. But bugs go undetected. APIs break silently. Bots trade against their own predictions. And nobody notices for days.

Code review tools catch bugs *before* merge. LLM observability tracks *API calls*. **Nobody checks if the AI-built system is actually working correctly right now.**

## Install

```bash
pip install watchdog-ai
```

## Quick Start

```bash
# Generate example config
wdog init

# Edit watchdog.yaml for your project, then:
wdog check

# Run continuously
wdog watch
```

## What It Checks

| Check Type | What It Does | Example |
|------------|-------------|---------|
| `process` | Is your service running? | Bot daemon crashed silently |
| `freshness` | Is your data current? | Database hasn't updated in 26h |
| `log_scan` | Any errors in logs? | 5 tracebacks in last 50 lines |
| `assertion` | Is your data valid? | Capital dropped below 50% |
| `http` | Is your API healthy? | Health endpoint returning 500 |
| `script` | Custom validation | Your own check script |

## Example Config

```yaml
project: my-trading-bot
interval: 5m

checks:
  - name: Bot is running
    type: process
    match: "python3 bot.py"
    severity: critical

  - name: Data is fresh
    type: freshness
    path: ./data/trades.json
    max_age: 2h

  - name: No crashes
    type: log_scan
    path: ./logs/bot.log
    patterns: ["traceback", "error"]
    threshold: 3
    severity: critical

  - name: Capital is safe
    type: assertion
    source: ./data/state.json
    conditions:
      - expr: "$.balance > 0"
        severity: critical
      - expr: "$.balance > $.initial * 0.5"
        message: "Balance below 50%!"

notify:
  - type: webhook
    url: ${SLACK_WEBHOOK_URL}
    on: [critical]
```

## Commands

```bash
wdog init           # Generate example config
wdog check          # Run all checks once
wdog check --json   # Machine-readable output
wdog watch          # Run on schedule
wdog list           # List configured checks
```

## Exit Codes

- `0` — All healthy
- `1` — Warnings present
- `2` — Critical issues found

Works with CI/CD, cron, and monitoring systems.

## Born from Real Pain

This tool exists because:
- Our stock bot traded LONG while predictions said DOWN — for days
- Our exchange API broke silently and nobody noticed
- A strategy looked great on 2 days of data but was a loser over 6 months

We built watchdog for ourselves first. Now it's yours.

## License

MIT
