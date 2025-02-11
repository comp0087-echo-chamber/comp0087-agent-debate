# comp0087-agent-debate
Purpose of this investigation - Getting opinionated agents to debate, and seeing how that influences a neutral default model observer
[Project Github](https://github.com/comp0087-echo-chamber)
## Setup instructions - MacOS
https://hadna.space/jv/notes/41-ollama-macos
1) Install [Ollama](https://ollama.com/)
2) run a model:
```
ollama run llama3.2:3b
```
3) Create a python virtual environment and install requirements
```
python3 -m venv venv
source venv/bin/activate
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