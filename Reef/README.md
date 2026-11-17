# Reef Scripts

Scripts for reef-scale underwater photogrammetry.

See the [main README](../README.md) for how to install the scripts.

## Add Scalebars 85.5mm

Use this script where the distance between targets is 85.5 mm

[AddScalebars85.5.py](AddScalebars85.5.py) adds the menu item **Tools → Reef - Add Scalebars 85.5mm**.

For the 85.5mm markers printed from Metashape, sometimes the edges are cut off which means Metashape will not automatically identify them. In that case, you must manually add the markers

- Make sure they are named: A1, A2, B1, B2 etc
- Markers are grouped by letter, then sorted by number.
- Within each group, markers are paired in order: 1st with 2nd, 3rd with 4th, and so on.
- Existing scalebars with the same name are left as they are.

## Add Scalebars (targets)

[AddScalebarsTargets.py](AddScalebarsTargets.py) adds two menu items:

- **Tools → Reef - Add Scalebars 100mm**
- **Tools → Reef - Add Scalebars 150mm**

Choose the menu item that matches the distance between the targets in each pair.

It adds a scalebar between each pair of markers named `target 1` and `target 2`, `target 3` and `target 4`, and so on.

- Names are not case sensitive (`Target 1` also works).
- If a pair is missing one target, the pair is skipped (add the target manually if this is the case)
- Each scalebar is named after its pair, for example `target 1-target 2`.
- The script only **adds** scalebars. If a scalebar with that name already exists, it is left as it is, even if its distance is different.

## Set Marker Depths

[SetDepths.py](SetDepths.py) adds the menu item **Tools → Reef - Set Marker Depths**.

This levels the model and sets the marker depths to the depths measured on the dive.

Before running it:

- Align the photos, so the markers have estimated positions.
- Name the markers `target 1`, `target 2`, and so on. You need at least 3 markers with estimated positions.

When you run it:

1. It asks for the depth of each target. **Enter depth as a positive number** (for example `4.2`). The script stores it as a negative Z.
   - If it only asks about the first target in each pair (`target 1`, `target 3`, …). The second target (`target 2`, `target 4`, …) is given the same depth.
   - Click Cancel to stop without changing anything.
2. It fits a flat plane through the markers and rotates them so the plane is level, keeping their positions relative to each other.
3. It sets each marker's Z to the depth you entered, and imports the new positions as the marker reference coordinates.

The console shows each marker's original and corrected position.

## Extract Shape Data

[ExtractShapeData.py](ExtractShapeData.py) adds the menu item **Tools → Reef - Extract Shape data**.

It exports the shapes in the current chunk so you can open them in Excel. For each shape it includes the label, any attributes, the area and the fitted area.
NOTE: There are many different ways to measure surface area, including Mesh area, DEM and Projected Area, and hidden surfaces area. Ensure the type of surface area extracted by this code is what is best suited to your project obecjtive.

1. Run the menu item.
2. In the console (**View → Console**), copy the text below the line `↓↓↓ Copy Below ↓↓↓`.
3. Go to <https://www.convertcsv.com/json-to-csv.htm> and paste it into **Step 1**.
4. Under **Step 3**, click **JSON to Excel**.

- **Area**: Calculates the area by projecting the shape vertices directly onto the flat XY plane of the project's coordinate system. It completely ignores any Z (elevation/height) variations, treating the shape as a flat footprint from a top-down, 2D map view.

- **Area Fitted**: Calculates the area covered by the shape on a best-fit plane that is dynamically computed using the 3D (XYZ) coordinates of the shape's vertices. This accounts for a tilted or sloped surface rather than flattening everything onto a strict horizontal XY plane.
- **DEM Surface area**: Not calculated by this script.
- **Model 3D Surface area**: Not calculated by this script.
