from ._shared_imports import *

def get_injdelay(paths_files, path_results, **kwargs):
  is_sane = True
  AS = {}  # Actionable summary for this test.
  explanation = ""

  message = ""
  status, path_ROOTFile = get_file_regex(paths_files, regex=r"(?i)(?=.*injectiondelay)(?!.*latency).*\.root$")
  if not status:
    return False, "FELIS ERROR when finding root file for injdelay", None, None, None

  status, paths_chipCanvases = find_rootPaths(path_ROOTFile)
  if not status:
    return False, "FELIS ERROR when finding chip paths file for injdelay", None, None, None

  ROOTFile = ROOT.TFile(path_ROOTFile, "READ")
  ROOT.gStyle.SetImageScaling(3.0)
  ROOT.gROOT.SetBatch(True)

  number_board = 0

  for path_chipCanvases in paths_chipCanvases:
    numbers = extract_pathNumbers(path_chipCanvases)
    number_board = numbers[0]
    chip_id = numbers[-1]

    # Canvases
    injectionDelay_scan_plot = "D_B({0})_O({1})_H({2})_InjDelayScan_Chip({3})".format(*numbers)
    injectionDelay_best_plot = "D_B({0})_O({1})_H({2})_InjectionDelay_Chip({3})".format(*numbers)

    # Actionable Summary Text
    injdelay_mean = key_AS["injdelay"][0].format(chip_id)
    injdelay_mean_limits = (0, 60)
    injdelay_stddev = key_AS["injdelay"][1].format(chip_id)
    injdelay_stddev_limits = (0, 32)
    injdelay_best = key_AS["injdelay"][2].format(chip_id)
    injdelay_best_limits = (0, 50)

    tdirectory = ROOTFile.Get(path_chipCanvases)

    name_canvas = injectionDelay_scan_plot
    canvas = tdirectory.Get(name_canvas)
    export_canvas(canvas, name_canvas, path_results)

    histogram = canvas.GetPrimitive(name_canvas)
    mean, std_dev = histogram.GetMean(), histogram.GetStdDev()
    AS[injdelay_mean] = mean
    AS[injdelay_stddev] = std_dev

    if not in_range(mean, injdelay_mean_limits):
      is_sane = False
      explanation += explanation_template.format(injdelay_mean, mean, injdelay_mean_limits)

    if not in_range(std_dev, injdelay_stddev_limits):
      is_sane = False
      explanation += explanation_template.format(injdelay_stddev, std_dev, injdelay_stddev_limits)

    name_canvas = injectionDelay_best_plot
    canvas = tdirectory.Get(name_canvas)

    histogram = canvas.GetPrimitive(name_canvas)
    mean = histogram.GetMean()
    AS[injdelay_best] = mean

    if not in_range(mean, injdelay_best_limits):
      is_sane = False
      explanation += explanation_template.format(injdelay_best, mean, injdelay_best_limits)

  begin, num_corrupted, num_repeat = check_health(ROOTFile, number_board)
  if num_repeat > 9:
    is_sane = False
    explanation += explanation_template.format("injdelay_num_repeat", ">9", "0-9")
  AS[key_AS["injdelay"][3]] = num_corrupted

  ROOTFile.Close()
  return status, message, AS, is_sane, explanation
