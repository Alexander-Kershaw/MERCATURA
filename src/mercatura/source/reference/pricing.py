from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class PriceBand:
    minimum_gbp: Decimal
    maximum_gbp: Decimal


SUBCATEGORY_PRICE_BANDS: dict[str, PriceBand] = {
    # Electronics
    "HEAD": PriceBand(minimum_gbp=Decimal(value="15"), maximum_gbp=Decimal(value="250")),
    "SPKR": PriceBand(minimum_gbp=Decimal(value="20"), maximum_gbp=Decimal(value="300")),
    "CACC": PriceBand(minimum_gbp=Decimal(value="8"), maximum_gbp=Decimal(value="180")),
    "MACC": PriceBand(minimum_gbp=Decimal(value="5"), maximum_gbp=Decimal(value="100")),
    # Home
    "BEDD": PriceBand(minimum_gbp=Decimal(value="8"), maximum_gbp=Decimal(value="140")),
    "BATH": PriceBand(minimum_gbp=Decimal(value="5"), maximum_gbp=Decimal(value="90")),
    "LAMP": PriceBand(minimum_gbp=Decimal(value="12"), maximum_gbp=Decimal(value="180")),
    "HSTR": PriceBand(minimum_gbp=Decimal(value="5"), maximum_gbp=Decimal(value="160")),
    "DECO": PriceBand(minimum_gbp=Decimal(value="5"), maximum_gbp=Decimal(value="120")),
    # Kitchen
    "CKWR": PriceBand(minimum_gbp=Decimal(value="10"), maximum_gbp=Decimal(value="180")),
    "BAKE": PriceBand(minimum_gbp=Decimal(value="5"), maximum_gbp=Decimal(value="80")),
    "TBLW": PriceBand(minimum_gbp=Decimal(value="5"), maximum_gbp=Decimal(value="120")),
    "KTUL": PriceBand(minimum_gbp=Decimal(value="4"), maximum_gbp=Decimal(value="100")),
    # Apparel
    "TOP": PriceBand(minimum_gbp=Decimal(value="8"), maximum_gbp=Decimal(value="80")),
    "KNIT": PriceBand(minimum_gbp=Decimal(value="15"), maximum_gbp=Decimal(value="130")),
    "OUTR": PriceBand(minimum_gbp=Decimal(value="30"), maximum_gbp=Decimal(value="250")),
    "BOTM": PriceBand(minimum_gbp=Decimal(value="15"), maximum_gbp=Decimal(value="120")),
    "AACC": PriceBand(minimum_gbp=Decimal(value="5"), maximum_gbp=Decimal(value="90")),
    # Beauty
    "SKIN": PriceBand(minimum_gbp=Decimal(value="4"), maximum_gbp=Decimal(value="65")),
    "HAIR": PriceBand(minimum_gbp=Decimal(value="3"), maximum_gbp=Decimal(value="45")),
    "BODY": PriceBand(minimum_gbp=Decimal(value="3"), maximum_gbp=Decimal(value="45")),
    # Sport
    "FITN": PriceBand(minimum_gbp=Decimal(value="8"), maximum_gbp=Decimal(value="180")),
    "RUNN": PriceBand(minimum_gbp=Decimal(value="5"), maximum_gbp=Decimal(value="80")),
    "OUTD": PriceBand(minimum_gbp=Decimal(value="10"), maximum_gbp=Decimal(value="220")),
    # Toys
    "GAME": PriceBand(minimum_gbp=Decimal(value="5"), maximum_gbp=Decimal(value="80")),
    "BUIL": PriceBand(minimum_gbp=Decimal(value="8"), maximum_gbp=Decimal(value="150")),
    "ARTS": PriceBand(minimum_gbp=Decimal(value="4"), maximum_gbp=Decimal(value="70")),
    # Office
    "STAT": PriceBand(minimum_gbp=Decimal(value="2"), maximum_gbp=Decimal(value="40")),
    "DESK": PriceBand(minimum_gbp=Decimal(value="4"), maximum_gbp=Decimal(value="100")),
    "PAPR": PriceBand(minimum_gbp=Decimal(value="2"), maximum_gbp=Decimal(value="30")),
    # Garden & DIY
    "GARD": PriceBand(minimum_gbp=Decimal(value="5"), maximum_gbp=Decimal(value="100")),
    "TOOL": PriceBand(minimum_gbp=Decimal(value="5"), maximum_gbp=Decimal(value="150")),
    "OUTL": PriceBand(minimum_gbp=Decimal(value="10"), maximum_gbp=Decimal(value="200")),
}
