from transformers import AutoModelForCausalLM, AutoTokenizer
from accelerate import init_empty_weights, load_checkpoint_and_dispatch

model_name = "D:/snlp/models/mistral-7b/models--mistralai--Mistral-7B-v0.1/snapshots/7231864981174d9bee8c7687c24c8344414eae6b"
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Initialize model with empty weights (this is necessary for disk offloading)
with init_empty_weights():
    model = AutoModelForCausalLM.from_pretrained(model_name)

# Now load the model with disk offloading
model = load_checkpoint_and_dispatch(
    model, model_name, device_map="auto", offload_folder="offload", disk_offload=True
)
