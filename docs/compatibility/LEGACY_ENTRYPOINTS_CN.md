# 兼容入口与 Legacy 路径说明

本项目现在推荐使用：

```text
scripts/run_teleop_follower.py
scripts/run_teleop_leader.py
scripts/run_server.py
scripts/run_client.py
configs/
```

下面这些路径暂时保留，是为了兼容历史实验、测试和对照实现。

## `policy_server.py`

旧的 constant-based LeRobot async inference policy server 入口。

适合：

- 快速验证 LeRobot async policy server 是否还能启动；
- 对照最早期的 SO-101 + SmolVLA 实验路径；
- 跑兼容测试。

不适合：

- 新增配置驱动实验；
- TCP teleoperation；
- 多机器人/多配置复现实验。

新实验优先使用：

```bash
python3 scripts/run_server.py --config configs/remote_inference/so101_smolvla.yaml
```

## `robot_client.py`

旧的 constant-based LeRobot async inference robot client 入口。

适合：

- 快速验证 LeRobot robot client 兼容性；
- 对照最早期的 SO-101 robot-side path；
- 跑兼容测试。

新实验优先使用：

```bash
python3 scripts/run_client.py --config configs/remote_inference/so101_smolvla.yaml
```

## `legacy/`

旧 UDP teleoperation 实现。

适合：

- 对照 UDP 协议、ACK、RTT、timeout 处理；
- 保留历史测试覆盖；
- 作为通信实验参考。

不适合作为当前主线，因为当前 config-driven teleoperation 使用 TCP：

```bash
python3 scripts/run_teleop_follower.py --config configs/teleop/local_starai_tcp.yaml
python3 scripts/run_teleop_leader.py --config configs/teleop/local_starai_tcp.yaml
```

## `lerobot_remote/runtime/remote_teleop.py`

旧模块名，当前仅作为兼容导出。

新代码应使用：

```python
from lerobot_remote.runtime.teleoperation import (
    run_tcp_teleop_follower_server,
    run_tcp_teleop_leader_client,
)
```

## 移除前置条件

这些路径不能立即删除。删除前至少需要满足：

- README 和 reproduction docs 不再引用旧入口作为主路径；
- tests 中不再依赖旧 import；
- 至少一次真实硬件复现实验确认新入口稳定；
- 历史实验复现说明中明确标注替代命令；
- 删除操作有独立 GSD 计划和回滚策略。
