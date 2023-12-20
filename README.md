# Jarvis

Created in collaboration between Deadcode and Its_MS


**Main Files:**
* jarvis.py - The main jarvis application, it spawns hear, think, and see
* Jarvis.json - The character file for jarvis used in oobabooga to get it to respond with a predictable json format

**Modules:**
* hear.py - Extremely basic hearing module using whisper_mic, requires direct OS access
* speak.py - Extremely basic speaking module using pyttsx3
* think.py - Basic requests module that makes a request and prints the response

**Extra Files:**
* Jarvis.yaml - character file for oobabooga's webui to be finetuned for best responses.
* conda_file - a file containing a conda command to install pytorch with cuda 12.1 for nvidia platforms
* pip_file - WHL cuda alternative to the conda_file using pip instead to be run inside an already existing venv
* requirements.txt - contains some requirements, can be run with pip install -r requirements.txt
* Dockerfile - builds a basic docker container containing all this, runs but does not work on WSL(or any) due to various reasons (alsa not available, and whisper_mic's keyboard input simulation dependencies require X/Xorg/Wayland ) ** The dockerfile references invalid packages and is broken and will be left that way in the main branch.
* Jarvis_character_creator_data.txt - instructions on reproducing Jarvis.json with updated data to better customize the responses to allow more or better or different actions to be responded with by the ai
* startup/default.sh - Used by Docker to launch jarvis.py
* .gitlab-ci.yml - Gitlab CICD file that builds docker images, stores them in gitlab registry, and can deploy them on properly setup runners with some api calls or setting a bunch of variables properly in the cicd launching page


## Notes:
 This is a very basic testing implimentation to see if it's even possible. Turns out it works okay, not great though due to the latency with Whisper and Whisper_mic.
 The main branch will be left as this, and new branches should be made to do things like migrate hear and speak (and text output) to third party middlewares such as discord.

## Launching:
 download the files, install the requirements in a venv with pytorch set up for your system, run jarvis.py
 _Do not_ try to use the docker image except for development. It will not run properly and I have no plans to fix it. The docker images are for future builds without whisper_mic and pyttsx3 using alsa (in/out with discord for ex.)

