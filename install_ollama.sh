#!/bin/bash
curl https://ollama.ai/install.sh | sh
/usr/local/bin/ollama serve &
ollama pull mistral
ollama pull llava
killall ollama -9
