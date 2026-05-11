# SO-101 Remote VLA / Teleoperation Platform 中文说明

## 1. 项目定位

本项目是一个面向 SO-101 机械臂的轻量级远程 VLA 推理实验框架。当前第一条真实运行路径是：

```text
SO-101 follower + OpenCV cameras + LeRobot async inference + SmolVLA
```

项目目标不是一次性做成完整机器人平台，而是先把远程推理实验中最容易混乱的部分固定下来：

- 服务器端和机器人端有清晰的 Python 入口；
- 配置文件能描述模式、模型、机械臂、相机、网络和日志；
- 真实 LeRobot 路径可以从配置构建 runtime config；
- 没有硬件时可以用 mock TCP 路径调试通信；
- 每次运行保存 metadata、events、metrics 和 summary，方便复现实验。

## 2. 当前支持能力

### 已可用

| 能力 | 状态 |
| --- | --- |
| 常量版 LeRobot async server/client | 可用，入口是 `policy_server.py` 和 `robot_client.py` |
| YAML/JSON 配置加载与校验 | 可用，入口是 `configs/*.yaml` |
| 配置驱动 dry-run | 可用，三个 `scripts/run_*.py --dry-run` 都不会碰硬件 |
| 配置驱动真实远程推理 | 已接入 LeRobot async config，入口是 `scripts/run_server.py` / `scripts/run_client.py` |
| debug mock TCP roundtrip | 可用，用 `configs/debug_mock_robot.yaml` 测试协议和日志 |
| 长度头 TCP 协议 | 可用，位于 `so101_remote/network/` |
| 运行产物记录 | 可用，保存到 config 中的 `experiment.save_dir` |
| 中文项目说明 | 本文档 |

### 尚未完成

| 能力 | 当前边界 |
| --- | --- |
| 本地真实推理 `local_inference` | 配置和 dry-run 已有，真实本地 policy loop 尚未接 LeRobot 本地 API |
| 配置驱动 TCP 遥操作 `remote_teleoperation` | 配置已定义，真实运行仍建议使用 `legacy/` 旧 UDP 路径 |
| WebUI 实时显示 | config 已保留 `webui` 字段，真实 Gradio/FastAPI UI 尚未实现 |
| 图像二进制传输优化 | 当前 TCP mock 用 JSON，后续再接 JPEG/msgpack |
| 多机械臂适配 | 代码边界已预留，当前真实支持 SO-101 follower |

## 3. 目录结构

```text
configs/
  remote_inference_so101_smolvla.yaml   # 远程推理：服务器推理，机器人端执行
  local_inference_so101_smolvla.yaml    # 本地推理配置，当前用于校验和后续扩展
  remote_teleop_so101_tcp.yaml          # TCP 遥操作配置，当前用于设计和校验
  debug_mock_robot.yaml                 # 无硬件 TCP mock 调试

scripts/
  run_server.py                         # 配置驱动服务器入口
  run_client.py                         # 配置驱动客户端入口
  run_local.py                          # 配置驱动本地入口

so101_remote/
  config_loader.py                      # 配置文件加载
  config_schema.py                      # 配置 schema 和校验
  lerobot_factory.py                    # 从 PlatformConfig 构建 LeRobot config
  runtime.py                            # 根据 mode 分发真实/模拟运行
  network/                              # TCP 长度头协议和 client/server helper
  recorder.py                           # run directory、metadata、metrics、summary
  metrics.py                            # 指标和事件结构

legacy/
  leader_sender.py                      # 旧 UDP leader 发送端
  follower_receiver.py                  # 旧 UDP follower 接收端
```

## 4. 配置文件怎么改

远程推理主要改 `configs/remote_inference_so101_smolvla.yaml`：

```yaml
experiment:
  name: so101_remote_smolvla_pickplace
  mode: remote_inference
  task_name: pick_place_cube
  save_dir: runs/so101_remote_smolvla_pickplace

robot:
  type: so101_follower
  port: /dev/ttyACM0
  id: my_blue_follower_arm

model:
  type: smolvla
  model_path: HF_USER/FINETUNE_MODEL_NAME
  device: cuda

network:
  server_host: 192.168.1.151
  server_port: 9000
```

关键字段说明：

- `experiment.mode`: 当前真实远程推理使用 `remote_inference`。
- `experiment.save_dir`: 每次运行产物保存目录。
- `robot.port`: 机器人端 SO-101 串口，例如 `/dev/ttyACM0`。
- `robot.id`: LeRobot 校准 id，需要和本机校准记录匹配。
- `model.model_path`: Hugging Face 模型名或本地 checkpoint 路径。
- `network.server_host`: GPU 服务器在局域网或 Tailscale 中的 IP。
- `network.server_port`: LeRobot async inference server 监听端口。
- `camera.cameras`: 相机名称必须和模型训练/推理期望的 observation key 对齐。

## 5. 使用方式

### 5.1 先做配置 dry-run

在任意一台机器上先检查配置：

