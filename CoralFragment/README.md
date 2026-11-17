# Coral Fragment Scripts

Scripts for modelling individual coral fragments photographed on Christine's automated turntable.

See the [main README](../README.md) for how to install the scripts.

## Typical workflow

1. Align photos.
2. **Tools → Coral Spinner - Set Scale**
3. Build the model (mesh).
4. **Tools → Coral Spinner - Remove Base**

## Set Scale

[SetScale.py](SetScale.py) adds the menu item **Tools → Coral Spinner - Set Scale**.

It scales the model and positions it using the four targets on the turntable:

- Detects the targets in the photos. They become markers named `target 1` to `target 4`.
- Places the targets at the corners of an 80 mm square, centred on the origin, at height 0:

  | Marker   | X (m) | Y (m) |
  | -------- | ----- | ----- |
  | target 1 | -0.04 | -0.04 |
  | target 2 | -0.04 | 0.04  |
  | target 3 | 0.04  | -0.04 |
  | target 4 | 0.04  | 0.04  |

- Adds four 80 mm scalebars around the edges of the square (1–2, 2–4, 1–3 and 3–4).
- Updates the transform.

After this, the turntable surface is at Z = 0, and the coral sits above it at the centre.

## Remove Base

[RemoveBase.py](RemoveBase.py) adds the menu item **Tools → Coral Spinner - Remove Base**.

It deletes the parts of the mesh that aren't coral:

- anything less than 2 mm above the turntable surface
- anything outside the 80 mm square between the targets

Run **Set Scale** first, so the model is in the right position.

This permanently changes the mesh. If you might need the original, duplicate the chunk or save a copy of the project first.
