# NOTICE · 来源、许可与署名

本仓库汇集、改编了以下公开数据。逐项写明来源、许可，以及我们做了什么改动。

| 来源 | 许可 | 本仓库用到的部分 | 我们的改动 |
|---|---|---|---|
| [Asian Legacy Library (ACIP)](https://www.asianlegacylibrary.org/) 藏文电子文本，包括官方下载包和 2016 年版 | 公有领域（ACIP 声明） | 甘珠尔、丹珠尔、松绷的文本编号、书名、音节数 | 三个版本合并、去重；规范化比对；修正梵文叠字 |
| [dhammareader-tibetan-edition](https://github.com/yytt132/dhammareader-tibetan-edition)（commit 1ce8bbf） | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | ACIP 校正版文本的目录信息、汉文书名、大正藏对应、版权判定 | 汉文书名经过校订，原译名保留在 `dhammareader原译名` 列；补入 ACIP 本地版独有条目；重新分类编号 |
| [Esukhia derge-kangyur](https://github.com/Esukhia/derge-kangyur) / [derge-tengyur](https://github.com/Esukhia/derge-tengyur) | 公有领域（机械复制公有领域作品） | 德格版的篇目切分与音节数 | 按 `{D…}` 编号切分，保留原拼写 |
| [rKTs（Resources for Kanjur & Tanjur Studies）](https://github.com/brunogml/rKTs) | [CC0](https://creativecommons.org/publicdomain/zero/1.0/)，上游请求注明出处 | 德格、拉萨、rKTs 编号对照；藏文、梵文书名；英文书名（rKTs 数据中的 `English84000` 字段，源自 [84000](https://84000.co/) 项目） | 与 ACIP 文件对齐 |
| [CBETA 中华电子佛典](https://www.cbeta.org/) | 古代译文本身属公有领域；电子本依 [CBETA 版权说明](https://www.cbeta.org/copyright.php)，本仓库只作适量引用并注明出处 | 译稿中采用的**古代**汉译引文（玄奘、鸠摩罗什、真谛等），以及大正藏编号 | 繁转简；逐条标注 CBETA 编号与页栏行 |
| 近现代汉译书目（大慈恩月光藏等公开网站） | 各网站所有 | **只收**书名、链接与匹配结论，**不收**简介或译文正文 | — |

## 有意不收录的内容

- **受著作权保护的作品文本**：松绷中由现代作者（卒于 1955 年之后）撰写的作品，以及 dhammareader 判定受著作权保护的作品。目录里保留它们的条目，并在 `版权提示` 列中标出，但不提供文本。
- **现代汉译者的译文**：法尊法师（1980 年去世）等现代译者的汉译，在中国法下仍受保护。译稿中的相关引文一律依藏文自译，只标 CBETA 出处供读者对照。
- **翻译试点用作比对的参照译文**：只保留“一致 / 不一致”的比对结论。
- **藏文全文**：约 3GB，不放在本仓库。获取方法见 README。

## 本仓库自身成果的许可

- 目录、对照表、注释关系、译稿、文档：[CC BY 4.0](LICENSE-DATA)
- 脚本与网页代码：[MIT](LICENSE-CODE)

引用时请注明本仓库，并按上表一并注明各上游来源（dhammareader 的 CC BY 4.0 要求署名）。
