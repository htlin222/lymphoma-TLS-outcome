# 圖表產生工作流程更新：從 Python 轉換至 R

**更新日期**: 2024-02-07
**狀態**: ✅ 完成
**影響範圍**: 所有圖表產生與組裝工作流程

---

## 📋 總結

本次更新將整個 meta-analysis 專案的圖表產生工作流程從 Python (PIL/Pillow) 轉換為 R (ggplot2/patchwork/cowplot)，以提高重現性、整合性與發表品質。

---

## 🎯 主要變更

### 1. 新增文件

#### `/Users/htlin/meta-pipe/docs/R_FIGURE_GUIDE.md` (630+ 行)

**內容**:

- R 套件生態系統參考 (CRAN, Bioconductor, Tidyverse, rOpenSci, R-universe)
- 完整工作流程範例 (森林圖、多面板圖、亞組分析)
- 發表品質匯出設定 (ggsave, dpi=300)
- 期刊特定要求 (Nature/Lancet/JAMA)
- 疑難排解指南
- 專業主題套件 (ggthemr, hrbrthemes, viridis, ggsci)

**使用時機**:

- Stage 06 (Analysis): 產生所有統計圖表
- Stage 07 (Manuscript): 組裝多面板圖表

**套件資源**:

1. **CRAN** (cran.r-project.org) — R 套件官方總倉庫
2. **Bioconductor** (bioconductor.org) — 生物資訊學專用套件庫
3. **Tidyverse** (tidyverse.org) — 資料科學核心套件群 (dplyr、ggplot2)
4. **rOpenSci** (ropensci.org) — 經同儕審查的科學研究套件
5. **R-universe** (r-universe.dev) — 新一代套件搜尋整合平台

---

### 2. 更新現有文件

#### `CLAUDE.md` (主要代理指令檔)

**變更**:

- 新增 "R Figure Generation" 到 Essential 文件列表
- Stage 06 (Analysis) 現在強調 **R-only 工作流程**
- 移除 Python 圖表產生參考
- 新增 R 套件資源連結
- 加入 `ggsave()` 範例 (300 DPI 要求)

**關鍵指令更新**:

```r
# 原本 (Python)
# python assemble_figures.py figure1.png vertical ...

# 現在 (R)
library(patchwork)
combined <- p1 / p2 / p3
ggsave("figure1.png", width=10, height=12, dpi=300)
```

---

#### `docs/MANUSCRIPT_ASSEMBLY.md`

**變更**:

- Phase 3 (Figure Assembly) 現在使用 R 套件 (patchwork, cowplot)
- 移除 Python PIL/Pillow 參考
- 新增 R 多面板組裝範例
- 更新最佳實踐：使用 R `ggsave()`
- 新增「不要使用 Python 繪圖」指南

**新工作流程**:

```r
# 使用 patchwork 組合圖表
library(patchwork)

# 垂直排列
combined <- p1 / p2 / p3

# 水平排列
combined <- p1 | p2 | p3

# 網格排列 (2x2)
combined <- (p1 | p2) / (p3 | p4)

# 匯出
ggsave("figure.png", width=10, height=12, dpi=300)
```

---

#### `~/.claude/skills/scientific-figure-assembly/SKILL.md`

**變更**:

- 技能描述改為強調 R 工作流程
- `allowed-tools` 改為包含 `Rscript`
- 重新結構化內容：
  - **推薦**: Method 1: patchwork (ggplot2)
  - **推薦**: Method 2: cowplot (通用)
  - **不推薦**: Python 方法 (標記為 Legacy)

**新範例**:

```r
# 完整 meta-analysis 森林圖組裝
library(meta)
library(patchwork)

# 建立個別圖表
res_pcr <- metabin(event.e, n.e, event.c, n.c, data=data)
res_efs <- metagen(TE, seTE, data=data)
res_os <- metagen(TE, seTE, data=data)

# 組合
combined <- forest(res_pcr) / forest(res_efs) / forest(res_os) +
  plot_annotation(tag_levels = "A")

# 匯出 300 DPI
ggsave("figure1_efficacy.png", width=10, height=14, dpi=300)
```

