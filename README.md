# Mobb GitHub action

This action posts the code and a SAST report to the Mobb vulnerability analysis engine and links the URL of the fix report to the PR. If you are using this on a private repo then the Mobb user the API key belongs to must have access to the repo and must approve github access for the user on the Mobb platform beforehand.

The action supports two modes:

- **Fix-only mode (default)**: provide an existing SAST report via `report-file` and Mobb generates fixes for the findings.
- **Scan-and-fix mode**: omit `report-file` and the Mobb CLI runs its own SAST scan (powered by opengrep) before producing fixes. Combine with `diff-aware: true` on pull requests to limit the scan to changes since the PR base commit.

## Inputs

## `report-file`

**Optional** The full path of the SAST report file. Omitting this input switches the action into **scan-and-fix mode**: the Mobb CLI performs its own internal SAST scan (via opengrep) instead of consuming an external report.

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

## `organization-id`

**Optional** The Organization ID to use with the Mobb platform. If not specified, the default organization will be used.

## `diff-aware`

**Optional** `true` or `false` (default `false`). Part of Mobb's scan-and-fix mode (enabled by omitting `report-file`). When set to `true` and the workflow is triggered by a `pull_request` event, Mobb performs a diff-aware scan limited to changes since the PR base SHA (passed to the CLI as `--baseline-commit`). Has no effect outside a pull request context.


## Outputs

## `fix-report-url`

The Mobb fix report URL.

## Example usage

### Fix-only mode with an existing SAST report (Checkmarx)

```
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
        uses: mobb-dev/action@v1
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
        uses: mobb-dev/action@v1
        with:
          # report-file intentionally omitted -> enables scan-and-fix mode
          api-key: ${{ secrets.MOBB_API_TOKEN }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
          diff-aware: true
          auto-pr: true
          auto-commit: true
```

> Note: `diff-aware: true` requires a `pull_request` (or `pull_request_target`) trigger so the action can read `github.event.pull_request.base.sha`. On other event types the flag is silently ignored and Mobb falls back to a full scan.
