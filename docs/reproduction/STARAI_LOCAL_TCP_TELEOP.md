# StarAI 本地 TCP 遥操作成功复现说明

本文档专门记录已经跑通的 StarAI 本地 TCP 遥操作路径。

## 使用的 YAML

```text
configs/teleop/local_starai_tcp.yaml
```

该配置用于同一台机器上的 StarAI leader/follower TCP 遥操作：

- server 端连接 follower 从臂；
- client 端连接 leader 主臂；
- 两端通过 `127.0.0.1:9012` 建立 TCP 连接；
- 不加载 VLA 模型，`model.type` 为 `mock`，只做遥操作动作转发。

## 当前硬件与标定

配置中的 follower：

```yaml
robot:
  type: lerobot_robot_viola
  port: /dev/ttyUSB1
  id: my_awesome_staraiviola_arm
  calibration_dir: calibrations/robots/starai_viola
  skip_initial_position: true
```

配置中的 leader：

```yaml
teleop:
  enabled: true
  type: lerobot_teleoperator_violin
  port: /dev/ttyUSB0
  id: my_awesome_staraiviolin_arm
  calibration_dir: calibrations/teleoperators/starai_violin
```

项目内标定文件：

```text
calibrations/robots/starai_viola/my_awesome_staraiviola_arm.json
calibrations/teleoperators/starai_violin/my_awesome_staraiviolin_arm.json
```

## 关键安全配置

```yaml
safety:
  max_action_delta: 1.0
  max_first_action_delta: 12.0
  action_min: -100
  action_max: 100
  require_action_keys_match: true
```

含义：

- 第一帧 leader/follower 姿态差距超过 `12.0` 会拒绝执行；
- 每帧动作变化最大限制为 `1.0`；
- action 数值必须在 `[-100, 100]`；
- leader action keys 必须和 follower 关节 keys 匹配。

另一个关键配置：

```yaml
robot:
  skip_initial_position: true
```

它会跳过 StarAI follower 官方包里的硬编码初始姿态移动，避免 server 启动时从臂自己抬起来。

## 启动命令

所有命令从项目根目录运行：

```bash
cd ~/Documents/VLA+无线通信/lerobot-remote-vla-teleop
conda activate lerobot
```

第一个终端启动 follower/server：

```bash
python3 scripts/run_teleop_follower.py --config configs/teleop/local_starai_tcp.yaml
```

第二个终端启动 leader/client：

```bash
python3 scripts/run_teleop_leader.py --config configs/teleop/local_starai_tcp.yaml
```

## 成功时的现象

server 端应看到：

```text
StarAI follower startup initial-position move skipped by config.
TCP teleop follower listening on 127.0.0.1:9012
```

client 端应看到 leader 关节角度打印，例如：

```text
Leader action frame=0: Motor_0.pos=..., Motor_1.pos=..., Motor_2.pos=..., ...
```

实际打印频率由配置决定：

```yaml
logging:
  print_leader_actions: true
  print_action_interval: 10
```

即每 10 帧打印一次 leader action。

## Dry-run 验证命令

不连接硬件，只验证配置能被脚本正常读取：

```bash
python3 scripts/run_teleop_follower.py --config configs/teleop/local_starai_tcp.yaml --dry-run
python3 scripts/run_teleop_leader.py --config configs/teleop/local_starai_tcp.yaml --dry-run
```

## 自动化测试命令

```bash
python3 -m unittest tests.test_config_loader tests.test_starai tests.test_tcp_teleop -v
```

完整测试：

```bash
python3 -m unittest discover -s tests -v
```

## 常见问题

### 第一帧被拒绝

如果 server 报：

```text
First ACTION is too far from follower startup position
```

说明 leader 和 follower 当前姿态差太大。处理方式：

1. 停止 server/client；
2. 手动把 leader 和 follower 摆到接近的安全姿态；
3. 先启动 server，再启动 client；
4. 不要直接把 `max_first_action_delta` 调得很大。

### leader 打印大量 -100

如果 client 打印类似：

```text
Motor_0.pos=-100.000, Motor_1.pos=-100.000
```

但实际机械臂并不在限位附近，优先检查：

- `/dev/ttyUSB0` 是否真的是 leader；
- leader 供电和电机 ID；
- `calibrations/teleoperators/starai_violin/my_awesome_staraiviolin_arm.json` 是否是当前这台 leader 的标定文件；
- StarAI/FashionStar SDK 读取当前位置是否正常。

### server 启动后从臂自己动

当前成功配置已经启用：

```yaml
skip_initial_position: true
```

如果仍然发生 server 启动时从臂自动运动，先确认运行的是：

```text
configs/teleop/local_starai_tcp.yaml
```

并确认终端出现：

```text
StarAI follower startup initial-position move skipped by config.
```
