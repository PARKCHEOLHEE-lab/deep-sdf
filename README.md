# DeepSDF

Simple implementation of the paper [DeepSDF: Learning Continuous Signed Distance Functions for Shape Representation.](https://arxiv.org/pdf/1901.05103) with the skyscrapers data. Leveraging the Deep Signed Distance Functions model with latent vectors, this project aims to build the algorithm that can `synthesize` infinite number of skyscrapers similar to trained data.
The detailed process for this project is archived __[here](https://parkcheolhee-lab.github.io/synthesized-skyscrapers/).__

<br>

<p align="center">
  <img src="deep_sdf/assets/synthesis.gif">
  <br><br>
  <i>Synthesized data with deepSDF model</i>
</p>

# Installation
This repository uses the [image](/.devcontainer/Dockerfile) named `nvcr.io/nvidia/pytorch:23.10-py3` for running devcontainer.


1. Ensure you have Docker and Visual Studio Code with the Remote - Containers extension installed.
2. Clone the repository.

    ```
        git clone https://github.com/PARKCHEOLHEE-lab/deep-sdf.git
    ```
3. Open the project with VSCode.
4. When prompted at the bottom left on the VSCode, click `Reopen in Container` or use the command palette (F1) and select `Remote-Containers: Reopen in Container`.
5. VS Code will build the Docker container and set up the environment.
6. Once the container is built and running, you're ready to start working with the project.

<br>

# File Details
### data
- `raw-skyscrapers`: The directory containing the raw data for skyscrapers.
- `preprocessed-skyscrapers`: The directory containing preprocessed skyscrapers for training.
- ~~`preprocessed-skyscrapers-dynamic-sampled`: The directory containing dynamically sampled data by the number of raw data' vertices.~~ (deprectaed)

### src
- `config.py`: Configurations related to the model and data.
- `data_creator.py`: Creates the data consisting of xyz coordinates and sdf values.
- `model.py`: Defines the classes for SDFdatset, SDFdecoder, SDFdecoderTrainer.
- `reconstruct.py`: Defines a class to reconstruct skyscrapers with skimage.measure.marching_cubes.
- `synthesize.py`: Defines Synthesizer for creating synthesized data.
- `utils.py`: Utility functions not related to the model.

### notebooks
- `deep_sdf.ipynb`: Execute the whole processes for the training and testing.

### runs
- `2024-03-24_12-40-26`: The directory containing the model's states, reconstruction results.
- `2024-03-24_12-40-26/states/all_states.pth`: Pre-trained model states.
