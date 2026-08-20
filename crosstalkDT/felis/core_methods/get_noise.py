from ._shared_imports import *

def get_noise(paths_files, path_results, **kwargs):
  # TODO
  # extract the number of masked pixels, 2d masked pixels canvas, lims between 0 and 5000

  is_sane = True
  AS = {}  # Actionable summary for this test.
  explanation = ""

  message = ""
  status, path_ROOTFile = get_file_regex(paths_files)
  if not status:
    return False, "FELIS ERROR when finding root file for noise", None, None, None

  status, paths_chipCanvases = find_rootPaths(path_ROOTFile)
  if not status:
    return False, "FELIS ERROR when finding chip paths file for noise", None, None, None

  ROOTFile = ROOT.TFile(path_ROOTFile, "READ")
  ROOT.gStyle.SetImageScaling(3.0)
  ROOT.gROOT.SetBatch(True)

  number_board = 0

  for path_chipCanvases in paths_chipCanvases:
    numbers = extract_pathNumbers(path_chipCanvases)
    number_board = numbers[0]
    chip_id = numbers[-1]

    # Canvases
    masked_pixels_plot = "D_B({0})_O({1})_H({2})_Masked1Dcol_Chip({3})".format(*numbers)

    # Actionable Summary Text
    num_masked_pixels = key_AS["noise"][0].format(chip_id)
    num_masked_pixels_limits = (0, 1000)

    tdirectory = ROOTFile.Get(path_chipCanvases)

    name_canvas = masked_pixels_plot
    canvas = tdirectory.Get(name_canvas)
    export_canvas(canvas, name_canvas, path_results)

    histogram = canvas.GetPrimitive(name_canvas)
    num_pixels = histogram.GetEntries()
    AS[num_masked_pixels] = num_pixels

    if not in_range(num_pixels, num_masked_pixels_limits):
      is_sane = False
      explanation += explanation_template.format(num_masked_pixels, num_pixels, num_masked_pixels_limits)

  
  begin, num_corrupted, num_repeat = check_health(ROOTFile, number_board)
  if num_repeat > 9:
    is_sane = False
    explanation += explanation_template.format("noise_num_repeat", ">9", "0-9")
  AS[key_AS["noise"][1]] = num_corrupted

  ROOTFile.Close()
  return status, message, AS, is_sane, explanation
