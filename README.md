# Zone Plate Generator

A PostScript generator for creating zone plates, zone sieves, and photon sieves for photography and optical experiments.

## Overview

This PostScript program generates three types of diffractive optical elements on a single page:

1. **Zone Plates**: Concentric rings of alternating transparent and opaque zones that focus light
2. **Zone Sieves**: Similar to zone plates but with rings formed by discrete holes
3. **Photon Sieves**: A variant with holes in the transparent zones

The script arranges these elements in a grid layout on a Letter-sized page with descriptive text for each type or a single type centered on the page

## Features

- Generates zone plates based on configurable focal length and desired number of zones
- Calculates proper zone spacing based on optical formulas
- Creates multiple elements in a grid pattern with specified rows and columns
- Automatically calculates effective f-stop values for each element type
- Includes punch outline markers for cutting the elements out after printing
- Displays measurements in both metric (mm) and imperial (inches) units
- Shows camera positioning information for duplication work
- Supports four display modes: grid view of all elements or individual centered plates
- Outputs ready-to-print PostScript file

## Usage

### Basic Usage

1. Download the `zone_plate_gen.ps` file
2. Edit the parameters at the top of the file as needed (see Parameters section)
3. Print the file to a PostScript-compatible printer or use a PostScript viewer
4. For best results, print on high-resolution transparent film

### Printing with Ghostscript

```powershell
# Print with default parameters
gswin64c -dNOPAUSE -dBATCH -sDEVICE=pdfwrite -dPDFSETTINGS=/printer -sOutputFile=zone_plates.pdf zone_plate_gen.ps

# Convert to a high-resolution image
gswin64c -dNOPAUSE -dBATCH -sDEVICE=png16m -r600 -sOutputFile=zone_plates.png zone_plate_gen.ps
```

## Parameters

The script has several configurable parameters at the top:

| Parameter | Default | Description |
|-----------|---------|-------------|
| FOCAL | 210 | Focal length in millimeters |
| RINGS | 8 | Number of zones (total rings will be RINGS × 2) |
| PUNCH_DIAMETER | 10 | Diameter of the punch outline in mm to cut out the zone plate |
| MAG | 15 | Magnification factor for the printed zone plate |
| WAVE_LENGTH | 0.00056 | Design wavelength in mm (0.00056 = daylight, 0.00022 = green light) |
| SIEVE_SCALE | 1.5 | Scale factor for the sieve holes on a ring |
| SIEVE_SPACE | 0.46 | Space between sieve holes in mm (larger values needed for higher magnification) |
| ROWS | 3 | Number of rows per element type |
| COLS | 9 | Number of columns per row |
| TYPE | PHOTON | Type of zone plate to generate (valid values: GRID, PLATE, SIEVE, PHOTON) |
| DUP_FOCAL | 180 | Duplicating camera focal length in millimeters (used for camera positioning info) |

## Example Configurations

### Standard Zone Plate for Visible Light

```postscript
/FOCAL 200 def        % 200mm focal length
/RINGS 8 def          % 8 zones (16 rings)
MAG 1 def            % 1:1 scale
/WAVE_LENGTH 0.00056 def  % Daylight
```

### Telephoto Zone Plate

```postscript
/FOCAL 500 def        % 500mm focal length
/RINGS 12 def         % 12 zones (24 rings)
MAG 1.5 def          % 1.5× magnification
/WAVE_LENGTH 0.00056 def  % Daylight
```

### Wide-Angle Zone Sieve

```postscript
/FOCAL 35 def         % 35mm focal length
/RINGS 5 def          % 5 zones
/SIEVE_SCALE 2.0 def  % Larger holes
/SIEVE_SPACE 0.25 def % Spacing between holes
/TYPE (SIEVE) def     % Generate a single zone sieve
```

## Optical Principles

Zone plates work by diffraction and interference. The radius of each zone follows the formula:

```
r_n = sqrt(n * λ * f + (n² * λ²) / 4) * MAG
```

Where:
- r_n = radius of zone n
- n = zone number
- λ = wavelength of light
- f = focal length
- MAG = magnification factor

The effective f-stop is calculated based on the diameter and focal length.

## Camera Positioning Information

When generating a single centered element (using TYPE set to PLATE, SIEVE, or PHOTON), the script displays helpful information for positioning a duplication camera:

- **Magnification**: Shows the current MAG value
- **Camera Focal Length**: Shows the DUP_FOCAL value (camera lens focal length)
- **Camera Distance**: Calculated distance for proper positioning using the formula:
  ```
  Distance = Magnification × (Focal Length + Focal Length / Magnification)
  ```

This information is shown in both millimeters and inches for convenience. Proper camera positioning is critical when duplicating zone plates onto film or other media.

## Understanding the Output

The generator has four display modes controlled by the TYPE parameter:

1. **GRID**: Displays a full page with multiple elements arranged in a grid pattern:
   - A border frame (8" × 10")
   - Three grids of optical elements (Zone Plates, Zone Sieves, Photon Sieves)
   - Text descriptions with calculated parameters below each grid

2. **PLATE**: Displays a single Zone Plate centered on the page with description and camera positioning information

3. **SIEVE**: Displays a single Zone Sieve centered on the page with description and camera positioning information

4. **PHOTON**: Displays a single Photon Sieve centered on the page with description and camera positioning information

Each optical element has a circular outline for cutting, and the pattern will focus light when printed on transparent media and used with a camera.

## Tips for Best Results

- Use high-resolution film printing (3600 DPI or higher)
- Print on clear, stable transparent film
- For photography: use with a camera body cap with a hole, or mount to the front of a lens
- For testing: use a laser pointer or bright point light source to observe focusing
- Experiment with different focal lengths to find the best for your needs
- When duplicating, use the camera positioning information for precise results
- All measurements are displayed in both metric (mm) and imperial (inches) units for convenience

## Mathematical References

The program includes utilities for calculating:
- Zone radii based on optical formulas
- Number of holes needed in each ring for zone sieves
- Effective f-stop for both zone plates and zone sieves
- Camera positioning distance for duplication work

Key formulas used:

1. **Zone radius calculation**:
   ```
   r_n = sqrt(n * λ * f + (n² * λ²) / 4) * MAG
   ```
   Where:
   - r_n = radius of zone n
   - n = zone number
   - λ = wavelength of light
   - f = focal length
   - MAG = magnification factor

2. **Camera distance calculation**:
   ```
   Distance = MAG * (DUP_FOCAL + DUP_FOCAL / MAG)
   ```
   Where:
   - MAG = magnification factor
   - DUP_FOCAL = duplicating camera lens focal length

## License

See the LICENSE file for details.

## Attribution

The PostScript concepts and original ideas for this generator were inspired by the work of Guillermo Peñate.
For additional details and background on zone plates and sieves, see:
- [Zone Plate and Sieves by Guillermo Peñate](https://pinholeday.org/docs/Zone_Plate_and_Sieves/)


