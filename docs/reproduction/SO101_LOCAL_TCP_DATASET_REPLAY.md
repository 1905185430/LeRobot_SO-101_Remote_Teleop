# SO-101 本地 TCP 数据集复现说明

本文档记录如何在同一台机器上，把已有 LeRobot SO-101 数据集的一段 episode action 通过本项目 TCP follower 路径复现到 SO-101 follower。

## 目标边界

本流程验证的是：

- 数据集 action 能从 YAML 指定的本地路径读取；
- replay client 不读取物理 leader arm；
- replay client 连接本机 `127.0.0.1` TCP follower；
- follower 继续使用现有 SO-101 TCP 安全检查；
- run artifacts 记录实际复现的数据集、episode、frame 范围、timing、endpoint 和安全配置。

本流程不负责：

- 采集 LeRobot 数据集；
- 自动从 HuggingFace 下载数据集；
- 两台机器远程 TCP 数据集复现；
- VLA 训练、评测或策略推理；
- 绕过安全限制强行复现不安全轨迹。

数据集可以由你自己用 LeRobot 本地命令采集，也可以提前从 HuggingFace 下载到本地。Phase 7 只消费一个已经存在的本地数据集路径。

## 推荐预检：官方 LeRobot Replay

在测试本项目 TCP replay 之前，建议先用 LeRobot 官方 replay 验证 dataset、episode、follower、标定和本地直连复现本身没有问题。

不同 LeRobot 版本的命令入口可能显示为：

```bash
python -m lerobot.replay ...
```

或：

```bash
lerobot-replay ...
```

如果官方 replay 都无法让 follower 正常复现，请先修复数据集、标定、串口或 LeRobot 环境，再测试本项目的 TCP replay。本文档里的 TCP replay 不是替代官方 replay，而是在官方 replay 通过后，验证“数据集 action 经过本项目 TCP 传输后仍可复现”。

## 使用的 YAML

```text
configs/replay/local_so101_tcp_dataset.yaml
```

关键字段：

```yaml
dataset:
  path: /tmp/lerobot/so101_dataset
  episode: 0
  start_frame: 0
  end_frame: -1
  timing: fixed_hz
  replay_frequency: 50
```

含义：

- `dataset.path`：本地 LeRobot 数据集目录。运行前必须改成你机器上的真实路径。
- `dataset.episode`：要复现的单个 episode 编号。
- `dataset.start_frame`：从 episode 的第几帧 action 开始。
- `dataset.end_frame`：结束帧；`-1` 表示一直到 episode 末尾。
- `dataset.timing: fixed_hz`：按固定频率发送 action，当前推荐路径。
- `dataset.replay_frequency`：`fixed_hz` 模式下的发送频率。

也支持：

```yaml
dataset:
  timing: source_timestamps
```

但只有数据集每帧提供清晰 timestamp 时才可用。如果缺少 timestamp，runtime 会直接失败，不会静默回退到 `fixed_hz`。

## 本地 TCP 配置

该配置使用本机 TCP：

```yaml
network:
  protocol: tcp
  server_host: 127.0.0.1
  server_port: 9012
```

Follower 仍然是 SO-101 follower：

```yaml
robot:
  type: so101_follower
  port: /dev/ttyACM1
  id: follower_arm
  calibration_dir: calibrations/robots/so_follower
```

`teleop` section 保留是为了复用现有 TCP teleoperation config 约束和 follower 启动路径；dataset replay client 不会读取物理 leader：

```yaml
teleop:
  enabled: true
  type: so101_leader
  port: /dev/ttyACM0
  id: dataset_replay
```

同一台机器上串口顺序可能变化，运行前检查：

```bash
ls -l /dev/ttyACM*
```

## 安全行为

当前配置保留 SO-101 TCP 安全检查：

```yaml
safety:
  max_action_delta: 2.0
  max_first_action_delta: 55.0
  action_min: -180
  action_max: 180
  require_action_keys_match: true
```

Replay 行为：

- replay client 发送前校验 action 数值范围；
- follower 校验 action keys；
- follower 校验第一帧和当前 follower 姿态的差值；
- follower 继续执行每帧 `max_action_delta` 限幅；
- 任何 dataset read、action range、TCP、ACK 或 follower safety 失败都会中止当前 replay。

