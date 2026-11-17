# Reef Scripts

Scripts for reef-scale underwater photogrammetry.

See the [main README](../README.md) for how to install the scripts.

## Marker names

**All the reef scripts need markers named `target 1`, `target 2`, `target 3`, and so on.** Targets are paired: `target 1` with `target 2`, `target 3` with `target 4`, and so on.

Metashape names the targets it detects automatically like this. If it can't detect a target (for example, when the edges of a printed target are cut off), add the marker by hand and rename it to `target N`. Metashape calls hand-added markers `point 1`, `point 2`, … by default, and the scripts ignore markers with those names. If your targets are not grouped into pairs of 1 with 2, 3 with 4, etc then you will need to rename them.

Names are not case sensitive (`Target 1` also works).

## Add Scalebars

[AddScalebars.py](AddScalebars.py) adds the menu item **Tools → Reef - Add Scalebars**.

1. It asks for the distance between the targets in each pair, **in mm**. For example, 15cm is `150` and 8.55cm is `85.5`.
   - Click Cancel to stop without adding anything.
2. It adds a scalebar of that length between each pair of markers named `target 1` and `target 2`, `target 3` and `target 4`, and so on.

- If a pair is missing one target, the pair is skipped (add the target manually if this is the case)
- Each scalebar is named after its pair, for example `target 1-target 2`.
- The script only **adds** scalebars. If a scalebar with that name already exists, it is left as it is, even if its distance is different.

## Set Marker Depths

[SetDepths.py](SetDepths.py) adds the menu item **Tools → Reef - Set Marker Depths**.

This tilts the model and moves it up or down so the markers match the depths measured on the dive.

Before running it:

- Align the photos, so the markers have estimated positions.
- Name the markers `target 1`, `target 2`, and so on (see [Marker names](#marker-names)). You need at least 3 markers with estimated positions. Markers with other names are ignored.

When you run it:

1. It asks for the depth of each target. **Enter depth as a positive number** (for example `4.2`). The script stores it as a negative Z.
   - It only asks about the first target in each pair (`target 1`, `target 3`, …). The second target (`target 2`, `target 4`, …) is given the same depth.
   - Click Cancel to stop without changing anything.
2. It finds the tilt and depth that best match the depths you entered, then rotates and moves the markers to match. The markers keep their positions relative to each other: the model isn't stretched or rescaled. Its size comes from the scalebars.
3. It imports the new positions as the marker reference coordinates.

Because the model only moves as a whole, each marker ends up close to the depth you entered, but usually not exactly on it. The console shows each marker's original and corrected position, how far it is from the depth you entered, and the overall (RMS) difference. A large difference usually means a depth was typed wrong, a marker is mislabelled, or the scalebars are wrong.

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
