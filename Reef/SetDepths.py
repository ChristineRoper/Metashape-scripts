# Metashape Python script for georeferencing reef coordinates
#
# Script: GeoreferenceReef.py
# Description: Corrects reef point positioning using 3D coordinate transformation
#
# This script performs coordinate transformation to correct reef point positioning by:
# 1. Exporting markers from Metashape to a temporary CSV file
# 2. Finding the best-fit plane through 3D points using Principal Component Analysis (PCA)
#    as a starting guess for which way is up
# 3. Finding the tilt that makes the points' heights best match the user-provided depths
# 4. Rotating and shifting the points to that tilt and depth. This is a rigid move, so
#    distances between points are unchanged (scale comes from the scalebars)
# 5. Importing the corrected coordinates back into Metashape

import Metashape
import tempfile
import os
import csv
import math
import random
import re
from typing import List, Dict, Optional, Tuple

# Might have to
# * Check all markers
# * Update transform so they get estimates
# * Uncheck all
# * Update transform again so the markers aren't affecting it


class Point3D:
    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z

    def __repr__(self):
        return f"Point3D(x={self.x:.6f}, y={self.y:.6f}, z={self.z:.6f})"


class CoordinateTransformer:
    """
    Reef Coordinate Correction
    This code takes points with relative correct positions but incorrect orientation
    and rigidly rotates and shifts them so their z-coordinates best match known depths.
    """

    @staticmethod
    def correct_reef_coordinates(
        points: List[Point3D], correct_z: List[float]
    ) -> List[Point3D]:
        """
        Rotate and shift the points so their z-coordinates best match the correct depths
        (least squares), while preserving their relative positions.

        This is a rigid move: points are not stretched or scaled, so the corrected
        z-coordinates will only match the correct depths as closely as the model allows.
        """
        if len(points) != len(correct_z):
            raise ValueError(
                "The number of points and correct z-coordinates must match"
            )

        if len(points) < 3:
            raise ValueError("Need at least 3 points to determine a plane")

        # Step 1: Find the centroid of the points
        centroid = CoordinateTransformer.find_centroid(points)

        # Step 2: Center the points around the origin
        centered_points = [
            Point3D(p.x - centroid.x, p.y - centroid.y, p.z - centroid.z)
            for p in points
        ]

        if CoordinateTransformer.are_collinear(centered_points):
            raise ValueError(
                "The markers are (almost) in a straight line, so the tilt can't be determined"
            )

        # Step 3: Use the best-fit plane as a first guess for which way is up
        initial_up = CoordinateTransformer.find_plane_normal(centered_points)

        # Step 4: Tilt "up" so the points' heights best match the correct depths
        mean_z = sum(correct_z) / len(correct_z)
        z_offsets = [z - mean_z for z in correct_z]
        up = CoordinateTransformer.fit_up_direction(
            centered_points, z_offsets, initial_up
        )

        # Step 5: Rotate the points so "up" is the z-axis, then shift to the mean depth
        rotation_matrix = CoordinateTransformer.calculate_rotation_matrix(up)
        rotated_points = [
            CoordinateTransformer.apply_rotation(p, rotation_matrix)
            for p in centered_points
        ]

        return [
            Point3D(p.x + centroid.x, p.y + centroid.y, p.z + mean_z)
            for p in rotated_points
        ]

    @staticmethod
    def are_collinear(centered_points: List[Point3D]) -> bool:
        """True if the (centered) points all lie on, or very close to, one line"""
        vectors = [[p.x, p.y, p.z] for p in centered_points]
        lengths = [math.sqrt(CoordinateTransformer.dot_product(v, v)) for v in vectors]
        longest = max(lengths)
        if longest == 0:
            return True

        # Measure how far each point is from the line through the farthest point
        direction = vectors[lengths.index(longest)]
        max_offset = max(
            math.sqrt(
                CoordinateTransformer.dot_product(
                    CoordinateTransformer.cross_product(direction, v),
                    CoordinateTransformer.cross_product(direction, v),
                )
            )
            / longest
            for v in vectors
        )
        return max_offset < 1e-6 * longest

    @staticmethod
    def find_plane_normal(centered_points: List[Point3D]) -> List[float]:
        """
        Find the upward-pointing normal of the best-fit plane through the
        (centered) points using Principal Component Analysis (PCA)
        """
        # Create the covariance matrix for Principal Component Analysis (PCA)
        covariance_matrix = CoordinateTransformer.create_covariance_matrix(
            centered_points
        )

        # Find the eigenvectors of the covariance matrix
        eigenvectors, eigenvalues = CoordinateTransformer.find_eigenvectors_and_values(
            covariance_matrix
        )

        # Sort eigenvectors by eigenvalue (ascending)
        indices = sorted(range(len(eigenvalues)), key=lambda i: eigenvalues[i])

        # The normal vector to the best-fit plane is the eigenvector with the smallest
        # eigenvalue. Calculate it as the cross product of the other two, because power
        # iteration finds it unreliably (it is pure noise when the points are exactly flat)
        normal_vector = CoordinateTransformer.normalize_vector(
            CoordinateTransformer.cross_product(
                eigenvectors[indices[2]], eigenvectors[indices[1]]
            )
        )

        # Ensure normal vector points upward (since photos are taken from above)
        return CoordinateTransformer.ensure_upward_normal(normal_vector)

    @staticmethod
    def fit_up_direction(
        centered_points: List[Point3D],
        z_offsets: List[float],
        initial_up: List[float],
    ) -> List[float]:
        """
        Find the unit "up" vector for which each point's height (its dot product with
        "up") best matches its z offset, in the least-squares sense.

        Uses Gauss-Newton iteration starting from initial_up: each step tilts "up"
        towards two perpendicular directions by amounts found with linear least squares.
        Starting from the upward plane normal keeps the result the right way up.
        """
        up = CoordinateTransformer.normalize_vector(initial_up)

        for _ in range(100):
            t1, t2 = CoordinateTransformer.perpendicular_vectors(up)

            # Build the 2x2 normal equations for the tilt step (s1, s2)
            a11 = a12 = a22 = b1 = b2 = 0.0
            for p, z_offset in zip(centered_points, z_offsets):
                coords = [p.x, p.y, p.z]
                residual = CoordinateTransformer.dot_product(up, coords) - z_offset
                j1 = CoordinateTransformer.dot_product(t1, coords)
                j2 = CoordinateTransformer.dot_product(t2, coords)
                a11 += j1 * j1
                a12 += j1 * j2
                a22 += j2 * j2
                b1 += j1 * residual
                b2 += j2 * residual

            det = a11 * a22 - a12 * a12
            if det <= 1e-12 * (a11 + a22) ** 2:
                raise ValueError(
                    "The markers are (almost) in a straight line, so the tilt can't be determined"
                )

            s1 = -(a22 * b1 - a12 * b2) / det
            s2 = -(a11 * b2 - a12 * b1) / det

            # Limit each step to a moderate tilt so the iteration can't jump wildly
            step = math.sqrt(s1 * s1 + s2 * s2)
            if step > 0.5:
                s1 *= 0.5 / step
                s2 *= 0.5 / step

            up = CoordinateTransformer.normalize_vector(
                [up[k] + s1 * t1[k] + s2 * t2[k] for k in range(3)]
            )

            if step < 1e-12:
                break

        return up

    @staticmethod
    def perpendicular_vectors(v: List[float]) -> Tuple[List[float], List[float]]:
        """Return two unit vectors perpendicular to unit vector v and to each other"""
        helper = [1.0, 0.0, 0.0] if abs(v[0]) < 0.9 else [0.0, 1.0, 0.0]
        t1 = CoordinateTransformer.normalize_vector(
            CoordinateTransformer.cross_product(v, helper)
        )
        t2 = CoordinateTransformer.cross_product(v, t1)
        return t1, t2

    @staticmethod
    def cross_product(v1: List[float], v2: List[float]) -> List[float]:
        """Calculate the cross product of two vectors"""
        return [
            v1[1] * v2[2] - v1[2] * v2[1],
            v1[2] * v2[0] - v1[0] * v2[2],
            v1[0] * v2[1] - v1[1] * v2[0],
        ]

    @staticmethod
    def ensure_upward_normal(normal: List[float]) -> List[float]:
        """
        Ensure the normal vector points upward (positive z direction).
        Since photos are taken from above, the plane normal should point upward.
        If the normal points downward (negative z), flip it.
        """
        if normal[2] < 0:
            return [-normal[0], -normal[1], -normal[2]]
        return normal

    @staticmethod
    def find_centroid(points: List[Point3D]) -> Point3D:
        """Find the centroid (average position) of a set of points"""
        sum_x = sum(p.x for p in points)
        sum_y = sum(p.y for p in points)
        sum_z = sum(p.z for p in points)

        return Point3D(sum_x / len(points), sum_y / len(points), sum_z / len(points))

    @staticmethod
    def create_covariance_matrix(centered_points: List[Point3D]) -> List[List[float]]:
        """Create the 3x3 covariance matrix for the centered points"""
        # Initialize 3x3 matrix with zeros
        cov_matrix = [[0.0 for _ in range(3)] for _ in range(3)]

        # Calculate covariance matrix
        for p in centered_points:
            cov_matrix[0][0] += p.x * p.x
            cov_matrix[0][1] += p.x * p.y
            cov_matrix[0][2] += p.x * p.z
            cov_matrix[1][0] += p.y * p.x
            cov_matrix[1][1] += p.y * p.y
            cov_matrix[1][2] += p.y * p.z
            cov_matrix[2][0] += p.z * p.x
            cov_matrix[2][1] += p.z * p.y
            cov_matrix[2][2] += p.z * p.z

        # Normalize by the number of points
        for i in range(3):
            for j in range(3):
                cov_matrix[i][j] /= len(centered_points)

        return cov_matrix

    @staticmethod
    def find_eigenvectors_and_values(
        matrix: List[List[float]],
    ) -> Tuple[List[List[float]], List[float]]:
        """
        Implementation of a simple power iteration method to find eigenvectors and eigenvalues
        Note: For production code, it's recommended to use a linear algebra library like numpy
        """
        n = len(matrix)
        eigenvectors = []
        eigenvalues = []

        # Make a copy of the matrix to work with
        working_matrix = [row[:] for row in matrix]

        for k in range(n):
            # Start with a random vector
            vector = [random.random(), random.random(), random.random()]
            # Normalize
            vector = CoordinateTransformer.normalize_vector(vector)

            # Power iteration
            for iteration in range(100):
                # Multiply matrix by vector
                new_vector = [0.0, 0.0, 0.0]
                for i in range(n):
                    for j in range(n):
                        new_vector[i] += working_matrix[i][j] * vector[j]

                # Calculate eigenvalue
                eigenvalue = CoordinateTransformer.dot_product(new_vector, vector)

                # Normalize the new vector
                vector = CoordinateTransformer.normalize_vector(new_vector)

                # Store eigenvalue and eigenvector
                if iteration == 99:
                    eigenvalues.append(eigenvalue)
                    eigenvectors.append(vector)

                    # Deflate the matrix to find the next eigenvector
                    for i in range(n):
                        for j in range(n):
                            working_matrix[i][j] -= eigenvalue * vector[i] * vector[j]

        return eigenvectors, eigenvalues

    @staticmethod
    def dot_product(v1: List[float], v2: List[float]) -> float:
        """Calculate the dot product of two vectors"""
        return sum(a * b for a, b in zip(v1, v2))

    @staticmethod
    def normalize_vector(v: List[float]) -> List[float]:
        """Normalize a vector (divide by its length)"""
        length = math.sqrt(sum(val * val for val in v))
        return [val / length for val in v]

    @staticmethod
    def calculate_rotation_matrix(normal: List[float]) -> List[List[float]]:
        """Calculate the rotation matrix to align the normal vector with the z-axis"""
        # Normalize the normal vector
        n = CoordinateTransformer.normalize_vector(normal)

        # If the normal is already aligned with the z-axis, no rotation is needed
        if abs(n[0]) < 1e-10 and abs(n[1]) < 1e-10 and abs(n[2] - 1.0) < 1e-10:
            return [[1, 0, 0], [0, 1, 0], [0, 0, 1]]

        # If the normal is opposite to the z-axis, rotate 180° about the x-axis
        # (not -I, which would mirror the points rather than rotate them)
        if abs(n[0]) < 1e-10 and abs(n[1]) < 1e-10 and abs(n[2] + 1.0) < 1e-10:
            return [[1, 0, 0], [0, -1, 0], [0, 0, -1]]

        # Calculate the rotation axis by cross product of normal and z-axis (0,0,1)
        rotation_axis = CoordinateTransformer.normalize_vector([n[1], -n[0], 0])

        # Calculate the rotation angle
        cos_theta = n[2]  # Dot product of normal and (0,0,1)
        sin_theta = math.sqrt(1 - cos_theta * cos_theta)

        # Rodrigues' rotation formula
        x, y, z = rotation_axis

        # Cross-product matrix K
        K = [[0, -z, y], [z, 0, -x], [-y, x, 0]]

        # K²
        K2 = [
            [-(y * y + z * z), x * y, x * z],
            [x * y, -(x * x + z * z), y * z],
            [x * z, y * z, -(x * x + y * y)],
        ]

        # Calculate rotation matrix: R = I + sin(θ)K + (1-cos(θ))K²
        R = [[0.0 for _ in range(3)] for _ in range(3)]

        for i in range(3):
            for j in range(3):
                R[i][j] = (
                    (1 if i == j else 0)
                    + sin_theta * K[i][j]
                    + (1 - cos_theta) * K2[i][j]
                )

        return R

    @staticmethod
    def apply_rotation(point: Point3D, rotation_matrix: List[List[float]]) -> Point3D:
        """Apply a rotation matrix to a point"""
        return Point3D(
            rotation_matrix[0][0] * point.x
            + rotation_matrix[0][1] * point.y
            + rotation_matrix[0][2] * point.z,
            rotation_matrix[1][0] * point.x
            + rotation_matrix[1][1] * point.y
            + rotation_matrix[1][2] * point.z,
            rotation_matrix[2][0] * point.x
            + rotation_matrix[2][1] * point.y
            + rotation_matrix[2][2] * point.z,
        )


