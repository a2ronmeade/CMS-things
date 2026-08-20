from ._shared_imports import *

def get_pixelalive(paths_files, path_results, **kwargs):
  module_specs = kwargs.get("module_specs")
  is_sane = True
  AS = {}  # Actionable summary for this test.
  explanation = ""

  message = ""
  status, path_ROOTFile = get_file_regex(paths_files)
  if not status:
    return False, "FELIS ERROR when finding root file for pixelalive", None, None, None

  # Search for OUT.txt files and process them
  status2, paths_TXTFiles = get_file_regex(paths_files, regex=r"(?i).*OUT\.txt$", multiple=True)
  
  # Define the patterns to search for
  core_col_patterns = [
    "EN_CORE_COL_0",
    "EN_CORE_COL_1", 
    "EN_CORE_COL_2",
    "EN_CORE_COL_3"
  ]

  processed_patterns = set()
  total_bad_columns = 0

  if paths_TXTFiles:
    for path in paths_TXTFiles:
      try:
        # Extract chip number from filename
        chip_num_match = re.search(r'_(\d+)_OUT\.txt$', path)
        if chip_num_match:
          chip_num = chip_num_match.group(1)
        else:
          continue  # Skip files that don't match the expected pattern
            
        with open(path, "r", encoding="utf-8") as file:
          for line in file:
            for pattern in core_col_patterns:
              pattern_key = f"{pattern}_CHIP_{chip_num}"
              if pattern in line and pattern_key not in processed_patterns:
                parts = line.split()
                if len(parts) >= 4:
                  hex_val = parts[3]  # Get the Value column

                  # Convert hex to an integer.
                  value = int(hex_val, 16)
                  # Use 6 bits if the value fits in 6 bits, otherwise use 16 bits.
                  expected_length = 6 if value < (1 << 6) else 16
                  # Convert the integer to a binary string padded with zeros.
                  binary_val = format(value, f"0{expected_length}b")
                  
                  # Count the zeros in the fixed-width binary string.
                  num_zeros = binary_val.count("0")
                  
                  AS[key_AS["pixelalive"][0].format(pattern_key)] = num_zeros
                  total_bad_columns += num_zeros
                  AS["PIXELALIVE_{}".format(pattern_key)] = binary_val
                processed_patterns.add(pattern_key)

      except Exception as e:
        print(f"FELIS ERROR processing {path}: {e}")

  # Store total bad columns
  if total_bad_columns > 0:
    AS[key_AS["pixelalive"][1]] = total_bad_columns

  status, paths_chipCanvases = find_rootPaths(path_ROOTFile)
  if not status:
    return False, "FELIS ERROR when finding chip paths file for pixelalive", None, None, None

  ROOTFile = ROOT.TFile(path_ROOTFile, "READ")
  ROOT.gStyle.SetImageScaling(3.0)
  ROOT.gROOT.SetBatch(True)

  # Extract the type of pixelelive if present in the name. Ex analog, digital
  name_test = kwargs.get("name_test")
  type_pixelalive = ""
  match = re.search(r"(?i)pixelalive_(.*)", name_test)
  if match:
    type_pixelalive = match.group(1)
  match = re.search(r"(?i)pixel_alive_(.*)", name_test)
  if match:
    type_pixelalive = match.group(1)
  match = re.search(r"(?i)pixel alive_(.*)", name_test)
  if match:
    type_pixelalive = match.group(1)    
  print("type_pixelalive", type_pixelalive)

  number_board = 0

  for path_chipCanvases in paths_chipCanvases:
    numbers = extract_pathNumbers(path_chipCanvases)
    number_board = numbers[0]
    chip_id = numbers[-1]

    # Canvases
    pixelalive_occ_1d_plot = "D_B({0})_O({1})_H({2})_Occ1D_Chip({3})".format(*numbers)
    pixelalive_occ_2d_plot = "D_B({0})_O({1})_H({2})_PixelAlive_Chip({3})".format(*numbers)
    pixelalive_masked_1d_col_plot = "D_B({0})_O({1})_H({2})_Masked1Dcol_Chip({3})".format(*numbers)

    # Actionable Summary Text
    pixelalive_occ_mean = key_AS["pixelalive"][2].format(chip_id)
    pixelalive_occ_stddev = key_AS["pixelalive"][3].format(chip_id)
    pixelalive_masked1dCol_numEntries = key_AS["pixelalive"][4].format(chip_id)

    tdirectory = ROOTFile.Get(path_chipCanvases)

    # Gets AS from occ_1d canvas.
    name_canvas = pixelalive_occ_1d_plot
    canvas = tdirectory.Get(name_canvas)
    canvas.SetLogy()
    canvas.SetTitle(name_canvas + " " + type_pixelalive)
    title = ROOT.TLatex(0.5, 0.92, type_pixelalive)
    title.SetNDC()
    title.SetTextAlign(22)
    title.SetTextSize(0.03)
    title.Draw()
    export_canvas(canvas, name_canvas, path_results)
    histogram = canvas.GetPrimitive(name_canvas)
    mean, std_dev = histogram.GetMean(), histogram.GetStdDev()
    AS[pixelalive_occ_mean] = mean
    AS[pixelalive_occ_stddev] = std_dev

    # Gets AS from occ_2d canvas.
    ROOT.gStyle.SetPalette(57)
    ROOT.gStyle.SetOptStat(0)  # Hides stats box
    name_canvas = pixelalive_occ_2d_plot
    canvas = tdirectory.Get(name_canvas)
    hist = canvas.GetPrimitive(name_canvas)
    hist.SetMinimum(0)
    canvas = flip_chip(module_specs["subdetector"], chip_id, hist)
    canvas.SetTitle(name_canvas + " " + type_pixelalive)
    title = ROOT.TLatex(0.5, 0.92, type_pixelalive)
    title.SetNDC()
    title.SetTextAlign(22)
    title.SetTextSize(0.03)
    title.Draw()
    export_canvas(canvas, name_canvas, path_results)
    ROOT.gStyle.SetOptStat(1111)  # Brings stats box back
    ROOT.gStyle.SetPalette(112)  # Brings default color palette back

    # Gets AS from masked_1d_col canvas.
    name_canvas = pixelalive_masked_1d_col_plot
    canvas = tdirectory.Get(name_canvas)
    canvas.SetTitle(name_canvas + " " + type_pixelalive)
    title = ROOT.TLatex(0.5, 0.92, type_pixelalive)
    title.SetNDC()
    title.SetTextAlign(22)
    title.SetTextSize(0.03)
    title.Draw()
    export_canvas(canvas, name_canvas, path_results)

    histogram = canvas.GetPrimitive(name_canvas)
    numEntries = histogram.GetEntries()
    AS[pixelalive_masked1dCol_numEntries] = numEntries

  begin, num_corrupted, num_repeat = check_health(ROOTFile, number_board)
  if num_repeat > 9:
    is_sane = False
    explanation += explanation_template.format("pixelalive_num_repeat", ">9", "0-9")
  AS[key_AS["pixelalive"][5]] = num_corrupted

  ROOTFile.Close()
  return status, message, AS, is_sane, explanation
