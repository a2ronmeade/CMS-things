from ._shared_imports import *

def get_latency(paths_files, path_results, **kwargs):
  is_sane = True
  AS = {}  # Actionable summary for this test.
  explanation = ""

  message = ""
  status, path_ROOTFile = get_file_regex(paths_files)
  if not status:
    return False, "FELIS ERROR when finding root file for latency", None, None, None

  status, paths_chipCanvases = find_rootPaths(path_ROOTFile)
  if not status:
    return False, "FELIS ERROR when finding chip paths file for latency", None, None, None

  ROOTFile = ROOT.TFile(path_ROOTFile, "READ")
  ROOT.gStyle.SetImageScaling(3.0)
  ROOT.gROOT.SetBatch(True)

  number_board = 0

  for path_chipCanvases in paths_chipCanvases:
    numbers = extract_pathNumbers(path_chipCanvases)
    number_board = numbers[0]
    chip_id = numbers[-1]


    # Canvases
    latency_plot = "D_B({0})_O({1})_H({2})_LatencyScan_Chip({3})".format(*numbers)

    # Actionable Summary Text
    latency_mode = key_AS["latency"][0].format(chip_id)
    latency_mode_limits = (0, 512)
    latency_width = key_AS["latency"][1].format(chip_id)
    latency_width_limits = (0, 512)

    tdirectory = ROOTFile.Get(path_chipCanvases)

    # Gets AS from Latency Scan canvas.
    name_canvas = latency_plot
    canvas = tdirectory.Get(name_canvas)
    canvas.SetLogy()
    #if not canvas:
    #  print(f"FELIS FELIS ERROR: Canvas {name_canvas} not found")
    export_canvas(canvas, name_canvas, path_results)

    histogram = canvas.GetPrimitive(name_canvas)
    std_dev = histogram.GetStdDev()
    mode = histogram.GetBinCenter(histogram.GetMaximumBin())
    
    AS[latency_mode] = mode
    AS[latency_width] = std_dev

    if not in_range(mode, latency_mode_limits):
      is_sane = False
      explanation += explanation_template.format(latency_mode, mode, latency_mode_limits)

    if not in_range(std_dev, latency_width_limits):
      is_sane = False
      explanation += explanation_template.format(latency_width, std_dev, latency_width_limits)

  begin, num_corrupted, num_repeat = check_health(ROOTFile, number_board)
  if num_repeat > 9:
    is_sane = False
    explanation += explanation_template.format("latency_num_repeat", ">9", "0-9")
  AS[key_AS["latency"][2]] = num_corrupted
 
  ROOTFile.Close()
  return status, message, AS, is_sane, explanation