---

## 📦 R 套件依賴

### 核心套件 (必裝)

```r
# Meta-analysis
install.packages(c("meta", "metafor", "dmetar"))

# 視覺化
install.packages(c("ggplot2", "patchwork", "cowplot"))
```

### 專業主題套件 (建議)

```r
# 色彩與主題
install.packages(c(
  "viridis",      # 色盲友善色彩
  "scico",        # 科學色彩圖
  "ggsci",        # 期刊色彩方案 (Nature, NEJM, Lancet)
  "ggthemes",     # 專業主題 (Economist, WSJ)
  "hrbrthemes"    # 排版專注主題
))

# ggthemr 需從 GitHub 安裝
# devtools::install_github("Mikata-Project/ggthemr")
```

---

## 🔄 工作流程比較

### 舊工作流程 (Python)

```bash
# Step 1: R 產生個別圖表
Rscript 01_forest_plot.R  # 產生 forest_plot.png

# Step 2: Python 組裝
uv run python assemble_figures.py figure1.png vertical \
  forest_pcr.png forest_efs.png forest_os.png

# 問題:
# - 需要切換語言 (R → Python)
# - 額外依賴 (Pillow)
# - 難以整合統計資訊
```

### 新工作流程 (R)

```r
# 全程在 R 中完成
library(meta)
library(patchwork)

# Step 1: 分析與繪圖
res_pcr <- metabin(...)
res_efs <- metagen(...)
res_os <- metagen(...)

# Step 2: 組裝 (同一個 R session)
combined <- forest(res_pcr) / forest(res_efs) / forest(res_os)

# Step 3: 匯出
ggsave("figure1.png", width=10, height=14, dpi=300)

# 優點:
# ✅ 單一語言 (R)
# ✅ 無需外部依賴
# ✅ 直接整合統計結果
# ✅ 更易重現
```

---

## 🎨 ggplot2 最佳實踐

### 為什麼重要？

在 meta-analysis 專案中，ggplot2 是主要的視覺化工具。遵循最佳實踐可以：

✅ **提高程式碼可讀性** - 團隊成員更容易理解和維護
✅ **確保可重現性** - 明確的參數設定避免依賴預設值
✅ **改善視覺效果** - 專業的外觀提升可信度
✅ **支援無障礙** - 色盲友善的色彩確保所有讀者都能理解

### 核心原則

#### 1. 使用 Tidy Data (長格式)

```r
# ❌ 寬格式 (難以繪圖)
data_wide <- data.frame(
  study = c("Trial A", "Trial B"),
  ici_events = c(50, 60),
  control_events = c(40, 45)
)

# ✅ 長格式 (易於 ggplot2)
library(tidyr)
data_long <- data_wide %>%
  pivot_longer(
    cols = ends_with("_events"),
    names_to = "treatment",
    values_to = "events"
  )

# 現在可以輕鬆繪圖
ggplot(data_long, aes(x = study, y = events, fill = treatment)) +
  geom_col(position = "dodge")
```

#### 2. 全域 vs 局部美學映射

```r
# ✅ 好：全域美學 (避免重複)
ggplot(data, aes(x = time, y = response, color = treatment)) +
  geom_point() +
  geom_line()

# ❌ 壞：重複美學映射
ggplot(data) +
  geom_point(aes(x = time, y = response, color = treatment)) +
  geom_line(aes(x = time, y = response, color = treatment))
```

#### 3. 選擇正確的 geom

```r
# ✅ 已彙總資料用 geom_col()
ggplot(summary_data, aes(x = group, y = mean)) +
  geom_col()

# ❌ 不要用 geom_bar(stat = "identity")
ggplot(summary_data, aes(x = group, y = mean)) +
  geom_bar(stat = "identity")

# ✅ 處理重疊點用 geom_jitter()
ggplot(data, aes(x = treatment, y = response)) +
  geom_jitter(width = 0.2, alpha = 0.5)
```

