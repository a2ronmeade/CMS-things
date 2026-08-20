import ROOT, requests, re, array, os, math  # noqa: E401

# URLs
url_accountInfo = "https://panthera.fit.edu/request_handlers/felis_get_accountInfo.php"

# Sanity explanation Template
explanation_template = "Insane: {} has value {} and is not in interval {} \n"

def extract_pathNumbers(path):
  pattern = r"_(\d+)"  # Find all numbers to the right of an underscore
  numbers = re.findall(pattern, path)
  numbers = [int(num) for num in numbers]
  return numbers

def in_range(value, range):
  if range[0] <= value <= range[1]:
    return True
  else:
    return False

def export_canvas(canvas, name_canvas, path_results):
  canvas.Draw()
  canvas.SetCanvasSize(1200, 900)
  canvas.Update()
  canvas.SaveAs(path_results + "/" + name_canvas + ".png")
  #canvas.SaveAs(path_results + "/" + name_canvas + ".svg") # Take up too much space!

def get_file_regex(paths_files, regex=r"(?i)(?=.*run)(?!.*monitor).*\.root$", multiple=False):
  """
  Returns matching file paths based on regex pattern.

  If `multiple=True`, returns all matching files as a list.
  If `multiple=False`, returns a single file only if exactly one match is found.
  """
  matches = [path for path in paths_files if re.search(regex, path)]

  if multiple:
    return bool(matches), matches  # Return all matching files
  elif len(matches) == 1:
    return True, matches[0]  # Return single match if exactly one file is found
  else:
    return False, None  # Return False if no match or multiple matches and `multiple=False`

def find_rootPaths(file_path, pattern = r"Detector/Board_\d+/OpticalGroup_\d+/Hybrid_\d+/Chip_\d+"):
  # Returns a list of paths inside the root file that match the pattern
  def recursive_search(directory, current_path):
    paths = []
    for key in directory.GetListOfKeys():
      obj_name = key.GetName()
      obj = key.ReadObj()
      new_path = f"{current_path}/{obj_name}" if current_path else obj_name
      if isinstance(obj, ROOT.TDirectoryFile):
        if re.fullmatch(pattern, new_path):
          paths.append(new_path)
        paths.extend(recursive_search(obj, new_path))
      elif re.fullmatch(pattern, new_path):
        paths.append(new_path)
    return paths

  root_file = ROOT.TFile.Open(file_path)
  if not root_file or root_file.IsZombie():
    return False, []

  try:
    matching_paths = recursive_search(root_file, "")
  finally:
    root_file.Close()

  return (True, matching_paths) if matching_paths else (False, [])

def get_accountInfo(username: str, userpass: str) -> tuple[bool, str, dict]:
  """
  Given a username and password, gets account information from panthera.
  Args:
    username (str): Username
    userpass (str): Password

  Returns:
    status (bool): Whether it ran successfully.
    message (str): Details about the status.
    data (dict): Dictionary of user data. Returns None if failed to connect.
  """
  try:
    response = requests.post(url_accountInfo, data={"username": username, "userpass": userpass}, timeout=60)
    if response.status_code == 200:
      if response.headers.get('Content-Type') == 'application/json':
        return True, "Account query ran successfully.", response.json()
      else:
        return False, response.text, None
    else:
      return False, f"Failed to query server for account info. Server responded with status code: {response.status_code}", None
  except requests.exceptions.RequestException as e:
    # Handle exceptions related to the request itself, such as network problems.
    return False, f"Request failed: {str(e)}", None

# Mapping between (subdetector, moduleType, chipID) to a universal chip ID
# This, unfortunately, has nothing to do with Panthera's universal chip ID
flip_map = {
  "TFPX": {12: "flipV", 13: "flipV", 14: "flipH", 15: "flipH"},
  "TBPX": {1: "flipV", 0: "flipV", 2: "flipH", 3: "flipH"},
  "TEPX": {14: "flipV", 15: "flipV", 13: "flipH", 12: "flipH"}
}

# Returns a TCanvas
# Arguments = string, integer, TH1F
def flip_chip(subdetector, chipID, h_original):
  
  flipDir = flip_map[subdetector][chipID]
  c_inverted = ROOT.TCanvas("c_inverted", "c_inverted", 700, 700)
  
  if (flipDir == "flipV"):

    # Create vertically inverted histogram (flipping bin contents)
    nbinsX = h_original.GetNbinsX()
    nbinsY = h_original.GetNbinsY()
    h_inverted = ROOT.TH2F("h_inverted", h_original.GetTitle()+"; Columns; Rows", nbinsX, 0, nbinsX, nbinsY, 0, nbinsY)
    for i in range(0, nbinsX + 1):
      for j in range(0, nbinsY + 1):
        h_inverted.SetBinContent(i, nbinsY - j + 1, h_original.GetBinContent(i, j))
    h_inverted.SetMinimum(0)

    # Draw the canvas
    h_inverted.Draw("colz")
    h_inverted.GetYaxis().SetLabelOffset(999)
    h_inverted.GetYaxis().SetTickLength(0)

    # Invert the y-axis
    gaxis = ROOT.TGaxis(0, nbinsY, 0, 0, 0, nbinsY, 10, "+R")
    gaxis.SetLabelFont(42)
    gaxis.SetLabelSize(0.035)
    gaxis.SetNdivisions(510)
    gaxis.Draw()

    c_inverted._hist = h_inverted
    c_inverted._gaxis = gaxis
    c_inverted.Update()
    return c_inverted

  elif (flipDir == "flipH"):

    # Create horizontally inverted histogram (flipping bin contents)
    nbinsX = h_original.GetNbinsX()
    nbinsY = h_original.GetNbinsY()
    h_inverted = ROOT.TH2F("h_inverted", h_original.GetTitle()+"; ; Rows", nbinsX, 0, nbinsX, nbinsY, 0, nbinsY)
    for i in range(0, nbinsX + 1):
      for j in range(0, nbinsY + 1):
        h_inverted.SetBinContent(nbinsX - i +1, j, h_original.GetBinContent(i, j))

    # Draw the canvas
    h_inverted.Draw("colz")
    h_inverted.GetXaxis().SetLabelOffset(999)
    h_inverted.GetXaxis().SetTickLength(0)

    # Invert the x-axis
    gaxis = ROOT.TGaxis(nbinsX, 0, 0, 0, 0, nbinsX, 10, "-R")
    gaxis.SetLabelFont(42)
    gaxis.SetLabelSize(0.035)
    gaxis.SetNdivisions(510)
    gaxis.Draw()

    c_inverted._hist = h_inverted
    c_inverted._gaxis = gaxis
    c_inverted.Update()
    return c_inverted

#health check command that returns if calibration occured correctly, number of corrupted packets, and number of calibration trials
def check_health(file, int_board):
  tdir = file.Get("Detector/Board_{0}".format(int_board))
  beginOfCalib = int(tdir.Get("D_ITBeginOfCalib_Board_({0})".format(int_board)).GetString().Data())
  endOfCalibNcorruptedPackets = int(tdir.Get("D_ITEndOfCalibNcorruptedPackets_Board_({0})".format(int_board)).GetString().Data())
  endOfCalibNtrialsPackets = int(tdir.Get("D_ITEndOfCalibNtrialsPackets_Board_({0})".format(int_board)).GetString().Data())
  return [beginOfCalib, endOfCalibNcorruptedPackets, endOfCalibNtrialsPackets]

  #add numbers[0] to every check health call, 
  #number is usually called in a function, get it from that and add it


  