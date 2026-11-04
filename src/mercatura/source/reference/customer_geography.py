from dataclasses import dataclass

"""
===============================================================================================

CUSTOMER GEOGRAPHY DEFINITIONS

===============================================================================================

Customers obviously exist in many different locations in not only one market region.

Here I am creating a CustomerGeography dataclass to contain attributes describing the 
geographical location of the customer including:

- The customers market_code (what geographic market region is the customer in)
- The city the customer is registered to live in
- The region the customer lives in.

===============================================================================================
"""


@dataclass(frozen=True, slots=True)
class CustomerGeography:
    market_code: str
    city: str
    region: str


CUSTOMER_GEOGRAPHIES: tuple[CustomerGeography, ...] = (
    # ================================================================================
    # United Kingdom
    # ================================================================================
    CustomerGeography(
        market_code="GB",
        city="London",
        region="England",
    ),
    CustomerGeography(
        market_code="GB",
        city="Nottingham",
        region="England",
    ),
    CustomerGeography(
        market_code="GB",
        city="Manchester",
        region="England",
    ),
    CustomerGeography(
        market_code="GB",
        city="Birmingham",
        region="England",
    ),
    CustomerGeography(
        market_code="GB",
        city="Glasgow",
        region="Scotland",
    ),
    # ================================================================================
    # Germany
    # ================================================================================
    CustomerGeography(
        market_code="DE",
        city="Berlin",
        region="Berlin",
    ),
    CustomerGeography(
        market_code="DE",
        city="Hamburg",
        region="Hamburg",
    ),
    CustomerGeography(
        market_code="DE",
        city="Munich",
        region="Bavaria",
    ),
    CustomerGeography(
        market_code="DE",
        city="Frankfurt",
        region="Hesse",
    ),
    CustomerGeography(
        market_code="DE",
        city="Cologne",
        region="North Rhine-Westphalia",
    ),
    # ================================================================================
    # United States
    # ================================================================================
    CustomerGeography(
        market_code="US",
        city="New York",
        region="New York",
    ),
    CustomerGeography(
        market_code="US",
        city="Chicago",
        region="Illinois",
    ),
    CustomerGeography(
        market_code="US",
        city="Los Angeles",
        region="California",
    ),
    CustomerGeography(
        market_code="US",
        city="Dallas",
        region="Texas",
    ),
    CustomerGeography(
        market_code="US",
        city="Atlanta",
        region="Georgia",
    ),
    # ================================================================================
    # China
    # ================================================================================
    CustomerGeography(
        market_code="CN",
        city="Shanghai",
        region="Shanghai",
    ),
    CustomerGeography(
        market_code="CN",
        city="Beijing",
        region="Beijing",
    ),
    CustomerGeography(
        market_code="CN",
        city="Guangzhou",
        region="Guangdong",
    ),
    CustomerGeography(
        market_code="CN",
        city="Chengdu",
        region="Sichuan",
    ),
    CustomerGeography(
        market_code="CN",
        city="Shenzhen",
        region="Guangdong",
    ),
    # ================================================================================
    # Norway
    # ================================================================================
    CustomerGeography(
        market_code="NO",
        city="Oslo",
        region="Oslo",
    ),
    CustomerGeography(
        market_code="NO",
        city="Bergen",
        region="Vestland",
    ),
    CustomerGeography(
        market_code="NO",
        city="Trondheim",
        region="Trøndelag",
    ),
    # ================================================================================
    # Russia
    # ================================================================================
    CustomerGeography(
        market_code="RU",
        city="Moscow",
        region="Moscow",
    ),
    CustomerGeography(
        market_code="RU",
        city="Saint Petersburg",
        region="Saint Petersburg",
    ),
    CustomerGeography(
        market_code="RU",
        city="Yekaterinburg",
        region="Sverdlovsk",
    ),
    CustomerGeography(
        market_code="RU",
        city="Kazan",
        region="Tatarstan",
    ),
    # ================================================================================
    # Japan
    # ================================================================================
    CustomerGeography(
        market_code="JP",
        city="Tokyo",
        region="Tokyo",
    ),
    CustomerGeography(
        market_code="JP",
        city="Osaka",
        region="Osaka",
    ),
    CustomerGeography(
        market_code="JP",
        city="Nagoya",
        region="Aichi",
    ),
    CustomerGeography(
        market_code="JP",
        city="Fukuoka",
        region="Fukuoka",
    ),
    # ================================================================================
    # South Korea
    # ================================================================================
    CustomerGeography(
        market_code="KR",
        city="Seoul",
        region="Seoul",
    ),
    CustomerGeography(
        market_code="KR",
        city="Busan",
        region="Busan",
    ),
    CustomerGeography(
        market_code="KR",
        city="Incheon",
        region="Incheon",
    ),
    CustomerGeography(
        market_code="KR",
        city="Daegu",
        region="Daegu",
    ),
    # ================================================================================
    # France
    # ================================================================================
    CustomerGeography(
        market_code="FR",
        city="Paris",
        region="Île-de-France",
    ),
    CustomerGeography(
        market_code="FR",
        city="Lyon",
        region="Auvergne-Rhône-Alpes",
    ),
    CustomerGeography(
        market_code="FR",
        city="Lille",
        region="Hauts-de-France",
    ),
    CustomerGeography(
        market_code="FR",
        city="Marseille",
        region="Provence-Alpes-Côte d'Azur",
    ),
    CustomerGeography(
        market_code="FR",
        city="Toulouse",
        region="Occitanie",
    ),
    # ================================================================================
    # Netherlands
    # ================================================================================
    CustomerGeography(
        market_code="NL",
        city="Amsterdam",
        region="North Holland",
    ),
    CustomerGeography(
        market_code="NL",
        city="Rotterdam",
        region="South Holland",
    ),
    CustomerGeography(
        market_code="NL",
        city="Utrecht",
        region="Utrecht",
    ),
    CustomerGeography(
        market_code="NL",
        city="Eindhoven",
        region="North Brabant",
    ),
    # ================================================================================
    # Poland
    # ================================================================================
    CustomerGeography(
        market_code="PL",
        city="Warsaw",
        region="Masovian",
    ),
    CustomerGeography(
        market_code="PL",
        city="Kraków",
        region="Lesser Poland",
    ),
    CustomerGeography(
        market_code="PL",
        city="Poznań",
        region="Greater Poland",
    ),
    CustomerGeography(
        market_code="PL",
        city="Wrocław",
        region="Lower Silesian",
    ),
    CustomerGeography(
        market_code="PL",
        city="Gdańsk",
        region="Pomeranian",
    ),
)