def target_number(label: str) -> Optional[int]:
    """Return N for a marker labelled "target N" (case-insensitive), otherwise None"""
    match = re.match(r"^target\s+(\d+)$", label, re.IGNORECASE)
    return int(match.group(1)) if match else None


def get_user_z_corrections(labels: List[str]) -> Dict[str, float]:
    """
    Get Z-coordinate corrections from user for each target using Metashape dialogs.
    The second target of a pair (target 2, 4, ...) reuses the depth of the first.
    """
    corrections = {}
    depth_by_number = {}

    for marker_label in labels:
        number = target_number(marker_label)
        # The second target of a pair gets the same depth as the first
        if number % 2 == 0 and number - 1 in depth_by_number:
            corrections[marker_label] = depth_by_number[number - 1]
            continue

        while True:
            try:
                depth_str = Metashape.app.getString(
                    f"Enter correct depth for '{marker_label}':"
                )
                if depth_str is None:  # User cancelled
                    raise RuntimeError("User cancelled depth input")
                z_value = -float(depth_str)
                corrections[marker_label] = z_value
                depth_by_number[number] = z_value
                break
            except ValueError:
                Metashape.app.messageBox("Please enter a valid number.")
                continue
            except RuntimeError:
                raise

    return corrections


def read_reference_file(file_path: str) -> Tuple[List[str], List[Dict[str, str]]]:
    """
    Read the reference file and extract data
    Returns: (header_lines, data_rows)
    """
    header_lines = []
    data_rows = []

    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

        # Find where data starts (after comment lines)
        data_start_idx = 0
        for i, line in enumerate(lines):
            if line.strip().startswith("# "):
                header_lines.append(line.strip())
            else:
                data_start_idx = i
                break

        # Parse CSV data
        csv_lines = lines[data_start_idx:]
        if csv_lines:
            reader = csv.DictReader(csv_lines)
            data_rows = list(reader)

    return header_lines, data_rows


