import hashlib
import json

from mercatura.source.simulation.config import SimulationConfig

SIMULATION_ID_VERSION = 1


def build_simulation_id(config: SimulationConfig) -> str:

    payload = {"simulation_id_version": SIMULATION_ID_VERSION, **config.canonical_payload()}

    canonical_json: str = json.dumps(obj=payload, sort_keys=True, separators=(",", ":"))

    digest: str = hashlib.sha256(string=canonical_json.encode(encoding="utf-8")).hexdigest()

    return f"sim_v{SIMULATION_ID_VERSION}_{digest[:20]}"
