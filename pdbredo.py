# Imports
from typing import Dict, Tuple

import os
import shutil
import subprocess
import multiprocessing
import joblib

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
            pdb_path = dir.glob("dimple.pdb")
            mtz_path = dir.glob("dimple.mtz")
            datasets[dir.name] = {"pdb": next(pdb_path),
                                  "mtz": next(mtz_path),
                                  }

        except:
            continue

    return datasets


# make_output_dir
def make_output_dir_dep(output: Path,
                    dataset: Tuple[str, Dict[str, Path]],
                    ):

    output_path = output / dataset[0]

    try:
        shutil.rmtree(str(output_path))

    except Exception as e:
        print(e)

    os.mkdir(str(output_path))

    return output_path


# make_output_dir
def make_output_dir(output_dir_path: Path):

    try:
        shutil.rmtree(str(output_dir_path))

    except Exception as e:
        print(e)

    os.mkdir(str(output_dir_path))

    return output_dir_path


# save feedback
def save_feedback(output_dir: Path, feedback: str):
    with open(str(output_dir / "feedback.txt"), "w") as f:
        f.write(str(feedback))


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
        print("outs\n\t{}".format(outs))
        print("errs\n\t {}".format(errs))

        return outs


# call wrapper
def call_wrapper(obj):
    return obj()


def already_done(target_output_dir_path: Path):

    final_pdb_regex = "*_final.pdb"

    try:
        next(target_output_dir_path.glob(final_pdb_regex))
        print("\tALREADY FINISHED: {}".format(target_output_dir_path))
        return True

    except:
        return False


def process_dataset(args, target):

    dtag = target[0]
    dataset = target[1]

    print("### RUNNING PDBREDO FOR: {} ###".format(dtag))

    target_output_dir_path = Path(args.output) / dtag

    if already_done(target_output_dir_path):
        return

    make_output_dir(target_output_dir_path)

    redo = Redo(data_dir=args.data_dir,
                output_dir=args.output_dir,
                image_path=args.image_path,
                xyzin=str(dataset["pdb"]),
                mtzin=str(dataset["mtz"]),
                dirout=str(target_output_dir_path),
                )

    feedback = redo()

    save_feedback(target_output_dir_path,
                  feedback,
                  )


# main
if __name__ == "__main__":
    # Get args
    args = parse_args()

    # Parse targets
    targets = parse_targets(Path(args.initial_model))
    # print("Targets\n\t{}".format(targets))

    joblib.Parallel(n_jobs=int(args.n_procs),
                    verbose=7,
                    )(joblib.delayed(process_dataset)(args,
                                                      dataset,
                                                      )
                      for dataset
                      in list(targets.items())
                      )

    #
    # # make output dirs
    # output_paths = list(map(lambda dataset: make_output_dir(Path(args.output),
    #                                                         dataset,
    #                                                         ),
    #                         targets.items(),
    #                         )
    #                     )
    # # print("Output paths\n\t{}".format(list(output_paths)))
    #
    # # funcs
    # redos = []
    # for i, dtag in enumerate(targets):
    #     dataset = targets[dtag]
    #     output_path = output_paths[i]
    #     redo = Redo(data_dir=args.data_dir,
    #                 output_dir=args.output_dir,
    #                 image_path=args.image_path,
    #                 xyzin=str(dataset["pdb"]),
    #                 mtzin=str(dataset["mtz"]),
    #                 dirout=str(output_path),
    #                 )
    #
    #     redos.append(redo)
    #
    #
    # # run refinements
    # print("Running redos")
    # print("\tRunning {} redos".format(len(redos)))
    # # print("\t{}".format(redos))
    # # feedback = map(call_wrapper,
    # #                redos,
    # #                )
    # # feedback = map(lambda x: x(),
    # #                redos,
    # #                )
    # # for i, redo in enumerate(redos):
    # #     print("\tDoing redo: {}".format(i))
    # #     redo()
    # feedback = multiprocessing.Pool(processes=int(args.n_procs)).map(call_wrapper,
    #                                                                  redos,
    #                                                                  )
    #
    # print("Saving feedback")
    # # cache feedback
    # map(save_feedback,
    #     feedback,
    #     )
