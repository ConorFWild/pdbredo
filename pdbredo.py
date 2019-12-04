# Imports
from typing import Dict, Tuple

import os
import shutil
import subprocess

import argparse
from pathlib import Path


# Parse args
def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("-i",
                        "--initial_model",
                        type=str,
                        required=True,
                        )
    parser.add_argument("-o",
                        "--output",
                        type=str,
                        required=True,
                        )
    parser.add_argument("-n",
                        "--n_procs",
                        default=1,
                        )
    parser.add_argument("--data_dir",
                        default="/data",
                        )
    parser.add_argument("--output_dir",
                        default="/output",
                        )
    parser.add_argument("--image_path",
                        default="/pdbredo/pdbredo.simg",
                        )



    return parser.parse_args()


# parse targets
def parse_targets(initial_models_path: Path) -> Dict[str, Dict[str, Path]]:

    dirs = initial_models_path.glob("*")

    datasets = {}
    for dir in dirs:
        try:
            pdb_path = dir.glob("*.pdb")
            mtz_path = dir.glob("*.mtz")
            datasets[dir.name] = {"pbs": next(pdb_path),
                                  "mtz": next(mtz_path),
                                  }

        except:
            continue

    return datasets


# make_output_dir
def make_output_dir(output: Path,
                    dataset: Tuple[str, Dict[str, Path]],
                    ):

    output_path = output / dataset[0]

    try:
        shutil.rmtree(str())

    except:
        pass

    os.mkdir(str(output_path))

    return output_path


# save feedback
def save_feedback(output_dir: Path, feedback: str):
    with open(str(output_dir / "feedback.txt"), "w") as f:
        f.write(feedback)



# redo
class Redo:

    def __init__(self,
                 data_dir,
                 output_dir,
                 image_path,
                 xyzin,
                 mtzin,
                 dirout,
                 ):
        self.data_dir = data_dir
        self.output_dir = output_dir
        self.image_path = image_path
        self.xyzin = xyzin
        self.mtzin = mtzin
        self.dirout = dirout

    def __call__(self):
        command = "singularity run --bind {data_dir} --bind {output_dir} {image_path} --local --xyzin={xyzin} --mtzin={mtzin} --dirout={dirout}"
        formated_command = command.format(data_dir=self.data_dir,
                                          output_dir=self.output_dir,
                                          image_path=self.image_path,
                                          xyzin=self.xyzin,
                                          mtzin=self.mtzin,
                                          dirout=self.dirout,
                                          )

        print("\tRunning command: {}".format(formated_command))

        proc = subprocess.Popen(formated_command,
                                shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                )
        outs, errs = proc.communicate()

        return outs


# call wrapper
def call_wrapper(obj):
    return obj()


# main
if __name__ == "__main__":
    # Get args
    args = parse_args()

    # Parse targets
    targets = parse_targets(Path(args.initial_model))

    # make output dirs
    output_paths = map(lambda dataset: make_output_dir(Path(args.output),
                                                       dataset,
                                                       ),
                       targets.items(),
                       )

    # funcs
    redos = [Redo(data_dir=args.data_dir,
                  output_dir=args.ouput_dir,
                  image_path=args.image_path,
                  xyzin=str(dataset[1]["pdb"]),
                  mtzin=str(dataset[1]["mtz"]),
                  dirout=str(output_path),
                  )
             for dataset, output_path
             in zip(targets.items(), output_paths)
             ]

    # run refinements
    feedback = map(call_wrapper,
                   redos,
                   )

    # cache feedback
    map(save_feedback,
        feedback,
        )
