from ._shared_imports import *

def get_scurve(paths_files, path_results, **kwargs):
  is_sane = True
  AS = {}  # Actionable summary for this test.
  explanation = ""

  message = ""
  status, path_ROOTFile = get_file_regex(paths_files)
  if not status:
    return False, "FELIS ERROR when finding root file for scurve", None, None, None

  status, paths_chipCanvases = find_rootPaths(path_ROOTFile)
  if not status:
    return False, "FELIS ERROR when finding chip paths file for scurve", None, None, None

  ROOTFile = ROOT.TFile(path_ROOTFile, "READ")
  ROOT.gStyle.SetImageScaling(3.0)
  ROOT.gROOT.SetBatch(True)

  number_board = 0

  for path_chipCanvases in paths_chipCanvases:
    numbers = extract_pathNumbers(path_chipCanvases)
    number_board = numbers[0]
    chip_id = numbers[-1]

    # Canvases
    scurve_threshold_1d_plot = "D_B({0})_O({1})_H({2})_Threshold1D_Chip({3})".format(*numbers)
    scurve_noise_1d_plot = "D_B({0})_O({1})_H({2})_Noise1D_Chip({3})".format(*numbers)
    scurve_scurves_1d_plot = "D_B({0})_O({1})_H({2})_SCurves_Chip({3})".format(*numbers)
    # Actionable Summary Text
    scurve_threshold_mean = key_AS["scurve"][0].format(chip_id)
    scurve_threshold_mean_limits = (100, 1000)
    scurve_threshold_width = key_AS["scurve"][1].format(chip_id)
    scurve_threshold_width_limits = (0, 200)
    scurve_noise_mean = key_AS["scurve"][2].format(chip_id)
    scurve_noise_mean_limits = (0, 60)
    scurve_noise_width = key_AS["scurve"][3].format(chip_id)
    scurve_noise_width_limits = (0, 20)

    tdirectory = ROOTFile.Get(path_chipCanvases)

    # Gets AS from threshold_1d canvas.
    name_canvas = scurve_threshold_1d_plot
    canvas = tdirectory.Get(name_canvas)
    # canvas.SetLogy() # TODO decide on this, axis formatting issue
    export_canvas(canvas, name_canvas, path_results)

    histogram = canvas.GetPrimitive(name_canvas)
    mean, std_dev = histogram.GetMean(), histogram.GetStdDev()
    AS[scurve_threshold_mean] = mean
    AS[scurve_threshold_width] = std_dev

    if not in_range(mean, scurve_threshold_mean_limits):
      is_sane = False
      explanation += explanation_template.format(scurve_threshold_mean, mean, scurve_threshold_mean_limits)

    if not in_range(std_dev, scurve_threshold_width_limits):
      is_sane = False
      explanation += explanation_template.format(scurve_threshold_width, std_dev, scurve_threshold_width_limits)

    # Gets AS from noise_1d canvas.
    name_canvas = scurve_noise_1d_plot
    canvas = tdirectory.Get(name_canvas)
    # canvas.SetLogy() # TODO decide on this, axis formatting issue
    export_canvas(canvas, name_canvas, path_results)

    histogram = canvas.GetPrimitive(name_canvas)
    mean, std_dev = histogram.GetMean(), histogram.GetStdDev()
    AS[scurve_noise_mean] = mean
    AS[scurve_noise_width] = std_dev

    if not in_range(mean, scurve_noise_mean_limits):
      is_sane = False
      explanation += explanation_template.format(scurve_noise_mean, mean, scurve_noise_mean_limits)

    if not in_range(std_dev, scurve_noise_width_limits):
      is_sane = False
      explanation += explanation_template.format(scurve_noise_width, std_dev, scurve_noise_width_limits)

    # Gets AS from scurve_1d canvas.
    name_canvas = scurve_scurves_1d_plot
    canvas = tdirectory.Get(name_canvas)
    canvas.SetLogz()
    export_canvas(canvas, name_canvas, path_results)  

  begin, num_corrupted, num_repeat = check_health(ROOTFile, number_board)
  if num_repeat > 9:
    is_sane = False
    explanation += explanation_template.format("scurve_num_repeat", ">9", "0-9")
  AS[key_AS["scurve"][4]] = num_corrupted

  ROOTFile.Close()
  return status, message, AS, is_sane, explanation
