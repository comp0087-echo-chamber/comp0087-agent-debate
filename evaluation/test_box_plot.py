from DebateEvaluator import DebateEvaluator
import os

model = "llama3.2:latest"
eval = DebateEvaluator(model, "neutral_republican", "unstructured", scale="binary")

debate_transcripts_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "debate_transcripts_democrat")

eval._generate_bin_box_plot([], "gun violence")

