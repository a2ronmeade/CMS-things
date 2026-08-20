from ._shared_imports import *

def get_crosstalk(paths_files, path_results, **kwargs):
  is_sane = True
  AS = {}
  explanation = ""
  message = ""

  # We expect exactly 3 PixelAlive files: injtype1, injtype5, injtype6
  status_files, pixelalive_files = get_file_regex(paths_files, regex=r"(?i).*PixelAlive.*\.root$", multiple=True)
  if not status_files or len(pixelalive_files) != 3:
    return (
      False,
      "FELIS ERROR: Exactly three PixelAlive root files (injtype1, injtype5, injtype6) are required.",
      None,
      False,
      "",
    )

  # Sort the file names in alphabetical order
  pixelalive_files.sort()  

  # Open the three files
  f_injtype1 = ROOT.TFile.Open(pixelalive_files[0])
  f_injtype5 = ROOT.TFile.Open(pixelalive_files[1])
  f_injtype6 = ROOT.TFile.Open(pixelalive_files[2])
  if (not f_injtype1 or f_injtype1.IsZombie() or
      not f_injtype5 or f_injtype5.IsZombie() or
      not f_injtype6 or f_injtype6.IsZombie()):
    return (
      False,
      "FELIS ERROR opening one or more PixelAlive root files.",
      None,
      False,
      "",
    )

  # Use the first file to find chip directories
  pattern = r"Detector/Board_\d+/OpticalGroup_\d+/Hybrid_\d+/Chip_\d+"
  status_paths, chip_paths = find_rootPaths(pixelalive_files[0], pattern=pattern)
  if not status_paths or not chip_paths:
    return (
      False,
      "FELIS ERROR: No chip paths found in the PixelAlive root file.",
      None,
      False,
      "",
    )

  # Define thresholds from your crosstalk logic
  alive_eff = 0.90
  coupled_eff = 0.90
  uncoupled_eff = 0.2
  tot_eff = 0.01

  # Define tolerances for clustering
  cluster_tolerance = 1
  large_cluster_threshold = 50

  def find_clusters(coords, tol):
    clusters = []
    visited = set()
    for coord in coords:
      if coord in visited:
        continue
      stack = [coord]
      cluster = []
      while stack:
        current = stack.pop()
        if current in visited:
          continue
        visited.add(current)
        cluster.append(current)
        # Check for neighboring points within the tolerance
        for other in coords:
          if other not in visited:
            if abs(other[0] - current[0]) <= tol and abs(other[1] - current[1]) <= tol:
              stack.append(other)
      clusters.append(cluster)
    return clusters

  # Prepare a 2-color palette: 0 => black, 1 => yellow
  nColors = 2
  palette = [0] * nColors
  palette[0] = ROOT.TColor.GetColor("#000000")  # black
  palette[1] = ROOT.TColor.GetColor("#FFFF00")  # yellow
  palette_arr = array.array('i', palette)
  ROOT.gStyle.SetPalette(nColors, palette_arr)

  number_board = 0

  # Loop over each chip path
  for chip_path in chip_paths:
    numbers = extract_pathNumbers(chip_path)
    number_board = numbers[0]

    if len(numbers) < 4:
      continue
    number_board
    board, og, hybrid, chip_id = numbers[:4]
    chip_str = str(chip_id)

    shortBaseDir = f"D_B({board})_O({og})_H({hybrid})_"
    hist_name = f"{shortBaseDir}PixelAlive_Chip({chip_str})"
    canvas_path = f"{chip_path}/{hist_name}"

    # additional ToT 
    tot_name = f"{shortBaseDir}ToT2D_Chip({chip_str})" 
    tot_canvas_path = f"{chip_path}/{tot_name}"

    def get_hist(rootfile, fullpath, primitive_name):
      c = rootfile.Get(fullpath)
      return c.GetPrimitive(primitive_name) if c else None

    # Grab histograms for each injection type
    h1 = get_hist(f_injtype1, canvas_path, hist_name)
    h5 = get_hist(f_injtype5, canvas_path, hist_name)
    h6 = get_hist(f_injtype6, canvas_path, hist_name)
    h_tot = get_hist(f_injtype5, tot_canvas_path, tot_name)
    if not h1 or not h5 or not h6 or not h_tot:
      continue

    # Clone the hist for our missing bump map
    n_cols = h1.GetXaxis().GetNbins()
    n_rows = h1.GetYaxis().GetNbins()
    h_missing = h1.Clone(f"MissingBumpMap_Chip{chip_str}")
    h_missing.Reset()
    h_missing.SetTitle(f"Missing bump map for chip {chip_str}")

    missing_coords = []

    # Mark each pixel: 0 => missing (black), 1 => good (yellow)
    for row in range(n_rows):
      for col in range(n_cols):
        eff1 = h1.GetBinContent(col+1, row+1)
        eff5 = h5.GetBinContent(col+1, row+1)
        eff6 = h6.GetBinContent(col+1, row+1)
        tot = h_tot.GetBinContent(col+1, row+1)
        if not tot: 
          tot = 0.0
          

        # "Open bump" / "Missing bump" if eff1 ≥ 0.9, eff5 ≤ 1e-5, eff6 ≤ 1e-5
        is_missing = (
          eff1 >= alive_eff and
          (eff5 <= coupled_eff or tot <= tot_eff) and
          eff6 <= uncoupled_eff
        )
        if is_missing:
          missing_coords.append((row, col))
          h_missing.SetBinContent(col+1, row+1, 0)  # black
        else:
          h_missing.SetBinContent(col+1, row+1, 1)  # yellow

    # Identify clusters of missing points after processing all pixels
    num_bad_pixels = len(missing_coords)
    if num_bad_pixels > 1000:
      largest_cluster_size = -999
    else:    
      clusters = find_clusters(missing_coords, cluster_tolerance)
      largest_cluster_size = max((len(cluster) for cluster in clusters), default=0)

    AS[key_AS["crosstalk"][0].format(chip_str)] = num_bad_pixels
    AS[key_AS["crosstalk"][1].format(chip_str)] = largest_cluster_size

    # Set palette/contours so 0->black, 1->yellow
    h_missing.SetContour(nColors)
    h_missing.SetMinimum(-0.5)
    h_missing.SetMaximum(1.5)

    # Draw to canvas
    c = ROOT.TCanvas(f"c_crosstalk_{chip_str}", "", 1200, 900)
    h_missing.Draw("COLZ")

    # Add text with the count of bad pixels
    t = ROOT.TLatex()
    t.SetNDC(True)
    t.SetTextSize(0.03)
    t.DrawLatex(0.15, 0.92, f"Disconnected bumps: {num_bad_pixels}")

    # Export canvas
    export_canvas(c, f"MissingBumpMap_Chip({chip_str})", path_results)

    # Write coordinates to a text file
    txt_file = f"{path_results}/MissingBumps_Chip({chip_str}).txt"
    with open(txt_file, "w") as outtxt:
      outtxt.write("row,col\n")
      for (row, col) in missing_coords:
        outtxt.write(f"{row},{col}\n")

  begin1, num_corrupted1, num_repeat1 = check_health(f_injtype1, number_board)
  if num_repeat1 > 9:
    is_sane = False
    explanation += explanation_template.format("crosstalk1_num_repeat", ">9", "0-9")
  AS[key_AS["crosstalk"][2]] = num_corrupted1

  begin5, num_corrupted5, num_repeat5 = check_health(f_injtype5, number_board)
  if num_repeat5 > 9:
    is_sane = False
    explanation += explanation_template.format("crosstalk5_num_repeat", ">9", "0-9")
  AS[key_AS["crosstalk"][3]] = num_corrupted5

  begin6, num_corrupted6, num_repeat6 = check_health(f_injtype6, number_board)
  if num_repeat6 > 9:
    is_sane = False
    explanation += explanation_template.format("crosstalk3_num_repeat", ">9", "0-9")
  AS[key_AS["crosstalk"][4]] = num_corrupted6


  # Close files
  f_injtype1.Close()
  f_injtype5.Close()
  f_injtype6.Close()

  # Return standard FELIS tuple
  return True, "Crosstalk analysis completed successfully.", AS, is_sane, explanation