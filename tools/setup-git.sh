#!/bin/sh
# One-off per clone: show .mecal changes as readable settings/tables in git diff/log -p.
git config diff.mecal.textconv "python3 tools/mecal.py dump"
git config diff.mecal.cachetextconv true
echo "mecal diff driver configured"