```bash
python3 scripts/run_server.py --config configs/remote_inference_so101_smolvla.yaml --dry-run
python3 scripts/run_client.py --config configs/remote_inference_so101_smolvla.yaml --dry-run
```

你应该看到 JSON summary，其中包含：

- `mode`
- `robot`
- `model`
- `network.endpoint`
- `camera_names`
- `lerobot` 解析后的真实运行摘要

### 5.2 启动真实远程推理服务器

在 GPU 服务器上运行：

```bash
python3 scripts/run_server.py --config configs/remote_inference_so101_smolvla.yaml
```

这条路径会：

1. 加载配置；
2. 创建 run directory；
3. 保存 `config.yaml` 和 metadata；
4. 构建 LeRobot `PolicyServerConfig`；
5. 调用 LeRobot `serve(config)`。

如果没有安装 LeRobot，会明确报错，不会静默失败。

### 5.3 启动真实远程推理客户端

在机器人端电脑上运行：

```bash
python3 scripts/run_client.py --config configs/remote_inference_so101_smolvla.yaml
```

这条路径会：

1. 加载配置；
2. 根据 `camera.cameras` 构建 OpenCV camera config；
3. 根据 `robot` 构建 SO-101 follower config；
4. 根据 `model` 和 `network` 构建 LeRobot `RobotClientConfig`；
5. 启动 LeRobot `RobotClient`；
6. 开启 action receiver thread；
7. 调用 `client.control_loop(task_name)`。

### 5.4 无硬件 TCP mock 调试

先开一个终端启动 mock server：

```bash
python3 scripts/run_server.py --config configs/debug_mock_robot.yaml
```

再开另一个终端启动 mock client：

```bash
python3 scripts/run_client.py --config configs/debug_mock_robot.yaml
```

这个模式不会加载 LeRobot，不会连接机械臂，只测试：

- TCP 是否能绑定和连接；
- 长度头协议是否能收发；
- OBSERVATION -> ACTION roundtrip 是否正常；
- run directory 和 metrics 是否正常生成。

## 6. 运行产物

每次运行都会写入 `experiment.save_dir` 下的 run directory，例如：

```text
runs/so101_remote_smolvla_pickplace/
  20260511-184200-policy-server-xxxxxx/
    config.yaml
    metadata.json
    metrics.jsonl
    events.jsonl
    metrics.csv
    summary.md
```

主要文件：

- `config.yaml`: 本次运行使用的配置快照。
- `metadata.json`: role、server、robot、policy、git commit、resolved settings。
- `events.jsonl`: 启动、异常、恢复等事件。
- `metrics.jsonl`: 延迟等数值指标。
- `metrics.csv`: 方便后续画图或导入表格。
- `summary.md`: 本次运行的简要统计。

## 7. 调试顺序

建议按下面顺序排查：

1. `python3 -m unittest discover -s tests -v`
2. `scripts/run_*.py --dry-run` 检查配置是否正确。
3. `debug_mock_robot.yaml` 跑 mock TCP server/client。
4. GPU 服务器运行 `scripts/run_server.py --config configs/remote_inference_so101_smolvla.yaml`。
5. 机器人端确认串口、相机、校准 id 后运行 client。
6. 如果失败，先看终端错误，再看对应 run directory 的 `events.jsonl` 和 `metadata.json`。

常见问题：

- 连接失败：检查 `network.server_host` 是否是服务器在同一局域网/Tailscale 中可访问的 IP。
- 端口占用：修改 `network.server_port`。
- SO-101 找不到：检查 `robot.port` 和 Linux 权限。
- 相机打不开：检查 `camera.cameras.*.index`。
- 模型加载失败：检查 `model.model_path`、GPU 环境、LeRobot/Transformers 依赖。

## 8. 当前推荐工作流

真实实验优先使用配置驱动入口：

```bash
# server
python3 scripts/run_server.py --config configs/remote_inference_so101_smolvla.yaml

# client
python3 scripts/run_client.py --config configs/remote_inference_so101_smolvla.yaml
```

如果你只想验证旧的最小 LeRobot async 路径，也可以继续使用常量版：

```bash
python3 policy_server.py
python3 robot_client.py
```

如果你要做旧遥操作参考实验，当前仍使用：

```bash
python3 legacy/leader_sender.py --help
python3 legacy/follower_receiver.py --help
```

## 9. 后续优先级

建议下一步按这个顺序继续：

1. 在真实 LeRobot 环境跑通 `remote_inference` 的 server/client 启动。
2. 把真实运行日志中的异常和 LeRobot 输出整理进 run artifacts。
3. 实现 Gradio WebUI，只读显示最新图像、关节、动作、RTT 和错误。
4. 接入本地真实推理 `local_inference`，作为无线远程推理的 baseline。
5. 实现配置驱动 TCP 遥操作，并把 `legacy/` 的安全逻辑迁移过来。
6. 优化图像传输，从 JSON/base64 过渡到 msgpack + JPEG bytes。
