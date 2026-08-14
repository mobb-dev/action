# Mobb GitHub action

This action posts the code and a SAST report to the Mobb vulnerability analysis engine and links the URL of the fix report to the PR. If you are using this on a private repo then the Mobb user the API key belongs to must have access to the repo and must approve github access for the user on the Mobb platform beforehand.

This repo contains two actions:

- **The root action** (`mobb-dev/action@v1.2`) runs Mobb's `analyze` command. It supports:
  - **Fix-only mode (default)**: provide an existing SAST report via `report-file` and Mobb generates fixes for the findings.
  - **Scan-and-fix mode**: omit `report-file` and the Mobb CLI runs its own SAST scan before producing fixes. Combine with `diff-aware: true` on pull requests to limit the scan to changes since the PR base commit.
- **The review action** (`mobb-dev/action/review@v1.2`) runs Mobb's `review` command, which comments fixes directly onto a pull request. It always requires an external SAST report — see [Review action](#review-action) below.

## Requirements

The actions invoke the Mobb CLI (Bugsy) as [`@mobb.ai/cli`](https://www.npmjs.com/package/@mobb.ai/cli), which ships as a prebuilt standalone binary, so the CLI itself no longer depends on the Node version on your runner. `npx` still needs some Node present; the actions install Node 20 for you.

### Supported runners

- **GitHub-hosted `ubuntu-*` runners (x64 and arm64)** — what this action is tested on in CI.
- **Self-hosted Linux runners with glibc 2.28 or newer** — Debian 10+, Ubuntu 20.04+, RHEL 8+.

The Mobb CLI ships prebuilt binaries for `linux-x64`, `linux-arm64`, `macos-x64`, `macos-arm64` and `win-x64`, each exercised by this repo's CLI smoke matrix.

For other environments, you can invoke the CLI directly with `npx mobbdev@latest` — the Node-based build of the same Bugsy, which runs anywhere Node 18.20+ is available.

## Inputs

## `report-file`

**Optional** The full path of the SAST report file. Omitting this input switches the action into **scan-and-fix mode**: the Mobb CLI performs its own internal SAST scan instead of consuming an external report.

## `api-key`

**Required** The Mobb API key to use with the action.

## `github-token`

**Required** The GitHub api token to use with the action. Usually available as `${{ secrets.GITHUB_TOKEN }}`.

## `mobb-project-name` 

**Optional** The Mobb Project Name where the fix analysis will be stored. If this is not specified, it will the analysis will default into the "My first project". 

## `auto-pr` 

**Optional** `true` or `false`. Enables Automatic Pull Request for fresh fixes. 

## `commit-directly`

**Optional** `true` or `false`. This requires `auto-pr` to be set to `true`. Once set, Fixes will be committed directly to the source branch. 

## `create-one-pr`

**Optional** `true` or `false` (default `false`). Opens a single unified pull request containing all fixes instead of one pull request per fix. Requires `auto-pr` to be set to `true`. Use this or `commit-directly`, not both.

## `organization-id`

**Optional** The Organization ID to use with the Mobb platform. If not specified, the default organization will be used.

## `polling`

**Optional** `true` or `false` (default `false`). Makes the CLI use HTTP polling instead of a WebSocket connection for status updates. Enable this on runners behind a proxy or firewall that blocks WebSocket traffic.

## `diff-aware`

**Optional** `true` or `false` (default `false`). Part of Mobb's scan-and-fix mode (enabled by omitting `report-file`). When set to `true` and the workflow is triggered by a `pull_request` event, Mobb performs a diff-aware scan limited to changes since the PR base SHA (passed to the CLI as `--baseline-commit`). Has no effect outside a pull request context.


## Outputs

## `fix-report-url`

The Mobb fix report URL.

## Example usage

### Fix-only mode with an existing SAST report (Checkmarx)

```yaml
# This example utilizes Mobb with Checkmarx via GitHub Actions

on: [pull_request]

jobs:
  Checkmarx-Mobb-example:
    runs-on: ubuntu-latest
    name: Fix Checkmarx findings with Mobb

    steps:
      - name: Checkout repo to get code
        uses: actions/checkout@v3

      - name: Setup Node on this machine
        uses: actions/setup-node@v3.6.0
        with:
          node-version: 18

      - name: Download and configure Checkmarx CLI
        run: |
          wget https://github.com/Checkmarx/ast-cli/releases/download/2.0.54/ast-cli_2.0.54_linux_x64.tar.gz -O checkmarx.tar.gz
          tar -xf checkmarx.tar.gz
          ./cx configure set --prop-name cx_apikey --prop-value ${{ secrets.CX_API_KEY }}
          ./cx configure set --prop-name cx_base_auth_uri --prop-value ${{ secrets.CX_BASE_AUTH_URI }}
          ./cx configure set --prop-name cx_base_uri --prop-value ${{ secrets.CX_BASE_URI }}
          ./cx configure set --prop-name cx_tenant --prop-value ${{ secrets.CX_TENANT }}
        shell: bash -l {0}

      - name: Run Checkmarx SAST scan
        run: ./cx scan create --project-name my-test-project -s ./ --report-format json --scan-types sast --branch nobranch  --threshold "sast-high=1"
        shell: bash -l {0}

      - name: Run Mobb on the findings and get fixes
        if: always()
        uses: mobb-dev/action@v1.2
        with:
          report-file: "cx_result.json"
          api-key: ${{ secrets.MOBB_API_TOKEN }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
```
### Scan-and-fix mode with diff-aware scanning (no external SAST tool required)

```yaml
# Mobb runs its own SAST scan on the PR diff and opens fix PRs automatically.

name: Mobb Scan-and-Fix

on:
  pull_request:
    branches:
      - main

jobs:
  scan-and-fix:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
      statuses: write
      contents: read
    steps:
      - name: Checkout repo
        uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.sha }}

      - name: Mobb scan-and-fix
        uses: mobb-dev/action@v1.2
        with:
          # report-file intentionally omitted -> enables scan-and-fix mode
          api-key: ${{ secrets.MOBB_API_TOKEN }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
          diff-aware: true
          auto-pr: true
          commit-directly: true
```

> Note: `diff-aware: true` requires a `pull_request` (or `pull_request_target`) trigger so the action can read `github.event.pull_request.base.sha`. On other event types the flag is silently ignored and Mobb falls back to a full scan.

## Review action

The review action (`mobb-dev/action/review`) runs Mobb's `review` command, which posts fixes as comments on a pull request.

It has stricter requirements than the root action, because the Mobb CLI's `review` command requires all of them:

- **`report-file` is required.** The review action has no scan-and-fix mode — Mobb cannot scan for you here. Use the root action with `diff-aware: true` if you want Mobb to do the scanning.
- **`scanner` is required**, and must be one of `checkmarx`, `codeql`, `fortify`, `snyk`, `sonarqube`, `semgrep`, `datadog`, `blackduck`.
- **It only runs on `pull_request` events**, since it needs the PR number and head commit SHA.

### Review action inputs

`report-file`, `scanner`, `api-key`, `github-token`, `mobb-project-name` and `polling`.

`organization-id` is not available on the review action — the Mobb CLI rejects it on `review`.

### Review action example

```yaml
name: "Mobb/CodeQL"

on:
  pull_request:
    branches: ["*"]

jobs:
  review:
    name: Scan with CodeQL and comment fixes with Mobb
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
      statuses: write
      security-events: write
      contents: read
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Initialize CodeQL
        uses: github/codeql-action/init@v3
        with:
          languages: javascript-typescript

      - name: Perform CodeQL analysis
        uses: github/codeql-action/analyze@v3
        with:
          category: "/language:javascript-typescript"
          output: results

      - name: Run Mobb on the findings and get fixes
        uses: mobb-dev/action/review@v1.2
        with:
          report-file: results/javascript.sarif
          scanner: codeql
          api-key: ${{ secrets.MOBB_API_TOKEN }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

## Versioning

Use `@v1.2`, the active release tag:

```yaml
uses: mobb-dev/action@v1.2
# or, for the review action
uses: mobb-dev/action/review@v1.2
```
