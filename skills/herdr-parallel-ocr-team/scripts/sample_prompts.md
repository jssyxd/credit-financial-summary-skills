# 每 pane 的任务 prompt 模板

> 共同规则：白板 agent 无上下文 → prompt 必须自包含（路径全用绝对路径）；只回摘要不贴全文；先读共享契约再干活。

## 模板 A：扫描审计报告 → auditYYYY.json
```
读取并执行 {_extract}/EXTRACTION_SPEC.md。
你的角色：提取 {绝对路径}/{文件}.pdf（纯扫描，33页）。
步骤：
1) 用 python {_extract}/ocr_page.py <pdf> --pages 1-33 --out {_extract}/ocrYYYY 全页OCR（约3分钟）；
2) 根据每页 p0NN.json 首行文本定位 资产负债表/利润表/现金流量表 页（母公司/单体口径，勿取合并列）；
3) 重建三表全部行项目：期末/期初（BS），本期/上期（IS、CF），金额单位按表头(通常元)；
4) 按规范跑恒等式（资产=负债+权益等），不通过必须用 ocr_crop.py 放大裁剪重OCR修正，禁止凑数；
5) 输出 JSON 到 {_extract}/auditYYYY.json（schema 见规范）。
完成后只回复：JSON路径、三表页码、恒等式是否全过、notes摘要、最有把握/最没把握的数字各一。
```

## 模板 B：文本层报表（坐标重建）
```
读取并执行 {_extract}/EXTRACTION_SPEC.md。
你的角色：提取 {绝对路径}/{文件}.pdf（文本层，3页，双栏行次制简式报表）。
用 python {_extract}/pdf_rowdump.py <pdf> 逐行判读；资产侧/负债侧按表头x分界，
行次token(1..61)定行，金额列按x升序=期末列→年初列；空白/'-'→0（用合计行验证）。
输出 JSON 到 {_extract}/audit2606.json；内部恒等式必须全部闭合。
```

## 模板 C：附注关键信息（账龄/折旧/明细）→ notesYYYY.json
```
新任务(附注提取)：{绝对路径}/{文件}.pdf 报表页之后为附注。
用 ocr_page.py 逐页定位附注标题(如“四、会计项目注释”)，表格区用 ocr_crop.py 放大精读。
逐项确认并记录：①现金流量表补充资料/折旧摊销/利息拆分(未见则注明) ②货币资金期末期初及受限披露
③应收账款账龄/坏账/前五 ④其他应收款账龄/坏账/性质top ⑤存货分类 ⑥固定资产原值/累计折旧/本期计提
⑦长期股权投资被投资单位明细 ⑧短期借款 ⑨应付账款/预收(合同负债)/其他应付款(含其中应付利息) ⑩营业外收支/公允价值构成。
附注若为“各科目仅期末/期初单行”的极简版，明确写“未见”，不要留空。
输出 {_extract}/notesYYYY.json  {key:{金额,页码,原文}}，再回复一段中文摘要。
```

## 收尾话术
```
汇总校验：python {_extract}/validate_extraction.py --json audit2023.json audit2024.json audit2025.json audit2606.json
差异必须逐条可解释（命名变体/口径拆分），否则回查对应年份。
```
