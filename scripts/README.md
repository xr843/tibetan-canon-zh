# 脚本说明

这些脚本都假定在一个**数据根目录**下运行。用环境变量 `CANON_ROOT` 指定这个目录（默认是当前目录）。

数据根目录的布局如下：

```
<CANON_ROOT>/
├── _来源/
│   ├── dhammareader/repo/   # git clone https://github.com/yytt132/dhammareader-tibetan-edition（本项目用的是 commit 1ce8bbf）
│   ├── ALL官方/              # Asian Legacy Library 官方下载包（KANGYUR.zip、TENGYUR.zip、SUNGBUM 等）
│   ├── Esukhia/derge-kangyur, derge-tengyur
│   └── rKTs/repo/            # git clone https://github.com/brunogml/rKTs
└── 藏文大藏经/ACIP/          # （可选）ACIP 2016 年 Unicode 版本地拷贝；没有这一份时，相关脚本只合并前两个来源
```

## 运行顺序

1. 合并文本：
   - 甘珠尔、丹珠尔：`canon/merge_canon.py kangyur|tengyur`
   - 松绷：`sungbum/build.py`，再运行 `sungbum/add_short.py` 和 `sungbum/add_lost.py`
2. 德格版切分与编号对照：`canon/derge_and_map.py kangyur|tengyur`
3. 各部汉文目录：
   - 甘珠尔、丹珠尔：`canon/build_canon_catalog.py`
   - 松绷：`sungbum/build_catalog.py`
4. 总目录：`canon/build_master_catalog.py`（需要 openpyxl）
5. 检索网页数据：`canon/build_site_data.py`
6. 注释关系候选：`canon/commentary_candidates.py`。生成的是候选，需要人工或模型确认后，才写入 `catalog/relations/注释关系表.tsv`

## 依赖

Python 3.10 及以上，另需 `pyewts`、`openpyxl`。

注意：`pyewts` 0.2.0 在处理梵文叠字时有 bug，例如 མཎྜལ 会被转成 མཨལ。`sungbum/fixmap_safe.json` 是修正这些叠字的对照表。

## 有些步骤无法自动重现

`汉文书名` 的拟译、注释关系的确认、近现代汉译的匹配，部分是由 AI 逐条判断后写入表格的，不是脚本输出的结果。所以重新运行脚本，得到的是目录的**结构**，而不是这些判断。这些判断以仓库里的 tsv 为准。
