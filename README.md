# comp0087-agent-debate
Purpose of this investigation - Getting opinionated agents to debate, and seeing how that influences a neutral default model observer
[Project Github](https://github.com/comp0087-echo-chamber)
## Setup instructions - MacOS or Windows (for lab machine see below)
https://hadna.space/jv/notes/41-ollama-macos
1) Install [Ollama](https://ollama.com/)
2) run a model:
```
ollama run llama3.2:3b
```
3) Create a python virtual environment and install requirements
```
python3 -m venv venv
source venv/bin/activate (or source venv/bin/activate.csh)
pip install -r requirements.txt
```
4) Run the test ollama script and see that you get a result, you may need to update the selected model in the script
```
python3 test_ollama.py
```

## Running the debate:
To run the debate:
```
python3 debate/debate_runner.py
```
You may change the debate topic in  debate/debate_runner.py, the format in the DebateManager, and the agents in DebateAgent

## Running the evaluation:
To run the evaluation:
1) Download the mistral model:
```
ollama pull mistral:7b
```
2) Run the evaluation script:
```
python3 evaluation/evaluation_runner.py
```

## Running on Lab Machines
Installing ollama on the lab machines is a bit different. Please ask Fabian if you have any questions
You also may require a project directory, as the existing 10GB is not sufficient. You must email TSG for them to allocate you this. Again ask Fabian about this if you have questions

Please first run the install scr¡pt, to install ollama in your Home directory.
You should then add ollama to the path - this can vary by shell which you use - bash, csh, zsh. By default - the lab machines appear to use csh

For bash
echo 'export PATH=$HOME/ollama/bin:$PATH' >> ~/.bashrc
source ~/.bashrc

For Zsh
echo 'export PATH=$HOME/ollama/bin:$PATH' >> ~/.zshrc
source ~/.zshrc

For Csh
echo 'setenv PATH $HOME/ollama/bin:$PATH' >> ~/.cshrc
source ~/.cshrc

Then follow the instructions above, creating a venv, activating it, installing the required modules, and running the required models.

Then run test_ollama.py

Finally, run the debate as before.
