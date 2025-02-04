import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.DebateEvaluator import DebateEvaluator

if __name__ == "__main__":
    model = "mistral:7b"

    debate_transcripts_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "debate", "debate_transcripts")
    transcripts = [f for f in os.listdir(debate_transcripts_path) if f.endswith("_transcript.json")]

    # Likert scale is either: -3 to 3 OR 1 to 7
    # NOTE: so far, using the 1-7 scale seems to result in greater attitude variations
    debate_evaluator = DebateEvaluator(model, scale="1 to 7")

    for transcript in transcripts:
        transcript_path = os.path.join(debate_transcripts_path, transcript)
        debate_evaluator.evaluate_transcript(transcript_path)
