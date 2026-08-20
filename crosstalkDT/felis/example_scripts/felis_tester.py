"""
Sample code showing how Felis is used.
This is not a part of Felis.
"""

from felis.felis import Felis # Change the import path as needed

my_felis = Felis("/home/scott/Downloads/scratch", False)

name_module = "EX0007"

status, message = my_felis.set_module(name_module, "TFPX", has_sensor = True, type_module = "1x2")
# The kwargs in set_module() are not needed if the module's information is already in Panthera
print(status, message)

paths_files = ["/home/scott/Nextcloud/Notebook/Physics_Notebook/Panthera/scratch_code/test_results/pixelalive/Run000024_PixelAlive.root",
                "/home/scott/Nextcloud/Notebook/Physics_Notebook/Panthera/scratch_code/test_results/pixelalive/Run000024_CMSIT_RD53B.xml",
                "/home/scott/Nextcloud/Notebook/Physics_Notebook/Panthera/scratch_code/test_results/pixelalive/Run000024_CMSIT_RD53B_ROC0.txt",
                "/home/scott/Nextcloud/Notebook/Physics_Notebook/Panthera/scratch_code/test_results/pixelalive/Run000024_CMSIT_RD53B_ROC2.txt"]
name_test = "00_PIXELALIVE"
type_test = "pixelalive"

status, message, sanity, explanation = my_felis.set_result(paths_files, name_module, name_test, type_test)
print(status, message)

paths_files = ["/home/scott/Nextcloud/Notebook/Physics_Notebook/Panthera/Threshold_adjust_testing_4/Results/Run000211_Gain.root",
                    "/home/scott/Nextcloud/Notebook/Physics_Notebook/Panthera/scratch_code/test_results/latency/Run000025_CMSIT_RD53B.xml",
                    "/home/scott/Nextcloud/Notebook/Physics_Notebook/Panthera/scratch_code/test_results/latency/Run000025_CMSIT_RD53B_ROC0.txt",
                    "/home/scott/Nextcloud/Notebook/Physics_Notebook/Panthera/scratch_code/test_results/latency/Run000025_CMSIT_RD53B_ROC2.txt"]
name_test = "01_GAINSCAN"
type_test = "gain"

status, message, sanity, explanation = my_felis.set_result(paths_files, name_module, name_test, type_test)
print(status, message)

paths_files = ["/home/scott/Downloads/Result_RunIVCurve_SH0011.root",
               "/home/scott/Downloads/Run000013_MonitorDQM.root"]
name_test = "02_IVCURVE"
type_test = "ivcurve"

status, message, sanity, explanation = my_felis.set_result(paths_files, name_module, name_test, type_test)
print(status, message)

status, message = my_felis.upload_results(name_module, "user", "pass", type_sequence = "test_sequence_2", version_ph2acf = "1.0")
print(status, message)
