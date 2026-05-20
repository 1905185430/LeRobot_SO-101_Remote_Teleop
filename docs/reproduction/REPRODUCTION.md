# 复现索引

所有命令默认在项目根目录执行：

```bash
cd ~/Documents/VLA+无线通信/lerobot-remote-vla-teleop
conda activate lerobot
```

## 已记录的硬件复现

| 场景 | 文档 | 配置 |
| --- | --- | --- |
| StarAI 本地 TCP 遥操作 | [STARAI_LOCAL_TCP_TELEOP.md](STARAI_LOCAL_TCP_TELEOP.md) | `configs/teleop/local_starai_tcp.yaml` |
| SO-101 本地 TCP 遥操作 | [SO101_LOCAL_TCP_TELEOP.md](SO101_LOCAL_TCP_TELEOP.md) | `configs/teleop/local_so101_tcp.yaml` |
| SO-101 本地 TCP 数据集复现 | [SO101_LOCAL_TCP_DATASET_REPLAY.md](SO101_LOCAL_TCP_DATASET_REPLAY.md) | `configs/replay/local_so101_tcp_dataset.yaml` |
| SO-101 无线 TCP 遥操作 | [SO101_WIRELESS_TCP_TELEOP.md](SO101_WIRELESS_TCP_TELEOP.md) | `configs/teleop/remote_so101_tcp.yaml` |

## 快速 Dry-Run

远程推理：

```bash
python3 scripts/run_server.py --config configs/remote_inference/so101_smolvla.yaml --dry-run
python3 scripts/run_client.py --config configs/remote_inference/so101_smolvla.yaml --dry-run
```

StarAI 本地 TCP 遥操作：

```bash
python3 scripts/run_teleop_follower.py --config configs/teleop/local_starai_tcp.yaml --dry-run
python3 scripts/run_teleop_leader.py --config configs/teleop/local_starai_tcp.yaml --dry-run
```

SO-101 无线 TCP 遥操作：

```bash
python3 scripts/run_teleop_follower.py --config configs/teleop/remote_so101_tcp.yaml --dry-run
python3 scripts/run_teleop_leader.py --config configs/teleop/remote_so101_tcp.yaml --dry-run
```

SO-101 本地 TCP 遥操作：

```bash
python3 scripts/run_teleop_follower.py --config configs/teleop/local_so101_tcp.yaml --dry-run
python3 scripts/run_teleop_leader.py --config configs/teleop/local_so101_tcp.yaml --dry-run
```

SO-101 本地 TCP 数据集复现：

```bash
python3 scripts/run_dataset_replay_client.py --config configs/replay/local_so101_tcp_dataset.yaml --dry-run
python3 scripts/run_teleop_follower.py --config configs/replay/local_so101_tcp_dataset.yaml --dry-run
```

## 自动化验证

核心测试：

```bash
python3 -m unittest tests.test_config_loader tests.test_starai tests.test_tcp_teleop tests.test_dataset_replay -v
```

完整测试：

```bash
python3 -m unittest discover -s tests -v
```

代码空白检查：

```bash
git diff --check
```

## 边界

- Dry-run 和 unit test 不证明真实机械臂安全运动。
- 真实遥操作前必须确认串口、标定文件、leader/follower 姿态和安全配置。
- 硬件运行后的判断以具体复现文档和 run artifacts 为准。
