# SO-101 本地 TCP 遥操作复现说明

本文档记录在同一台机器上通过 TCP 操作 SO-101 leader/follower 的配置和启动步骤。

## 适用场景

本地 TCP 遥操作指：

- SO-101 follower 从臂和 SO-101 leader 主臂都连接在同一台电脑上；
- follower 侧脚本在本机监听 TCP；
- leader 侧脚本连接 `127.0.0.1` 并发送关节动作；
- 不加载 VLA 模型，`model.type` 为 `mock`，只做遥操作动作转发。

如果 leader 和 follower 分别连接在两台机器上，请使用无线/局域网文档：

```text
docs/reproduction/SO101_WIRELESS_TCP_TELEOP.md
```

## 使用的 YAML

```text
configs/teleop/local_so101_tcp.yaml
```

关键差异：

- `network.server_host: 127.0.0.1`
- `network.server_port: 9011`
- `experiment.save_dir: runs/so101_local_teleop_tcp`

## 当前配置

Follower 从臂：

```yaml
robot:
  type: so101_follower
  port: /dev/ttyACM1
  id: follower_arm
  calibration_dir: calibrations/robots/so_follower
```

Leader 主臂：

```yaml
teleop:
  enabled: true
  type: so101_leader
  port: /dev/ttyACM0
  id: leader_arm
  calibration_dir: calibrations/teleoperators/so_leader
```

网络：

```yaml
network:
  protocol: tcp
  server_host: 127.0.0.1
  server_port: 9011
```

同一台机器上两只 SO-101 的串口顺序可能会变化。运行前建议检查：

```bash
ls -l /dev/ttyACM*
```

如果 follower/leader 的串口和上面不一致，先修改 `configs/teleop/local_so101_tcp.yaml` 里的 `robot.port` 和 `teleop.port`。

## 标定文件

当前配置使用仓库内这对 SO-101 标定文件：

```text
calibrations/robots/so_follower/follower_arm.json
calibrations/teleoperators/so_leader/leader_arm.json
```

这两份标定需要成对使用。不要和下面旧文件混用：

```text
calibrations/robots/so_follower/my_awesome_follower_arm.json
calibrations/teleoperators/so_leader/so101_leader_arm.json
```

## 安全配置

```yaml
safety:
  max_action_delta: 2.0
  max_first_action_delta: 55.0
  action_min: -180
  action_max: 180
  require_action_keys_match: true
```

含义：

- `max_first_action_delta: 55.0`：第一帧 leader/follower 姿态差太大时拒绝执行；
- `max_action_delta: 2.0`：每帧实际发送给 follower 的动作变化被限幅；
- `action_min/action_max`：允许 SO-101 标定读数在 `[-180, 180]` 内；
- `require_action_keys_match: true`：leader action keys 必须和 follower 关节 keys 一致。

真实操作前仍然要手动把 leader 和 follower 摆到接近、无碰撞、远离限位的安全姿态。不要为了绕过第一帧报错而随意关闭安全检查。

## 启动命令

所有命令从项目根目录运行：

```bash
cd ~/Documents/VLA+无线通信/lerobot-remote-vla-teleop
conda activate lerobot
```

### 1. 启动 follower/server

第一个终端运行：

```bash
python3 scripts/run_teleop_follower.py --config configs/teleop/local_so101_tcp.yaml
```

期望看到：

```text
Run directory: runs/so101_local_teleop_tcp/<timestamp>-tcp-teleop-follower-xxxx/
TCP teleop follower listening on 127.0.0.1:9011
```

### 2. 启动 leader/client

第二个终端运行：

```bash
python3 scripts/run_teleop_leader.py --config configs/teleop/local_so101_tcp.yaml
```

期望看到：

```text
Run directory: runs/so101_local_teleop_tcp/<timestamp>-tcp-teleop-leader-xxxx/
TCP teleop leader connecting to 127.0.0.1:9011
Leader action frame=0: ...
```

实际 leader action 打印频率由配置决定：

```yaml
logging:
  print_leader_actions: true
  print_action_interval: 10
```

## WebUI

本地 SO-101 配置默认启用 WebUI：

```yaml
webui:
  enabled: true
  host: 127.0.0.1
  port: 7861
```

运行 follower 后，可以在本机浏览器打开：

```text
http://127.0.0.1:7861
```

WebUI 只用于观察连接状态、延迟、关节状态和动作，不替代真实机械臂周围的安全观察。

## 停止顺序

建议按下面顺序停止：

1. 先在 leader/client 终端按 `Ctrl+C`。
2. 确认 follower 没有继续接收新动作，也没有持续运动。
3. 再在 follower/server 终端按 `Ctrl+C`。
4. 停止后让两只机械臂保持在安全姿态，必要时断开电源或释放扭矩。

停止后检查本次运行目录：

```text
runs/so101_local_teleop_tcp/<timestamp>-tcp-teleop-follower-xxxx/
runs/so101_local_teleop_tcp/<timestamp>-tcp-teleop-leader-xxxx/
```

重点查看：

- `events.jsonl` 是否有 `exception`；
- `metadata.json` 里的 config、robot id、teleop id、endpoint 是否正确；
- `summary.md` 是否正常生成。

## Dry-run 验证

不连接硬件，只验证配置能被脚本正常读取：

```bash
python3 scripts/run_teleop_follower.py --config configs/teleop/local_so101_tcp.yaml --dry-run
python3 scripts/run_teleop_leader.py --config configs/teleop/local_so101_tcp.yaml --dry-run
```

## 自动化测试

核心测试：

```bash
python3 -m unittest tests.test_config_loader tests.test_tcp_teleop -v
```

完整测试：

```bash
python3 -m unittest discover -s tests -v
```

## 常见问题

### follower 或 leader 串口打不开

先检查当前串口：

```bash
ls -l /dev/ttyACM*
```

如果只看到一个设备，或者设备顺序和配置不一致，重新插拔后再确认 `robot.port` 和 `teleop.port`。同机双 SO-101 常见情况是：

- leader: `/dev/ttyACM0`
- follower: `/dev/ttyACM1`

但这不是硬性保证，以实际设备枚举为准。

### client 连接被拒绝

现象：

```text
ConnectionRefusedError: [Errno 61] Connection refused
```

处理：

- 确认 follower/server 终端已经启动；
- 确认 server 监听的是 `127.0.0.1:9011`；
- 确认没有旧进程占用或关闭了 `9011` 端口。

本地检查端口：

```bash
nc -vz 127.0.0.1 9011
```

### 第一帧被拒绝

现象：

```text
First ACTION is too far from follower startup position
```

处理：

- 停止 leader/client 和 follower/server；
- 手动把 leader 和 follower 摆到接近的安全姿态；
- 确认使用的是成对标定文件；
- 先启动 follower/server，再启动 leader/client。

### action key 不匹配

现象：

```text
ACTION keys do not match follower joints
```

优先检查：

- `robot.id` 是否对应 `calibrations/robots/so_follower/follower_arm.json`；
- `teleop.id` 是否对应 `calibrations/teleoperators/so_leader/leader_arm.json`；
- 是否误用了旧标定文件或不同批次机械臂的标定。
