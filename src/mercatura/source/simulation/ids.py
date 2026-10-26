from uuid import NAMESPACE_DNS, UUID, uuid5

MERCATURA_NAMESPACE: UUID = uuid5(
    namespace=NAMESPACE_DNS,
    name="mercatura.project-meridian",
)


class DeterministicIdGenerator:
    def __init__(self, simulation_id: str) -> None:
        if not simulation_id.strip():
            raise ValueError("simulation_id must not be empty")

        self._simulation_id: str = simulation_id

        self._simulation_namespace: UUID = uuid5(
            namespace=MERCATURA_NAMESPACE,
            name=simulation_id,
        )

    @property
    def simulation_id(self) -> str:
        return self._simulation_id

    def uuid_for(
        self,
        namespace: str,
        key: str | int,
    ) -> UUID:
        if not namespace.strip():
            raise ValueError("namespace must not be empty")

        material: str = f"{namespace}:{key}"

        return uuid5(
            namespace=self._simulation_namespace,
            name=material,
        )

    def id_for(
        self,
        namespace: str,
        key: str | int,
        *,
        prefix: str | None = None,
    ) -> str:
        identifier: str = self.uuid_for(
            namespace,
            key,
        ).hex

        if prefix is None:
            return identifier

        if not prefix.strip():
            raise ValueError("prefix must not be empty")

        return f"{prefix}_{identifier}"
