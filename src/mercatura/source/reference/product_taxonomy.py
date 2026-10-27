from dataclasses import dataclass

"""
==========================================================================================

PRODUCT TAXONOMY DEFINITIONS

==========================================================================================

The product category dataclass has the following attributes:

- department_code: a code use to identify the associated department associate with the
product
- department_nameL the name of the product department
- category_code: an identifying code for the category of product
- category_name: the product category
- subcategory_code: an identification code for subcategories associated with the product
- subcategory_name: the name of the product subcategories
- product_terms: terms associated with the overarching product
- materials: associated materials the product has constructed from
- colour_applicable: if colours of products are part of the catalogue
- unit_of_measure: measure of product, default to "EACH"
- weight: adjusts the prevelence of subcategories in the catalogue

-----------------------------------------------------------------------------------------

The taxonomy spans 30 subcatagories over 9 departments.

==========================================================================================
"""


@dataclass(frozen=True, slots=True)
class ProductCategory:
    department_code: str
    department_name: str
    category_code: str
    category_name: str
    subcategory_code: str
    subcategory_name: str
    product_terms: tuple[str, ...]
    materials: tuple[str, ...] = ()
    colour_applicable: bool = True
    unit_of_measure: str = "EACH"
    weight: int = 1


PRODUCT_TAXONOMY: tuple[ProductCategory, ...] = (
    # ------------------------------------------------------------------
    # Electronics
    # ------------------------------------------------------------------
    ProductCategory(
        department_code="ELEC",
        department_name="Electronics",
        category_code="AUDIO",
        category_name="Audio",
        subcategory_code="HEAD",
        subcategory_name="Headphones",
        product_terms=(
            "Wireless Headphones",
            "Over-Ear Headphones",
            "In-Ear Headphones",
            "Noise-Cancelling Headphones",
            "Gaming Headset",
        ),
        materials=("Plastic", "Aluminium", "Composite"),
        weight=3,
    ),
    ProductCategory(
        department_code="ELEC",
        department_name="Electronics",
        category_code="AUDIO",
        category_name="Audio",
        subcategory_code="SPKR",
        subcategory_name="Speakers",
        product_terms=(
            "Bluetooth Speaker",
            "Portable Speaker",
            "Bookshelf Speaker",
            "Soundbar",
            "Smart Speaker",
        ),
        materials=("Plastic", "Aluminium", "Fabric"),
        weight=2,
    ),
    ProductCategory(
        department_code="ELEC",
        department_name="Electronics",
        category_code="COMP",
        category_name="Computing",
        subcategory_code="CACC",
        subcategory_name="Computer Accessories",
        product_terms=(
            "Wireless Mouse",
            "Mechanical Keyboard",
            "USB-C Hub",
            "Laptop Stand",
            "Webcam",
            "Docking Station",
        ),
        materials=("Plastic", "Aluminium", "Composite"),
        weight=3,
    ),
    ProductCategory(
        department_code="ELEC",
        department_name="Electronics",
        category_code="MOBILE",
        category_name="Mobile Accessories",
        subcategory_code="MACC",
        subcategory_name="Mobile Accessories",
        product_terms=(
            "Phone Case",
            "Wireless Charger",
            "Power Bank",
            "Charging Cable",
            "Phone Stand",
        ),
        materials=("Plastic", "Silicone", "Aluminium"),
        weight=3,
    ),
    # ------------------------------------------------------------------
    # Home
    # ------------------------------------------------------------------
    ProductCategory(
        department_code="HOME",
        department_name="Home",
        category_code="BED",
        category_name="Bedding",
        subcategory_code="BEDD",
        subcategory_name="Bedding",
        product_terms=(
            "Duvet Cover",
            "Fitted Sheet",
            "Pillow",
            "Bed Throw",
            "Pillowcase Set",
        ),
        materials=("Cotton", "Linen", "Polyester"),
        weight=3,
    ),
    ProductCategory(
        department_code="HOME",
        department_name="Home",
        category_code="BATH",
        category_name="Bathroom",
        subcategory_code="BATH",
        subcategory_name="Bathroom Textiles",
        product_terms=(
            "Bath Towel",
            "Hand Towel",
            "Bath Mat",
            "Shower Curtain",
            "Bath Robe",
        ),
        materials=("Cotton", "Bamboo", "Polyester"),
        weight=2,
    ),
    ProductCategory(
        department_code="HOME",
        department_name="Home",
        category_code="LIGHT",
        category_name="Lighting",
        subcategory_code="LAMP",
        subcategory_name="Lamps",
        product_terms=(
            "Table Lamp",
            "Floor Lamp",
            "Desk Lamp",
            "Pendant Light",
            "Wall Light",
        ),
        materials=("Steel", "Aluminium", "Glass", "Wood"),
        weight=2,
    ),
    ProductCategory(
        department_code="HOME",
        department_name="Home",
        category_code="STOR",
        category_name="Storage",
        subcategory_code="HSTR",
        subcategory_name="Home Storage",
        product_terms=(
            "Storage Basket",
            "Storage Box",
            "Shelving Unit",
            "Drawer Organiser",
            "Clothes Rack",
        ),
        materials=("Plastic", "Steel", "Wood", "Fabric"),
        weight=3,
    ),
    ProductCategory(
        department_code="HOME",
        department_name="Home",
        category_code="DECOR",
        category_name="Home Decor",
        subcategory_code="DECO",
        subcategory_name="Decorative Accessories",
        product_terms=(
            "Decorative Vase",
            "Wall Mirror",
            "Photo Frame",
            "Candle Holder",
            "Decorative Cushion",
        ),
        materials=("Glass", "Ceramic", "Wood", "Metal"),
        weight=2,
    ),
    # ------------------------------------------------------------------
    # Kitchen
    # ------------------------------------------------------------------
    ProductCategory(
        department_code="KIT",
        department_name="Kitchen",
        category_code="COOK",
        category_name="Cookware",
        subcategory_code="CKWR",
        subcategory_name="Cookware",
        product_terms=(
            "Frying Pan",
            "Saucepan",
            "Stock Pot",
            "Casserole Dish",
            "Wok",
        ),
        materials=("Stainless Steel", "Aluminium", "Cast Iron"),
        colour_applicable=False,
        weight=3,
    ),
    ProductCategory(
        department_code="KIT",
        department_name="Kitchen",
        category_code="BAKE",
        category_name="Bakeware",
        subcategory_code="BAKE",
        subcategory_name="Bakeware",
        product_terms=(
            "Baking Tray",
            "Cake Tin",
            "Loaf Tin",
            "Muffin Tray",
            "Roasting Dish",
        ),
        materials=("Steel", "Aluminium", "Silicone"),
        colour_applicable=False,
        weight=2,
    ),
    ProductCategory(
        department_code="KIT",
        department_name="Kitchen",
        category_code="TABLE",
        category_name="Tableware",
        subcategory_code="TBLW",
        subcategory_name="Tableware",
        product_terms=(
            "Dinner Plate Set",
            "Ceramic Mug",
            "Glass Tumbler Set",
            "Cutlery Set",
            "Serving Bowl",
        ),
        materials=("Ceramic", "Glass", "Stainless Steel"),
        weight=3,
    ),
    ProductCategory(
        department_code="KIT",
        department_name="Kitchen",
        category_code="TOOLS",
        category_name="Kitchen Tools",
        subcategory_code="KTUL",
        subcategory_name="Kitchen Utensils",
        product_terms=(
            "Chef Knife",
            "Chopping Board",
            "Kitchen Utensil Set",
            "Kitchen Scales",
            "Food Grater",
        ),
        materials=("Stainless Steel", "Wood", "Plastic"),
        weight=2,
    ),
    # ------------------------------------------------------------------
    # Apparel
    # ------------------------------------------------------------------
    ProductCategory(
        department_code="APP",
        department_name="Apparel",
        category_code="TOPS",
        category_name="Tops",
        subcategory_code="TOP",
        subcategory_name="Tops",
        product_terms=(
            "Cotton T-Shirt",
            "Oxford Shirt",
            "Polo Shirt",
            "Long-Sleeve Top",
            "Casual Shirt",
        ),
        materials=("Cotton", "Linen", "Polyester"),
        weight=4,
    ),
    ProductCategory(
        department_code="APP",
        department_name="Apparel",
        category_code="KNIT",
        category_name="Knitwear",
        subcategory_code="KNIT",
        subcategory_name="Knitwear",
        product_terms=(
            "Crew-Neck Sweater",
            "Cardigan",
            "Roll-Neck Sweater",
            "Knitted Vest",
            "Zip Sweater",
        ),
        materials=("Cotton", "Wool", "Merino Wool", "Acrylic"),
        weight=3,
    ),
    ProductCategory(
        department_code="APP",
        department_name="Apparel",
        category_code="OUTER",
        category_name="Outerwear",
        subcategory_code="OUTR",
        subcategory_name="Outerwear",
        product_terms=(
            "Rain Jacket",
            "Puffer Jacket",
            "Wool Coat",
            "Lightweight Jacket",
            "Parka",
        ),
        materials=("Polyester", "Nylon", "Wool"),
        weight=3,
    ),
    ProductCategory(
        department_code="APP",
        department_name="Apparel",
        category_code="BOTTOM",
        category_name="Bottoms",
        subcategory_code="BOTM",
        subcategory_name="Trousers and Bottoms",
        product_terms=(
            "Chino Trousers",
            "Straight-Leg Jeans",
            "Joggers",
            "Cargo Trousers",
            "Tailored Trousers",
        ),
        materials=("Cotton", "Denim", "Polyester"),
        weight=3,
    ),
    ProductCategory(
        department_code="APP",
        department_name="Apparel",
        category_code="ACCESS",
        category_name="Accessories",
        subcategory_code="AACC",
        subcategory_name="Apparel Accessories",
        product_terms=(
            "Baseball Cap",
            "Knitted Scarf",
            "Leather Belt",
            "Beanie",
            "Gloves",
        ),
        materials=("Cotton", "Wool", "Leather", "Polyester"),
        weight=2,
    ),
    # ------------------------------------------------------------------
    # Beauty and personal care
    # ------------------------------------------------------------------
    ProductCategory(
        department_code="BEAU",
        department_name="Beauty",
        category_code="SKIN",
        category_name="Skincare",
        subcategory_code="SKIN",
        subcategory_name="Skincare",
        product_terms=(
            "Facial Cleanser",
            "Daily Moisturiser",
            "Hydrating Serum",
            "Face Cream",
            "Eye Cream",
        ),
        colour_applicable=False,
        weight=3,
    ),
    ProductCategory(
        department_code="BEAU",
        department_name="Beauty",
        category_code="HAIR",
        category_name="Haircare",
        subcategory_code="HAIR",
        subcategory_name="Haircare",
        product_terms=(
            "Daily Shampoo",
            "Conditioner",
            "Hair Mask",
            "Styling Cream",
            "Hair Serum",
        ),
        colour_applicable=False,
        weight=2,
    ),
    ProductCategory(
        department_code="BEAU",
        department_name="Beauty",
        category_code="BODY",
        category_name="Body Care",
        subcategory_code="BODY",
        subcategory_name="Body Care",
        product_terms=(
            "Body Lotion",
            "Hand Cream",
            "Body Wash",
            "Body Scrub",
            "Hand Wash",
        ),
        colour_applicable=False,
        weight=2,
    ),
    # ------------------------------------------------------------------
    # Sport and outdoors
    # ------------------------------------------------------------------
    ProductCategory(
        department_code="SPORT",
        department_name="Sport",
        category_code="FIT",
        category_name="Fitness",
        subcategory_code="FITN",
        subcategory_name="Fitness Equipment",
        product_terms=(
            "Yoga Mat",
            "Resistance Band Set",
            "Dumbbell Set",
            "Foam Roller",
            "Training Mat",
        ),
        materials=("Rubber", "Foam", "Steel", "Composite"),
        weight=3,
    ),
    ProductCategory(
        department_code="SPORT",
        department_name="Sport",
        category_code="RUN",
        category_name="Running",
        subcategory_code="RUNN",
        subcategory_name="Running Accessories",
        product_terms=(
            "Running Belt",
            "Running Bottle",
            "Running Cap",
            "Arm Phone Holder",
            "Reflective Vest",
        ),
        materials=("Polyester", "Nylon", "Plastic"),
        weight=2,
    ),
    ProductCategory(
        department_code="SPORT",
        department_name="Sport",
        category_code="OUTDOOR",
        category_name="Outdoor",
        subcategory_code="OUTD",
        subcategory_name="Outdoor Equipment",
        product_terms=(
            "Day Backpack",
            "Insulated Bottle",
            "Camping Chair",
            "Hiking Pole Set",
            "Camping Lantern",
        ),
        materials=("Nylon", "Aluminium", "Steel", "Plastic"),
        weight=3,
    ),
    # ------------------------------------------------------------------
    # Toys
    # ------------------------------------------------------------------
    ProductCategory(
        department_code="TOYS",
        department_name="Toys",
        category_code="GAMES",
        category_name="Games",
        subcategory_code="GAME",
        subcategory_name="Games and Puzzles",
        product_terms=(
            "Strategy Board Game",
            "Family Card Game",
            "Jigsaw Puzzle",
            "Trivia Game",
            "Puzzle Game",
        ),
        materials=("Cardboard", "Paper", "Plastic"),
        colour_applicable=False,
        weight=2,
    ),
    ProductCategory(
        department_code="TOYS",
        department_name="Toys",
        category_code="BUILD",
        category_name="Construction Toys",
        subcategory_code="BUIL",
        subcategory_name="Construction Toys",
        product_terms=(
            "Building Block Set",
            "Construction Kit",
            "Model Building Set",
            "Magnetic Building Set",
            "Engineering Kit",
        ),
        materials=("Plastic", "Wood", "Metal"),
        weight=2,
    ),
    ProductCategory(
        department_code="TOYS",
        department_name="Toys",
        category_code="ART",
        category_name="Arts and Crafts",
        subcategory_code="ARTS",
        subcategory_name="Arts and Crafts",
        product_terms=(
            "Painting Set",
            "Craft Kit",
            "Drawing Set",
            "Modelling Clay Set",
            "Colouring Set",
        ),
        materials=("Paper", "Plastic", "Wood"),
        weight=2,
    ),
    # ------------------------------------------------------------------
    # Office
    # ------------------------------------------------------------------
    ProductCategory(
        department_code="OFF",
        department_name="Office",
        category_code="STAT",
        category_name="Stationery",
        subcategory_code="STAT",
        subcategory_name="Stationery",
        product_terms=(
            "Hardcover Notebook",
            "Ballpoint Pen Set",
            "Weekly Planner",
            "Sketchbook",
            "Sticky Note Set",
        ),
        materials=("Paper", "Cardboard", "Plastic"),
        weight=3,
    ),
    ProductCategory(
        department_code="OFF",
        department_name="Office",
        category_code="DESK",
        category_name="Desk Accessories",
        subcategory_code="DESK",
        subcategory_name="Desk Accessories",
        product_terms=(
            "Desk Organiser",
            "Document Tray",
            "Pen Holder",
            "Laptop Riser",
            "Desk Mat",
        ),
        materials=("Plastic", "Metal", "Wood", "Leather"),
        weight=2,
    ),
    ProductCategory(
        department_code="OFF",
        department_name="Office",
        category_code="PAPER",
        category_name="Paper Products",
        subcategory_code="PAPR",
        subcategory_name="Paper Products",
        product_terms=(
            "Printer Paper",
            "Index Card Pack",
            "Envelope Pack",
            "Writing Pad",
            "Presentation Card",
        ),
        materials=("Paper",),
        colour_applicable=False,
        unit_of_measure="PACK",
        weight=2,
    ),
    # ------------------------------------------------------------------
    # Garden and DIY
    # ------------------------------------------------------------------
    ProductCategory(
        department_code="GARD",
        department_name="Garden & DIY",
        category_code="GARDEN",
        category_name="Gardening",
        subcategory_code="GARD",
        subcategory_name="Gardening",
        product_terms=(
            "Plant Pot",
            "Watering Can",
            "Garden Trowel",
            "Plant Mister",
            "Garden Planter",
        ),
        materials=("Plastic", "Steel", "Ceramic"),
        weight=2,
    ),
    ProductCategory(
        department_code="GARD",
        department_name="Garden & DIY",
        category_code="TOOLS",
        category_name="Tools",
        subcategory_code="TOOL",
        subcategory_name="Hand Tools",
        product_terms=(
            "Screwdriver Set",
            "Claw Hammer",
            "Adjustable Wrench",
            "Pliers Set",
            "Tape Measure",
        ),
        materials=("Steel", "Rubber", "Plastic"),
        colour_applicable=False,
        weight=2,
    ),
    ProductCategory(
        department_code="GARD",
        department_name="Garden & DIY",
        category_code="OUTLIVE",
        category_name="Outdoor Living",
        subcategory_code="OUTL",
        subcategory_name="Outdoor Living",
        product_terms=(
            "Outdoor Cushion",
            "Garden Lantern",
            "Folding Chair",
            "Picnic Blanket",
            "Outdoor Storage Box",
        ),
        materials=("Polyester", "Steel", "Plastic", "Wood"),
        weight=2,
    ),
)

