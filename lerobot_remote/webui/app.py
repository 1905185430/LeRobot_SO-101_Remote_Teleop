"""Optional Gradio dashboard helpers."""

from __future__ import annotations

import html
from importlib import import_module
from typing import Mapping

from ..config.schema import PlatformConfig
from .state import DashboardState


def launch_dashboard(config: PlatformConfig, state: DashboardState):
    """Launch an optional Gradio dashboard and return the app object.

    Gradio is intentionally optional. If it is not installed, this returns `None`
    and records a state event so robotics runtime startup can continue.
    """
    if not config.webui.enabled:
        return None
    try:
        gr = import_module("gradio")
    except ImportError:
        state.log("webui disabled because gradio is not installed")
        return None

    app = gr.Blocks(title=f"{config.experiment.name} dashboard")
    with app:
        gr.Markdown(f"# {config.experiment.name}")
        status = gr.JSON(label="Runtime")
        images = gr.HTML(label="Images")
        joints = gr.JSON(label="Joint State")
        action = gr.JSON(label="Latest Action")
        metrics = gr.JSON(label="Metrics")
        logs = gr.Textbox(label="Events", lines=12)
        refresh = gr.Button("Refresh")

        def render():
            return render_dashboard_snapshot(state)

        refresh.click(render, outputs=[status, images, joints, action, metrics, logs])

    app.launch(
        server_name=config.webui.host,
        server_port=config.webui.port,
        prevent_thread_lock=True,
        quiet=True,
    )
    state.log(f"webui listening on {config.webui.host}:{config.webui.port}")
    return app


def render_dashboard_snapshot(
    state: DashboardState,
) -> tuple[dict[str, object], str, dict[str, float], dict[str, float], dict[str, object], str]:
    """Render dashboard state into Gradio component values."""
    snapshot = state.snapshot()
    status = {
        "experiment": snapshot["experiment_name"],
        "mode": snapshot["mode"],
        "role": snapshot["role"],
        "model": snapshot["model_type"],
        "robot": snapshot["robot_type"],
        "endpoint": snapshot["endpoint"],
        "connection_status": snapshot["connection_status"],
    }
    metrics = {
        "latency_ms": snapshot["latest_latency_ms"],
        "inference_ms": snapshot["latest_inference_ms"],
        "image_count": len(snapshot["latest_images"]),
    }
    logs = "\n".join(str(event) for event in snapshot["events"])
    return (
        status,
        render_images_html(snapshot["latest_images"]),
        snapshot["latest_joint_states"],
        snapshot["latest_action"],
        metrics,
        logs,
    )


def render_images_html(images: Mapping[str, str]) -> str:
    """Render base64 image payloads as simple HTML."""
    if not images:
        return "<p>No images received.</p>"
    blocks: list[str] = []
    for name, payload in sorted(images.items()):
        safe_name = html.escape(str(name))
        safe_payload = html.escape(str(payload))
        if safe_payload.startswith("data:image/"):
            src = safe_payload
        else:
            src = f"data:image/jpeg;base64,{safe_payload}"
        blocks.append(
            "<figure style='display:inline-block;margin:8px'>"
            f"<figcaption>{safe_name}</figcaption>"
            f"<img src='{src}' style='max-width:320px;max-height:240px;border:1px solid #ddd' />"
            "</figure>"
        )
    return "\n".join(blocks)