不要为了让轨迹“跑完”而关闭这些安全限制。若 `max_action_delta` 触发，实际 follower 轨迹会被限幅，不能再视为完全忠实复现数据集轨迹。

## Dry-run 验证

先检查 YAML 能正常解析：

```bash
python3 scripts/run_dataset_replay_client.py --config configs/replay/local_so101_tcp_dataset.yaml --dry-run
python3 scripts/run_teleop_follower.py --config configs/replay/local_so101_tcp_dataset.yaml --dry-run
```

Dry-run 不会导入 LeRobot，不会检查真实 `dataset.path` 是否存在，也不会连接 TCP 或机械臂。

## 启动顺序

所有命令从项目根目录运行：

```bash
cd ~/Documents/VLA+无线通信/lerobot-remote-vla-teleop
conda activate lerobot
```

### 1. 启动 follower/server

第一个终端运行：

```bash
python3 scripts/run_teleop_follower.py --config configs/replay/local_so101_tcp_dataset.yaml
```

期望看到：

```text
Run directory: runs/so101_local_tcp_dataset_replay/<timestamp>-tcp-teleop-follower-xxxx/
TCP teleop follower listening on 127.0.0.1:9012
```

### 2. 启动 dataset replay client

第二个终端运行：

```bash
python3 scripts/run_dataset_replay_client.py --config configs/replay/local_so101_tcp_dataset.yaml
```

期望看到：

```text
Run directory: runs/so101_local_tcp_dataset_replay/<timestamp>-dataset-replay-client-xxxx/
Dataset replay client connecting to 127.0.0.1:9012
Dataset replay: path=... episode=0 frames=... timing=fixed_hz
```

## 停止顺序

建议顺序：

1. 先让 dataset replay client 自然结束，或在 client 终端按 `Ctrl+C`。
2. 确认 follower 没有继续运动。
3. 再在 follower/server 终端按 `Ctrl+C`。
4. 停止后让机械臂保持在安全姿态，必要时断电或释放扭矩。

## Run Artifacts

Replay client 运行目录：

```text
runs/so101_local_tcp_dataset_replay/<timestamp>-dataset-replay-client-xxxx/
```

重点检查：

- `metadata.json`：包含 dataset path、episode、frame range、frame count、timing、endpoint 和 safety；
- `events.jsonl`：包含 replay start/complete 或 exception；
- `metrics.jsonl` / `metrics.csv`：包含 TCP 往返相关指标；
- `summary.md`：包含 metadata、metric statistics 和 event counts；
- `config.yaml`：本次运行使用的配置副本。

Follower 运行目录：

```text
runs/so101_local_tcp_dataset_replay/<timestamp>-tcp-teleop-follower-xxxx/
```

重点检查 follower 的 `events.jsonl`。如果出现 `tcp teleop action delta limited`，说明 follower 实际执行轨迹被每帧限幅修正过。

## 自动化测试

核心测试：

```bash
python3 -m unittest tests.test_dataset_replay tests.test_tcp_teleop -v
```

完整测试：

```bash
python3 -m unittest discover -s tests -v
```

## 常见问题

### dataset.path 不存在

现象：

```text
dataset.path does not exist
```

处理：

- 确认数据集已经采集或下载到本机；
- 修改 `configs/replay/local_so101_tcp_dataset.yaml` 的 `dataset.path`；
- 再运行 dataset replay client。

### source_timestamps 失败

现象：

```text
source_timestamps requires timestamp metadata
```

处理：

- 改回 `dataset.timing: fixed_hz`；
- 或确认你的 LeRobot 数据集每帧提供 timestamp 字段。

### 第一帧被拒绝

现象：

```text
First ACTION is too far from follower startup position
```

处理：

- 停止 replay client 和 follower；
- 手动把 follower 摆到数据集第一帧附近的安全姿态；
- 确认使用正确的 SO-101 follower 标定；
- 不要直接关闭 `max_first_action_delta`。

### action key 不匹配

现象：

```text
ACTION keys do not match follower joints
```

处理：

- 确认数据集是 SO-101-compatible action；
- 确认 action 包含 6 个 SO-101 关节；
- 确认 follower 标定和 `robot.id` 正确。
