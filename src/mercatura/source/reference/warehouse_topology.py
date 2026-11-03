from dataclasses import dataclass

from mercatura.source.systems.wms.model import (
    WarehouseType,
)


@dataclass(frozen=True, slots=True)
class WarehouseSite:
    market_code: str
    city: str
    region: str
    timezone: str
    warehouse_type: WarehouseType
    supports_store_replenishment: bool
    supports_ecommerce: bool


WAREHOUSE_SITES: tuple[WarehouseSite, ...] = (
    # =======================================================================================
    # United Kingdom
    # =======================================================================================
    WarehouseSite(
        market_code="GB",
        city="Nottingham",
        region="England",
        timezone="Europe/London",
        warehouse_type="NATIONAL_DC",
        supports_store_replenishment=True,
        supports_ecommerce=False,
    ),
    WarehouseSite(
        market_code="GB",
        city="Birmingham",
        region="England",
        timezone="Europe/London",
        warehouse_type="REGIONAL_DC",
        supports_store_replenishment=True,
        supports_ecommerce=False,
    ),
    WarehouseSite(
        market_code="GB",
        city="Manchester",
        region="England",
        timezone="Europe/London",
        warehouse_type="REGIONAL_DC",
        supports_store_replenishment=True,
        supports_ecommerce=False,
    ),
    WarehouseSite(
        market_code="GB",
        city="London",
        region="England",
        timezone="Europe/London",
        warehouse_type="ECOMMERCE_FC",
        supports_store_replenishment=False,
        supports_ecommerce=True,
    ),
    # =======================================================================================
    # Germany
    # =======================================================================================
    WarehouseSite(
        market_code="DE",
        city="Frankfurt",
        region="Hesse",
        timezone="Europe/Berlin",
        warehouse_type="HYBRID_FC",
        supports_store_replenishment=True,
        supports_ecommerce=True,
    ),
    WarehouseSite(
        market_code="DE",
        city="Hamburg",
        region="Hamburg",
        timezone="Europe/Berlin",
        warehouse_type="REGIONAL_DC",
        supports_store_replenishment=True,
        supports_ecommerce=False,
    ),
    WarehouseSite(
        market_code="DE",
        city="Berlin",
        region="Berlin",
        timezone="Europe/Berlin",
        warehouse_type="REGIONAL_DC",
        supports_store_replenishment=True,
        supports_ecommerce=False,
    ),
    # =======================================================================================
    # United States
    # =======================================================================================
    WarehouseSite(
        market_code="US",
        city="Newark",
        region="New Jersey",
        timezone="America/New_York",
        warehouse_type="HYBRID_FC",
        supports_store_replenishment=True,
        supports_ecommerce=True,
    ),
    WarehouseSite(
        market_code="US",
        city="Atlanta",
        region="Georgia",
        timezone="America/New_York",
        warehouse_type="REGIONAL_DC",
        supports_store_replenishment=True,
        supports_ecommerce=False,
    ),
    WarehouseSite(
        market_code="US",
        city="Chicago",
        region="Illinois",
        timezone="America/Chicago",
        warehouse_type="REGIONAL_DC",
        supports_store_replenishment=True,
        supports_ecommerce=False,
    ),
    WarehouseSite(
        market_code="US",
        city="Dallas",
        region="Texas",
        timezone="America/Chicago",
        warehouse_type="REGIONAL_DC",
        supports_store_replenishment=True,
        supports_ecommerce=False,
    ),
    WarehouseSite(
        market_code="US",
        city="Los Angeles",
        region="California",
        timezone="America/Los_Angeles",
        warehouse_type="ECOMMERCE_FC",
        supports_store_replenishment=False,
        supports_ecommerce=True,
    ),
    # =======================================================================================
    # China
    # =======================================================================================
    WarehouseSite(
        market_code="CN",
        city="Shanghai",
        region="Shanghai",
        timezone="Asia/Shanghai",
        warehouse_type="HYBRID_FC",
        supports_store_replenishment=True,
        supports_ecommerce=True,
    ),
    WarehouseSite(
        market_code="CN",
        city="Beijing",
        region="Beijing",
        timezone="Asia/Shanghai",
        warehouse_type="REGIONAL_DC",
        supports_store_replenishment=True,
        supports_ecommerce=False,
    ),
    WarehouseSite(
        market_code="CN",
        city="Guangzhou",
        region="Guangdong",
        timezone="Asia/Shanghai",
        warehouse_type="REGIONAL_DC",
        supports_store_replenishment=True,
        supports_ecommerce=False,
    ),
    WarehouseSite(
        market_code="CN",
        city="Chengdu",
        region="Sichuan",
        timezone="Asia/Shanghai",
        warehouse_type="ECOMMERCE_FC",
        supports_store_replenishment=False,
        supports_ecommerce=True,
    ),
    # =======================================================================================
    # Norway
    # =======================================================================================
    WarehouseSite(
        market_code="NO",
        city="Oslo",
        region="Oslo",
        timezone="Europe/Oslo",
        warehouse_type="HYBRID_FC",
        supports_store_replenishment=True,
        supports_ecommerce=True,
    ),
    # =======================================================================================
    # Russia
    # =======================================================================================
    WarehouseSite(
        market_code="RU",
        city="Moscow",
        region="Moscow",
        timezone="Europe/Moscow",
        warehouse_type="HYBRID_FC",
        supports_store_replenishment=True,
        supports_ecommerce=True,
    ),
    WarehouseSite(
        market_code="RU",
        city="Yekaterinburg",
        region="Sverdlovsk",
        timezone="Asia/Yekaterinburg",
        warehouse_type="REGIONAL_DC",
        supports_store_replenishment=True,
        supports_ecommerce=False,
    ),
    # =======================================================================================
    # Japan
    # =======================================================================================
    WarehouseSite(
        market_code="JP",
        city="Tokyo",
        region="Tokyo",
        timezone="Asia/Tokyo",
        warehouse_type="HYBRID_FC",
        supports_store_replenishment=True,
        supports_ecommerce=True,
    ),
    WarehouseSite(
        market_code="JP",
        city="Osaka",
        region="Osaka",
        timezone="Asia/Tokyo",
        warehouse_type="REGIONAL_DC",
        supports_store_replenishment=True,
        supports_ecommerce=False,
    ),
    WarehouseSite(
        market_code="JP",
        city="Nagoya",
        region="Aichi",
        timezone="Asia/Tokyo",
        warehouse_type="REGIONAL_DC",
        supports_store_replenishment=True,
        supports_ecommerce=False,
    ),
    # =======================================================================================
    # South Korea
    # =======================================================================================
    WarehouseSite(
        market_code="KR",
        city="Seoul",
        region="Seoul",
        timezone="Asia/Seoul",
        warehouse_type="HYBRID_FC",
        supports_store_replenishment=True,
        supports_ecommerce=True,
    ),
    WarehouseSite(
        market_code="KR",
        city="Busan",
        region="Busan",
        timezone="Asia/Seoul",
        warehouse_type="REGIONAL_DC",
        supports_store_replenishment=True,
        supports_ecommerce=False,
    ),
    # =======================================================================================
    # France
    # =======================================================================================
    WarehouseSite(
        market_code="FR",
        city="Paris",
        region="Île-de-France",
        timezone="Europe/Paris",
        warehouse_type="HYBRID_FC",
        supports_store_replenishment=True,
        supports_ecommerce=True,
    ),
    WarehouseSite(
        market_code="FR",
        city="Lyon",
        region="Auvergne-Rhône-Alpes",
        timezone="Europe/Paris",
        warehouse_type="REGIONAL_DC",
        supports_store_replenishment=True,
        supports_ecommerce=False,
    ),
    WarehouseSite(
        market_code="FR",
        city="Lille",
        region="Hauts-de-France",
        timezone="Europe/Paris",
        warehouse_type="REGIONAL_DC",
        supports_store_replenishment=True,
        supports_ecommerce=False,
    ),
    # =======================================================================================
    # Netherlands
    # =======================================================================================
    WarehouseSite(
        market_code="NL",
        city="Rotterdam",
        region="South Holland",
        timezone="Europe/Amsterdam",
        warehouse_type="HYBRID_FC",
        supports_store_replenishment=True,
        supports_ecommerce=True,
    ),
    WarehouseSite(
        market_code="NL",
        city="Amsterdam",
        region="North Holland",
        timezone="Europe/Amsterdam",
        warehouse_type="REGIONAL_DC",
        supports_store_replenishment=True,
        supports_ecommerce=False,
    ),
    # =======================================================================================
    # Poland
    # =======================================================================================
    WarehouseSite(
        market_code="PL",
        city="Warsaw",
        region="Masovian",
        timezone="Europe/Warsaw",
        warehouse_type="HYBRID_FC",
        supports_store_replenishment=True,
        supports_ecommerce=True,
    ),
    WarehouseSite(
        market_code="PL",
        city="Poznań",
        region="Greater Poland",
        timezone="Europe/Warsaw",
        warehouse_type="REGIONAL_DC",
        supports_store_replenishment=True,
        supports_ecommerce=False,
    ),
)
