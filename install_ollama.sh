#!/bin/bash
curl https://ollama.ai/install.sh | sh
/usr/local/bin/ollama serve &
sleep 5s
echo "Pulling mistral"
ollama pull mistral
ollama pull mistral
echo "Pulling llava"
ollama pull llava
killall ollama -9
