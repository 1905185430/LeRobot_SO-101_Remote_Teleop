# 项目架构导览

这份文档只解释当前推荐路径。它的目标是让你能判断：

- 该运行哪个入口；
- YAML 里的字段会影响哪一侧硬件；
- 一个 TCP 遥操作动作在代码里怎么流动；
- 想调整行为时应该先看哪个文件。

## 1. 当前推荐入口

### TCP 遥操作

推荐使用按机械臂角色命名的入口：

```bash
# follower / 从臂侧，监听 TCP
python3 scripts/run_teleop_follower.py --config configs/teleop/local_starai_tcp.yaml

# leader / 主臂侧，连接 follower
python3 scripts/run_teleop_leader.py --config configs/teleop/local_starai_tcp.yaml
```

这两个脚本直接说明了机械臂角色，避免把网络 server/client 和机械臂 leader/follower 混在一起。

### 远程 VLA 推理

远程推理仍使用通用入口：

```bash
# GPU / policy server
python3 scripts/run_server.py --config configs/remote_inference/so101_smolvla.yaml

# robot-side client
python3 scripts/run_client.py --config configs/remote_inference/so101_smolvla.yaml
```

## 2. TCP 遥操作心智模型

以 StarAI 本地 TCP 遥操作为例：

```text
configs/teleop/local_starai_tcp.yaml
  -> scripts/run_teleop_follower.py
     -> config.robot
     -> build follower robot
     -> listen on 127.0.0.1:9012

configs/teleop/local_starai_tcp.yaml
  -> scripts/run_teleop_leader.py
     -> config.teleop
     -> build leader device
     -> connect to 127.0.0.1:9012
```

运行时动作流：

```text
leader_device.get_action()
  -> build ACTION message
  -> TCP send
  -> follower server receives ACTION
  -> safety checks and delta limiting
  -> follower_robot.send_action(action)
```

压缩成一句话：

```text
leader.get_action() -> TCP ACTION -> follower.send_action(action)
```

## 3. YAML 字段对应关系

TCP 遥操作里最重要的字段：

```text
experiment.mode = remote_teleoperation
```

这告诉 runtime 走遥操作路径。

```text
robot
```

定义 follower / 从臂，例如 StarAI Viola 或 SO-101 follower。

```text
teleop
```

定义 leader / 主臂，例如 StarAI Violin 或 SO-101 leader。

```text
network.server_host
network.server_port
```

定义 TCP 连接地址。follower 监听这个地址，leader 连接这个地址。

```text
safety
```

定义动作安全限制，例如第一帧最大差距、每帧最大变化、动作数值范围、关节 key 是否必须匹配。

## 4. 代码调用链

### 从入口到运行模式

```text
scripts/run_teleop_follower.py
  -> load_config()
  -> run_tcp_teleop_follower_server()

scripts/run_teleop_leader.py
  -> load_config()
  -> run_tcp_teleop_leader_client()
```

通用入口多一层 dispatch：

```text
scripts/run_server.py
  -> run_configured_server()
  -> config.mode == remote_teleoperation
  -> run_tcp_teleop_follower_server()

scripts/run_client.py
  -> run_configured_client()
  -> config.mode == remote_teleoperation
  -> run_tcp_teleop_leader_client()
```

### 从运行模式到硬件

```text
lerobot_remote/runtime/teleoperation.py
  -> build_teleop_follower_robot(config)
  -> config.robot
  -> StarAI/SO101 follower object

lerobot_remote/runtime/teleoperation.py
  -> build_teleop_leader_device(config)
  -> config.teleop
  -> StarAI/SO101 leader object
```

硬件类型分发在：

```text
lerobot_remote/robots/factory.py
```

StarAI 具体构造在：

```text
lerobot_remote/robots/starai.py
```

SO-101 具体构造在：

```text
lerobot_remote/robots/so101.py
```

## 5. Package 职责地图

```text
lerobot_remote/config/
  读取 YAML/JSON，变成 PlatformConfig

lerobot_remote/runtime/
  根据 mode 和角色编排一次运行

lerobot_remote/teleop/
  TCP leader/client 和 follower/server 的控制循环、安全检查

lerobot_remote/robots/
  构造 SO-101 / StarAI 硬件对象

lerobot_remote/network/
  TCP 消息编码、解码、收发

lerobot_remote/recording/
  metrics、events、run directory、summary

lerobot_remote/policies/
  LeRobot async inference policy/client 配置构造

lerobot_remote/webui/
  可选 Gradio 状态和展示
```

## 6. 常见修改应该看哪里

### 修改 StarAI 本地 TCP 遥操作参数

先看：

```text
configs/teleop/local_starai_tcp.yaml
```

### 修改 leader 读取动作、发送频率、ACK 行为

先看：

```text
lerobot_remote/teleop/client.py
```

### 修改 follower 收到动作后的安全检查和执行

先看：

```text
lerobot_remote/teleop/server.py
lerobot_remote/teleop/safety.py
```

### 修改 TCP 消息格式

先看：

```text
lerobot_remote/network/protocol.py
```

### 修改 StarAI import 或 calibration 构造

先看：

```text
lerobot_remote/robots/starai.py
```

### 修改 SO-101 import 或 calibration 构造

先看：

```text
lerobot_remote/robots/so101.py
```
