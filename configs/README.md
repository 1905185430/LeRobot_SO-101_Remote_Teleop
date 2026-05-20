# 配置文件分类

本目录按运行类型维护 YAML 配置。启动命令应使用对应子目录下的路径。

## Debug / Mock

| 文件 | 用途 | 是否需要硬件 |
| --- | --- | --- |
| `debug/debug_mock_robot.yaml` | 本地 TCP mock server/client roundtrip，验证协议、run directory、metrics。 | 否 |

## Local Inference

| 文件 | 用途 | 是否需要硬件 |
| --- | --- | --- |
| `local_inference/so101_smolvla.yaml` | SO-101 + SmolVLA 本地推理配置，用于后续本地 baseline。 | 是 |

## Remote Inference

| 文件 | 用途 | 是否需要硬件 |
| --- | --- | --- |
| `remote_inference/so101_smolvla.yaml` | SO-101 机器人端采集 observation，GPU/server 端运行 SmolVLA 推理。 | 是 |

## TCP Teleoperation

| 文件 | 用途 | 是否需要硬件 |
| --- | --- | --- |
| `teleop/remote_so101_tcp.yaml` | SO-101 leader/follower TCP 遥操作配置。 | 是 |
| `teleop/remote_starai_tcp.yaml` | StarAI leader/follower TCP 遥操作远程配置模板。 | 是 |
| `teleop/local_starai_tcp.yaml` | StarAI leader/follower 在同一台机器上的 TCP 遥操作配置。当前已通过 dry-run、配置解析和自动化测试。 | 是 |
| `teleop/local_so101_tcp.yaml` | SO-101 leader/follower 在同一台机器上的 TCP 遥操作配置。 | 是 |

## Dataset Replay

| 文件 | 用途 | 是否需要硬件 |
| --- | --- | --- |
| `replay/local_so101_tcp_dataset.yaml` | 从本地 LeRobot SO-101 数据集读取 selected episode action，并通过 `127.0.0.1` TCP follower 复现。 | 是 |

`replay/local_so101_tcp_dataset.yaml` 使用简单 scalar `dataset:` 字段：

```yaml
dataset:
  path: /tmp/lerobot/so101_dataset
  episode: 0
  start_frame: 0
  end_frame: -1
  timing: fixed_hz
  replay_frequency: 50
```

运行前把 `dataset.path` 改成真实本地 LeRobot 数据集目录。数据集采集和 HuggingFace 下载不由该配置自动完成。

## 当前推荐 StarAI 本地遥操作配置

本地 StarAI TCP 遥操作使用：

```bash
python3 scripts/run_server.py --config configs/teleop/local_starai_tcp.yaml
python3 scripts/run_client.py --config configs/teleop/local_starai_tcp.yaml
```

该配置使用项目内标定目录：

```text
calibrations/robots/starai_viola/my_awesome_staraiviola_arm.json
calibrations/teleoperators/starai_violin/my_awesome_staraiviolin_arm.json
```

并启用：

```yaml
robot:
  skip_initial_position: true

logging:
  print_leader_actions: true
  print_action_interval: 10
```

含义：

- `skip_initial_position: true`：server 启动时跳过 StarAI follower 官方硬编码初始姿态移动。
- `print_leader_actions: true`：client 终端定期打印 leader 发出的关节角度。
- `print_action_interval: 10`：每 10 帧打印一次。
