from ._shared_imports import *

def get_thrmin(paths_files, path_results, **kwargs):
  # Canvases

  # Actionable Summary Text
  thrmin_number = key_AS["thrmin"][0]
  thrmin_number_limits = (90, 200)

  is_sane = True
  AS = {}  # Actionable summary for this test.
  explanation = ""

  message = ""
  status, path_ROOTFile = get_file_regex(paths_files)
  if not status:
    return False, "FELIS ERROR when finding root file for thrmin", None, None, None

  status, paths_chipCanvases = find_rootPaths(path_ROOTFile)
  if not status:
    return False, "FELIS ERROR when finding chip paths file for thrmin", None, None, None

  for path_chipCanvases in paths_chipCanvases:
    chip_id = path_chipCanvases[-2:]

    number = 1
    AS[thrmin_number.format(chip_id)] = number

    if not in_range(number, thrmin_number_limits):
      is_sane = False
      explanation += explanation_template.format(thrmin_number.format(chip_id), number, thrmin_number_limits)

  return status, message, AS, is_sane, explanation
