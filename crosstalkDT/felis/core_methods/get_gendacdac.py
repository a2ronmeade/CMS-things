from ._shared_imports import *

def get_gendacdac(paths_files, path_results, **kwargs):
  is_sane = True
  AS = {}  # Actionable summary for this test.
  explanation = ""

  message = ""
  status, path_ROOTFile = get_file_regex(paths_files)
  if not status:
    return False, "FELIS ERROR when finding root file for gendacdac", None, None, None

  status, paths_chipCanvases = find_rootPaths(path_ROOTFile)
  if not status:
    return False, "FELIS ERROR when finding chip paths file for gendacdac", None, None, None

  ROOTFile = ROOT.TFile(path_ROOTFile, "READ")
  ROOT.gStyle.SetImageScaling(3.0)
  ROOT.gROOT.SetBatch(True)

  for path_chipCanvases in paths_chipCanvases:
    numbers = extract_pathNumbers(path_chipCanvases)
    #chip_id = numbers[-1]

    # Canvases
    genDac_plot = "D_B({0})_O({1})_H({2})_GenericDacDacScanScan_Chip({3})".format(*numbers)

    tdirectory = ROOTFile.Get(path_chipCanvases)

    name_canvas = genDac_plot
    canvas = tdirectory.Get(name_canvas)
    export_canvas(canvas, name_canvas, path_results)

  ROOTFile.Close()
  return status, message, AS, is_sane, explanation
