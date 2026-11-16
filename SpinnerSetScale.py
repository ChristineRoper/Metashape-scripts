import Metashape

marker_pairs = [
    ("target 1", "target 2"),
    ("target 2", "target 4"),
    ("target 1", "target 3"),
    ("target 3", "target 4"),
]

positions = {
    "target 1": (-0.04, -0.04),
    "target 2": (-0.04, 0.04),
    "target 3": (0.04, -0.04),
    "target 4": (0.04, 0.04),
}


def set_scale():
    """Entry point function that will appear in Metashape Tools menu"""

    # Check if a document is open
    if not Metashape.app.document:
        Metashape.app.messageBox("Please open a Metashape document first.")
        return

    # Get Metashape chunk
    chunk = Metashape.app.document.chunk

    if not chunk:
        Metashape.app.messageBox("No chunk found in the document.")
        return

    chunk.detectMarkers()

    for marker in chunk.markers:
        if marker.label in positions:
            position = positions[marker.label]
            marker.reference.location = Metashape.Vector((position[0], position[1], 0))

    for marker1, marker2 in marker_pairs:
        marker1 = next((m for m in chunk.markers if m.label == marker1), None)
        marker2 = next((m for m in chunk.markers if m.label == marker2), None)

        if marker1 and marker2:
            scalebar = chunk.addScalebar(marker1, marker2)
            scalebar.label = f"{marker1.label}-{marker2.label}"
            scalebar.reference.distance = 0.08  # 80mm

    chunk.updateTransform()


# Register the script with Metashape
MENU_LABEL = "Tools/Coral Spinner - Set Scale"
Metashape.app.addMenuItem(MENU_LABEL, set_scale)
