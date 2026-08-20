import ROOT

def print_root_contents(directory, indent=""):
    for key in directory.GetListOfKeys():
        obj = key.ReadObj()

        print(f"{indent}{obj.GetName()} [{obj.ClassName()}]")

        if obj.InheritsFrom("TDirectory"):
            print_root_contents(obj, indent + "    ")

f = ROOT.TFile.Open(
    "files/fc7_board_1_Run001671_PixelAlive_Board_0_Hybrid_0.root"
)

print_root_contents(f)