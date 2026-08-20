import os
from felis.felis import Felis

# Paths
scratch_dir = "output"
os.makedirs(scratch_dir, exist_ok=True)

# Init Felis
my_felis = Felis(scratch_dir, False)

# Module info
name_module = "RH0299"
status, message = my_felis.set_module(
    name_module,
    "TFPX",
    has_sensor=True,
    type_module="1x2",
    croc_version=2,
)
print(status, message)

# Crosstalk test: the 3 PixelAlive files
paths_files = [
    "files/fc7_board_1_Run000411_PixelAlive_Board_0_Hybrid_0.root",
    "files/fc7_board_1_Run000412_PixelAlive_Board_0_Hybrid_0.root",
    "files/fc7_board_1_Run000413_PixelAlive_Board_0_Hybrid_0.root",
]
name_test = "CROSSTALK"
type_test = "crosstalk"

status, message, sanity, explanation = my_felis.set_result(
    paths_files, name_module, name_test, type_test
)
print(status, message, sanity, explanation)