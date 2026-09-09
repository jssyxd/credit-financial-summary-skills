# herdr 网格与 agent 启动速查（真实命令示例）

以下命令来自实战（windows + pi-node 环境，herdr 会话 wM）；**先跑 `herdr --help` / `herdr pane` 以本机语法为准**，所有 id 从命令返回 JSON 读取。

## 环境自检
```bash
test "${HERDR_ENV:-}" = 1 && echo "ok in herdr"
herdr pane list --workspace wM        # -> pane_id / agent_status / tab_id
herdr pane layout --pane wM:p1        # 当前 pane 矩形, 决定往右/往下拆
```

## 搭 2×2 网格（主 pane + 3 个 agent pane）
```bash
herdr pane split --current --direction right --cwd "D:/path/to/project" --no-focus   # -> wM:p3 (右)
herdr pane split --current --direction down  --cwd "D:/path/to/project" --no-focus   # -> wM:p4 (左下)
herdr pane split --pane wM:p3 --direction down --cwd "D:/path/to/project" --no-focus # -> wM:p5 (右下)
```
说明：`--current`=调用者所在 pane；`--no-focus` 不抢用户焦点；分割后各 pane 是空 shell，cwd 已设好。

## 启动 agent（pane 必须停在 shell 提示符）
```bash
herdr agent start audit2023 --kind omp --pane wM:p3 --timeout 90000
# 返回 agent_status: idle / interactive_ready: true 即可派活
```

## 派活（白板 agent，prompt 自包含）
```bash
herdr agent prompt audit2023 "读取并执行 <契约文件绝对路径>；你的角色=提取 <PDF绝对路径>；... 输出 JSON 到 <绝对路径>；完成后只回复摘要。" 
# 需要等结果: 追加 --wait --timeout 120000
```

## 轮询/读取
```bash
herdr agent list          # 各 agent 状态
herdr agent read audit2023 --source recent-unwrapped --lines 12   # 看最近输出
```

## 兜底（agent 丢失/空返/卡死）
```bash
herdr pane split --current --direction right --cwd "$PWD" --no-focus   # 新建 pane
herdr agent start notes2025 --kind omp --pane <新pane_id> --timeout 90000
herdr agent prompt notes2025 "重派任务: ..."
```
注意：不要动用户自己开的 pane/会话（实战中 wM:t2 的 pi orchestrator 属用户，未触碰）。

## 常见问题
- `agent target not found`：该 pane 的 agent 已被释放/关闭 → 按“兜底”重建；
- `agent_prompt_stalled`：prompt 后 5s 内无状态变化 → 先用 `agent read` 看是否在跑长 OCR，必要时加 `--timeout` 重发；
- pane 太小影响 TUI：用 `agent prompt`/`agent read` 文本驱动，或 `herdr pane resize --direction up --amount 0.3` 调大。