def write_reference_file(
    file_path: str, header_lines: List[str], data_rows: List[Dict[str, str]]
):
    """
    Write the reference file with updated coordinates
    """
    with open(file_path, "w", encoding="utf-8", newline="") as file:
        # Write header comments
        for header in header_lines:
            file.write(header + "\n")

        # Write CSV data
        if data_rows:
            fieldnames = data_rows[0].keys()
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data_rows)


def extract_points_with_coordinates(
    data_rows: List[Dict[str, str]],
) -> Tuple[List[Point3D], List[str]]:
    """Extract "target N" markers that have estimated coordinates"""
    points_to_transform = []
    point_labels = []

    for row in data_rows:
        if target_number(row["#Label"]) is None:
            print(f"Skipping {row['#Label']}: not named like 'target 1'")
            continue
        if (
            row.get("X_est")
            and row.get("Y_est")
            and row.get("Z_est")
            and row["X_est"].strip()
            and row["Y_est"].strip()
            and row["Z_est"].strip()
        ):
            try:
                x_est = float(row["X_est"])
                y_est = float(row["Y_est"])
                z_est = float(row["Z_est"])
                points_to_transform.append(Point3D(x_est, y_est, z_est))
                point_labels.append(row["#Label"])
            except ValueError:
                print(f"Warning: Could not parse coordinates for {row['#Label']}")
                continue

    return points_to_transform, point_labels


