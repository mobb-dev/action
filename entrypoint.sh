#!/bin/sh -l

repository=$(git remote get-url origin)
repository=${repository%".git"}
branch=$(git rev-parse --abbrev-ref HEAD)
npx mobbdev@latest analyze -y -r $repository -b $branch -k "$1" -f "$2"