#!/bin/bash
# 字数统计与硬区间校验（2026-10-01 用户定标：**每章 2200–2500 字，口径＝非空白字符**，
# 即汉字+标点+字母数字，只扣空格换行——与线上平台 word_count 同口径；纯汉字数作辅助参考一并输出）。
# 判定：<2200 不足（须扩写）；>2500 超长（须删减，>3000 考虑拆章）；2200–2500 达标。
# 注意：纯汉字计数禁用 \p{Han}（本机 perl 5.34 实测该性质会把 。，、《》误计为汉字），
# 一律用显式码位区间。
# 用法: bash count_han.sh <文件.md> [文件2.md ...]
# 退出码: 全部文件落在 2200–2500 区间返回 0，否则返回 1（可脚本化批量校验）
LOW=2200
HIGH=2500
rc=0
for f in "$@"; do
  if [ ! -f "$f" ]; then
    printf "%s\t文件不存在\n" "$f"
    rc=1
    continue
  fi
  # 门槛数=非空白字符（去标题行）；辅助参考=纯汉字（显式区间，防 \p{Han} 混入标点）
  n=$(python3 -c "
import re
s = open('$f', encoding='utf-8').read()
body = re.sub(r'^#.*\n', '', s, count=1)
nonws = len(re.sub(r'\s', '', body))
han = len(re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]', body))
print(f'{nonws}\t{han}')
")
  gate=$(printf '%s' "$n" | cut -f1)
  han=$(printf '%s' "$n" | cut -f2)
  if [ "$gate" -lt "$LOW" ]; then
    verdict="不足(<${LOW}，须扩写)"
    rc=1
  elif [ "$gate" -gt "$HIGH" ]; then
    verdict="超长(>${HIGH}，须删减)"
    rc=1
  else
    verdict="达标(${LOW}-${HIGH})"
  fi
  printf "%s\t%s 字(非空白)\t纯汉字 %s\t%s\n" "$f" "$gate" "$han" "$verdict"
done
exit $rc