#### 4. 永遠明確標示

```r
# ✅ 好：完整的標籤
ggplot(data, aes(x = time, y = survival, color = treatment)) +
  geom_line() +
  labs(
    title = "Overall Survival by Treatment",
    subtitle = "Kaplan-Meier estimates (N=1,174 patients)",
    x = "Time since randomization (months)",
    y = "Survival probability",
    color = "Treatment arm"
  )
```

#### 5. 使用色盲友善色彩

```r
# ✅ 連續變數用 viridis
ggplot(data, aes(x, y, color = p_value)) +
  geom_point() +
  scale_color_viridis_c(option = "plasma")

# ✅ 分類變數用 ColorBrewer 或 ggsci
library(ggsci)
ggplot(data, aes(x, y, fill = treatment)) +
  geom_boxplot() +
  scale_fill_lancet()  # Lancet 期刊色彩
```

#### 6. 建立可重用的主題

```r
# ✅ 定義一次，到處使用
my_meta_theme <- function() {
  theme_minimal(base_size = 14) +
    theme(
      plot.title = element_text(face = "bold", size = 16),
      legend.position = "bottom",
      panel.grid.minor = element_blank()
    )
}

# 套用到所有圖表
p1 <- ggplot(data1, aes(x, y)) + geom_point() + my_meta_theme()
p2 <- ggplot(data2, aes(x, y)) + geom_line() + my_meta_theme()
```

### 完整範例：遵循最佳實踐的 Meta-Analysis 圖表

```r
library(ggplot2)
library(dplyr)
library(tidyr)
library(hrbrthemes)
library(ggsci)

# 1. 準備 tidy data
forest_data <- extraction_data %>%
  select(study_id, rr, ci_lower, ci_upper, weight) %>%
  arrange(desc(weight))

# 2. 定義自訂主題
meta_theme <- function() {
  theme_ipsum_rc(base_size = 12) +
    theme(
      plot.title = element_text(face = "bold", size = 14),
      legend.position = "bottom",
      panel.grid.minor = element_blank()
    )
}

# 3. 漸進式建構圖表
p <- ggplot(forest_data, aes(x = rr, y = reorder(study_id, weight)))

# 加入參考線
p <- p + geom_vline(xintercept = 1, linetype = "dashed", color = "gray50")

# 加入點和誤差線
p <- p + geom_point(aes(size = weight), color = pal_lancet()(1))
p <- p + geom_errorbarh(aes(xmin = ci_lower, xmax = ci_upper), height = 0.2)

# 明確設定刻度
p <- p + scale_x_continuous(
  limits = c(0.5, 2.0),
  breaks = seq(0.5, 2.0, by = 0.25),
  trans = "log10"
)

# 完整標籤
p <- p + labs(
  title = "Forest Plot: Pathologic Complete Response",
  subtitle = "Risk ratio with 95% CI (5 RCTs, N=2,402 patients)",
  x = "Risk Ratio (log scale)",
  y = NULL
)

# 套用主題
p <- p + meta_theme()

# 4. 匯出
ggsave("figures/forest_plot.png", width = 10, height = 6, dpi = 300)
```

### 常見錯誤與修正

| ❌ 不要這樣做  | ✅ 應該這樣做         | 原因         |
| -------------- | --------------------- | ------------ |
| 使用預設色彩   | viridis/ggsci 色彩    | 色盲友善     |
| 省略軸標籤     | 使用 `labs()`         | 清晰度       |
| 寬格式資料     | Tidy 長格式           | 易於映射     |
| 重複美學定義   | 全域定義在 `ggplot()` | DRY 原則     |
| 預設灰色主題   | `theme_minimal()`     | 專業外觀     |
| 不必要的網格線 | 用 `theme()` 移除     | 減少視覺雜訊 |

### 快速參考

