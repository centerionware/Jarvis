#!/bin/bash

# This needs to install the dependencies for jarvis in comfyui
# It has to download and install the following packages:
# Models: SDXL-Turbo SDXL Harrlogos
# Custom Nodes: ComfyUI-Impact-Pack  ComfyUI-Inspire-Pack  ComfyUI-Manager  __pycache__  chatbox_overlay.py  efficiency-nodes-comfyui
# Custom Images: at least the text_box.png for the chatbox_overlay.py (512x512 with a box of ~200x100 iirc near the top left corner of the image ~25px from the edges)
# 

mkdir /app/ComfyUI/models/loras
mkdir /app/ComfyUI/models/checkpoints
mkdir /app/ComfyUI/models/checkpoints/SDXL-TURBO/

apt install wget

wget https://huggingface.co/HarroweD/HarrlogosXL/resolve/main/Harrlogos_v2.0.safetensors -O /app/ComfyUI/models/loras/Harrlogos_v2.0.safetensors

wget https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0_0.9vae.safetensors?download=true -O comfyui/models/checkpoints/sd_xl_base_1.0_0.9vae.safetensors
wget https://huggingface.co/stabilityai/stable-diffusion-xl-refiner-1.0/resolve/main/sd_xl_refiner_1.0_0.9vae.safetensors?download=true -O /app/ComfyUI/models/checkpoints/sd_xl_refiner_1.0_0.9vae.safetensors
wget https://huggingface.co/stabilityai/sdxl-turbo/resolve/main/sd_xl_turbo_1.0_fp16.safetensors?download=true -O /app/ComfyUI/models/checkpoints/SDXL-TURBO/sd_xl_turbo_1.0_fp16.safetensors

cd /app/ComfyUI/custom_nodes

git clone https://github.com/ltdrdata/ComfyUI-Manager
git clone https://github.com/ltdrdata/ComfyUI-Impact-Pack
git clone https://github.com/ltdrdata/ComfyUI-Inspire-Pack
git clone https://github.com/jags111/efficiency-nodes-comfyui

