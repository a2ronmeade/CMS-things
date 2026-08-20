from ._shared_imports import *

def get_voltagetuning(paths_files, path_results, **kwargs):
  # Canvases

  # Actionable Summary Text
  voltagetuning_number = "VOLTAGETUNING_NUMBER_{}"
  voltagetuning_number_limits = (90, 200)

  is_sane = True
  AS = {}  # Actionable summary for this test.
  explanation = ""

  message = ""
  status, path_ROOTFile = get_file_regex(paths_files)
  if not status:
    return False, "FELIS ERROR when finding root file for voltagetuning", None, None, None

  status, paths_chipCanvases = find_rootPaths(path_ROOTFile)
  if not status:
    return False, "FELIS ERROR when finding chip paths file for voltagetuning", None, None, None

  for path_chipCanvases in paths_chipCanvases:
    chip_id = path_chipCanvases[-2:]

    number = 1
    AS[voltagetuning_number.format(chip_id)] = number

    if not in_range(number, voltagetuning_number_limits):
      is_sane = False
      explanation += explanation_template.format(voltagetuning_number.format(chip_id), number, voltagetuning_number_limits)

  return status, message, AS, is_sane, explanation
