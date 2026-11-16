import json

def extract_data():
    output = []
    for shape in Metashape.app.document.chunk.shapes.items():
        attributes = dict(shape.attributes)
        attributes["label"] = shape.label
        attributes["area"] = shape.area()
        attributes["areaFitted"] = shape.areaFitted()
        output.append(attributes)
    print(f"\n\n↓↓↓ Copy Below ↓↓↓\n\n{json.dumps(output)}\n")

# https://www.convertcsv.com/json-to-csv.htm
# Paste into "Step 1"
# Click "JSON to Excel" under "Step 3"


# Register the script with Metashape
MENU_LABEL = "Tools/Reef - Extract Shape data"
Metashape.app.addMenuItem(MENU_LABEL, extract_data)