```r
# === 資料準備 ===
data %>% pivot_longer(cols, names_to, values_to)

# === 圖表結構 ===
ggplot(data, aes(x, y, color = group)) +  # 全域美學
  geom_point() +                          # 幾何層
  scale_color_viridis_d() +               # 色彩刻度
  labs(title, x, y) +                     # 標籤
  theme_minimal() +                       # 基礎主題
  theme(legend.position = "bottom")       # 微調

# === 匯出 ===
ggsave("file.png", width = 10, height = 6, dpi = 300)
```

---

## 📊 圖表類型範例

### 1. 森林圖 (Forest Plots)

```r
library(meta)

# 二元結局 (RR, OR)
res <- metabin(event.e, n.e, event.c, n.c, data=data, sm="RR")

# 連續結局 (HR from log-HR)
res <- metagen(TE=log_hr, seTE=se_log_hr, data=data, sm="HR")

# 匯出
png("forest_plot.png", width=10, height=8, units="in", res=300)
forest(res)
dev.off()
```

### 2. 多面板組合 (使用 patchwork)

```r
library(patchwork)

# 垂直排列 (常見於 meta-analysis)
figure1 <- p_pcr / p_efs / p_os +
  plot_annotation(
    title = "Figure 1. Efficacy Outcomes",
    tag_levels = "A"
  )

ggsave("figure1.png", width=10, height=14, dpi=300)

# 網格排列 (2x2 亞組分析)
figure2 <- (p_age | p_sex) / (p_stage | p_histology) +
  plot_annotation(tag_levels = "A")

ggsave("figure2.png", width=14, height=12, dpi=300)
```

### 3. 漏斗圖 (Publication Bias)

```r
# 基本漏斗圖
funnel(res, studlab=TRUE)

# 加強型漏斗圖 (contour-enhanced)
library(metafor)
funnel(res,
       level = c(90, 95, 99),
       shade = c("white", "gray", "darkgray"),
       refline = 0)

# 匯出
ggsave("funnel_plot.png", width=8, height=8, dpi=300)
```

### 4. 使用專業主題

```r
library(ggsci)
library(viridis)

# 使用 Lancet 色彩方案
p <- ggplot(data, aes(x, y, color=group)) +
  geom_point() +
  scale_color_lancet() +
  theme_minimal(base_size=12)

# 使用色盲友善色彩 (必須!)
p <- ggplot(data, aes(x, y, fill=value)) +
  geom_tile() +
  scale_fill_viridis_c(option="viridis") +
  theme_minimal()

ggsave("figure.png", width=10, height=8, dpi=300)
```

### 5. 發表級表格 (使用 gtsummary)

**gtsummary** 是製作專業摘要表格的必備套件，在 meta-analysis 手稿中至關重要。

#### 安裝

```r
install.packages("gtsummary")

# 建議搭配套件
install.packages(c("gt", "flextable", "kableExtra"))
```

#### 基本表格建立

```r
library(gtsummary)
library(dplyr)

# 載入研究特性資料
data <- read.csv("05_extraction/extraction.csv")

# 表格 1: 研究特性
tbl_baseline <- data %>%
  select(age_mean, female_pct, stage_iii_pct, pdl1_positive_pct) %>%
  tbl_summary(
    label = list(
      age_mean ~ "年齡（歲）",
      female_pct ~ "女性（%）",
      stage_iii_pct ~ "第三期（%）",
      pdl1_positive_pct ~ "PD-L1 陽性（%）"
    ),
    statistic = list(
      all_continuous() ~ "{mean} ({sd})",
      all_categorical() ~ "{n} ({p}%)"
    ),
    digits = list(
      all_continuous() ~ 1,
      all_categorical() ~ 0
    )
  ) %>%
  bold_labels() %>%
  modify_caption("表格 1. 納入研究的基線特性")

# 匯出為 Word
tbl_baseline %>%
  as_flex_table() %>%
  flextable::save_as_docx(path = "07_manuscript/tables/table1.docx")

# 匯出為 HTML (用於 Quarto)
tbl_baseline %>%
  as_gt() %>%
  gt::gtsave("07_manuscript/tables/table1.html")
```

#### 比較表格（附 P 值）

