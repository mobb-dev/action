# Mobb analyze GitHub action

This action posts the current PR code and a SAST report to mobb analyze and prints the URL of the fix report to the workflow log.

## Inputs

## `report-file`

**Required** The full path of the SAST report file.

## `api-key`

**Required** The Mobb API key to use with the action.

## Outputs

## `url`

The Mobb fix report URL.

## Example usage

uses: mobbdev/action@v1
with:
report-file: '/path/to/report.json'
api-key: '1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef'
