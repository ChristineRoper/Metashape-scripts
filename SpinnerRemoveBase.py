import Metashape


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

    model = chunk.model

    # Find faces that have vertices below 0.02m

    T = chunk.transform.matrix
    for i, face in enumerate(model.faces):
        for vertex_idx in face.vertices:  # face.vertices is a tuple of 3 vertex indices
            vertex = model.vertices[vertex_idx]
            coord = T.mulp(vertex.coord)
            if coord.z < 0.002 or abs(coord.x) > 0.04 or abs(coord.y) > 0.04:
                face.selected = True
                break

    # Remove selected faces
    model.removeSelection()


# Register the script with Metashape
MENU_LABEL = "Tools/Coral Spinner - Remove Base"
Metashape.app.addMenuItem(MENU_LABEL, set_scale)