# Metashape Python script for adding scalebars between paired points
#
# Script: AddScalebars.py
# Description: Adds scalebars between pairs of points named like "target 1", "target 2", etc.
#
# This script adds a Tools menu item that asks for the distance between the targets
# in each pair (in mm), then automatically creates scalebars for point pairs:
# - Points are named "target 1", "target 2", "target 3", "target 4", etc.
# - Pairs are matched: target 1-target 2, target 3-target 4, target 5-target 6, etc.
# - Each scalebar is set to the distance entered (e.g. 85.5, 100 or 150mm)
# - Scalebars are named after the point pair (e.g., "target 1-target 2")
# - Only ADDS scalebars. If there are existing scalebars they will not be updated

import Metashape
import re
from typing import List, Optional, Tuple


def find_point_pairs_targets(
    markers: List[Metashape.Marker],
) -> List[Tuple[Metashape.Marker, Metashape.Marker]]:
    """
    Find pairs of markers based on naming pattern "target 1", "target 2", etc.
    Pairs are matched: target 1-target 2, target 3-target 4, target 5-target 6, etc.
    Returns list of marker pairs
    """
    target_markers = {}

    for marker in markers:
        if not marker.label:
            continue

        # Extract number from "target N" pattern (case-insensitive)
        match = re.match(r"^target\s+(\d+)$", marker.label, re.IGNORECASE)
        if match:
            number = int(match.group(1))
            target_markers[number] = marker

    pairs = []
    # Create pairs from consecutive odd/even numbers (1-2, 3-4, 5-6, etc.)
    # Check all odd numbers and see if the next even number exists
    for num in target_markers.keys():
        if num % 2 == 1:  # If this is an odd number
            if num + 1 in target_markers:  # Check if the next even number exists
                marker1 = target_markers[num]
                marker2 = target_markers[num + 1]
                pairs.append((marker1, marker2))

    return pairs


def create_scalebar(
    chunk: Metashape.Chunk,
    marker1: Metashape.Marker,
    marker2: Metashape.Marker,
    distance: float,
) -> bool:
    """
    Create a scalebar between two markers with the specified distance (in metres).
    Returns False if a scalebar with the same name already exists.
    """
    scalebar_label = f"{marker1.label}-{marker2.label}"

    # Check if scalebar already exists
    for scalebar in chunk.scalebars:
        if scalebar.label == scalebar_label:
            print(f"Scalebar {scalebar_label} already exists, skipping...")
            return False

    # Create new scalebar
    scalebar = chunk.addScalebar(marker1, marker2)
    scalebar.label = scalebar_label
    scalebar.reference.distance = distance

    print(f"Created scalebar {scalebar_label} with distance {distance}m")
    return True


def ask_scalebar_distance() -> Optional[float]:
    """
    Ask the user for the distance between the targets in each pair, in mm.
    Returns the distance in metres, or None if the user cancelled.
    """
    while True:
        try:
            distance_str = Metashape.app.getString(
                "Enter the distance between the targets in each pair, in mm.\n"
                "For example, 15cm is 150mm."
            )
        except RuntimeError:  # User cancelled
            return None
        if distance_str is None:  # User cancelled
            return None

        try:
            # Allow "150" or "150mm"
            distance_mm = float(re.sub(r"\s*mm$", "", distance_str.strip(), flags=re.IGNORECASE))
        except ValueError:
            Metashape.app.messageBox("Please enter a number, for example 150.")
            continue

        if distance_mm <= 0:
            Metashape.app.messageBox("The distance must be more than 0mm.")
            continue

        return distance_mm / 1000


def add_scalebars() -> None:
    """Ask for the scalebar length and add scalebars between all target pairs"""

    # Check if a document is open
    if not Metashape.app.document:
        Metashape.app.messageBox("Please open a Metashape document first.")
        return

    # Get Metashape chunk
    chunk = Metashape.app.document.chunk

    if not chunk:
        Metashape.app.messageBox("No chunk found in the document.")
        return

    if not chunk.markers:
        Metashape.app.messageBox("No markers found in the document.")
        return

    # Find point pairs
    pairs = find_point_pairs_targets(chunk.markers)

    if not pairs:
        Metashape.app.messageBox(
            "No valid point pairs found. Points should be named like 'target 1', 'target 2', 'target 3', 'target 4', etc."
        )
        return

    print(f"Found {len(pairs)} point pairs:")
    for marker1, marker2 in pairs:
        print(f"  {marker1.label} - {marker2.label}")

    scalebar_distance = ask_scalebar_distance()
    if scalebar_distance is None:
        print("Cancelled, no scalebars added.")
        return

    # Create scalebars for each pair
    created_count = 0
    for marker1, marker2 in pairs:
        if create_scalebar(chunk, marker1, marker2, scalebar_distance):
            created_count += 1

    skipped_count = len(pairs) - created_count
    message = f"Created {created_count} scalebars of {scalebar_distance * 1000:g}mm."
    if skipped_count:
        message += f"\n{skipped_count} already existed and were left as they are."
    Metashape.app.messageBox(message)


# Register the script with Metashape
MENU_LABEL = "Tools/Reef - Add Scalebars"
Metashape.app.addMenuItem(MENU_LABEL, add_scalebars)
