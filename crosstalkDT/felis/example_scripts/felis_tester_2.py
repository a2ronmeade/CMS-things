from felis.felis import Felis

"""
Sample code showing how you can import an old workspace by linking to a json file in the constructor.
"""

my_felis = Felis("/home/scott/Downloads/scratch/2024-06-17_14-26-15/dict_modules.json", False)

name_module = "RH0001"

status, message = my_felis.upload_results(name_module, "user", "pass", type_sequence = "test_sequence_2")
print(status, message)