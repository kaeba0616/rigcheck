"""Parse Live2D runtime JSON files."""
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class Live2DModel:
    """Parsed Live2D runtime model data."""
    name: str
    base_path: Path

    # From model3.json
    moc_file: str = ""
    textures: list[str] = field(default_factory=list)
    eye_blink_ids: list[str] = field(default_factory=list)
    lip_sync_ids: list[str] = field(default_factory=list)
    hit_areas: list[dict] = field(default_factory=list)
    expression_files: list[str] = field(default_factory=list)
    motion_files: list[str] = field(default_factory=list)

    # From cdi3.json
    parameters: list[dict] = field(default_factory=list)
    parameter_groups: list[dict] = field(default_factory=list)
    parts: list[dict] = field(default_factory=list)
    combined_parameters: list[list[str]] = field(default_factory=list)

    # From physics3.json
    physics_settings: list[dict] = field(default_factory=list)
    physics_meta: dict = field(default_factory=dict)

    # From expression files
    expressions: list[dict] = field(default_factory=list)

    # From motion files
    motions: list[dict] = field(default_factory=list)


def _read_json(path: Path) -> Optional[dict]:
    """Read and parse a JSON file, returning None if it doesn't exist."""
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_model(runtime_dir: str | Path) -> Live2DModel:
    """Parse a Live2D runtime directory into a structured model."""
    base = Path(runtime_dir)

    # Find model3.json (the entry point)
    model3_files = list(base.glob("*.model3.json"))
    if not model3_files:
        raise FileNotFoundError(f"No .model3.json found in {base}")

    model3_path = model3_files[0]
    model_name = model3_path.stem.replace(".model3", "")
    model = Live2DModel(name=model_name, base_path=base)

    # Parse model3.json
    model3 = _read_json(model3_path)
    if model3:
        refs = model3.get("FileReferences", {})
        model.moc_file = refs.get("Moc", "")
        model.textures = refs.get("Textures", [])

        for group in model3.get("Groups", []):
            if group.get("Name") == "EyeBlink":
                model.eye_blink_ids = group.get("Ids", [])
            elif group.get("Name") == "LipSync":
                model.lip_sync_ids = group.get("Ids", [])

        model.hit_areas = model3.get("HitAreas", [])

        for expr in refs.get("Expressions", []):
            model.expression_files.append(expr.get("File", ""))

        for _group_name, motion_list in refs.get("Motions", {}).items():
            for motion in motion_list:
                model.motion_files.append(motion.get("File", ""))

    # Parse cdi3.json
    cdi3_files = list(base.glob("*.cdi3.json"))
    if cdi3_files:
        cdi3 = _read_json(cdi3_files[0])
        if cdi3:
            model.parameters = cdi3.get("Parameters", [])
            model.parameter_groups = cdi3.get("ParameterGroups", [])
            model.parts = cdi3.get("Parts", [])
            model.combined_parameters = cdi3.get("CombinedParameters", [])

    # Parse physics3.json
    physics_files = list(base.glob("*.physics3.json"))
    if physics_files:
        physics = _read_json(physics_files[0])
        if physics:
            model.physics_meta = physics.get("Meta", {})
            model.physics_settings = physics.get("PhysicsSettings", [])

    # Parse expression files
    for expr_file in model.expression_files:
        expr_path = base / expr_file
        expr_data = _read_json(expr_path)
        if expr_data:
            model.expressions.append({
                "file": expr_file,
                **expr_data,
            })

    # Parse motion files
    for motion_file in model.motion_files:
        motion_path = base / motion_file
        motion_data = _read_json(motion_path)
        if motion_data:
            model.motions.append({
                "file": motion_file,
                **motion_data,
            })

    return model
