from mercatura.source.simulation import SimulationContext
from mercatura.source.systems.store.model import Store


def validate_stores(
    stores: tuple[Store, ...],
    context: SimulationContext,
) -> None:
    _validate_unique_ids(stores)
    _validate_unique_codes(stores)
    _validate_markets(stores, context)
    _validate_lifecycles(stores, context)


def _validate_unique_ids(
    stores: tuple[Store, ...],
) -> None:
    ids: list[str] = [store.store_id for store in stores]

    if len(ids) != len(set(ids)):
        raise ValueError("duplicate store_id detected")


def _validate_unique_codes(
    stores: tuple[Store, ...],
) -> None:
    codes: list[str] = [store.store_code for store in stores]

    if len(codes) != len(set(codes)):
        raise ValueError("duplicate store_code detected")


def _validate_markets(
    stores: tuple[Store, ...],
    context: SimulationContext,
) -> None:
    valid_markets: set[str] = {market.market_code for market in context.config.markets}

    invalid: set[str] = {
        store.market_code for store in stores if store.market_code not in valid_markets
    }

    if invalid:
        raise ValueError(f"unknown store markets: {sorted(invalid)}")


def _validate_lifecycles(
    stores: tuple[Store, ...],
    context: SimulationContext,
) -> None:
    for store in stores:
        if store.opened_at > context.config.end_date:
            raise ValueError(f"store {store.store_id} opens after the simulation period")

        if store.closed_at is not None and store.closed_at <= store.opened_at:
            raise ValueError(f"store {store.store_id} closed before opening")