# Overwrides so products have materials that make sense
PRODUCT_MATERIAL_OVERRIDES: dict[str, tuple[str, ...]] = {
    # Kitchen tools
    "Chef Knife": ("Stainless Steel",),
    "Chopping Board": (
        "Wood",
        "Plastic",
    ),
    "Kitchen Utensil Set": (
        "Stainless Steel",
        "Wood",
        "Plastic",
    ),
    "Kitchen Scales": (
        "Plastic",
        "Stainless Steel",
        "Glass",
    ),
    "Food Grater": (
        "Stainless Steel",
        "Plastic",
    ),
    # Fitness
    "Yoga Mat": (
        "Rubber",
        "Foam",
    ),
    "Resistance Band Set": (
        "Rubber",
        "Elastic",
    ),
    "Dumbbell Set": (
        "Steel",
        "Cast Iron",
        "Rubber",
    ),
    "Foam Roller": (
        "Foam",
        "Plastic",
    ),
    "Training Mat": (
        "Rubber",
        "Foam",
    ),
    # Stationery
    "Hardcover Notebook": (
        "Paper",
        "Cardboard",
    ),
    "Ballpoint Pen Set": (
        "Plastic",
        "Metal",
    ),
    "Weekly Planner": (
        "Paper",
        "Cardboard",
    ),
    "Sketchbook": (
        "Paper",
        "Cardboard",
    ),
    "Sticky Note Set": ("Paper",),
}
