"""
One-time build script: reads the raw 'Mushroom Data' folder, cleans up
filenames, copies reference images into static/img/dataset/, and writes
mushroom_info.json (the knowledge base used for report generation).

Run once: python build_dataset.py
"""
import json
import os
import re
import shutil

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "data")
DST = os.path.join(BASE, "static", "img", "dataset")
os.makedirs(DST, exist_ok=True)


def slugify(name):
    name = name.lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    return name.strip("_")


# category folder -> (category key, label, edibility, risk_level)
FOLDERS = {
    "Healthy  Edible mushrooms": ("healthy", "Healthy / Edible", "Edible", "safe"),
    "Poisonous mushrooms": ("poisonous", "Poisonous", "Not Edible - Toxic", "danger"),
    "Unhealthy  Inedible mushrooms": ("unhealthy", "Unhealthy / Inedible", "Not Recommended", "warning"),
}

# Hand-curated knowledge base built from the supplied text files
# (healthy_edible_mushrooms.txt / poisonous_mushrooms.txt / unhealthy_inedible_mushrooms.txt)
KNOWLEDGE = {
    "button_mushroom": dict(display_name="Button Mushroom", scientific_name="Agaricus bisporus",
        summary="One of the most commonly cultivated edible mushrooms worldwide.",
        details="Provides protein, B vitamins, selenium, potassium and other minerals. Should be sourced from reliable food suppliers and prepared properly.",
        sources="USDA FoodData Central; NIH Office of Dietary Supplements"),
    "oyster_mushroom": dict(display_name="Oyster Mushroom", scientific_name="Pleurotus species",
        summary="A widely cultivated edible mushroom used in many cuisines.",
        details="Provides protein, dietary fiber, B vitamins and bioactive compounds that support normal digestive function.",
        sources="USDA FoodData Central"),
    "shiitake_mushroom": dict(display_name="Shiitake Mushroom", scientific_name="Lentinula edodes",
        summary="A popular edible mushroom used in many cuisines.",
        details="Provides B vitamins, copper and selenium. Contains bioactive compounds currently being researched for immune-related effects.",
        sources="USDA FoodData Central; Memorial Sloan Kettering Cancer Center"),
    "milky_mushroom": dict(display_name="Milky Mushroom", scientific_name="Calocybe indica",
        summary="A cultivated edible mushroom commonly produced in India.",
        details="Provides protein, dietary fiber and minerals; nutrients are absorbed through normal digestion.",
        sources="ICAR; USDA FoodData Central"),
    "enoki_mushroom": dict(display_name="Enoki Mushroom", scientific_name="Flammulina filiformis",
        summary="An edible mushroom that must be cooked thoroughly.",
        details="Provides dietary fiber, B vitamins and minerals. Raw enoki has been linked to foodborne Listeria outbreaks, so thorough cooking is essential.",
        sources="FDA; USDA FoodData Central"),
    "portobello_mushroom": dict(display_name="Portobello Mushroom", scientific_name="Agaricus bisporus (mature)",
        summary="The mature form of the common button mushroom.",
        details="Provides protein, B vitamins and potassium, which contributes to normal nerve and muscle function.",
        sources="USDA FoodData Central"),
    "morel_mushroom": dict(display_name="Morel Mushroom", scientific_name="Morchella species",
        summary="Edible when correctly identified and properly cooked.",
        details="Raw or undercooked morels can cause illness, so correct identification and full cooking are essential before eating.",
        sources="FDA; Michigan State University Extension"),
    "maitake_mushroom": dict(display_name="Maitake Mushroom", scientific_name="Grifola frondosa",
        summary="An edible culinary mushroom with bioactive polysaccharides.",
        details="Research into its medicinal / immune-related effects is ongoing, but it is primarily used as a culinary ingredient.",
        sources="USDA FoodData Central; Memorial Sloan Kettering Cancer Center"),
    "lion_s_mane_mushroom": dict(display_name="Lion's Mane Mushroom", scientific_name="Hericium erinaceus",
        summary="An edible mushroom with limited human evidence for additional health claims.",
        details="Provides protein, fiber and bioactive compounds. Possible neurological effects are still being researched.",
        sources="USDA FoodData Central; Memorial Sloan Kettering Cancer Center"),
    "chanterelle_mushroom": dict(display_name="Chanterelle Mushroom", scientific_name="Cantharellus species",
        summary="Edible when correctly identified.",
        details="Provides dietary fiber, vitamins and minerals. Wild mushroom misidentification can result in poisoning, so confident ID is essential.",
        sources="USDA FoodData Central; FDA"),

    "death_cap": dict(display_name="Death Cap", scientific_name="Amanita phalloides",
        summary="No safe culinary use - can cause severe poisoning and acute liver failure.",
        details="Contains amatoxins, which inhibit RNA polymerase II and disrupt protein synthesis, mainly damaging the GI tract, liver and (in severe cases) kidneys. Symptoms often improve temporarily before serious liver injury develops.",
        sources="CDC; Merck Manual; Poison Control"),
    "destroying_angel_amanita_virosa": dict(display_name="Destroying Angel", scientific_name="Amanita virosa",
        summary="No safe culinary use - severe, delayed poisoning that can cause liver failure.",
        details="Contains amatoxins that disrupt protein production, mainly targeting the GI tract, liver and kidneys.",
        sources="CDC; Merck Manual"),
    "fly_agaric_amanita_muscaria": dict(display_name="Fly Agaric", scientific_name="Amanita muscaria",
        summary="Not recommended as food - causes neurological and gastrointestinal poisoning.",
        details="Contains ibotenic acid and muscimol, which affect brain neurotransmitter systems and can cause confusion, agitation, hallucinations and, in severe cases, seizures.",
        sources="Merck Manual; Poison Control"),
    "panther_cap_amanita_pantherina": dict(display_name="Panther Cap", scientific_name="Amanita pantherina",
        summary="No safe culinary use - causes neurological poisoning.",
        details="Contains ibotenic acid and muscimol affecting brain neurotransmitter pathways; can cause confusion, agitation and seizures in severe cases.",
        sources="Poison Control; Merck Manual"),
    "false_morel_gyromitra_esculenta": dict(display_name="False Morel", scientific_name="Gyromitra esculenta",
        summary="No safe culinary use - gyromitrin poisoning can cause seizures and liver injury.",
        details="Toxic metabolites interfere with pyridoxine-dependent neurotransmitter synthesis, targeting the GI tract, nervous system and liver.",
        sources="CDC; Poison Control"),
    "deadly_webcap_cortinarius_rubellus": dict(display_name="Deadly Webcap", scientific_name="Cortinarius rubellus",
        summary="No safe culinary use - can cause delayed, severe kidney injury.",
        details="Contains orellanine, which causes toxic injury to kidney tissue; symptoms can be delayed by days.",
        sources="Poison Control; Merck Manual"),
    "fool_s_webcap_cortinarius_orellanus": dict(display_name="Fool's Webcap", scientific_name="Cortinarius orellanus",
        summary="No safe culinary use - delayed renal poisoning.",
        details="Contains orellanine, causing toxic injury to kidney tissue that can require dialysis in severe cases.",
        sources="Poison Control; Merck Manual"),
    "jack_o_lantern_mushroom_omphalotus_olearius": dict(display_name="Jack-o'-Lantern Mushroom", scientific_name="Omphalotus olearius",
        summary="No safe culinary use - causes gastrointestinal poisoning.",
        details="Contains gastrointestinal toxic compounds that irritate the stomach and intestines, causing nausea, vomiting and cramps.",
        sources="Poison Control; FDA"),
    "deadly_dapperling_lepiota_brunneoincarnata": dict(display_name="Deadly Dapperling", scientific_name="Lepiota brunneoincarnata",
        summary="No safe culinary use - can cause severe delayed liver toxicity.",
        details="Contains amatoxins that inhibit RNA polymerase II and disrupt protein synthesis, causing delayed liver injury that can progress to failure.",
        sources="Poison Control; Merck Manual"),

    "false_morel": dict(display_name="False Morel (look-alike)", scientific_name="Gyromitra species",
        summary="Not recommended as food - some false morels contain gyromitrin.",
        details="Should not be confused with true edible morels. Gyromitrin can cause serious poisoning affecting the GI tract, nervous system and (in severe cases) liver.",
        sources="CDC; FDA; Poison Control"),
    "ink_cap_mushroom": dict(display_name="Ink Cap Mushroom", scientific_name="Coprinopsis species",
        summary="Toxicity differs between species - unknown wild specimens should be avoided.",
        details="Some species contain coprine, which produces an alcohol-related toxic reaction (flushing, nausea, palpitations, low blood pressure) if consumed with alcohol.",
        sources="Merck Manual; Poison Control"),
    "some_boletus_species": dict(display_name="Boletus species (unidentified)", scientific_name="Boletus spp.",
        summary="Some boletes are edible, some are toxic - never eat one based on appearance alone.",
        details="Toxic species can cause gastrointestinal poisoning of varying severity; confident species-level identification is required before eating.",
        sources="FDA; Poison Control"),
    "some_lactarius_species": dict(display_name="Lactarius species (unidentified)", scientific_name="Lactarius spp.",
        summary="Some species are edible after preparation, others are irritating - do not eat unidentified specimens.",
        details="Acrid or irritating species can cause gastrointestinal illness including nausea, vomiting and diarrhea.",
        sources="Poison Control; regional mycology guidance"),
    "some_russula_species": dict(display_name="Russula species (unidentified)", scientific_name="Russula spp.",
        summary="Edibility varies by species - the genus name alone cannot determine safety.",
        details="Certain species can cause gastrointestinal irritation such as nausea, vomiting, abdominal pain and diarrhea.",
        sources="Poison Control; regional mycology guidance"),
    "wood_ear_look_alikes": dict(display_name="Wood Ear look-alike", scientific_name="Auricularia spp. (unconfirmed)",
        summary="True Auricularia can be edible, but wild look-alikes require reliable identification.",
        details="Misidentification may result in eating a toxic species; effects depend entirely on the actual species involved.",
        sources="FDA; Poison Control"),
}

