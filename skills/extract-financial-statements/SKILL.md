# Skill: extract-financial-statements

把审计报告/财务报表 PDF（文本层或纯扫描）中的**资产负债表、利润表、现金流量表**全部行项目稳定提取为结构化 JSON（含 期末/期初 或 本期/上期 双栏），并用报表恒等式 + 跨年连续性自证，产出可用于授信简表与分析的证据底座。

## 触发场景
- 用户给出一年或多年审计报告 PDF（.pdf），要求"提取三张报表""做三年一期数据""出一份可供简表/分析使用的财务数据 JSON"；
- 源 PDF 可能是**扫描件**（无文字层）——必须 OCR；
- 报表体例可能是**新准则审计报表**或**银行简式会企表（双栏行次制）**。

## 前置
- Python 3.10+，`pip install pymupdf rapidocr-onnxruntime`；可选 `anydoc`。
- 建立项目目录与 `_extract/`（见仓库 docs/WORKFLOW.md）。

## 步骤

### 1. 分类输入
```bash
anydoc <file>.pdf -o _md/<file>.md     # 文本层→成功；扫描→报 "needs OCR"
python -c "import pymupdf; d=pymupdf.open('<file>.pdf'); print(d.page_count, d[0].get_text()[:200])"
```
- 有文本：进入坐标解析（步骤 3a）。
- 无文本：进入 OCR 管线（步骤 3b）。

### 2. 定位报表页
先 OCR/粗扫少量页（封面、目录、正文头部）确定：报表页页码、是否有“合并/母公司”两套、报表日期（期末/期初）、计量单位（通常“单位:元”）。

### 3a. 文本层 PDF 坐标重建（双栏行次制必用）
```bash
python scripts/pdf_rowdump.py <file>.pdf          # 逐行打印 y + 按 x 排序的 token
```
判读要点：
- 资产侧 token `x<270`，负债权益侧 `x≥270`（以表头实测为准）；
- 每行 token 顺序 = 科目名 | 行次(1..61 小整数) | 期末余额 | 年初余额；
- **金额列按 x 升序取 = 期末列→年初列**（不能按数值排序）；
- 单值重复两栏（如“使用权资产”只有一值）→ 两栏同值；
- 空白/“-”单元格 → 0（用合计行恒等式验证）。

### 3b. 扫描 PDF OCR 管线
```bash
python scripts/ocr_page.py <file>.pdf --pages 1-33 --out ocr_out    # 每页 p001.png + p001.json(lines含box)
# 可疑单元格放大重OCR（水印遮挡/位数可疑）
python scripts/ocr_crop.py <file>.pdf --page 12 --crop x0,y0,x1,y1 --out cell.png --dpi 500
```
重建规则：
- 按 box 的 y 中心聚类成行带、按 x 聚类成列带；科目名在左、数值右对齐；
- 折行科目与数字行归属：以数字行为准向上找最近科目；
- 表格线噪点行忽略；
- 千分位、小数点、负号（`-`/括号）最易错，逐位核对大额位数。

### 4. 科目与取值
- key = 报表原科目名（保留“一、/减：/加：”前缀亦可，匹配端会剥离）；值 = 元（负数允许，`-`/空 → 0 并在 notes 注明）。
- 记录 `unit`（元/万元），`period_end`（如 2023-12-31），`statement_pages`。
- 若同一报告含合并与母公司两套：**只取任务口径那一套**（授信场景通常合并口径 vs 本部=母公司单体口径各做一份），并核对表头后再取数。

### 5. 校验（交付前提，全部必须通过）
- BS/IS/CF 恒等式（见仓库 README 6.1），允许 ≤0.5 元差；
- 跨年连续性：本年度期末 = 下年度期初（逐年两两比对）；
- 差异逐条归因（命名变体、口径拆分如“应付利息并入其他应付款”），禁止凑数。

### 6. 输出 JSON
```json
{
  "source_file": "上海格派单体审计报告2023.pdf",
  "entity_scope": "母公司单体口径(本部)",
  "period_end": "2023-12-31",
  "unit": "元",
  "statement_pages": {"bs": [6], "is": [7], "cf": [8]},
  "bs": {"current": {"货币资金": 197827226.42, "...": 0}, "opening": {...}},
  "is": {"current": {...}, "prior": {...}},
  "cf": {"current": {...}, "prior": {...}},
  "notes": {"resolved_issues": [], "unresolved": []}
}
```

## 校验器
```bash
python scripts/validate_extraction.py --json audit2023.json audit2024.json audit2025.json audit2606.json
# 输出：各单位/期间、BS配平、连续性差异清单（含单边差异与差值）
```

## 已知局限
- 附注极简版（各科目仅期末/期初单行）无法提供折旧拆分、账龄分段、坏账、前五名等——需要这些请另 OCR 附注页并记入 notes（参考仓库 write-credit-financial-analysis 的反幻觉原则）。
- 扫描件 OCR 存在残差风险；以三重自证 + 放大重 OCR 兜底，仍残留项必须留在 notes.unresolved。
