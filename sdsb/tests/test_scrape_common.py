from scrape_common import (
    html_to_text,
    to_dollars,
    is_listable_plant,
    looks_like_seed,
    resolve_kind,
)


def _plant(**over):
    base = {"name": "Passion Fruit Vine", "type": "Vines", "price": 24.0}
    base.update(over)
    return base


def test_is_listable_plant_keeps_priced_plant():
    assert is_listable_plant(_plant()) is True


def test_is_listable_plant_drops_zero_and_none_price():
    assert is_listable_plant(_plant(price=0)) is False
    assert is_listable_plant(_plant(price=None)) is False


def test_is_listable_plant_drops_merch_by_name_or_type():
    assert is_listable_plant(_plant(name="Gift Card")) is False         # phrase
    assert is_listable_plant(_plant(name="E-Gift Card")) is False        # phrase
    assert is_listable_plant(_plant(name="Logo Sticker")) is False       # word
    assert is_listable_plant(_plant(type="Books")) is False              # word (plural)
    assert is_listable_plant(_plant(name="Flat Rate Shipping")) is False
    assert is_listable_plant(_plant(name="Ceramic Pottery")) is False


def test_is_listable_plant_keeps_real_plants_that_contain_merch_substrings():
    # word-boundary matching must NOT drop real plant names merely CONTAINING a term
    assert is_listable_plant(_plant(name="Mugwort", type="Herb")) is True
    assert is_listable_plant(_plant(name="Hatiora salicornioides", type="Cactus")) is True
    assert is_listable_plant(_plant(name="Bookleaf Pine", type="Tree")) is True


def test_is_listable_plant_drops_negative_price():
    assert is_listable_plant(_plant(price=-5.0)) is False


def test_is_listable_plant_drops_greeting_and_note_cards():
    # plant nurseries mix in seed-paper stationery — not a plant, not a seed
    assert is_listable_plant(_plant(name="Seed Paper Greeting Card", type="Accessory")) is False
    assert is_listable_plant(_plant(name="Wildflower Seed Paper Note Card", type="Greeting Cards")) is False


def test_is_listable_plant_drops_soil_top_dressing():
    # succulent stores list pumice/pebble top-dressing supplies — not live plants
    assert is_listable_plant(_plant(name="Grid Top Soil Dressing Pebbles", type="top dressing")) is False
    assert is_listable_plant(_plant(name="Horticultural Pumice Seed Starter", type="top dressing")) is False


# ---- looks_like_seed: seed inventory carried by a plant-kind source --------- #
def test_looks_like_seed_flags_seed_packs_and_loose_seed():
    assert looks_like_seed({"name": "Serrano Hot Pepper Seed Pack", "type": "Seeds & Seed Kits"}) is True
    assert looks_like_seed({"name": "Salvia columbariae Chia - Seed", "type": "Seed"}) is True
    # real loose seed that a nursery mis-typed as 'Annual' — caught via the name word
    assert looks_like_seed({"name": "Foothill Clover Annual 1tsp. Seed", "type": "Annual"}) is True


def test_looks_like_seed_ignores_live_plant_name_compounds():
    # 'seedless' / 'seedling' / 'hopseed' / 'dotseed' tokenize away from 'seed' -> live plants
    assert looks_like_seed({"name": "Grape Thompson Seedless", "type": "Fruit and Citrus"}) is False
    assert looks_like_seed({"name": "Cherimoya (Seedling)", "type": "Fruit and Citrus"}) is False
    assert looks_like_seed({"name": "Green Hopseed Bush", "type": "Shrubs"}) is False
    assert looks_like_seed({"name": "Dotseed Plantain", "type": "Annual"}) is False
    assert looks_like_seed({"name": "Chiltepin Chili Pepper", "type": "Fruit and Citrus"}) is False


def test_looks_like_seed_ignores_seo_breadcrumb_product_type():
    # Plants Express stuffs product_type with an SEO breadcrumb; a live plant whose
    # breadcrumb merely mentions "creeping thyme seeds" must NOT become seed inventory.
    rec = {"name": "Pink Creeping Thyme",
           "type": ("groundcover > creeping thyme > Thymus serpyllum > perennials > "
                    "ground cover > creeping thyme seeds > elfin thyme > wooly thyme")}
    assert looks_like_seed(rec) is False


# ---- resolve_kind: only plant-kind sources reclassify seed inventory -------- #
def test_resolve_kind_seed_source_stays_seed():
    assert resolve_kind({"name": "Anything", "type": "x"}, "seed") == "seed"
    assert resolve_kind({"name": "Cayenne Pepper Seeds", "type": "Vegetables"}, "seed") == "seed"


def test_resolve_kind_plant_source_reclassifies_seed_inventory():
    assert resolve_kind({"name": "Serrano Hot Pepper Seed Pack", "type": "Seeds & Seed Kits"}, "plant") == "seed"


def test_resolve_kind_plant_source_keeps_real_plants():
    assert resolve_kind({"name": "Chiltepin Chili Pepper", "type": "Fruit and Citrus"}, "plant") == "plant"
    assert resolve_kind({"name": "Grape Thompson Seedless", "type": "Fruit and Citrus"}, "plant") == "plant"


def test_html_to_text_paragraphs():
    assert html_to_text("<p>First para.</p><p>Second para.</p>") == "First para.\n\nSecond para."


def test_html_to_text_empty_inputs():
    assert html_to_text(None) == ""
    assert html_to_text("") == ""


def test_html_to_text_unescapes_entities():
    assert html_to_text("<p>Tom&amp;Jerry &gt; cats</p>") == "Tom&Jerry > cats"


def test_to_dollars_minor_units():
    assert to_dollars("395", 2) == 3.95
    assert to_dollars("1000", 2) == 10.0


def test_to_dollars_blank_or_none():
    assert to_dollars("", 2) is None
    assert to_dollars(None, 2) is None
