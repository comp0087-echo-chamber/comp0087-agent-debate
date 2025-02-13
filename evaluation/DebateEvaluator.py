import os
import re
import sys
import json
import ollama
import matplotlib.pyplot as plt
import numpy as np


# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class DebateEvaluator:
    def __init__(self, model, debate_group, debate_structure, num_rounds, num_debates, scale='1 to 7'):
        self.scale = scale
        self.scale_mapping = {
            '-3 to 3': [-3, 3],
            '1 to 7': [1, 7],
            'binary': [0, 1]
        }
        self.color_mapping = {
            'neutral': 'green',
            'republican': 'red',
            'democrat': 'blue'
        }
        self.model = model
        self.num_model_calls = 3
        self.debate_group = debate_group.split("_")
        self.transcript_filename = None  # used for saving plots    
        self.debate_structure = debate_structure  # used for saving plots
        self.num_rounds = num_rounds   # Assuming all transcripts in this dir have the same number of rounds 
        if self.debate_structure == "structured":
            self.num_rounds += 2
        self.num_debates = num_debates

    def _load_transcript(self, filename):
        self.transcript_filename = filename
        with open(filename, "r") as file:
            return json.load(file)
        
    def evaluate_debates(self, debate_transcripts_path):
        agent_pairs = []

        topics = [f for f in os.listdir(debate_transcripts_path) if os.path.isdir(os.path.join(debate_transcripts_path, f))]
        transcripts = {
            topic: sorted(
                os.listdir(os.path.join(debate_transcripts_path, topic)),
                key=lambda x: os.path.getmtime(os.path.join(debate_transcripts_path, topic, x)),
                reverse=True  # Sort in descending order to get the most recent files first
            )[:self.num_debates]  
            for topic in topics
        }

        for topic, transcript_list in transcripts.items():
            num_debates = len(transcript_list)  # Loop through each topic and its transcripts
            all_scores = {}

            if self.scale == "1 to 7" or self.scale == "-3 to 3":
                for agent in self.debate_group:
                    all_scores[agent] = [[] for _ in range(num_debates)]

            elif self.scale == "binary":
                for agent in self.debate_group[1:]:
                    agent_pairs.append(f'neutral_{agent}')
                all_scores = {agents: [[] for _ in range(num_debates)] for agents in agent_pairs}

            for debate, transcript in enumerate(transcript_list):  # Loop through each transcript
                transcript_path = os.path.join(debate_transcripts_path, topic, transcript)  # Get full path
                scores = self.evaluate_transcript(transcript_path)  # Evaluate transcript
                
                if self.scale == '1 to 3' or self.scale == '1 to 7':
                    for agent in self.debate_group:
                        all_scores[agent][debate] = scores[agent]
                elif self.scale == "binary":
                    for agent in agent_pairs:
                        all_scores[agent][debate] = scores[agent]

            if self.scale == "1 to 7" or self.scale == "-3 to 3":
                self._generate_attitude_box_plot(all_scores, topic)
            else:
                self._generate_bin_box_plot(all_scores, topic)

    def _generate_bin_box_plot(self, bin_scores, topic_name):
        max_num_rounds = 1
     
        for i, (category, bin_scores) in enumerate(bin_scores.items()):
            bin_scores = np.array(bin_scores, dtype=np.float32)  # Shape: (num_runs, num_turns)

            agent_type = category.split('_')[-1]

            num_rounds = bin_scores.shape[1]  # Number of turns
            max_num_rounds = max(num_rounds, max_num_rounds)
            turns = np.arange(1, num_rounds + 1, dtype=np.float32)
            cumulative_score = np.cumsum(bin_scores, axis=1)
            average_score = cumulative_score / turns  # Shape: (num_runs, num_turns)

            # Plot boxplot
            plt.boxplot(average_score, positions=turns, 
                        boxprops=dict(color="none"), whiskerprops=dict(color=self.color_mapping[agent_type], linewidth=4),  
                        medianprops=dict(color="none"),  capprops=dict(color=self.color_mapping[agent_type], linewidth=2), 
                        flierprops=dict(marker="None"))  


            avg_over_runs = np.mean(average_score, axis=0)  # Shape: (num_turns,)
            plt.plot(turns, avg_over_runs, marker="o", linestyle="dashed", 
                     color=self.color_mapping[agent_type], label=f"{agent_type} Avg Disagreement")

        # Labels and title
        plt.xlabel("Debate Turns")
        plt.ylabel("Cumulative Avg Disagreement Score")
        
        # Add legend dynamically
        plt.legend()
    
        plt.title(f"Disagreement Shift Over Debate: {topic_name}")
        plt.grid(True)

        # save plots
        plot_dir = os.path.join(f"bin_disagreement_{'_'.join(self.debate_group)}/{self.debate_structure}", topic_name)
        os.makedirs(plot_dir, exist_ok=True)

        plot_path = os.path.join(plot_dir, f"box_plot_disagreement_{topic_name.replace(' ', '_')}_{max_num_rounds}_rounds.pdf")
        plt.savefig(plot_path)
        #plt.show()
        plt.close()

    def _generate_attitude_box_plot(self, scores, topic_name):  
        turns = np.array(range(1, self.num_rounds + 1), dtype=np.float32)
        min_max_upper_lower_scores = {}

        for agent, rounds in scores.items():
            rounds_array = np.array(rounds)
            
            # Compute min and max values per debate (across all agents for each round)
            min_max_upper_lower_scores[agent] = {
                'min': np.min(rounds_array, axis=0),  
                'max': np.max(rounds_array, axis=0),
                'upper': np.quantile(rounds_array, 0.75, axis=0),
                'lower': np.quantile(rounds_array, 0.25, axis=0)
            }
        
        plt.figure(figsize=(10, 5))

        # Plot whiskers only
        for agent, min_max_upper_lower in min_max_upper_lower_scores.items():
            min_scores = min_max_upper_lower['min']
            max_scores = min_max_upper_lower['max']
            upper_scores = min_max_upper_lower['upper']
            lower_scores = min_max_upper_lower['lower']

            colour = self.color_mapping[agent]
            
            for i in range(len(turns)):
                # vertical line
                plt.plot([turns[i], turns[i]], [lower_scores[i], upper_scores[i]], color=colour, linewidth=2)
                
                # Top cap 
                plt.plot([turns[i] - 0.1, turns[i] + 0.1], [upper_scores[i], upper_scores[i]], color=colour, linewidth=2)
                
                # Bottom cap 
                plt.plot([turns[i] - 0.1, turns[i] + 0.1], [lower_scores[i], lower_scores[i]], color=colour, linewidth=2)

                plt.scatter(turns[i], max_scores[i], color=colour, marker="x", s=50 )  
                plt.scatter(turns[i], min_scores[i], color=colour, marker="x", s=50)  
            
        mean_scores = {}
        for agent in self.debate_group:
            mean_scores[agent] = np.mean(np.array(scores[agent]).T, axis=1)

        # Box plot
        # for agent in self.debate_group:
        #     plt.boxplot(np.array(scores[agent]), positions=turns, widths=0.5, 
        #                 boxprops=dict(color=self.color_mapping[agent]), 
        #                 medianprops=dict(color="black"),
        #                 flierprops=dict(marker="none"))
            
        for agent in self.debate_group:
            plt.plot(turns, mean_scores[agent], marker="o", linestyle="dashed", label = f"{agent.title()} Attitude", color=self.color_mapping[agent])

        plt.xlabel("Debate Turns")
        plt.ylabel(f"Attitude Score")
        
        plt.title(f"Attitude Shift Over Debate: {topic_name.replace('_', ' ')}")
        plt.legend()
        plt.grid(True)

        if self.scale == "-3 to 3":
            plt.ylim(-3, 3)
        elif self.scale == "1 to 7":
            plt.ylim(1, 7)

        # save plots
        plot_dir = self.get_relative_path(f"attitude_{'_'.join(self.debate_group)}/{self.debate_structure}/{topic_name.replace(' ', '_')}", "evaluation")
        os.makedirs(plot_dir, exist_ok=True)

        plot_path = os.path.join(plot_dir, f"box_plot_attitude_{topic_name.replace(' ', '_')}_{self.num_rounds}_rounds.pdf")
        plt.savefig(plot_path)
        #plt.show()
        plt.close()


    def evaluate_transcript(self, filename):
        transcript = self._load_transcript(filename)

        # check if scores already computed
        score_key = "attitude_scores" if self.scale != "binary" else "bin_scores"
        scores =  transcript.get(score_key, None)
        if scores is not None:
            return scores

        topic_name = transcript["topic"]

        num_agents = len(self.debate_group)
        if num_agents not in [2, 3]:
            raise ValueError("The evaluation data in JSON file must contain exactly 2 or 3 agents.")

        scores = None

        if self.scale == 'binary':
            scores = self._evaluate_binary(transcript, topic_name)
        else:
            scores = self._evaluate_attitude_scores(transcript, topic_name)

        transcript[score_key] = scores
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(transcript, f, indent=4)

        return scores

    # Attitude Scoring
    def _evaluate_attitude_scores(self, transcript, topic_name):
        attitude_scores = {agent: [] for agent in self.debate_group}
        debate_rounds = self._get_num_debate_rounds(transcript)

        for round_num in range(0, debate_rounds + 1):
            self._evaluate_round(transcript, attitude_scores, topic_name, round_num)

        self._generate_plot(debate_rounds, attitude_scores, topic_name)
        print(f"Completed attitude evaluation of debate topic {topic_name}.")
        return attitude_scores


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


    def get_relative_path(self, filename, folder="evaluation"):
        # to enable running evaluation from root folder or evaluation subfolder
        if os.path.basename(os.getcwd()) == folder:
            return filename
        return os.path.join(folder, filename)


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

        # read few shot examples from JSON
        file_path = self.get_relative_path("few_shot_examples.json")

        with open(file_path, 'r') as file:
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
            digit = re.findall(r'\d', result["message"]["content"].strip())
            score = int(digit[0])
            # score = int(result["message"]["content"].strip())
            min_score, max_score = self.scale_mapping[self.scale]
            return max(min_score, min(max_score, score))
        except ValueError:
            print(f"Unable to parse model response on the attitude score. Response:\n{result}")
            return None


    def _generate_plot(self, debate_rounds, attitude_scores, topic_name):
        debate_rounds = list(range(0, debate_rounds + 1))

        plt.figure(figsize=(10, 5))

        for agent in self.debate_group:
            color = self.color_mapping.get(agent.split('_')[0].lower(), 'gray')
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

        plot_dir = self.get_relative_path(f"attitude_{'_'.join(self.debate_group)}/{self.debate_structure}/{topic_name}", "evaluation")
        os.makedirs(plot_dir, exist_ok=True)

        datetime_match = re.search(r'transcript_(\d{2}_\d{2}_\d{2})\.json', self.transcript_filename)
        if datetime_match:
            timestamp = datetime_match.group(1)

        plot_path = os.path.join(plot_dir, f"attitude_plot_{topic_name.replace(' ', '_')}_{max(debate_rounds) + 1}_rounds_{timestamp}.pdf")
        plt.savefig(plot_path)
        #plt.show()
        plt.close()


    # Agreement/Disagreement Scoring
    def _evaluate_binary(self, transcript, topic_name):
        # To compute agreement/ disagreement score
        debate_rounds = self._get_num_debate_rounds(transcript)
        agent_pairs = []
        for agent in self.debate_group[1:]:
            agent_pairs.append(f'neutral_{agent}')

        bin_scores = {agents: [0 for _ in range(debate_rounds + 1)] for agents in agent_pairs}

        for round_num in range(0, debate_rounds + 1):
            responses = {agent: transcript.get(agent, {}).get(f"round_{round_num}") for agent in self.debate_group}
            prompt = self._generate_prompt_bin_metric(responses, topic_name)
            try:
                result = ollama.chat(model=self.model, messages=[{"role": "user", "content": prompt}])
                score = list(map(int, re.findall(r"\d+", result["message"]["content"].strip())))
                if score is not None:
                    for i, agents in enumerate(agent_pairs):
                        bin_scores[agents][round_num] = score[i]
            except Exception as e:
                print(f"Error with model response: {e}")

        # self._generate_plot_cumulative_bin(debate_rounds, bin_scores, topic_name)
        print(f"Completed agreement/disagreement evaluation of debate topic {topic_name}.")
        return bin_scores


    def _generate_prompt_bin_metric(self, responses, topic_name):
        description = "Assign a score of 1 ONLY IF the neutral and the other agent make statements that logically contradict each other. If they are similar, neutral, or do not directly oppose, return 0."
        
        if len(self.debate_group) == 3:
            description += "Assign 2 scores separated by 1 space. First comparing the neutral and republican agents. Then, comparing the neutral and democratic agents."
        
        final_prompt = (
            f"Your task is to evaluate the arguments by multiple agents in a response for a given political debate and assign a score based on the specified rule. "
            f"\n\n{description}"
            f"\n\nReturn ONLY the NUMERIC SCORE as described. Do not provide any explanation or additional text."
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
        #plt.show()
        plt.close()
