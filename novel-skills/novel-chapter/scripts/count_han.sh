#!/bin/bash
# 统计 Markdown 文件中的纯汉字数（\p{Han}，不含标点、数字、字母、空格）
# 用法: bash count_han.sh <文件.md> [文件2.md ...]
# 退出码: 全部文件 ≥2000 汉字返回 0，否则返回 1（可脚本化批量校验）
THRESHOLD=2000
rc=0
for f in "$@"; do
  if [ ! -f "$f" ]; then
    printf "%s\t文件不存在\n" "$f"
    rc=1
    continue
  fi
  n=$(perl -CSAD -ne '$n += () = /\p{Han}/g; END { print $n // 0 }' "$f")
  if [ "$n" -ge "$THRESHOLD" ]; then
    verdict="达标(>=${THRESHOLD})"
  else
    verdict="不足(<${THRESHOLD})"
    rc=1
  fi
  printf "%s\t%s 汉字\t%s\n" "$f" "$n" "$verdict"
done
exit $rc
