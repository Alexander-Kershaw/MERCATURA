import hashlib
import random


class RandomStreams:
    """
    ========================================================================================

    DETERMINISTIC RANDOM STREAMS

    ========================================================================================

    Instead of doing random.Random(777) and using it everywhere (this would cause
    hidden coupling) I instead will do something like:

    stream.get("crm") and stream.get("oms") which will get completely distinct seeds
    that are deterministic.

    The logic being used:

    - Use the root seed and the namespace to create a unique SHA-256.
    - Take the first 64 bits
    - From that create integer RNG seed

    This results in creating unique and well distributed deterministic integers.

    ========================================================================================
    """

    def __init__(self, root_seed: int) -> None:
        if root_seed < 0:
            raise ValueError("root_seed must be non-negative")

        self._root_seed: int = root_seed
        self._streams: dict[str, random.Random] = {}

    @property
    def root_seed(self) -> int:
        return self._root_seed

    def seed_for(self, namespace: str) -> int:

        if not namespace.strip():
            raise ValueError("namespace must not be empty")

        material: bytes = f"{self._root_seed}:{namespace}".encode()

        digest: bytes = hashlib.sha256(string=material).digest()

        return int.from_bytes(bytes=digest[:8], byteorder="big", signed=False)

    def get(self, namespace: str) -> random.Random:

        if namespace not in self._streams:
            self._streams[namespace] = random.Random(x=self.seed_for(namespace=namespace))

        return self._streams[namespace]
