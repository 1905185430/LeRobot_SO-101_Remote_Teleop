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
cd ~/wjx/lerobot-remote-vla-teleop
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
cd ~/Documents/VLA+无线通信/lerobot-remote-vla-teleop
conda activate lerobot
python3 scripts/run_client.py --config configs/teleop/remote_so101_tcp.yaml
```

## 停止顺序

正常停止时建议按下面顺序操作：

1. 先在 leader/client 终端按 `Ctrl+C`。
2. 确认 follower 从臂没有继续接收新动作，也没有持续运动。
3. 再在 follower/server 终端按 `Ctrl+C`。
4. 停止后让两台机械臂保持在安全姿态，必要时手动断开机械臂电源或释放扭矩。

不要先关闭 follower/server 再让 client 继续发送动作。这样虽然 TCP 会断开，但排查日志时会混入连接关闭错误，不利于判断真正问题。

停止后建议检查本次运行目录：

```text
runs/so101_remote_teleop_tcp/<timestamp>-tcp-teleop-follower-xxxx/
runs/so101_remote_teleop_tcp/<timestamp>-tcp-teleop-leader-xxxx/
```

重点查看：

- `events.jsonl` 是否有 `exception`；
- `metadata.json` 里的 config、robot id、teleop id、endpoint 是否正确；
- `summary.md` 是否正常生成。

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
