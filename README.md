# TOKAIRIKA POC2

## Overview
Quick demo TokaiRika detection using CLIP library.

## Installation
### Requirements
- Python 3.9

### Setup
1. Create a Conda environment:
    ```bash
    conda create --name tokai_poc python=3.9
    ```

2. Activate the created environment:
    ```bash
    conda activate tokai_poc
    ```

3. Install required packages using pip:
    ```bash
    pip install -r requirements.txt
    ```
   
4. Download CLIP model [here](https://openaipublic.azureedge.net/clip/models/5806e77cd80f8b59890b7e101eabd078d9fb84e6937f9e85e4ecb61988df416f/ViT-B-16.pt):
    ```bash
    # Download and place the CLIP model at: ./data/CLIP/ViT-B-16.pt   
    ```
   
5. Download REMBG model [here](https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx):
    ```bash
    # Download and place the REMBG model at: ./data/u2net/u2net.onnx   
    ```

## Usage
Execute the following command in the activated Conda environment:

   ```bash
   python GUI.py
   ```

## Build executable file
Execute the following command in the activated Conda environment:

   ```bash
   pyinstaller --noconfirm GUI.spec
   ```
