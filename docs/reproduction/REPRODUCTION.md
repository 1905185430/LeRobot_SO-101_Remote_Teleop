# 复现文档

本文档记录当前已通过的本地复现步骤和验证命令。所有命令默认在项目根目录执行：

```bash
cd ~/Documents/VLA+无线通信/lerobot-remote-vla-teleop
conda activate lerobot
```

## 1. StarAI 本地 TCP 遥操作

配置文件：

```text
configs/teleop/local_starai_tcp.yaml
```

项目内标定文件：

```text
calibrations/robots/starai_viola/my_awesome_staraiviola_arm.json
calibrations/teleoperators/starai_violin/my_awesome_staraiviolin_arm.json
```

当前配置使用的设备：

```yaml
robot:
  type: lerobot_robot_viola
  port: /dev/ttyUSB1
  id: my_awesome_staraiviola_arm
  calibration_dir: calibrations/robots/starai_viola
  skip_initial_position: true

teleop:
  type: lerobot_teleoperator_violin
  port: /dev/ttyUSB0
  id: my_awesome_staraiviolin_arm
  calibration_dir: calibrations/teleoperators/starai_violin
```

### 1.1 启动 server

第一个终端：

```bash
python3 scripts/run_server.py --config configs/teleop/local_starai_tcp.yaml
```

期望看到：

```text
StarAI follower startup initial-position move skipped by config.
```

这说明 server 启动时不会执行 StarAI follower 官方硬编码初始姿态移动。

### 1.2 启动 client

第二个终端：

```bash
python3 scripts/run_client.py --config configs/teleop/local_starai_tcp.yaml
```

期望看到类似：

```text
Leader action frame=0: Motor_0.pos=..., Motor_1.pos=..., ...
```

这说明 client 已经读到 leader 关节角度，并准备通过 TCP 发送给 server。

### 1.3 第一帧安全检查

如果 server 报：

```text
First ACTION is too far from follower startup position
```

说明 leader 和 follower 当前姿态差距超过配置阈值：

```yaml
safety:
  max_first_action_delta: 12.0
```

处理方式：

1. 不要直接把阈值调到很大。
2. 手动把 leader 和 follower 摆到接近的安全姿态。
3. 重新启动 server，再启动 client。

## 2. StarAI 本地 TCP 配置 dry-run

不连接硬件，只验证配置能被脚本正常读取：

```bash
python3 scripts/run_server.py --config configs/teleop/local_starai_tcp.yaml --dry-run
python3 scripts/run_client.py --config configs/teleop/local_starai_tcp.yaml --dry-run
```

期望输出包含：

```json
{
  "role": "server"
}
```

以及：

```json
{
  "role": "client"
}
```

## 3. 自动化测试复现

### 3.1 配置解析测试

```bash
python3 -m unittest tests.test_config_loader -v
```

验证内容：

- `configs/teleop/local_starai_tcp.yaml` 可以被解析；
- StarAI 本地配置启用了 `skip_initial_position`；
- 项目内 robot/teleop 标定目录配置正确；
- leader action 打印配置正确。

### 3.2 StarAI 构建测试

```bash
python3 -m unittest tests.test_starai -v
```

验证内容：

- StarAI follower/leader 类型名能被识别；
- StarAI follower 构建时能跳过 startup initial-position move；
- StarAI follower/leader 构建时会收到项目内 `calibration_dir`；
- StarAI action dict 可以被 TCP teleop 归一化。

### 3.3 TCP 遥操作测试

```bash
python3 -m unittest tests.test_tcp_teleop -v
```

验证内容：

- leader action message 构建；
- leader action 终端打印；
- leader 读取失败时不会发送不安全 action；
- follower 第一帧姿态差过大时拒绝；
- follower 每帧 action delta 限制；
- ACTION/ACK roundtrip。

### 3.4 完整测试套件

```bash
python3 -m unittest discover -s tests -v
```

最近一次通过结果：

```text
Ran 106 tests
OK
```

## 4. 代码格式检查

```bash
git diff --check
```

最近一次通过结果：无输出，退出码为 0。

## 5. 已知边界

- dry-run 和 unit test 不会证明真实机械臂安全运动，只证明配置、协议、安全检查和构建逻辑。
- 真实遥操作前必须确认 `/dev/ttyUSB0` 是 leader，`/dev/ttyUSB1` 是 follower。
- 如果 leader 打印大量 `-100` 且机械臂实际不在限位附近，优先检查标定文件、串口和 StarAI 电机读取。
- 如果第一帧安全检查拒绝，先摆正 leader/follower 姿态，不要直接放大 `max_first_action_delta`。
