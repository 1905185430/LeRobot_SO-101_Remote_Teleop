# SO-101 本地 TCP 数据集复现真机预验证

本文档用于真机预验证 `configs/replay/local_so101_tcp_dataset.yaml` 和 `scripts/run_dataset_replay_client.py`。验证通过后，再把结论整理归档到 `docs/reproduction/`。

当前文档不是“已成功复现”记录。它是实验前和实验中的检查表。

## 验证目标

证明在同一台机器上：

- 已有 LeRobot SO-101 数据集可以从 YAML 指定路径读取；
- 本项目 dataset replay client 不依赖物理 leader arm；
- dataset action 可以通过 `127.0.0.1` TCP 发送到 SO-101 follower；
- follower 保留 action key、第一帧姿态差、每帧 delta、action range 等安全检查；
- replay client 和 follower 都生成可追溯 run artifacts；
- 小帧 smoke test 和目标 episode replay 都没有出现不可接受的安全或复现问题。

## 不在本次预验证内

- 数据集采集流程本身。
- 自动下载 HuggingFace 数据集。
- 两台机器远程 TCP 数据集复现。
- VLA 推理、训练或策略评测。
- 为了让轨迹跑完而关闭安全检查。

## 验证记录表

运行前先填写：

| 项目 | 记录 |
| --- | --- |
| 日期 |  |
| 操作者 |  |
| Git commit | `git rev-parse --short HEAD` |
| Python/conda 环境 |  |
| LeRobot 版本或来源 |  |
| 数据集路径 |  |
| 数据集来源 | 本地采集 / HuggingFace 下载 / 其他 |
| Episode |  |
| 起止 frame |  |
| Follower 串口 |  |
| Follower 标定 |  |
| TCP endpoint | `127.0.0.1:9012` |
| 预期 replay frequency |  |

## 0. 真机安全准备

开始前确认：

- SO-101 follower 周围没有人手、线缆、杂物或易碰撞物体。
- 机械臂有清晰急停/断电方式。
- follower 上电后不会因为初始姿态直接撞限位或桌面。
- 数据集第一帧附近的姿态是安全姿态。
- 不修改或关闭这些 safety 字段：

```yaml
safety:
  max_action_delta: 2.0
  max_first_action_delta: 55.0
  action_min: -180
  action_max: 180
  require_action_keys_match: true
```

如果第一帧被拒绝，优先移动 follower 到接近数据集第一帧的安全姿态，而不是放宽 `max_first_action_delta`。

## 1. 环境和串口检查

从项目根目录执行：

```bash
cd ~/Documents/VLA+无线通信/lerobot-remote-vla-teleop
conda activate lerobot
git status --short --branch
git rev-parse --short HEAD
python3 -c "import lerobot; print('lerobot import ok')"
ls -l /dev/ttyACM*
```

通过标准：

- 当前分支和 commit 已记录；
- LeRobot 可以 import；
- `configs/replay/local_so101_tcp_dataset.yaml` 中的 `robot.port` 指向真实 follower；
- 没有未理解的工作区改动。

## 2. 修改 replay YAML

打开：

```text
configs/replay/local_so101_tcp_dataset.yaml
```

至少确认：

```yaml
dataset:
  path: /path/to/local/lerobot/dataset
  episode: 0
  start_frame: 0
  end_frame: -1
  timing: fixed_hz
  replay_frequency: 50

network:
  server_host: 127.0.0.1
  server_port: 9012

robot:
  type: so101_follower
  port: /dev/ttyACM1
  id: follower_arm
  calibration_dir: calibrations/robots/so_follower
```

建议先做小帧 smoke test，把 `end_frame` 临时设为 5 到 10 帧之间，并把 `replay_frequency` 设为较低值，例如 `5` 或 `10`。小帧通过后，再改回目标 episode/frame 范围。

## 3. 自动化和 dry-run 预检

运行：

```bash
python3 scripts/run_dataset_replay_client.py --config configs/replay/local_so101_tcp_dataset.yaml --dry-run
python3 scripts/run_teleop_follower.py --config configs/replay/local_so101_tcp_dataset.yaml --dry-run
python3 -m unittest tests.test_dataset_replay tests.test_tcp_teleop -v
```

通过标准：

- 两个 dry-run 都退出 0；
- 输出中的 `dataset.path`、`episode`、`network.endpoint` 和预期一致；
- 自动化测试通过。

## 4. 官方 LeRobot replay 预检

先用 LeRobot 官方 replay 直接验证数据集和 follower：

```bash
python -m lerobot.replay ...
```

