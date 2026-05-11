# SO-101 无线 TCP 遥操作成功复现说明

本文档记录已经成功跑通的一版 SO-101 无线/局域网 TCP 遥操作。

## 成功结论

当前版本已经完成：

- SO-101 leader 机器通过 TCP 发送关节动作；
- SO-101 follower 机器通过 TCP 接收动作并执行；
- 两台机器通过局域网连接；
- 使用项目仓库内的成对 SO-101 标定文件；
- 第一帧姿态安全检查、每帧动作限幅、action key 匹配检查均保留。

## 使用的 YAML

```text
configs/teleop/remote_so101_tcp.yaml
```

## 当前配置

Follower 从臂：

```yaml
robot:
  type: so101_follower
  port: /dev/ttyACM0
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
  server_host: 192.168.1.151
  server_port: 9001
```

这里 `192.168.1.151` 是 follower/server 机器的局域网 IP。

## 成功使用的标定文件

```text
calibrations/robots/so_follower/follower_arm.json
calibrations/teleoperators/so_leader/leader_arm.json
```

这对标定文件来自同一套 SO-101 leader/follower 标定，不能和下面旧文件混用：

```text
calibrations/robots/so_follower/my_awesome_follower_arm.json
calibrations/teleoperators/so_leader/so101_leader_arm.json
```

## 安全配置

```yaml
safety:
  max_action_delta: 2.0
  max_first_action_delta: 25.0
  action_min: -180
  action_max: 180
  require_action_keys_match: true
```

含义：

- `max_first_action_delta: 25.0`：leader/follower 初始姿态差太大时拒绝第一帧；
- `max_action_delta: 2.0`：每帧实际发送给 follower 的动作变化被限幅；
- `action_min/action_max`：允许 SO-101 标定读数在 `[-180, 180]` 内；
- `require_action_keys_match: true`：leader 和 follower 的关节 key 必须一致。

## 启动命令

### 1. Follower 机器启动 server

在连接 SO-101 follower 的机器上运行：

```bash
cd ~/wjx/LeRobot_SO-101_Remote_Teleop
conda activate lerobot
python3 scripts/run_server.py --config configs/teleop/remote_so101_tcp.yaml
```

期望看到：

```text
TCP teleop follower listening on 192.168.1.151:9001
```

### 2. Leader 机器启动 client

在连接 SO-101 leader 的机器上运行：

```bash
cd ~/Documents/VLA+无线通信/LeRobot_SO-101_Remote_Teleop
conda activate lerobot
python3 scripts/run_client.py --config configs/teleop/remote_so101_tcp.yaml
```

## 网络检查命令

在 leader/client 机器上：

```bash
ping 192.168.1.151
nc -vz 192.168.1.151 9001
```

`nc` 需要在 follower/server 已启动后运行。

## 成功前解决过的问题

### 1. server 没启动导致 client refused

现象：

```text
ConnectionRefusedError: [Errno 111] Connection refused
```

原因：server 没有在 `192.168.1.151:9001` 监听，或 server 启动后崩溃。

### 2. follower startup 读数超出默认范围

现象：

```text
ACTION value for shoulder_lift.pos=-121.582 is outside [-100.000, 100.000]
```

处理：SO-101 遥操作配置改为：

```yaml
action_min: -180
action_max: 180
```

### 3. 标定文件不成对

错误组合：

```text
my_awesome_follower_arm.json
so101_leader_arm.json
```

正确组合：

```text
follower_arm.json
leader_arm.json
```

### 4. 第一帧姿态差过大

现象：

```text
First ACTION is too far from follower startup position
```

处理：

- 使用正确成对标定；
- 启动前把 leader 和 follower 摆到接近姿态；
- 保留 `max_first_action_delta`，不要直接关闭安全检查。

## Dry-run 验证

不连接硬件，仅验证配置加载：

```bash
python3 scripts/run_server.py --config configs/teleop/remote_so101_tcp.yaml --dry-run
python3 scripts/run_client.py --config configs/teleop/remote_so101_tcp.yaml --dry-run
```

## 自动化测试

```bash
python3 -m unittest tests.test_tcp_teleop tests.test_config_loader -v
```

完整测试：

```bash
python3 -m unittest discover -s tests -v
```
