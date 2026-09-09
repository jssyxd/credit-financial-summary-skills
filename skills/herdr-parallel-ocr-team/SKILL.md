# Skill: herdr-parallel-ocr-team

在 herdr 终端多路复用器里，为「多份扫描财报/审计报告」各开一个 agent pane **并行 OCR + 提取 + 校验**，主 Agent 负责契约与终检，形成流水线协作。

## 触发场景
- 用户明确提到 herdr，且任务是把多份扫描件 PDF 并行读取/OCR/提取（如“合并/本部三年审计各 1 个 agent，一起读”）；
- 已有 extract-financial-statements 的 OCR 助手与 EXTRACTION_SPEC 契约。

## 前置（自检）
```bash
test "${HERDR_ENV:-}" = 1 || echo "不在 herdr 托管 pane 内，停止"
herdr --help            # 以实际安装为准
herdr agent             # 查看可用 kind(pi/omp/claude/...)
```
- 只有当 `HERDR_ENV=1` 且存在 herdr 二进制时才继续；否则不要遥控 herdr 会话。
- pane 布局以 `herdr pane list/layout` 返回为准；拆分/启动命令都读返回的 id，不要猜。

## 流程

### 1. 主 Agent 先做“契约与去重”
- 把所有源 PDF 用 `anydoc` 快速试一遍：**文本层的自己解析，别占 agent pane**（扫描件才派 pane）；
- 写共享提取规范 `_extract/EXTRACTION_SPEC.md`（含：口径=母公司/合并、期末/期初取哪栏、科目key保留原文、单位、恒等式清单、输出 JSON schema、notes 约定、只回摘要）；
- 把 OCR 助手 `ocr_page.py / ocr_crop.py` 放进 `_extract/`。

### 2. 建网格（示例命令，按布局调整）
```bash
herdr pane split --current --direction right  --cwd "$PWD" --no-focus   # 得到 p3
herdr pane split --pane wM:p3 --direction down --cwd "$PWD" --no-focus  # 得到 p5
herdr pane split --current --direction down   --cwd "$PWD" --no-focus   # 得到 p4
# 目标: 主 pane(p1) + 每份扫描件一个 shell pane
```

### 3. 每 pane 启动 agent 并派活
```bash
herdr agent start audit2023 --kind omp --pane wM:p3 --timeout 90000   # 等到 idle
herdr agent prompt audit2023 "读取并执行 D:/.../_extract/EXTRACTION_SPEC.md ；你的角色=提取 <文件.pdf>(纯扫描,33页)；先OCR定位三张母公司单体报表页，完整提取(期末=YYYY-12-31/期初)，全部行项目；按规范校验恒等式，失败必须放大裁剪重OCR；输出JSON到 _extract/audit2023.json；完成后只回复: JSON路径、三表页码、恒等式是否全过、notes摘要。" 
# 注意: pane agent 是白板, prompt 必须自包含(给文件路径与输出路径)
```
- 提示中命令不加 `--wait` 亦可（提交即返回）；需要阻塞时用 `--wait`；
- 轮询：`herdr agent list` 看状态；只读输出用 `herdr agent read <name> --source recent-unwrapped --lines N`。

### 4. 收尾与兜底
- 主 Agent 汇总各 JSON → 跑 `validate_extraction.py` 做**跨年连续性**（独立 OCR 通道互证）；
- agent 消失/卡死/输出空壳：`herdr pane split` 新建 pane → `herdr agent start <新名>` → 重派任务（不要无限等）；
- 每 pane 只承担“读→OCR→提取→自校验→写 JSON→回摘要”，**跨文件交叉校验与终检在主 Agent**；
- 完成后可把 pane/agent 留作 idle 或请用户关闭（不要动用户自己开的 pane/工作区）。

## 协作约定
- 产物统一进 `_extract/`：`auditYYYY.json`（三表）、`notesYYYY.json`（附注）、`ocr*/`（中间 OCR，可清理）；
- 共享规范是唯一契约，改契约=改文件+知会所有 pane；
- 文本层文件与扫描件并行：文本层主 Agent 自取，不浪费 pane。

## 已知局限
- herdr pane 内 TUI agent 需要合理 pane 尺寸（窄 pane 可改用 `agent prompt`/`agent read` 驱动）；
- 大规模并行 OCR 吃 CPU（rapidocr onnxruntime 单进程），pane 数与核数平衡；
- 只适合 herdr 环境；普通环境请改用任务并行 + 同一套脚本与契约。
