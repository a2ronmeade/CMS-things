from ._shared_imports import *

def get_threqu(paths_files, path_results, **kwargs):
  is_sane = True
  AS = {}  # Actionable summary for this test.
  explanation = ""

  message = ""
  status, path_ROOTFile = get_file_regex(paths_files)
  if not status:
    return False, "FELIS ERROR when finding root file for threqu", None, None, None

  status, paths_chipCanvases = find_rootPaths(path_ROOTFile)
  if not status:
    return False, "FELIS ERROR when finding chip paths file for threqu", None, None, None

  # Sanity check limits
  tdac_mean_limits = (5, 25)
  tdac_stddev_limits = (0, 999)
  tdac_outlier_limits = (0, 99999)

  ROOTFile = ROOT.TFile(path_ROOTFile, "READ")
  ROOT.gStyle.SetImageScaling(3.0)
  ROOT.gROOT.SetBatch(True)

  number_board = 0

  for path_chipCanvases in paths_chipCanvases:
    numbers = extract_pathNumbers(path_chipCanvases)
    number_board = numbers[0]
    chip_id = numbers[-1]

    # Anticipate canvas names
    str_TDAC1D = "D_B({0})_O({1})_H({2})_TDAC1D_Chip({3})".format(*numbers)
    str_Occ1D = "D_B({0})_O({1})_H({2})_Occ1D_Chip({3})".format(*numbers)
    str_ToT1D = "D_B({0})_O({1})_H({2})_ToT1D_Chip({3})".format(*numbers)

    # Actionable Summary Keys
    str_tdac_mean = key_AS["threqu"][0].format(chip_id)
    str_tdac_stddev = key_AS["threqu"][1].format(chip_id)
    str_tdac_outlier = key_AS["threqu"][2].format(chip_id)

    # Extract canvases, make plots, extract histograms
    tdirectory = ROOTFile.Get(path_chipCanvases)
    canvas = tdirectory.Get(str_TDAC1D)
    export_canvas(canvas, str_TDAC1D, path_results)

    h_TDAC1D = canvas.GetPrimitive(str_TDAC1D)
    tdac_mean = h_TDAC1D.GetMean()
    tdac_stddev = h_TDAC1D.GetStdDev()
    tdac_outlierlo = h_TDAC1D.GetBinContent(1)
    tdac_outlierhi = h_TDAC1D.GetBinContent(h_TDAC1D.GetNbinsX())
    tdac_outlier = tdac_outlierlo + tdac_outlierhi

    AS[str_tdac_mean] = tdac_mean
    AS[str_tdac_stddev] = tdac_stddev
    AS[str_tdac_outlier] = tdac_outlier

    if not in_range(tdac_mean, tdac_mean_limits):
      is_sane = False
      explanation += explanation_template.format(str_tdac_mean, tdac_mean, tdac_mean_limits)

    if not in_range(tdac_stddev, tdac_stddev_limits):
      is_sane = False
      explanation += explanation_template.format(str_tdac_stddev, tdac_stddev, tdac_stddev_limits)

    if not in_range(tdac_outlier, tdac_outlier_limits):
      is_sane = False
      explanation += explanation_template.format(str_tdac_outlier, tdac_outlier, tdac_outlier_limits)

    canvas = tdirectory.Get(str_Occ1D)
    export_canvas(canvas, str_Occ1D, path_results)

    canvas = tdirectory.Get(str_ToT1D)
    export_canvas(canvas, str_ToT1D, path_results)

  begin, num_corrupted, num_repeat = check_health(ROOTFile, number_board)
  if num_repeat > 9:
    is_sane = False
    explanation += explanation_template.format("threqu_num_repeat", ">9", "0-9")
  AS[key_AS["threqu"][3]] = num_corrupted
  
  ROOTFile.Close()
  return status, message, AS, is_sane, explanation
