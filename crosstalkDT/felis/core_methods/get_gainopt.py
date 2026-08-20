from ._shared_imports import *

#untested as nobody runs it so no root files, should work
def get_gainopt(paths_files, path_results, **kwargs):
  # Canvases
  number_board = 0

  # Actionable Summary Text
  gainopt_number = key_AS["gainopt"][0]
  gainopt_number_limits = (90, 200)

  is_sane = True
  AS = {}  # Actionable summary for this test.
  explanation = ""

  message = ""
  status, path_ROOTFile = get_file_regex(paths_files)
  if not status:
    return False, "FELIS ERROR when finding root file for gainopt", None, None, None

  status, paths_chipCanvases = find_rootPaths(path_ROOTFile)
  if not status:
    return False, "FELIS ERROR when finding chip paths file for gainopt", None, None, None

 
  for path_chipCanvases in paths_chipCanvases:
    numbers = extract_pathNumbers(path_chipCanvases)
    number_board = numbers[0]
    chip_id = path_chipCanvases[-1]

    number = 1
    AS[gainopt_number.format(chip_id)] = number

    if not in_range(number, gainopt_number_limits):
      is_sane = False
      explanation += explanation_template.format(gainopt_number.format(chip_id), number, gainopt_number_limits)

  ROOTFile = ROOT.TFile(path_ROOTFile, "READ")
  begin, num_corrupted, num_repeat = check_health(ROOTFile, number_board)
  if num_repeat > 9:
    is_sane = False
    explanation += explanation_template.format("gainopt_num_repeat", ">9", "0-9")
  AS[key_AS["gainopt"][0]] = num_corrupted

  return status, message, AS, is_sane, explanation