```r
# 表格 2: ICI vs 對照組比較
tbl_comparison <- data %>%
  select(treatment_arm, age_mean, female_pct, response_rate) %>%
  tbl_summary(
    by = treatment_arm,  # 按治療分組
    label = list(
      age_mean ~ "年齡（歲）",
      female_pct ~ "女性（%）",
      response_rate ~ "反應率（%）"
    ),
    statistic = list(all_continuous() ~ "{mean} ({sd})")
  ) %>%
  add_p(
    test = list(
      all_continuous() ~ "t.test",
      all_categorical() ~ "chisq.test"
    )
  ) %>%
  add_overall() %>%  # 加入整體欄位
  add_n() %>%  # 加入樣本數
  bold_labels() %>%
  italicize_levels() %>%
  modify_spanning_header(c("stat_1", "stat_2") ~ "**治療組別**")

# 套用 JAMA 期刊風格
tbl_comparison %>%
  theme_gtsummary_journal(journal = "jama")
```

#### 迴歸表格

```r
# 單變量迴歸
tbl_uv <- data %>%
  select(outcome, age, sex, stage, pdl1_status) %>%
  tbl_uvregression(
    method = glm,
    y = outcome,
    method.args = list(family = binomial),
    exponentiate = TRUE,  # 顯示 OR 而非 log-OR
    label = list(
      age ~ "年齡（每年）",
      sex ~ "性別（女性 vs 男性）",
      stage ~ "分期",
      pdl1_status ~ "PD-L1 狀態"
    )
  ) %>%
  bold_labels() %>%
  bold_p(t = 0.05)

# 多變量迴歸
model_mv <- glm(outcome ~ age + sex + stage + pdl1_status,
                data = data, family = binomial)

tbl_mv <- tbl_regression(
  model_mv,
  exponentiate = TRUE,
  label = list(
    age ~ "年齡（每年）",
    sex ~ "性別（女性 vs 男性）",
    stage ~ "分期",
    pdl1_status ~ "PD-L1 狀態"
  )
) %>%
  add_global_p() %>%  # 加入整體 p 值
  bold_labels() %>%
  bold_p(t = 0.05)

# 合併單變量與多變量表格
tbl_merged <- tbl_merge(
  tbls = list(tbl_uv, tbl_mv),
  tab_spanner = c("**單變量**", "**多變量**")
)
```

#### 期刊特定格式

```r
# JAMA 風格
tbl %>% theme_gtsummary_journal(journal = "jama")

# Lancet 風格
tbl %>% theme_gtsummary_journal(journal = "lancet")

# NEJM 風格
tbl %>% theme_gtsummary_journal(journal = "nejm")
```

#### gtsummary 最佳實踐

**表格建立**:

```r
# ✅ 好：乾淨的變數選擇
data %>%
  select(age, sex, stage) %>%  # 只選分析變數
  tbl_summary()

# ❌ 壞：包含 ID 欄位
data %>%
  tbl_summary()  # 包含 patient_id, date_enrolled 等
```

**自訂統計量**:

```r
# ✅ 好：明確的統計量
tbl_summary(
  statistic = list(
    all_continuous() ~ "{median} ({p25}, {p75})",  # 中位數（IQR）
    all_categorical() ~ "{n} ({p}%)"
  )
)
```

**P 值**:

```r
# ✅ 好：適當的檢定選擇
add_p(
  test = list(
    all_continuous() ~ "wilcox.test",  # 非參數檢定
    all_categorical() ~ "fisher.test"  # 小樣本精確檢定
  )
)
```

**常見錯誤**:

| ❌ 不要這樣做              | ✅ 應該這樣做     | 原因       |
| -------------------------- | ----------------- | ---------- |
| 包含 ID/日期欄位           | 先篩選分析變數    | 表格更乾淨 |
| 使用預設欄位名稱           | 提供 `label` 清單 | 讀者易讀   |
| 依賴自動檢定               | 指定 `test` 參數  | 控制假設   |
| 忘記 `exponentiate = TRUE` | 迴歸模型必用      | 顯示 OR/HR |
| 忽略遺漏值處理             | 設定 `missing`    | 控制呈現   |

