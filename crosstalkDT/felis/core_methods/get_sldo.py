from ._shared_imports import *

def get_sldo(paths_files, path_results, **kwargs):
  is_sane = True
  AS = {}  # Actionable summary for this test.
  explanation = ""

  message = ""
  status, path_ROOTFile = get_file_regex(paths_files)
  if not status:
    return False, "FELIS ERROR when finding root file for sldo", None, None, None

  status, paths_chipCanvases = find_rootPaths(path_ROOTFile)
  if not status:
    return False, "FELIS ERROR when finding chip paths file for sldo", None, None, None

  ROOTFile = ROOT.TFile(path_ROOTFile, "READ")
  ROOT.gStyle.SetImageScaling(3.0)
  ROOT.gROOT.SetBatch(True)


  for path_chipCanvases in paths_chipCanvases:
    numbers = extract_pathNumbers(path_chipCanvases)
    chip_id = numbers[-1]

    # Canvases
    sldo_analog_plot = "D_B({0})_O({1})_H({2})_SLDO_Analog_Chip({3})".format(*numbers)
    sldo_digital_plot = "D_B({0})_O({1})_H({2})_SLDO_Digital_Chip({3})".format(*numbers)

    # Actionable Summary Text
    sldo_number = key_AS["sldo"][0].format(chip_id)
    sldo_number_limits = (0, 1)

    tdirectory = ROOTFile.Get(path_chipCanvases)

    name_canvas = sldo_analog_plot
    canvas = tdirectory.Get(name_canvas)
    export_canvas(canvas, name_canvas, path_results)

    name_canvas = sldo_digital_plot
    canvas = tdirectory.Get(name_canvas)
    export_canvas(canvas, name_canvas, path_results)

    AS[sldo_number] = .5

    if not in_range(.5, sldo_number_limits):
      is_sane = False
      explanation += explanation_template.format(sldo_number, .5, sldo_number_limits)

  return status, message, AS, is_sane, explanation
