from ._shared_imports import *

def get_xray(paths_files, path_results, **kwargs):
  # Canvases

  # Actionable Summary Text
  xray_number = "PLACEHOLDER"
  xray_number_limits = (0, 10)

  is_sane = True
  AS = {}  # Actionable summary for this test.
  explanation = ""
  status = True

  message = ""

  number = 1
  AS[xray_number] = number

  if not in_range(number, xray_number_limits):
    is_sane = False
    explanation += explanation_template.format(xray_number, number, xray_number_limits)

  return status, message, AS, is_sane, explanation
