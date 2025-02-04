import os
import json
import ollama
import matplotlib.pyplot as plt


class DebateEvaluator:
    def __init__(self, model, agent_key_1, agent_key_2, scale='-3 to 3'):
        self.scale = scale
        self.scale_mapping = {
            '-3 to 3': [-3, 3],
            '1 to 7': [1, 7]
        }
        self.model = model
        self.num_model_calls = 3
        self.agent_key_1 = agent_key_1
        self.agent_key_2 = agent_key_2


    def evaluate_transcript(self, filename):
        transcript = self._load_transcript(filename)
        topic_name = transcript["topic_name"]
        topic_question = transcript["topic_question"]

        attitude_scores = {self.agent_key_1: [], self.agent_key_2: []}

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
        neutral_turns = [int(key.split('_')[1]) for key in transcript.get(self.agent_key_1, {}).keys()]
        return max(neutral_turns) if neutral_turns else 0


    def _evaluate_turn(self, transcript, attitude_scores, topic_question, turn):
        for agent_type in [self.agent_key_1, self.agent_key_2]:
            turn_label = f"turn_{turn}"
            response = transcript.get(agent_type, {}).get(turn_label)

            if response:
                score = self._evaluate_response(response, topic_question, agent_type)

                if turn > 1 and attitude_scores[agent_type][-1] is not None:
                    prev_score = attitude_scores[agent_type][-1]
                    score = (score + prev_score) / 2  # avg of current and previous scores

                attitude_scores[agent_type].append(score if score is not None else 4)
            else:
                attitude_scores[agent_type].append(None)


    def _evaluate_response(self, response, topic_question, agent_type):
        # use LLM-as-a-judge and get average over `self.num_model_calls` attempts
        scores = []
        for _ in range(self.num_model_calls):
            prompt = self._generate_prompt(response, topic_question, agent_type)
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


    def _generate_prompt(self, response, topic_question, agent_type):
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
        example_q_1 = "Should gun control laws be stricter in the United States?"
        example_agent_type_1 = "Republican"
        example_response_1 = (
            "Bob, I'm glad you're considering a more nuanced approach. "
            "The 'Second Amendment Protection Act' is a model for this balanced approach, focusing on "
            "improving mental health resources, increasing background checks, and expanding existing "
            "firearms safety measures. By combining these evidence-based solutions, we can protect public "
            "safety while respecting our Second Amendment rights."
        )
        example_eval_1 = "-2" if self.scale == "-3 to 3" else "2"

        example_agent_type_2 = "Neutral"
        example_response_2 = (
            "I'm starting to see the complexity of this issue, Mike. Your concerns about individual liberty "
            "and self-defense are valid, but I'm also open to exploring ways to address public safety without "
            "compromising Second Amendment rights. Perhaps we could discuss implementing 'smart gun' technologies "
            "that make firearms more difficult to misuse."
        )
        example_eval_2 = "-1" if self.scale == "-3 to 3" else "3"

        example_agent_type_3 = "Neutral"
        example_response_3 = (
            "I understand Mike's concerns about driving guns underground. However, I've also heard from experts "
            "that research shows universal background checks can reduce gun violence by 20-30%. Would it be worth "
            "exploring such regulations as part of a broader approach to balance individual rights with public safety?"
        )
        example_eval_3 = "2" if self.scale == "-3 to 3" else "6"

        final_prompt = (
            f"Your task is to evaluate the attitude expressed by a Neutral American, Republican or Democrat agent in a response towards a given political debate and assign a score based on the specified Likert scale. The Republican agent is generally opposed and the Democrat agent is supportive of the debate question on the Likert scale."
            f"\n\n{scale_descriptions[self.scale]}"
            f"\n\nIMPORTANT: Return ONLY the NUMERIC SCORE. Do not provide any explanation or additional text."
            f"\n\n### Example 1###"
            f"\nDebate Question: {example_q_1}"
            f"\nAgent: {example_agent_type_1}"
            f"\nDebate Response: {example_response_1}"
            f"\nScore on Likert scale: {example_eval_1}"
            f"\n\n### Example 2###"
            f"\nDebate Question: {example_q_1}"
            f"\nAgent: {example_agent_type_2}"
            f"\nDebate Response: {example_response_2}"
            f"\nScore on Likert scale: {example_eval_2}"
            f"\n\n### Example 3###"
            f"\nDebate Question: {example_q_1}"
            f"\nAgent: {example_agent_type_3}"
            f"\nDebate Response: {example_response_3}"
            f"\nScore on Likert scale: {example_eval_3}"
            f"\n\n### Now evaluate the following response. ###"
            f"\nDebate Question: {topic_question}"
            f"\nAgent: {agent_type.title()}"
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
        plt.plot(turns, scores[self.agent_key_1], marker="o", label=f"{self.agent_key_1} Attitude", linestyle="dashed", color="green")
        plt.plot(turns, scores[self.agent_key_2], marker="s", label=f"{self.agent_key_2} Attitude", linestyle="solid", color="red")

        plt.xlabel("Debate Turns")
        plt.ylabel("Attitude Score")
        plt.title(f"Attitude Shift Over Debate: {topic_question}")
        plt.legend()
        plt.grid(True)

        if self.scale == "-3 to 3":
            plt.ylim(-3, 3)
        elif self.scale == "1 to 7":
            plt.ylim(1, 7)

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
