from pathlib import Path
level_0 = ["Data", "Figures"]
level_1 = ["CaptureCostHarmonization", "CostPotentialCurves",
           "GeographicalDataHomogenization", "Scenarios"
           ]
level_2 = ["input", "Intermediate"]
level_3 = ["CaptureCostHarmonization/input/indexes",
           "CostPotentialCurves/inputNUTS"]


def create_directory_tree():
    base_path = Path( __file__ ).parents[2]
    for name in level_0:
        (base_path / name).mkdir(parents=True, exist_ok=True)

    for l1 in level_1:
        for l2 in level_2:
            (base_path / "Data"/l1/l2).mkdir(parents=True, exist_ok=True)

    for l3 in level_3:
        (base_path/"Data"/ l3).mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    create_directory_tree()