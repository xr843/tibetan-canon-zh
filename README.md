# 藏文大藏经汉文整理 · tibetan-canon-zh

藏文大藏经（甘珠尔、丹珠尔、松绷）的汉文整理工作，包括汉文总目录、版本对照、经论注疏关系和汉译稿。

*Tibetan Buddhist Canon (Kangyur, Tengyur, Sungbum) for Chinese readers: a unified Chinese catalog, edition concordances, a commentary-relation graph, and draft Chinese translations of untranslated works. See [English summary](#english-summary).*

> ⚠️ **AI 生成，未经人工审定。** 汉文拟译书名、注释关系和全部译稿，都由 AI（Anthropic Claude）在脚本和规则的辅助下生成，目前还没有经过懂藏文的专家审定。请只作研究线索使用，引用前请核对原文。发现错误欢迎提 [issue](../../issues) 或 PR，人工审校正是本项目最需要的帮助。

## 有什么

| 目录 | 内容 |
|---|---|
| [`catalog/`](catalog/) | **藏文大藏经总目录**，共 6,388 条：甘珠尔 1,138、丹珠尔 3,406、松绷 1,844。有 xlsx、tsv、md 三种格式 |
| [`catalog/kangyur/`](catalog/kangyur/)、[`catalog/tengyur/`](catalog/tengyur/) | 甘珠尔、丹珠尔的汉文目录，以及**版本对照表**（德格、拉萨、rKTs、ACIP 编号与大正藏对应） |
| [`catalog/sungbum/`](catalog/sungbum/) | 松绷（藏地祖师文集）的汉文目录，含作者生卒年和版权提示 |
| [`catalog/relations/`](catalog/relations/) | **经—论—注疏关系表**，共 1,044 条，并据此生成注疏谱系，例如《现观庄严论》有 56 部注疏 |
| [`catalog/translations-status/`](catalog/translations-status/) | 近现代汉译核对报告：哪些藏文典籍已有汉译 |
| [`site/`](site/) | 检索网页：可按书名、作者、编号检索，查看版本、汉译情况和注释关系 |
| [`translations/`](translations/) | 汉译稿，藏汉逐段对照，附校注 |
| [`scripts/`](scripts/) | 合并、编目、生成网页用的全部脚本 |
| [`docs/`](docs/) | [实施流程](docs/实施流程.md)、[翻译规范](docs/翻译规范.md)、译名规范、[汉译核查总表](docs/汉译核查总表_唯识部.md) |

### 汉译覆盖情况

在总目录 6,388 条中，**5,787 条未见任何汉译**（古代或近现代）。已知有汉译的：甘珠尔 329 条、丹珠尔 230 条、松绷 42 条。按“汉译情况”一列筛选“未见汉译”，就得到翻译空白清单。

### 译稿

**下载 Word / PDF 版**：[Release · 译稿下载](https://github.com/xr843/tibetan-canon-zh/releases/tag/translations)（由 Markdown 原稿自动生成；PDF 内嵌藏文字体，任何设备都能正常显示）。


只翻译同时满足以下三个条件的作品：
1. 没有现成汉译；
2. 作者在 1955 年以前去世，没有著作权问题；
3. 有校正版底本。

| 批次 | 作品 |
|---|---|
| 试点 | 俄曲·达玛巴扎《心与心所辨识摄略》；贡塘《三主要道修持法》；二世章嘉《修心八颂导引文》 |
| 第二批 | 宗喀巴《末那与阿赖耶难处》；贡塘《四谛建立》《理路幻钥》；贾曹杰《二谛建立》《中论八大难处释》；贡塘《俱舍论摄义》（底本缺六面，约缺 7%） |

每份译稿都是藏汉逐段对照，并附以下内容：
- **校注**：底本讹误，以及专有名词的比定依据；
- **引文核对表**：古代汉译引文据 CBETA 采用，现代译者的译文一律不采用，改为依藏文自译；
- **自查**：译者最没把握的地方。

[`translations/pilot/试点报告.md`](translations/pilot/试点报告.md) 说明了质量检验的方法和结果，以及已知的风险类型。

## 在线检索

开启 GitHub Pages 后，可直接在线访问 `site/`。在线版只含目录，不含藏文原文。

如需本地查看原文：先按下一节准备好数据，把 `site/` 放进数据根目录，再在数据根目录运行 `python3 -m http.server`。

## 藏文全文从哪里来

藏文全文约 3GB，不放在本仓库。可以从公开来源获取：
- ACIP 校正版：[dhammareader-tibetan-edition](https://github.com/yytt132/dhammareader-tibetan-edition)
- ACIP 官方包：[Asian Legacy Library](https://www.asianlegacylibrary.org/)
- 德格版：[Esukhia derge-kangyur](https://github.com/Esukhia/derge-kangyur)、[derge-tengyur](https://github.com/Esukhia/derge-tengyur)
- 编号对照：[rKTs](https://github.com/brunogml/rKTs)

再用 [`scripts/`](scripts/) 里的脚本重建合并版和目录，详见 [`scripts/README.md`](scripts/README.md)。

## 许可

- 目录、对照表、注释关系、译稿、文档：[CC BY 4.0](LICENSE-DATA)
- 代码：[MIT](LICENSE-CODE)

各上游来源的许可、署名，以及我们有意不收录的内容，见 [NOTICE.md](NOTICE.md)。

## 已知局限

- **拟译书名**：6,388 条中有 6,022 条书名是依藏文书名拟译的，不是通行译名，在 `译名类型` 一列里有标注。
- **注释关系**：由规则加人工补录得到，`把握` 一列为“低”的条目需要核对。
- **近现代汉译核对**：只覆盖了几个主要的公开书目，未见汉译不等于确实没有汉译。
- **译稿质量**：译稿只核对了能找到汉文参照的部分；作者自己的论述占译稿的大部分，这部分只能靠人工审定。

---

## English summary

This repository is a Chinese-language research catalog of the Tibetan Buddhist canon, covering the Kangyur, the Tengyur and the Sungbum (collected works of Tibetan masters). It contains:

- a **unified catalog** of 6,388 works, with Chinese titles, Tibetan/Wylie/Sanskrit/English titles, authors, Derge/Lhasa/rKTs/ACIP numbers, and Taishō parallels;
- **edition concordances**;
- a **commentary-relation graph** (which commentary explains which root text; 1,044 links);
- a survey of **existing Chinese translations** (5,787 works have none);
- **draft Chinese translations** of selected untranslated, public-domain Sungbum works. These are bilingual Tibetan–Chinese drafts with textual notes.

**All Chinese titles, relations and translations are AI-generated (Anthropic Claude) and have not yet been reviewed by human experts.** Corrections via issues and PRs are very welcome.

Tibetan full texts (~3 GB) are not included. They can be rebuilt from the public-domain or openly licensed sources listed in [NOTICE.md](NOTICE.md).

Licenses: data under CC BY 4.0, code under MIT.
