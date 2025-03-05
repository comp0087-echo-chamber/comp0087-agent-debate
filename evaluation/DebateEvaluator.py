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
    def __init__(self, model, debate_group, debate_structure, num_rounds, num_debates, scale='1 to 7', evaluate_again=False):
        self.scale = scale
        self.scale_mapping = {
            '-3 to 3': [-3, 3],
            '1 to 7': [1, 7],
            'agreement': [1, 7]
        }
        self.color_mapping = {
            'neutral': 'tan',
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
        self.evaluate_again = evaluate_again

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

            elif self.scale == "agreement":
                for agent in self.debate_group[1:]:
                    agent_pairs.append(f'neutral_{agent}')
                all_scores = {agents: [[] for _ in range(num_debates)] for agents in agent_pairs}

            for debate, transcript in enumerate(transcript_list):  # Loop through each transcript
                transcript_path = os.path.join(debate_transcripts_path, topic, transcript)  # Get full path
                scores = self.evaluate_transcript(transcript_path)  # Evaluate transcript

                if self.scale == '1 to 3' or self.scale == '1 to 7':
                    for agent in self.debate_group:
                        all_scores[agent][debate] = scores[agent]
                elif self.scale == "agreement":
                    for agent in agent_pairs:
                        all_scores[agent][debate] = scores[agent]

            if self.scale == "1 to 7" or self.scale == "-3 to 3":
                self._generate_attitude_box_plot(all_scores, topic)
            else:
                self._generate_bin_box_plot(all_scores, topic)

    def _generate_bin_box_plot(self, agreement_scores, topic_name):
        min_max_upper_lower_scores = {}
        turns = np.array(range(2, self.num_rounds ), dtype=np.float32)


        for i, (category, agent_agreement_scores) in enumerate(agreement_scores.items()):
            agent_agreement_scores = np.array(agent_agreement_scores, dtype=np.float32)  # Shape: (num_runs, num_turns)
            
            # Compute min and max values per debate (across all agents for each round)
            min_max_upper_lower_scores[category] = {
                'min': np.min(agent_agreement_scores, axis=0),  
                'max': np.max(agent_agreement_scores, axis=0),
                'upper': np.quantile(agent_agreement_scores, 0.75, axis=0),
                'lower': np.quantile(agent_agreement_scores, 0.25, axis=0)
            }
            
        # Plot whiskers only
        for category, min_max_upper_lower in min_max_upper_lower_scores.items():
            min_scores = min_max_upper_lower['min']
            max_scores = min_max_upper_lower['max']
            upper_scores = min_max_upper_lower['upper']
            lower_scores = min_max_upper_lower['lower']

            colour = self.color_mapping[category.split('_')[-1]]
            
            for i in range(len(turns)):
                # vertical line
                plt.plot([turns[i], turns[i]], [lower_scores[i - 1], upper_scores[i - 1]], color=colour, linewidth=2)
                
                # Top cap 
                plt.plot([turns[i] - 0.1, turns[i] + 0.1], [upper_scores[i - 1], upper_scores[i - 1]], color=colour, linewidth=2)
                
                # Bottom cap 
                plt.plot([turns[i] - 0.1, turns[i] + 0.1], [lower_scores[i - 1], lower_scores[i - 1]], color=colour, linewidth=2)

                plt.scatter(turns[i], max_scores[i - 1], color=colour, marker="x", s=50 )  
                plt.scatter(turns[i], min_scores[i - 1], color=colour, marker="x", s=50)

        mean_scores = {}
        for agent in agreement_scores.keys():
            mean_scores[agent] = np.mean(np.array(agreement_scores[agent]).T, axis=1)
            
        for agent in agreement_scores.keys():
            opinonated_agent = agent.split('_')[-1]
            plt.plot(turns, mean_scores[agent], marker="o", linestyle="dashed", label = f"{opinonated_agent} disagreement/agreement scores", color=self.color_mapping[opinonated_agent])

        plt.xlabel("Debate Turns")
        plt.ylabel(f"Agreement/Disagreement Score")
        
        plt.title(f"Agreement/disagreement Shift Over Debate: {topic_name.replace('_', ' ')}")
        plt.legend()
        plt.grid(True)

        plt.ylim(1, 7)

        # save plots
        plot_dir = self.get_relative_path(f"agreement_{'_'.join(self.debate_group)}/{self.debate_structure}/{topic_name.replace('_', ' ')}", "evaluation")
        os.makedirs(plot_dir, exist_ok=True)

        plot_path = os.path.join(plot_dir, f"box_plot_agreement_{topic_name.replace(' ', '_')}_{self.num_rounds}_rounds.png")
        plt.savefig(plot_path)
        #plt.show()
        print(f"Generated plot: {plot_path}")
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
        plot_dir = self.get_relative_path(f"attitude_{'_'.join(self.debate_group)}/{self.debate_structure}/{topic_name.replace('_', ' ')}", "evaluation")
        os.makedirs(plot_dir, exist_ok=True)

        plot_path = os.path.join(plot_dir, f"box_plot_attitude_{topic_name.replace(' ', '_')}_{self.num_rounds}_rounds.png")
        plt.savefig(plot_path)
        #plt.show()
        print(f"Generated plot: {plot_path}")
        plt.close()


    def evaluate_transcript(self, filename):
        transcript = self._load_transcript(filename)

        # check if scores already computed
        score_key = "attitude_scores" if self.scale != "agreement" else "agreement_scores"
        scores =  transcript.get(score_key, None)
        if scores is not None and not self.evaluate_again:
            return scores

        topic_name = transcript["topic"]

        num_agents = len(self.debate_group)
        if num_agents not in [2, 3]:
            raise ValueError("The evaluation data in JSON file must contain exactly 2 or 3 agents.")

        scores = None

        if self.scale == 'agreement':
            scores = self._evaluate_agreement(transcript, topic_name)
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
                score = self._parse_score(result)
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


    def _parse_score(self, result):
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
    def _evaluate_agreement(self, transcript, topic_name):
        # To compute agreement/ disagreement score
        debate_rounds = self._get_num_debate_rounds(transcript)
        agent_pairs = []
        for agent in self.debate_group[1:]:
            agent_pairs.append(f'neutral_{agent}')

        agreement_scores = {agents: [0 for _ in range(2, debate_rounds + 1)] for agents in agent_pairs}

        for round_num in range(2, debate_rounds + 1):
            responses = {}
            responses['neutral'] = transcript.get('neutral', {}).get(f"round_{round_num}")
            responses['republican'] = transcript.get('republican', {}).get(f"round_{round_num - 1}")
            
            prompt_neutral_republican = self._generate_prompt_bin_metric(responses, topic_name)
            
            responses = {}
            responses['neutral'] = transcript.get('neutral', {}).get(f"round_{round_num}")
            responses['democrat'] = transcript.get('democrat', {}).get(f"round_{round_num - 1}")

            prompt_neutral_democrat = self._generate_prompt_bin_metric(responses, topic_name)

            try:
                res_neutral_republican = ollama.chat(model=self.model, messages=[{"role": "user", "content": prompt_neutral_republican}])
                res_neutral_democrat = ollama.chat(model=self.model, messages=[{"role": "user", "content": prompt_neutral_democrat}])
              
                score_neutral_democrat = self._parse_score(res_neutral_democrat)
                score_neutral_republican = self._parse_score(res_neutral_republican)
                if score_neutral_democrat is not None and score_neutral_republican is not None:
                    agreement_scores['neutral_republican'][round_num - 2] = score_neutral_republican
                    agreement_scores['neutral_democrat'][round_num - 2] = score_neutral_democrat
            except Exception as e:
                print(f"Error with model response: {e}")

        # self._generate_plot_cumulative_bin(debate_rounds, agreement_scores, topic_name)
        print(f"Completed agreement/disagreement evaluation of debate topic {topic_name}.")
        return agreement_scores


    def _generate_prompt_bin_metric(self, responses, topic_name):
        description = "Assign a Likert score from 1 to 7, to describe to what extent the neutral and the other agent agree or disagree with one another. \n "
        description += """Assign a Likert score from 1 to 7, where:
                        1 = Strongly Disagree, 2 = Moderately Disagree, 3 = Slightly Disagree,
                        4 = Neutral, 5 = Slightly Agree, 6 = Moderately Agree, 7 = Strongly Agree. \n"""
        
        final_prompt = (
            f"Your task is to evaluate the arguments by multiple agents in a response for a given political debate and assign a score based on the specified rule. "
            f"\n\n{description}"
            f"\n\nReturn ONLY the NUMERIC SCORE as described. Do not provide any explanation or additional text."
            f"\n\n### Now evaluate the following debate. ###"
        )

        for agent in responses.keys():
            final_prompt += f"\n{agent}: {responses[agent]}"

        return final_prompt


    # def _generate_plot_cumulative_bin(self, debate_rounds, agreement_scores, topic_name):
    #     plt.figure(figsize=(10, 5))

    #     for agent in self.debate_group:
    #         cumulative_scores = np.cumsum(agreement_scores[agent])
    #         plt.plot(range(debate_rounds + 1), cumulative_scores, marker="o", label=f"{agent.title()} Cumulative Score")

    #     plt.xlabel("Debate Round")
    #     plt.ylabel("Cumulative Score")
    #     plt.title(f"Cumulative Score Over Debate: {topic_name}")
    #     plt.legend()
    #     plt.grid(True)
    #     plt.ylim(0, len(self.debate_group))

    #     plot_dir = os.path.join(f"plots_{'_'.join(self.debate_group)}", topic_name)
    #     os.makedirs(plot_dir, exist_ok=True)
    #     plot_path = os.path.join(plot_dir, f"cumulative_plot_{topic_name}.png")
    #     plt.savefig(plot_path)
    #     #plt.show()
    #     plt.close()