#### 快速參考：gtsummary

```r
# === 基本結構 ===
data %>%
  select(vars) %>%                    # 選擇變數
  tbl_summary(
    by = group_var,                   # 分層
    label = list(...),                # 變數標籤
    statistic = list(...)             # 統計量
  ) %>%
  add_p() %>%                         # P 值
  add_overall() %>%                   # 整體欄位
  bold_labels() %>%                   # 格式化
  theme_gtsummary_journal("jama")     # 期刊風格

# === 迴歸 ===
tbl_uvregression(method = glm, exponentiate = TRUE) # 單變量
tbl_regression(model, exponentiate = TRUE)          # 多變量

# === 匯出 ===
as_gt() %>% gt::gtsave("file.html")                # HTML
as_flex_table() %>% flextable::save_as_docx()      # Word
```

---

## 🎨 期刊特定要求

### Nature, Science, Cell

```r
# 使用 Arial/Helvetica 字型
library(ggplot2)

theme_nature <- theme_minimal(base_size=10) +
  theme(
    text = element_text(family="Arial"),
    axis.line = element_line(size=0.5),
    panel.grid.minor = element_blank()
  )

p <- ggplot(...) + theme_nature

# 匯出為期刊寬度 (單欄 89mm, 雙欄 183mm)
ggsave("figure.png",
       width=183, height=150, units="mm", dpi=300)
```

### Lancet (使用 ggsci 套件)

```r
library(ggsci)

p <- ggplot(data, aes(x, y, color=group)) +
  geom_point() +
  scale_color_lancet() +  # Lancet 官方色彩
  theme_minimal(base_size=10)

ggsave("figure.png", width=183, units="mm", dpi=300)
```

### JAMA

```r
# JAMA 要求
# - 300-600 DPI
# - TIFF 格式優先
# - Arial 字型 8-10pt

ggsave("figure.tiff",
       width=10, height=8, dpi=600,
       compression="lzw")
```

---

## ✅ 品質檢查清單

### 匯出前檢查

- [ ] 所有圖表使用 `dpi=300` 或更高
- [ ] 面板標籤 (A, B, C) 正確且清晰
- [ ] 字型大小在最終印刷尺寸下可讀 (≥8pt)
- [ ] 使用色盲友善色彩 (viridis/scico)
- [ ] 軸標籤、圖例完整
- [ ] 檔案大小合理 (<10 MB for PNG)

### R 腳本品質

- [ ] 所有套件明確載入 (`library()`)
- [ ] 可重現 (沒有硬編碼路徑)
- [ ] 註解清楚
- [ ] 使用 `here::here()` 或相對路徑
- [ ] 版本控制 (git commit R scripts)

---

## 🔧 疑難排解

### 問題 1: 套件找不到

```r
# 錯誤: package 'patchwork' not found

# 解決: 從 CRAN 安裝
install.packages("patchwork")

# 或檢查 CRAN mirror
options(repos = c(CRAN = "https://cloud.r-project.org/"))
install.packages("patchwork")
```

### 問題 2: 字型問題

```r
# 錯誤: font family not found

# 解決: 使用 cairo device
ggsave("figure.png", device="png", type="cairo")

# 或對於 PDF
cairo_pdf("figure.pdf", width=10, height=8)
# 你的圖表程式碼
dev.off()
```

### 問題 3: 文字太小

```r
# 問題: 匯出後文字無法閱讀

# 解決: 增加 base_size
p <- ggplot(data, aes(x, y)) +
  geom_point() +
  theme_minimal(base_size=14)  # 從預設 11 增加

ggsave("figure.png", width=10, height=8, dpi=300)
```

### 問題 4: 面板對齊問題

```r
# 使用 cowplot 的 align 參數
library(cowplot)

plot_grid(
  p1, p2, p3,
  labels = c("A", "B", "C"),
  align = "v",        # 垂直對齊
  axis = "l",         # 左軸對齊
  ncol = 1
)
```

