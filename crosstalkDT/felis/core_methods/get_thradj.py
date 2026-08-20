from ._shared_imports import *

def get_thradj(paths_files, path_results, **kwargs):
  is_sane = True
  AS = {}  # Actionable summary for this test.
  explanation = ""

  message = ""
  status, path_ROOTFile = get_file_regex(paths_files)
  if not status:
    return False, "FELIS ERROR when finding root file for thradj", None, None, None

  status, paths_chipCanvases = find_rootPaths(path_ROOTFile)
  if not status:
    return False, "FELIS ERROR when finding chip paths file for thradj", None, None, None

  ROOTFile = ROOT.TFile(path_ROOTFile, "READ")
  ROOT.gStyle.SetImageScaling(3.0)
  ROOT.gROOT.SetBatch(True)

  number_board = 0

  for path_chipCanvases in paths_chipCanvases:
    numbers = extract_pathNumbers(path_chipCanvases)
    number_board = numbers[0]
    chip_id = numbers[-1]

    # Canvases
    threshold_plot = "D_B({0})_O({1})_H({2})_Threshold_Chip({3})".format(*numbers)
    occ_1D_plot = "D_B({0})_O({1})_H({2})_Occ1D_Chip({3})".format(*numbers)
    ToT_1D_plot = "D_B({0})_O({1})_H({2})_ToT1D_Chip({3})".format(*numbers)

    # Actionable Summary Text
    thradj_gdac = key_AS["thradj"][0].format(chip_id)
    thradj_gdac_limits = (300, 500)

    tdirectory = ROOTFile.Get(path_chipCanvases)

    # Gets AS from Threshold_Chip canvas.
    name_canvas = threshold_plot
    canvas = tdirectory.Get(name_canvas)  # Will there ever be different L,M,R values of gdac?

    histogram = canvas.GetPrimitive(name_canvas)
    mode = histogram.GetBinCenter(histogram.GetMaximumBin())
    AS[thradj_gdac] = mode

    if not in_range(mode, thradj_gdac_limits):
      is_sane = False
      explanation += explanation_template.format(thradj_gdac, mode, thradj_gdac_limits)

    name_canvas = occ_1D_plot
    canvas = tdirectory.Get(name_canvas)
    export_canvas(canvas, name_canvas, path_results)

    name_canvas = ToT_1D_plot
    canvas = tdirectory.Get(name_canvas)
    export_canvas(canvas, name_canvas, path_results)

  begin, num_corrupted, num_repeat = check_health(ROOTFile, number_board)
  if num_repeat > 9:
    is_sane = False
    explanation += explanation_template.format("thradj_num_repeat", ">9", "0-9")
  AS[key_AS["thradj"][1]] = num_corrupted

  ROOTFile.Close()
  return status, message, AS, is_sane, explanation
