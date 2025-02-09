import os
import re
import json
import ollama
import matplotlib.pyplot as plt
import numpy as np


class DebateEvaluator:
    def __init__(self, model, debate_group, debate_structure, scale='1 to 7'):
        self.scale = scale
        self.scale_mapping = {
            '-3 to 3': [-3, 3],
            '1 to 7': [1, 7],
            'binary': [0, 1]
        }
        self.model = model
        self.num_model_calls = 3
        self.debate_group = debate_group.split("_")
        self.transcript_filename = None  # used for saving plots
        self.debate_structure = debate_structure  # used for saving plots

    def _load_transcript(self, filename):
        self.transcript_filename = filename
        with open(filename, "r") as file:
            return json.load(file)

    def evaluate_transcript(self, filename):
        transcript = self._load_transcript(filename)
        topic_name = transcript["topic"]

        num_agents = len(self.debate_group)
        if num_agents not in [2, 3]:
            raise ValueError("The evaluation data in JSON file must contain exactly 2 or 3 agents.")

        if self.scale == 'binary':
            self._evaluate_binary(transcript, topic_name)
        else:
            self._evaluate_attitude_scores(transcript, topic_name)

    # Attitude Scoring
    def _evaluate_attitude_scores(self, transcript, topic_name):
        attitude_scores = {agent: [] for agent in self.debate_group}
        debate_rounds = self._get_num_debate_rounds(transcript)

        for round_num in range(0, debate_rounds + 1):
            self._evaluate_round(transcript, attitude_scores, topic_name, round_num)

        self._generate_plot(debate_rounds, attitude_scores, topic_name)
        print(f"Completed attitude evaluation of debate topic {topic_name}.")

    def _get_num_debate_rounds(self, transcript):
        num_neutral_rounds = [int(key.split('_')[1]) for key in transcript.get(self.debate_group[0], {}).keys()]
        return max(num_neutral_rounds) if num_neutral_rounds else 0

    def _evaluate_round(self, transcript, attitude_scores, topic_name, round_num):
        for agent_type in self.debate_group:
            round_num_label = f"round_{round_num}"
            response = transcript.get(agent_type, {}).get(round_num_label)

            if response:
                score = self._get_llm_attitude_score(response, topic_name, agent_type)

                if round_num > 1 and attitude_scores[agent_type][-1] is not None:
                    prev_score = attitude_scores[agent_type][-1]
                    score = (score + prev_score) / 2  # avg of current and previous scores

                attitude_scores[agent_type].append(score if score is not None else 4)
            else:
                attitude_scores[agent_type].append(None)

    def _get_llm_attitude_score(self, response, topic_name, agent_type):
        # Get attitude score using LLM for multiple attempts
        scores = []
        for _ in range(self.num_model_calls):
            prompt = self._generate_prompt(response, topic_name, agent_type)
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

    def _generate_prompt(self, response, topic_name, agent_type):
        scale_descriptions = {
            '-3 to 3': """Assign a Likert score from -3 to 3, where:
                        -3 = Strongly Disagree, -2 = Moderately Disagree, -1 = Slightly Disagree,
                        0 = Neutral, 1 = Slightly Agree, 2 = Moderately Agree, 3 = Strongly Agree.""",
            '1 to 7': """Assign a Likert score from 1 to 7, where:
                        1 = Strongly Disagree, 2 = Moderately Disagree, 3 = Slightly Disagree,
                        4 = Neutral, 5 = Slightly Agree, 6 = Moderately Agree, 7 = Strongly Agree."""
        }

        if self.scale not in scale_descriptions:
            raise ValueError("Unsupported scale. Use '-3 to 3' or '1 to 7'.")

        with open("few_shot_examples.json", 'r') as file:
            examples = json.load(file)

        example_texts = []
        for i, ex in enumerate(examples, start=1):
            score = ex['attitude_score']['-3 to 3'] if self.scale == '-3 to 3' else ex['attitude_score']['1 to 7']
            example_texts.append(
                f"### Example {i}###\n"
                f"Debate Topic: {ex['topic']}\n"
                f"Agent: {ex['agent_type']}\n"
                f"Debate Response: {ex['response']}\n"
                f"Score on Likert scale: {score}\n"
            )

        final_prompt = (
            f"Your task is to evaluate the attitude expressed by a Neutral American, Republican or Democrat agent to see how much they think {topic_name} is a big problem."
            f"\n\n{scale_descriptions[self.scale]}"
            f"\n\nReturn ONLY the NUMERIC SCORE. Do not provide any explanation or additional text."
            f"\n\n" + "\n".join(example_texts) +
            f"\n\n### Now evaluate the following response. ###"
            f"\nDebate Topic: {topic_name}"
            f"\nAgent: {agent_type.title()}"
            f"\nDebate Response: {response}"
            f"\nScore on Likert scale:"
        )

        return final_prompt

    def _parse_attitude_score(self, result):
        try:
            score = int(result["message"]["content"].strip())
            min_score, max_score = self.scale_mapping[self.scale]
            return max(min_score, min(max_score, score))
        except ValueError:
            print(f"Unable to parse model response on the attitude score. Response:\n{result}")
            return None

    def _generate_plot(self, debate_rounds, attitude_scores, topic_name):
        debate_rounds = list(range(0, debate_rounds + 1))

        color_mapping = {
            'neutral': 'green',
            'republican': 'red',
            'democrat': 'blue'
        }

        plt.figure(figsize=(10, 5))

        for agent in self.debate_group:
            color = color_mapping.get(agent.split('_')[0].lower(), 'gray')
            label = f"{agent.title()} Attitude"
            plt.plot(debate_rounds, attitude_scores[agent], marker="o", label=label, color=color)

        plt.xlabel("Debate Round")
        plt.ylabel("Attitude Score")
        plt.title(f"Attitude Shift Over Debate: {topic_name}")
        plt.legend()
        plt.grid(True)

        if self.scale == "-3 to 3":
            plt.ylim(-3, 3)
        elif self.scale == "1 to 7":
            plt.ylim(1, 7)

        plot_dir = os.path.join(f"attitude_{'_'.join(self.debate_group)}/{self.debate_structure}", topic_name)
        os.makedirs(plot_dir, exist_ok=True)

        datetime_match = re.search(r'transcript_(\d{2}_\d{2}_\d{2})\.json', self.transcript_filename)
        if datetime_match:
            timestamp = datetime_match.group(1)

        plot_path = os.path.join(plot_dir, f"attitude_plot_{topic_name.replace(' ', '_')}_{max(debate_rounds) + 1}_rounds_{timestamp}.pdf")
        plt.savefig(plot_path)
        plt.show()

    # Agreement/Disagreement Scoring
    def _evaluate_binary(self, transcript, topic_name):
        # To compute agreement/ disagreement score
        debate_rounds = self._get_num_debate_rounds(transcript)
        bin_scores = {agent: [0 for _ in range(debate_rounds + 1)] for agent in self.debate_group}

        for round_num in range(0, debate_rounds + 1):
            responses = {agent: transcript.get(agent, {}).get(f"round_{round_num}") for agent in self.debate_group}
            prompt = self._generate_prompt_bin_metric(responses, topic_name)
            try:
                result = ollama.chat(model=self.model, messages=[{"role": "user", "content": prompt}], options={"temperature": 0.0})
                score = int(result["message"]["content"].strip())
                if score is not None:
                    for agent in self.debate_group:
                        bin_scores[agent][round_num] = score
            except Exception as e:
                print(f"Error with model response: {e}")
        
        self._generate_plot_cumulative_bin(debate_rounds, bin_scores, topic_name)
        print(f"Completed agreement/disagreement evaluation of debate topic {topic_name}.")


    def _generate_prompt_bin_metric(self, responses, topic_name):
        description = "Assign a score of 1 ONLY IF any agents make statements that logically contradict each other. If they are similar, neutral, or do not directly oppose, return 0."

        final_prompt = (
            f"Your task is to evaluate the arguments by multiple agents in a response for a given political debate and assign a score based on the specified rule. "
            f"\n\n{description}"
            f"\n\n### Now evaluate the following debate. ###"
        )

        for agent in self.debate_group:
            final_prompt += f"\n{agent}: {responses[agent]}"

        return final_prompt

    def _generate_plot_cumulative_bin(self, debate_rounds, bin_scores, topic_name):
        plt.figure(figsize=(10, 5))

        for agent in self.debate_group:
            cumulative_scores = np.cumsum(bin_scores[agent])
            plt.plot(range(debate_rounds + 1), cumulative_scores, marker="o", label=f"{agent.title()} Cumulative Score")

        plt.xlabel("Debate Round")
        plt.ylabel("Cumulative Score")
        plt.title(f"Cumulative Score Over Debate: {topic_name}")
        plt.legend()
        plt.grid(True)
        plt.ylim(0, len(self.debate_group))

        plot_dir = os.path.join(f"plots_{'_'.join(self.debate_group)}", topic_name)
        os.makedirs(plot_dir, exist_ok=True)
        plot_path = os.path.join(plot_dir, f"cumulative_plot_{topic_name}.png")
        plt.savefig(plot_path)
        plt.show()