def update_data_rows_with_corrections(
    data_rows: List[Dict[str, str]],
    point_labels: List[str],
    corrected_points: List[Point3D],
) -> None:
    """Update data rows with corrected coordinates"""
    point_corrections = dict(zip(point_labels, corrected_points))

    for row in data_rows:
        if row["#Label"] in point_corrections:
            corrected_point = point_corrections[row["#Label"]]
            row["X"] = f"{corrected_point.x:.6f}"
            row["Y"] = f"{corrected_point.y:.6f}"
            row["Z"] = f"{corrected_point.z:.6f}"
            row["X_est"] = f"{corrected_point.x:.6f}"
            row["Y_est"] = f"{corrected_point.y:.6f}"
            row["Z_est"] = f"{corrected_point.z:.6f}"


def georeference_reef():
    """Entry point function that will appear in Metashape Tools menu"""
    """Main function to execute the coordinate transformation workflow"""

    # Check if a document is open
    if not Metashape.app.document:
        Metashape.app.messageBox("Please open a Metashape document first.")
        return

    # Get Metashape chunk
    chunk = Metashape.app.document.chunk

    if not chunk:
        Metashape.app.messageBox("No chunk found in the document.")
        return

    # Create temporary file path
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False
    ) as temp_file:
        path = temp_file.name

    try:
        # Export reference from Metashape
        print("Exporting reference from Metashape...")
        chunk.exportReference(
            path, items=Metashape.ReferenceItems.ReferenceItemsMarkers, delimiter=","
        )

        # Read the reference file
        print("Reading reference file...")
        header_lines, data_rows = read_reference_file(path)

        points_to_transform, point_labels = extract_points_with_coordinates(data_rows)

        if len(points_to_transform) < 3:
            Metashape.app.messageBox(
                "Need at least 3 markers with estimated positions, named like "
                "'target 1', 'target 2', etc."
            )
            return

        print(f"Found {len(points_to_transform)} points with estimated coordinates:")
        for i, label in enumerate(point_labels):
            print(f"  {label}: {points_to_transform[i]}")

        # Get Z-coordinate corrections from user
        z_corrections = get_user_z_corrections(point_labels)
        correct_z_values = [
            z_corrections[marker_label] for marker_label in point_labels
        ]

        # Perform coordinate transformation
        print("Performing coordinate transformation...")
        transformer = CoordinateTransformer()
        corrected_points = transformer.correct_reef_coordinates(
            points_to_transform, correct_z_values
        )

        print("Transformation results:")
        squared_errors = []
        for marker_label, original, corrected, correct_z in zip(
            point_labels, points_to_transform, corrected_points, correct_z_values
        ):
            depth_error = corrected.z - correct_z
            squared_errors.append(depth_error * depth_error)
            print(f"  {marker_label}:")
            print(f"    Original:  {original}")
            print(f"    Corrected: {corrected}")
            print(f"    Difference from entered depth: {depth_error:+.3f}")

        rms_error = math.sqrt(sum(squared_errors) / len(squared_errors))
        print(
            f"RMS difference between corrected and entered depths: {rms_error:.3f}. "
            f"Large values suggest a wrong depth, a mislabelled marker or a scale problem."
        )

        update_data_rows_with_corrections(data_rows, point_labels, corrected_points)

        # Write the updated reference file
        print("Writing updated reference file...")
        write_reference_file(path, header_lines, data_rows)

        # Import the modified reference back into Metashape
        print(
            f"Importing modified reference back into Metashape, "
            f"skipping {len(header_lines)+1} rows..."
        )
        debug = chunk.importReference(
            path,
            format=Metashape.ReferenceFormatCSV,
            columns="nxyz",
            delimiter=",",
            skip_rows=len(header_lines) + 1,
            items=Metashape.ReferenceItems.ReferenceItemsMarkers,
            crs=chunk.crs,
        )

        print(debug)

        print("Coordinate transformation completed successfully!")

    except Exception as e:
        print(f"Error during coordinate transformation: {str(e)}")
        raise

    finally:
        # Clean up temporary file
        if os.path.exists(path):
            os.unlink(path)


# Register the script with Metashape
MENU_LABEL = "Tools/Reef - Set Marker Depths"
Metashape.app.addMenuItem(MENU_LABEL, georeference_reef)
