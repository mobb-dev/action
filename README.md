# Mobb GitHub action

This action posts the code and a SAST report to the Mobb vulnerability analysis engine and links the URL of the fix report to the PR. If you are using this on a private repo then the Mobb user the API key belongs to must have access to the repo and must approve github access for the user on the Mobb platform beforehand.

## Inputs

## `report-file`

**Required** The full path of the SAST report file.

## `api-key`

**Required** The Mobb API key to use with the action.

## `github-token`

**Required** The GitHub api token to use with the action. Usually available as `${{ secrets.GITHUB_TOKEN }}`.

## Outputs

## `fix-report-url`

The Mobb fix report URL.

## Example usage

```
on: [pull_request]

jobs:
  test_job:
    runs-on: ubuntu-latest
    steps:
      # To use this action,
      # you must check out the repository
      - name: Checkout
        uses: actions/checkout@v3
      - run: |
          # Run a SAST scan using a supprted tool, Snyk as an example
          npx snyk auth ${{ secrets.SNYK_API_KEY }}
          ! npx snyk code test --sarif-file-output=/home/runner/report.json ./
        shell: bash -l {0}
      - name: Mobb action step
        uses: mobb-dev/action@v2
        with:
          report-file: "/home/runner/report.json"
          api-key: ${{ secrets.MOBB_API_TOKEN }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
```
