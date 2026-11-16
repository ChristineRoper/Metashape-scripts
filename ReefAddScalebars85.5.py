# Metashape Python script for adding scalebars between paired points
#
# Script: AddScalebars.py
# Description: Adds scalebars between pairs of points named like D1,D2 or H1,H2
#
# This script automatically creates scalebars for point pairs:
# - Points are considered a pair if they have the same letter prefix (e.g., D1,D2 or H1,H2)
# - Each scalebar is set to 0.0855m (the known distance between paired points)
# - Scalebars are named after the point pair (e.g., "D1-D2" or "H1-H2")

import Metashape
import re
from typing import Dict, List, Tuple


def find_point_pairs_old(markers: List[Metashape.Marker]) -> List[Tuple[Metashape.Marker, Metashape.Marker]]:
    """
    Find pairs of markers based on naming pattern (e.g., D1,D2 or H1,H2)
    Returns list of marker pairs
    """
    marker_groups = {}
    
    for marker in markers:
        if not marker.label:
            continue

	
            
        # Extract letter prefix and number (e.g., "D1" -> ("D", "1"))
        match = re.match(r'^([A-Za-z]+)(\d+)$', marker.label)
        if match:
            prefix = match.group(1)
            number = match.group(2)
            
            if prefix not in marker_groups:
                marker_groups[prefix] = {}
            marker_groups[prefix][number] = marker
    
    pairs = []
    for prefix, markers_dict in marker_groups.items():
        numbers = sorted(markers_dict.keys(), key=int)
        
        # Create pairs from consecutive numbers (1,2 then 3,4, etc.)
        for i in range(0, len(numbers) - 1, 2):
            if i + 1 < len(numbers):
                marker1 = markers_dict[numbers[i]]
                marker2 = markers_dict[numbers[i + 1]]
                pairs.append((marker1, marker2))
    
    return pairs


def create_reef_scalebar(chunk: Metashape.Chunk, marker1: Metashape.Marker, marker2: Metashape.Marker, distance: float) -> None:
    """
    Create a scalebar between two markers with the specified distance
    """
    scalebar_label = f"{marker1.label}-{marker2.label}"
    
    # Check if scalebar already exists
    for scalebar in chunk.scalebars:
        if scalebar.label == scalebar_label:
            print(f"Scalebar {scalebar_label} already exists, skipping...")
            return
    
    # Create new scalebar
    scalebar = chunk.addScalebar(marker1, marker2)
    scalebar.label = scalebar_label
    scalebar.reference.distance = distance
    
    print(f"Created scalebar {scalebar_label} with distance {distance}m")


def add_reef_scalebars_85():
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
    
    if not chunk.markers:
        Metashape.app.messageBox("No markers found in the document.")
        return
    
    # Find point pairs
    pairs = find_point_pairs_old(chunk.markers)
    
    if not pairs:
        Metashape.app.messageBox("No valid point pairs found. Points should be named like D1,D2 or H1,H2.")
        return
    
    print(f"Found {len(pairs)} point pairs:")
    for marker1, marker2 in pairs:
        print(f"  {marker1.label} - {marker2.label}")
    
    # Set scalebar distance (0.0855m as specified)
    scalebar_distance = 0.0855
    
    # Create scalebars for each pair
    created_count = 0
    for marker1, marker2 in pairs:
        create_reef_scalebar(chunk, marker1, marker2, scalebar_distance)
        created_count += 1
    
    Metashape.app.messageBox(f"Successfully created {created_count} scalebars with distance {scalebar_distance}m")


# Register the script with Metashape
MENU_LABEL = "Tools/Reef - Add Scalebars 85.5mm"
Metashape.app.addMenuItem(MENU_LABEL, add_reef_scalebars_85)