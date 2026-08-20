from ._shared_imports import *

def get_gain(paths_files, path_results, **kwargs):
  is_sane = True
  AS = {}  # Actionable summary for this test.
  explanation = ""

  message = ""
  status, path_ROOTFile = get_file_regex(paths_files)
  if not status:
    return False, "FELIS ERROR when finding root file for gain", None, None, None

  status, paths_chipCanvases = find_rootPaths(path_ROOTFile)
  if not status:
    return False, "FELIS ERROR when finding chip paths file for gain", None, None, None

  ROOTFile = ROOT.TFile(path_ROOTFile, "READ")
  ROOT.gStyle.SetImageScaling(3.0)
  ROOT.gROOT.SetBatch(True)

  number_board = 0

  for path_chipCanvases in paths_chipCanvases:
    numbers = extract_pathNumbers(path_chipCanvases)
    number_board = numbers[0]
    chip_id = numbers[-1]

    # Canvases
    gain_scan_plot = "D_B({0})_O({1})_H({2})_Gain_Chip({3})".format(*numbers)
    slope_distro_plot = "D_B({0})_O({1})_H({2})_SlopeLowQ1D_Chip({3})".format(*numbers)
    intercept_distro_plot = "D_B({0})_O({1})_H({2})_InterceptLowQ1D_Chip({3})".format(*numbers)

    # Actionable Summary Text
    gain_slope_mean = key_AS["gain"][0].format(chip_id)
    gain_slope_mean_limits = (0, .1)
    gain_slope_width = key_AS["gain"][1].format(chip_id)
    gain_slope_width_limits = (0, .05)
    gain_intercept_mean = key_AS["gain"][2].format(chip_id)
    gain_intercept_mean_limits = (-15, 0)
    gain_intercept_width = key_AS["gain"][3].format(chip_id)
    gain_intercept_width_limits = (0, 2)

    tdirectory = ROOTFile.Get(path_chipCanvases)

    name_canvas = gain_scan_plot
    canvas = tdirectory.Get(name_canvas)
    export_canvas(canvas, name_canvas, path_results)

    name_canvas = slope_distro_plot
    canvas = tdirectory.Get(name_canvas)
    export_canvas(canvas, name_canvas, path_results)

    histogram = canvas.GetPrimitive(name_canvas)
    mean, std_dev = histogram.GetMean(), histogram.GetStdDev()
    AS[gain_slope_mean] = mean
    AS[gain_slope_width] = std_dev

    if not in_range(mean, gain_slope_mean_limits):
      is_sane = False
      explanation += explanation_template.format(gain_slope_mean, mean, gain_slope_mean_limits)

    if not in_range(std_dev, gain_slope_width_limits):
      is_sane = False
      explanation += explanation_template.format(gain_slope_width, std_dev, gain_slope_width_limits)

    name_canvas = intercept_distro_plot
    canvas = tdirectory.Get(name_canvas)
    export_canvas(canvas, name_canvas, path_results)

    histogram = canvas.GetPrimitive(name_canvas)
    mean, std_dev = histogram.GetMean(), histogram.GetStdDev()
    AS[gain_intercept_mean] = mean
    AS[gain_intercept_width] = std_dev

    if not in_range(mean, gain_intercept_mean_limits):
      is_sane = False
      explanation += explanation_template.format(gain_intercept_mean, mean, gain_intercept_mean_limits)

    if not in_range(std_dev, gain_intercept_width_limits):
      is_sane = False
      explanation += explanation_template.format(gain_intercept_width, std_dev, gain_intercept_width_limits)

  begin, num_corrupted, num_repeat = check_health(ROOTFile, number_board)
  if num_repeat > 9:
    is_sane = False
    explanation += explanation_template.format("gain_num_repeat", ">9", "0-9")
  AS[key_AS["gain"][4]] = num_corrupted

  ROOTFile.Close()
  return status, message, AS, is_sane, explanation
