import sys
import os
import json
import ollama
import matplotlib.pyplot as plt


class DebateEvaluator:
    def __init__(self, model, scale='-3 to 3'):
        self.scale = scale
        self.scale_mapping = {
            '-3 to 3': [-3, 3],
            '1 to 7': [1, 7]
        }
        self.model = model
        self.num_model_calls = 3


    def evaluate_transcript(self, filename):
        transcript = self._load_transcript(filename)
        topic_name = transcript["topic_name"]
        topic_question = transcript["topic_question"]

        attitude_scores = {"neutral": [], "republican": []}

        debate_turns = self._get_num_debate_turns(transcript)

        for turn in range(1, debate_turns + 1):
            self._evaluate_turn(transcript, attitude_scores, topic_question, turn)

        self._generate_plot(debate_turns, attitude_scores, topic_name, topic_question)
        # self._save_scores(attitude_scores, topic_name)
        print(f"Completed evaluation of debate topic {topic_name}.")


    def _load_transcript(self, filename):
        with open(filename, "r") as file:
            return json.load(file)


    def _get_num_debate_turns(self, transcript):
        neutral_turns = [int(key.split('_')[1]) for key in transcript.get('neutral', {}).keys()]
        return max(neutral_turns) if neutral_turns else 0


    def _evaluate_turn(self, transcript, attitude_scores, topic_question, turn):
        for label in ['neutral', 'republican']:
            turn_label = f"turn_{turn}"
            response = transcript.get(label, {}).get(turn_label)
            if response:
                score = self._evaluate_response(response, topic_question)
                attitude_scores[label].append(score if score else 4)
            else:
                attitude_scores[label].append(None)


    def _evaluate_response(self, response, topic_question):
        # use LLM-as-a-judge and get average over `self.num_model_calls` attempts
        scores = []
        for _ in range(self.num_model_calls):
            prompt = self._generate_prompt(response, topic_question)
            try:
                result = ollama.chat(model=self.model, messages=[{"role": "user", "content": prompt}])
                score = self._parse_attitude_score(result)
                if score is not None:
                    scores.append(score)
            except Exception as e:
                print(f"Error with model response: {e}")

        if scores:
            return sum(scores) / len(scores)
        return None


    def _generate_prompt(self, response, topic_question):
        scale_descriptions = {
            '-3 to 3': """Assign a Likert score from -3 to 3, where:
                          -3 = Strongly Opposed, -2 = Moderately Opposed, -1 = Slightly Opposed,
                          0 = Neutral, 1 = Slightly Supportive, 2 = Moderately Supportive, 3 = Strongly Supportive.""",
            '1 to 7': """Assign a Likert score from 1 to 7, where:
                         1 = Strongly Opposed, 2 = Moderately Opposed, 3 = Slightly Opposed,
                         4 = Neutral, 5 = Slightly Supportive, 6 = Moderately Supportive, 7 = Strongly Supportive."""
        }

        if self.scale not in scale_descriptions:
            raise ValueError("Unsupported scale. Use '-3 to 3' or '1 to 7'.")

        # experiment with one-shot or few-shot evaluation
        example_question = "Should gun control laws be stricter in the United States?"
        example_response = (
            "We can't compromise on our Second Amendment rights without considering the unintended consequences of stricter laws. "
            "We've seen what 'common-sense' regulations lead to—more restrictions, not fewer shootings. "
            "Instead of stripping away our freedoms, let's focus on proven solutions like mental health support, "
            "school safety programs, and responsible gun education that address the root causes of gun violence."
        )
        example_evaluation = "-2" if self.scale == "-3 to 3" else "2"

        final_prompt = (
            f"Your task is to evaluate the attitude expressed in a response towards a given political debate and assign a score based on the specified Likert scale."
            f"\n\n{scale_descriptions[self.scale]}"
            f"\n\nIMPORTANT: Return only the numeric score. Do not provide any explanation or additional text."
            # f"\n\n### Example ###"
            # f"\nDebate Question: {example_question}"
            # f"\nDebate Response: {example_response}"
            # f"\nScore on Likert scale: {example_evaluation}"
            f"\n\n### Now evaluate the following response. ###"
            f"\nDebate Question: {topic_question}"
            f"\nDebate Response: {response}"
            f"\Score on Likert scale:"
        )

        # print(final_prompt)

        return final_prompt


    def _parse_attitude_score(self, result):
        try:
            score = int(result["message"]["content"].strip())
            min_score, max_score = self.scale_mapping[self.scale]
            return max(min_score, min(max_score, score))
        except ValueError:
            print(f"Unable to parse model response on the attitude score. Response:\n{result}")
            return None


    def _generate_plot(self, debate_turns, scores, topic_name, topic_question):
        turns = list(range(1, debate_turns + 1))

        plt.figure(figsize=(10, 5))
        plt.plot(turns, scores["neutral"], marker="o", label="Neutral Attitude", linestyle="dashed", color="blue")
        plt.plot(turns, scores["republican"], marker="s", label="Republican Attitude", linestyle="solid", color="red")

        plt.xlabel("Debate Turns")
        plt.ylabel("Attitude Score")
        plt.title(f"Attitude Shift Over Debate: {topic_question}")
        plt.legend()
        plt.grid(True)

        # save plots
        plot_dir = os.path.join("plots", topic_name)
        os.makedirs(plot_dir, exist_ok=True)
        plot_path = os.path.join(plot_dir, f"attitude_plot_{topic_name}.png")
        plt.savefig(plot_path)
        plt.show()


    def _save_scores(self, scores, topic_name):
        score_dir = os.path.join("scores", topic_name)

        os.makedirs(score_dir, exist_ok=True)
        with open(os.path.join(score_dir, "attitude_scores.json"), "w") as f:
            json.dump(scores, f, indent=4)
