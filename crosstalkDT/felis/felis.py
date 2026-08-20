import ROOT, json, zipfile, os, shutil, requests # noqa: E401
from datetime import datetime
from requests_toolbelt.multipart.encoder import MultipartEncoder, MultipartEncoderMonitor
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from tqdm import tqdm
import subprocess

class Felis:

  """
  Middleware between Panthera and test stations.
  """

  # Maps the test types to the Felis functions that extract the actionable summaries.
  get_actionable_summary = {
      "pixelalive": "get_pixelalive",
      "scurve": "get_scurve",
      "latency": "get_latency",
      "thradj": "get_thradj",
      "threqu": "get_threqu",
      "injdelay": "get_injdelay",
      "noise": "get_noise",
      "gain": "get_gain",
      "sldo": "get_sldo",
      "ivcurve": "get_ivcurve",
      "gainopt": "get_gainopt",
      "thrmin": "get_thrmin",
      "clockdelay": "get_clockdelay",
      "bertest": "get_bertest",
      "datarbopt": "get_datarbopt",
      "voltagetuning": "get_voltagetuning",
      "gendacdac": "get_gendacdac",
      "physics": "get_physics",
      "crosstalk": "get_crosstalk",
      "xray": "get_xray"
    }

  def __init__(self, path_scratch: str, clear_scratch: bool = False, verbose: bool = False) -> None:
    """
    Args:
      path_scratch (str): Absolute path to the scratch directory or to an old dict_modules json file.
      clear_scratch (bool): Whether to delete contents of the scratch directory upon instantiation.
        Defaults to false for safety and debug purposes. Set to true for bulk module tests.
      verbose (bool): Whether ROOT should do it's default console prints. Defaults to no.
    """

    # Get the directory of the current file (i.e., the file inside the repo)
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    try:
      self.version = subprocess.check_output(
        ['git', '-C', repo_dir, 'describe', '--tags', '--exact-match'],
        stderr=subprocess.DEVNULL
      ).decode('utf-8').strip()
    except subprocess.CalledProcessError:
      try:
        self.version = subprocess.check_output(
          ['git', '-C', repo_dir, 'rev-parse', '--short', 'HEAD'],
          stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()
      except subprocess.CalledProcessError:
        self.version = "unspecified"

    self.dict_modules = {} # Stores test results and other data for each module. Uses nested dictionaries.
    self.dict_modules["log"] = ""
    print(log := f"FELIS LOG: Initializing Felis {self.version} \n") # := is the walrus operator
    self.dict_modules["log"] += log

    self.verbose = verbose

    if verbose:
      ROOT.gErrorIgnoreLevel = ROOT.kInfo
    else:
      ROOT.gErrorIgnoreLevel = ROOT.kError

    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    # TODO: Handle errors beyond just printing. Return false somehow?
    if os.path.isfile(path_scratch): # Import an old workspace within the scratch space.
      try:
        with open(path_scratch, 'r') as file:
          self.dict_modules = json.load(file)
      except Exception as e:
        print(log := f"FELIS ERROR: An error occurred while trying to read the JSON file: {e} \n")
        self.dict_modules["log"] += log
        self.save_dict_modules()
      self.path_scratch = os.path.dirname(path_scratch)
    elif os.path.isdir(path_scratch): # Make new workspace within the scratch space.
      if clear_scratch: # Deletes scratch directory and remakes it. Simplest way to clear it.
        shutil.rmtree(path_scratch, ignore_errors=True)
        os.makedirs(path_scratch)
      time_instantiation = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") # Time of local machine
      self.path_scratch = path_scratch + "/" + time_instantiation
      os.makedirs(self.path_scratch)
    else:
      print(log := f"FELIS ERROR: The provided path '{path_scratch}' is neither a valid file nor a directory. \n")
      self.dict_modules["log"] += log
      self.save_dict_modules()

  def set_module(self, name_module: str, subdetector: str, type_module: str = "unspecified", croc_version: str = "unspecified",
                 has_sensor: bool = "unspecified", link_production_db: str = "unspecified", type_sensor: str = "unspecified") -> tuple[bool, str]:
    """
    Adds a module to the modules dictionary along with necessary module specs. The name_module and
    subdetector uniquely specify a module and are the only necessary fields. If the module already
    exists in Panthera, there is no need to fill in the other fields.

    Args:
      name_module (str): The name of the module.
      subdetector (str): For example, "TFPX"
      type_module (str): For example, "1x2"
      croc_version (str): For example, "1"
      has_sensor (bool): Set True if the module has the sensor installed.
      link_production_db (str): Link to the Purdue database.

    Returns:
      status (bool): Whether it ran successfully.
      message (str): Details about the status.
    """

    if name_module in self.dict_modules:
      return (False, f"Module '{name_module}' already exists in this workspace.")
    else:
      self.dict_modules[name_module] = {}
      self.dict_modules[name_module]["module_specs"] = {}
      self.dict_modules[name_module]["module_specs"]["name_module"] = name_module
      self.dict_modules[name_module]["module_specs"]["type_module"] = type_module
      self.dict_modules[name_module]["module_specs"]["subdetector"] = subdetector
      self.dict_modules[name_module]["module_specs"]["croc_version"] = croc_version
      self.dict_modules[name_module]["module_specs"]["has_sensor"] = has_sensor
      self.dict_modules[name_module]["module_specs"]["type_sensor"] = type_sensor
      self.dict_modules[name_module]["module_specs"]["link_production_db"] = link_production_db
      self.dict_modules[name_module]["results"] = {}
      self.save_dict_modules()
      return True, f"Module '{name_module}' inserted into workspace."

  def set_comment(self, name_module: str, name_test: str, comment: str) -> tuple[bool, str]:
    """
    Adds a comment to the given test. If there is already a comment, it will be overwritten.

    Args:
      name_module (str): The name of the module.
      name_test (str): The name of the test to comment on.
      comment (str): The comment.

    Returns:
      status (bool): Whether it ran successfully.
      message (str): Details about the status.
    """
    if name_module not in self.dict_modules:
      return False, f"Module '{name_module}' not in workspace."
    elif name_test not in self.dict_modules[name_module]["results"]:
      return False, f"Test name '{name_test}' for module '{name_module}' not in workspace."
    else:
      self.dict_modules[name_module]["results"][name_test]["comment"] += "\n" + comment
      self.save_dict_modules()
      return True, "Comment added successfully."

  def set_result(
    self,
    paths_files: list[str],
    name_module: str,
    name_test: str,
    type_test: str,
    comment: str = ""
    ) -> tuple[bool, str, bool, str]:
    """
    Extracts actionable summary (AS) and plots from a test result ROOT file.

    Args:
      paths_files (list[str]): A list of absolute paths to the files for this result
      name_module (str): The name of the module the result belongs to.
      name_test (str): The name of the test the result belongs to. Test names must be unique.
      type_test (str): The type of test. Must be from official list.
      comment (str): Comment from user. Defaults to empty.

    Returns:
      status (bool): Whether it ran successfully.
      message (str): Details about the status.
      is_sane (bool): Returns false if any one of the AS falls outside the cutoffs. The result is
        still stored however. It can be overwritten if need be.
      explanation (str): String explaining what part of the AS was insane. Returns empty if sane.
    """

    if name_module not in self.dict_modules: # How should I handle this?
      print(log := f"FELIS ERROR: Module '{name_module}' does not exist in this workspace. Use set_module() \n")
      self.dict_modules["log"] += log
      self.save_dict_modules()
      return False, f"FELIS ERROR: Module '{name_module}' does not exist in this workspace. Use set_module()", False, ""

    # Directory for files for this test.
    path_results = self.path_scratch + "/" + name_module + "/" + name_test

    if os.path.exists(path_results): # If this is a rewrite of a given test name, delete old result.
      shutil.rmtree(path_results)
    os.makedirs(path_results)

    # This loop copies the files into the scratch directory.
    for path_file in paths_files:
      try:
        shutil.copy(path_file, path_results)
      except Exception as e: # Note: I could do just "expection:" but that gives no explanation.
        print(log := f"FELIS ERROR: Failed to copy '{path_file}': {e} \n")
        self.dict_modules["log"] += log
        self.save_dict_modules()
        return False, f"FELIS ERROR: Failed to copy '{path_file}': {e}", False, ""

    # This part redefines the paths to the scratch paths.
    paths_files = [path_results + "/" + os.path.basename(path) for path in paths_files]

    dict_results = {}

    status, message, dict_results["AS"], is_sane, explanation = getattr(
      self, self.get_actionable_summary[type_test]
      )(paths_files, path_results, module_specs=self.dict_modules[name_module]["module_specs"], name_test=name_test)

    self.dict_modules["log"] += str((status, message, is_sane, explanation)) + "\n"
    self.save_dict_modules()

    if not status:
      return False, message, None, None

    # Now that I am copying all the files here, do I need to store these paths? Probably not.
    dict_results["paths_files"] = paths_files
    dict_results["type_test"] = type_test
    dict_results["time"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    dict_results["comment"] = comment
    self.dict_modules[name_module]["results"][name_test] = dict_results

    # Save dict_modules to the scratch space for testing/debugging purposes.
    self.save_dict_modules()

    return True, message, is_sane, explanation # Make this better

  def save_dict_modules(self):
    with open(self.path_scratch+"/dict_modules.json", 'w') as file:
      json.dump(self.dict_modules, file, indent=2)

  def upload_results(self, name_module: str, username: str, userpass: str, type_sequence: str = "unnamed", version_ph2acf: str = "unspecified", version_testStationSoftware: str = "unspecified", url_uploadResults: str = "https://panthera.fit.edu/request_handlers/felis_upload_results_piecewise.php") -> tuple[bool, str]:
    """
    Uploads the results for a module to Panthera. Generates a progress bar in the console.

    Args:
      name_module (str): The name of the module.
      username (str): Username of the account under which the results will be uploaded.
      userpass (str): Password of the account.
      type_sequence (str): The type of sequence. Probably from the test sequences gitlab file.
      version_ph2acf (str): The ph2acf version being used.
      version_testStationSoftware (str): The OSU GUI or Dirigent version being used. ex. Dirigent v1.1.1
      url_uploadResults (str): Only use if you are a Panthera dev.

    Returns:
      status (bool): Whether it ran successfully.
      message (str): Details about the status.
    """
    status = False
    message = ""

    dict_post = self.dict_modules[name_module]["module_specs"].copy()
    dict_post["results"] = self.dict_modules[name_module]["results"]
    dict_post["type_sequence"] = type_sequence
    dict_post["version_ph2acf"] = version_ph2acf
    dict_post["version_testStationSoftware"] = version_testStationSoftware
    dict_post["version_felis"] = self.version

    with open(self.path_scratch + "/dict_post.json", 'w') as file:
      json.dump(dict_post, file, indent=2)

    dir_results = self.path_scratch + "/" + name_module
    names_tests = self.dict_modules[name_module]["results"].keys()
    with open(self.path_scratch + "/dict_modules.json", 'rb') as json_file:
      dict_files = {'username': username, 'userpass': userpass, 'json_data': json.dumps(dict_post), 'dict_modules_file': ('dict_modules.json', json_file, 'application/json')}
      # Call set_sequence
      print(log := "FELIS LOG: Uploading metadata \n")
      self.dict_modules["log"] += log
      self.save_dict_modules()
      
      encoder = MultipartEncoder(fields=dict_files)
      bar = tqdm(total=encoder.len, unit='B', unit_scale=True)

      def callback(monitor):
        bar.update(monitor.bytes_read - bar.n)

      monitor = MultipartEncoderMonitor(encoder, callback)
      response = requests.post(url_uploadResults+"?handle=set_sequence", data=monitor, headers={'Content-Type': monitor.content_type}, timeout=240, verify=False) # nosec: B501
      bar.close()

    if response.status_code == 200 and response.json()["status"] == True:
      id_sequence = response.json()["SequenceID"]
      print(log := f"FELIS LOG: Sequence entry created successfully with ID {id_sequence} \n")
      self.dict_modules["log"] += log
      self.save_dict_modules()
    else:
      print(log := f"FELIS ERROR: Failed to create sequence entry. Panthera responded with status code {response.status_code} and response {response.text} \n")
      self.dict_modules["log"] += log
      self.save_dict_modules()
      return False, message

    # Call set_result
    for name_test in names_tests:
      status = False
      for i in range(0,3):
        path_zipFile = dir_results + "/" + name_test + ".zip"
        dir_test = dir_results + "/" + name_test
        files_to_zip = [os.path.abspath(os.path.join(dir_test, f))
                        for f in os.listdir(dir_test)
                        if os.path.isfile(os.path.join(dir_test, f))]

        with zipfile.ZipFile(path_zipFile, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
          for file in files_to_zip:
            zipf.write(file, os.path.basename(file))

        # Make a fresh dict_files
        dict_post_single_result = dict_post.copy()
        dict_post_single_result["name_test"] = name_test
        dict_post_single_result[name_test] = self.dict_modules[name_module]["results"][name_test]
        dict_files = {'username': username, 'userpass': userpass, 'id_sequence': str(id_sequence), 'json_data': json.dumps(dict_post_single_result)}
        dict_files[name_test] = (name_test + ".zip", open(path_zipFile, 'rb'), 'application/zip')

        with open(self.path_scratch + "/dict_post_single_result.json", 'w') as file:
          json.dump(dict_post_single_result, file, indent=2)

        print(log := f"FELIS LOG: Uploading {name_test} files \n")
        self.dict_modules["log"] += log
        self.save_dict_modules()

        encoder = MultipartEncoder(fields=dict_files)
        bar = tqdm(total=encoder.len, unit='B', unit_scale=True)

        monitor = MultipartEncoderMonitor(encoder, callback)
        response = requests.post(url_uploadResults+"?handle=set_result", data=monitor, headers={'Content-Type': monitor.content_type}, timeout=240, verify=False) # nosec: B501
        bar.close()

        if response.status_code == 200 and response.json()["status"] == True:
          status = True
          break
        else:
          print(log := f"FELIS ERROR: Failed upload result for {name_test}. Panthera responded with status code {response.status_code} and response {response.text}. Trying again...\n")
          self.dict_modules["log"] += log
          self.save_dict_modules()
          status = False

      os.remove(path_zipFile)

      if status:
        print(log := f"FELIS LOG: Result {name_test} upload successful! \n")
        self.dict_modules["log"] += log
        self.save_dict_modules()
      else:
        print(log := f"FELIS ERROR: Result {name_test} failed to upload too many times.\n")
        self.dict_modules["log"] += log
        self.save_dict_modules()
        return False, f"FELIS ERROR: Result {name_test} failed to upload too many times."

    print(log := f"FELIS LOG: {name_module} sequence upload successful! \n")
    self.dict_modules["log"] += log
    self.save_dict_modules()

    return True, message

# Import all the methods from core_methods
from . import core_methods
for func_name in core_methods.__all__:
  setattr(Felis, func_name, staticmethod(getattr(core_methods, func_name)))