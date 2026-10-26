from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StoreLocation:
    market_code: str
    location_code: str
    city: str
    region: str
    timezone: str
    postal_prefix: str


STORE_LOCATIONS: dict[str, tuple[StoreLocation, ...]] = {
    "GB": (
        StoreLocation("GB", "LONDON", "London", "Greater London", "Europe/London", "SW1"),
        StoreLocation("GB", "BIRMINGHAM", "Birmingham", "West Midlands", "Europe/London", "B1"),
        StoreLocation(
            "GB", "MANCHESTER", "Manchester", "Greater Manchester", "Europe/London", "M1"
        ),
        StoreLocation("GB", "LEEDS", "Leeds", "West Yorkshire", "Europe/London", "LS1"),
        StoreLocation("GB", "GLASGOW", "Glasgow", "Glasgow City", "Europe/London", "G1"),
        StoreLocation("GB", "EDINBURGH", "Edinburgh", "City of Edinburgh", "Europe/London", "EH1"),
        StoreLocation("GB", "LIVERPOOL", "Liverpool", "Merseyside", "Europe/London", "L1"),
        StoreLocation("GB", "BRISTOL", "Bristol", "Bristol", "Europe/London", "BS1"),
        StoreLocation("GB", "SHEFFIELD", "Sheffield", "South Yorkshire", "Europe/London", "S1"),
        StoreLocation(
            "GB",
            "NEWCASTLE",
            "Newcastle upon Tyne",
            "Tyne and Wear",
            "Europe/London",
            "NE1",
        ),
        StoreLocation("GB", "NOTTINGHAM", "Nottingham", "Nottinghamshire", "Europe/London", "NG1"),
        StoreLocation("GB", "CARDIFF", "Cardiff", "Cardiff", "Europe/London", "CF10"),
    ),
    "DE": (
        StoreLocation("DE", "BERLIN", "Berlin", "Berlin", "Europe/Berlin", "101"),
        StoreLocation("DE", "HAMBURG", "Hamburg", "Hamburg", "Europe/Berlin", "200"),
        StoreLocation("DE", "MUNICH", "München", "Bayern", "Europe/Berlin", "803"),
        StoreLocation("DE", "COLOGNE", "Köln", "Nordrhein-Westfalen", "Europe/Berlin", "506"),
        StoreLocation("DE", "FRANKFURT", "Frankfurt am Main", "Hessen", "Europe/Berlin", "603"),
        StoreLocation(
            "DE",
            "STUTTGART",
            "Stuttgart",
            "Baden-Württemberg",
            "Europe/Berlin",
            "701",
        ),
        StoreLocation(
            "DE",
            "DUSSELDORF",
            "Düsseldorf",
            "Nordrhein-Westfalen",
            "Europe/Berlin",
            "402",
        ),
    ),
    "US": (
        StoreLocation("US", "NEW_YORK", "New York", "New York", "America/New_York", "100"),
        StoreLocation("US", "CHICAGO", "Chicago", "Illinois", "America/Chicago", "606"),
        StoreLocation(
            "US",
            "LOS_ANGELES",
            "Los Angeles",
            "California",
            "America/Los_Angeles",
            "900",
        ),
        StoreLocation("US", "HOUSTON", "Houston", "Texas", "America/Chicago", "770"),
        StoreLocation("US", "PHOENIX", "Phoenix", "Arizona", "America/Phoenix", "850"),
        StoreLocation("US", "SEATTLE", "Seattle", "Washington", "America/Los_Angeles", "981"),
        StoreLocation("US", "DENVER", "Denver", "Colorado", "America/Denver", "802"),
        StoreLocation("US", "MIAMI", "Miami", "Florida", "America/New_York", "331"),
    ),
    "CN": (
        StoreLocation("CN", "BEIJING", "北京", "北京市", "Asia/Shanghai", "100"),
        StoreLocation("CN", "SHANGHAI", "上海", "上海市", "Asia/Shanghai", "200"),
        StoreLocation("CN", "SHENZHEN", "深圳", "广东省", "Asia/Shanghai", "518"),
        StoreLocation("CN", "GUANGZHOU", "广州", "广东省", "Asia/Shanghai", "510"),
        StoreLocation("CN", "CHENGDU", "成都", "四川省", "Asia/Shanghai", "610"),
        StoreLocation("CN", "WUHAN", "武汉", "湖北省", "Asia/Shanghai", "430"),
    ),
    "NO": (
        StoreLocation("NO", "OSLO", "Oslo", "Oslo", "Europe/Oslo", "01"),
        StoreLocation("NO", "BERGEN", "Bergen", "Vestland", "Europe/Oslo", "50"),
        StoreLocation("NO", "TRONDHEIM", "Trondheim", "Trøndelag", "Europe/Oslo", "70"),
    ),
    "RU": (
        StoreLocation("RU", "MOSCOW", "Москва", "Москва", "Europe/Moscow", "101"),
        StoreLocation(
            "RU",
            "SAINT_PETERSBURG",
            "Санкт-Петербург",
            "Санкт-Петербург",
            "Europe/Moscow",
            "190",
        ),
        StoreLocation(
            "RU",
            "YEKATERINBURG",
            "Екатеринбург",
            "Свердловская область",
            "Asia/Yekaterinburg",
            "620",
        ),
        StoreLocation(
            "RU",
            "NOVOSIBIRSK",
            "Новосибирск",
            "Новосибирская область",
            "Asia/Novosibirsk",
            "630",
        ),
    ),
    "JP": (
        StoreLocation("JP", "TOKYO", "東京", "東京都", "Asia/Tokyo", "100"),
        StoreLocation("JP", "OSAKA", "大阪", "大阪府", "Asia/Tokyo", "530"),
        StoreLocation("JP", "YOKOHAMA", "横浜", "神奈川県", "Asia/Tokyo", "220"),
        StoreLocation("JP", "NAGOYA", "名古屋", "愛知県", "Asia/Tokyo", "450"),
        StoreLocation("JP", "FUKUOKA", "福岡", "福岡県", "Asia/Tokyo", "810"),
        StoreLocation("JP", "SAPPORO", "札幌", "北海道", "Asia/Tokyo", "060"),
    ),
    "KR": (
        StoreLocation("KR", "SEOUL", "서울", "서울특별시", "Asia/Seoul", "03"),
        StoreLocation("KR", "BUSAN", "부산", "부산광역시", "Asia/Seoul", "48"),
        StoreLocation("KR", "INCHEON", "인천", "인천광역시", "Asia/Seoul", "21"),
        StoreLocation("KR", "DAEGU", "대구", "대구광역시", "Asia/Seoul", "41"),
        StoreLocation("KR", "DAEJEON", "대전", "대전광역시", "Asia/Seoul", "34"),
    ),
    "FR": (
        StoreLocation("FR", "PARIS", "Paris", "Île-de-France", "Europe/Paris", "750"),
        StoreLocation(
            "FR",
            "LYON",
            "Lyon",
            "Auvergne-Rhône-Alpes",
            "Europe/Paris",
            "690",
        ),
        StoreLocation(
            "FR",
            "MARSEILLE",
            "Marseille",
            "Provence-Alpes-Côte d'Azur",
            "Europe/Paris",
            "130",
        ),
        StoreLocation("FR", "TOULOUSE", "Toulouse", "Occitanie", "Europe/Paris", "310"),
        StoreLocation("FR", "LILLE", "Lille", "Hauts-de-France", "Europe/Paris", "590"),
        StoreLocation(
            "FR",
            "BORDEAUX",
            "Bordeaux",
            "Nouvelle-Aquitaine",
            "Europe/Paris",
            "330",
        ),
    ),
    "NL": (
        StoreLocation(
            "NL",
            "AMSTERDAM",
            "Amsterdam",
            "Noord-Holland",
            "Europe/Amsterdam",
            "101",
        ),
        StoreLocation(
            "NL",
            "ROTTERDAM",
            "Rotterdam",
            "Zuid-Holland",
            "Europe/Amsterdam",
            "301",
        ),
        StoreLocation(
            "NL",
            "THE_HAGUE",
            "Den Haag",
            "Zuid-Holland",
            "Europe/Amsterdam",
            "251",
        ),
        StoreLocation(
            "NL",
            "UTRECHT",
            "Utrecht",
            "Utrecht",
            "Europe/Amsterdam",
            "351",
        ),
    ),
    "PL": (
        StoreLocation(
            "PL",
            "WARSAW",
            "Warszawa",
            "Mazowieckie",
            "Europe/Warsaw",
            "00",
        ),
        StoreLocation(
            "PL",
            "KRAKOW",
            "Kraków",
            "Małopolskie",
            "Europe/Warsaw",
            "30",
        ),
        StoreLocation(
            "PL",
            "WROCLAW",
            "Wrocław",
            "Dolnośląskie",
            "Europe/Warsaw",
            "50",
        ),
        StoreLocation(
            "PL",
            "POZNAN",
            "Poznań",
            "Wielkopolskie",
            "Europe/Warsaw",
            "60",
        ),
        StoreLocation(
            "PL",
            "GDANSK",
            "Gdańsk",
            "Pomorskie",
            "Europe/Warsaw",
            "80",
        ),
    ),
}


def locations_for_market(
    market_code: str,
) -> tuple[StoreLocation, ...]:
    try:
        return STORE_LOCATIONS[market_code]
    except KeyError as exc:
        raise KeyError(f"no store geography configured for market: {market_code}") from exc