records = []
for folder, (cat_key, cat_label, edibility, risk) in FOLDERS.items():
    folder_path = os.path.join(SRC, folder)
    if not os.path.isdir(folder_path):
        continue
    for fname in sorted(os.listdir(folder_path)):
        fpath = os.path.join(folder_path, fname)
        if not os.path.isfile(fpath):
            continue
        base, ext = os.path.splitext(fname)
        # normalise mangled unicode escapes left over from the zip (e.g. #U2019, #U2014)
        clean_base = base.replace("#U2019", "'").replace("#U2014", "-")
        slug = slugify(clean_base)
        dst_name = f"{slug}{ext.lower()}"
        shutil.copy2(fpath, os.path.join(DST, dst_name))

        info = KNOWLEDGE.get(slug, {})
        records.append({
            "id": slug,
            "image": f"img/dataset/{dst_name}",
            "category": cat_key,
            "category_label": cat_label,
            "edibility": edibility,
            "risk_level": risk,
            "display_name": info.get("display_name", clean_base.title()),
            "scientific_name": info.get("scientific_name", "Unidentified species"),
            "summary": info.get("summary", ""),
            "details": info.get("details", ""),
            "sources": info.get("sources", ""),
        })

with open(os.path.join(BASE, "mushroom_info.json"), "w", encoding="utf-8") as f:
    json.dump(records, f, indent=2, ensure_ascii=False)

print(f"Wrote {len(records)} reference records to mushroom_info.json")
for r in records:
    print(" -", r["id"], "=>", r["display_name"], "(", r["category"], ")")