或你的 LeRobot 版本使用：

```bash
lerobot-replay ...
```

通过标准：

- 官方 replay 能读取同一个 dataset 和 episode；
- follower 能安全完成小帧或目标片段；
- 没有标定、串口、action shape、episode index、权限等错误。

如果官方 replay 失败，停止本项目 TCP replay 预验证，先修复 LeRobot/dataset/follower 问题。

## 5. 本项目 TCP 小帧 Smoke Test

保持 `dataset.end_frame` 为小帧范围，例如 `5` 或 `10`，`dataset.replay_frequency` 使用低频。

终端 A 启动 follower：

```bash
python3 scripts/run_teleop_follower.py --config configs/replay/local_so101_tcp_dataset.yaml
```

看到类似输出后继续：

```text
TCP teleop follower listening on 127.0.0.1:9012
```

终端 B 启动 replay client：

```bash
python3 scripts/run_dataset_replay_client.py --config configs/replay/local_so101_tcp_dataset.yaml
```

通过标准：

- replay client 自然结束，退出码为 0；
- follower 没有碰撞、剧烈抖动、持续运动或异常发热；
- replay client 输出 frame count 和小帧范围一致；
- follower 端没有第一帧安全拒绝；
- run artifacts 写入成功。

失败即停止，不进入完整 episode。

## 6. 目标 Episode Replay

小帧 smoke test 通过后，恢复目标配置：

```yaml
dataset:
  start_frame: <目标起始帧>
  end_frame: <目标结束帧，或 -1>
  replay_frequency: <目标频率>
```

重复第 5 步启动 follower 和 replay client。

通过标准：

- replay client 自然结束；
- follower 全程运动安全；
- 没有不可接受的 `exception`；
- 没有 TCP 断连、ACK mismatch、dataset read failure；
- 如果 `tcp teleop action delta limited` 出现，需要记录为“轨迹被限幅修正”，不能归档为完全忠实复现；
- 实际动作和官方 LeRobot replay 的运动趋势一致。

## 7. Run Artifacts 检查

记录两个运行目录：

```text
runs/so101_local_tcp_dataset_replay/<timestamp>-dataset-replay-client-xxxx/
runs/so101_local_tcp_dataset_replay/<timestamp>-tcp-teleop-follower-xxxx/
```

Replay client 目录必须包含：

- `metadata.json`
- `events.jsonl`
- `metrics.jsonl`
- `metrics.csv`
- `summary.md`
- `config.yaml`

重点检查：

```bash
cat runs/so101_local_tcp_dataset_replay/<client-run>/metadata.json
cat runs/so101_local_tcp_dataset_replay/<client-run>/events.jsonl
cat runs/so101_local_tcp_dataset_replay/<client-run>/summary.md
cat runs/so101_local_tcp_dataset_replay/<follower-run>/events.jsonl
```

通过标准：

- `metadata.json` 中 dataset path、episode、start/end frame、frame count、timing、endpoint 和 safety 与本次记录一致；
- `events.jsonl` 中有 replay start/complete；
- 没有未解释的 error 级别事件；
- follower 端没有安全拒绝或异常限幅；如果有限幅，要在结论中降级记录。

## 8. 结论判定

| 判定 | 条件 |
| --- | --- |
| PASS | 官方 replay 通过；TCP smoke 通过；目标 episode 通过；artifacts 完整；无未解释安全异常。 |
| PARTIAL | 小帧通过但完整 episode 未通过；或出现 delta limited；或 artifacts 不完整但运动链路可证明。 |
| FAIL | 官方 replay 失败；TCP replay 无法读取数据集；follower 安全拒绝；TCP/ACK 失败；出现不安全运动。 |

填写：

```text
结论：PASS / PARTIAL / FAIL
原因：
Replay client run dir：
Follower run dir：
是否可归档到 reproduction：
后续修复项：
```

## 9. 归档到 reproduction 的条件

只有满足 PASS 时，才把结果整理进 `docs/reproduction/`。

归档文档应包含：

- 数据集来源和路径描述，但不要写入私人 token 或敏感路径；
- 真实使用的 YAML 关键字段；
- follower 串口和标定；
- 官方 LeRobot replay 预检结果；
- 本项目 TCP replay 命令；
- run artifacts 路径；
- 通过/失败前解决的问题；
- 是否出现 `delta limited`；
- 仍然未验证的边界，例如两机远程 TCP replay。

建议归档目标：

```text
docs/reproduction/SO101_LOCAL_TCP_DATASET_REPLAY.md
```