---

## 📚 學習資源

### 線上書籍

1. **Doing Meta-Analysis in R** (Harrer et al.)
   - https://bookdown.org/MathiasHarrer/Doing_Meta_Analysis_in_R/
   - 使用 R 進行 meta-analysis 的完整指南

2. **R Graphics Cookbook** (Chang)
   - https://r-graphics.org/
   - ggplot2 發表級圖表範例

3. **Data Visualization with R** (Kabacoff)
   - https://rkabacoff.github.io/datavis/
   - 現代視覺化技術

### 套件文件

```r
# 檢視套件說明
help(package = "patchwork")

# 檢視函數說明
?ggsave

# 檢視 vignettes
vignette(package = "patchwork")
browseVignettes("patchwork")
```

### 線上資源

- **patchwork**: https://patchwork.data-imaginist.com/
- **cowplot**: https://wilkelab.org/cowplot/
- **ggplot2**: https://ggplot2.tidyverse.org/
- **metafor**: https://www.metafor-project.org/

---

## 🚀 下一步

### 現有專案遷移

如果你有現有的 Python 圖表組裝腳本：

1. **保留原始 R 繪圖腳本** (如 `01_forest_plot.R`)
2. **移除 Python 組裝步驟**
3. **在 R 腳本中直接使用 patchwork 組合**
4. **測試輸出品質** (檢查 DPI, 對齊, 標籤)
5. **更新文件** (記錄新工作流程)

### 新專案

1. **從 R 開始** - 不要產生中間 PNG 檔案
2. **在 R session 中組合** - 使用 patchwork/cowplot
3. **單次匯出** - 直接匯出最終圖表
4. **版本控制 R 腳本** - 而非 PNG 檔案

---

## 📝 Commit 資訊

本次更新包含以下 commits:

### meta-pipe 專案

1. **Switch figure generation from Python to R** (8125281)
   - 建立 R_FIGURE_GUIDE.md (450+ 行)
   - 更新 CLAUDE.md (Stage 06 強調 R)
   - 更新 MANUSCRIPT_ASSEMBLY.md (移除 Python)

2. **Add professional R theme packages to figure guide** (5cd84f2)
   - Linter 自動加入專業主題套件文件
   - viridis, scico, ggsci, ggthemr, hrbrthemes

### skills 倉庫

1. **Update scientific-figure-assembly skill to use R** (4a33027)
   - 改為 R-first 工作流程
   - Python 方法標記為 Legacy
   - 新增完整 R 範例

---

## 🎯 影響評估

### 正面影響

✅ **單一語言工作流程** - 全程在 R 中完成，減少上下文切換
✅ **更好整合** - 統計分析與視覺化無縫整合
✅ **發表品質** - R 套件預設即為發表品質
✅ **易於重現** - 單一 R 腳本即可重現所有圖表
✅ **更易維護** - 減少依賴 (不需 Python Pillow)
✅ **更好文件** - R 社群文件豐富 (CRAN, R-universe)

### 學習曲線

⚠️ **需學習 patchwork/cowplot** - 但語法簡單直觀
⚠️ **R 套件生態** - 需熟悉 CRAN, Bioconductor 等資源
✅ **有豐富範例** - R_FIGURE_GUIDE.md 提供完整範例

### 向後相容性

⚠️ **Python 腳本仍可用** - 標記為 Legacy，但仍可執行
⚠️ **現有圖表需重新產生** - 建議使用 R 重新產生以統一工作流程
✅ **漸進式遷移** - 可逐步將 Python 腳本轉換為 R

---

## 📧 支援

如有問題，請參考：

1. **R_FIGURE_GUIDE.md** - 完整工作流程與疑難排解
2. **MANUSCRIPT_ASSEMBLY.md** - 手稿組裝指南
3. **CLAUDE.md** - 主要代理指令
4. **R 套件文件** - 使用 `?function_name` 或 `help(package="package_name")`

---

**更新完成日期**: 2024-02-07
**下次審查**: 專案完成後進行技能泛化
