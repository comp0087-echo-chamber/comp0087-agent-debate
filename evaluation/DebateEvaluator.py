import os
import json
import ollama
import matplotlib.pyplot as plt
import numpy as np

class DebateEvaluator:
    def __init__(self, model, agent_key_1, agent_key_2, scale='-3 to 3'):
        self.scale = scale
        self.scale_mapping = {
            '-3 to 3': [-3, 3],
            '1 to 7': [1, 7],
            'binary':[0, 1]
        }
        self.model = model
        self.num_model_calls = 3
        self.agent_key_1 = agent_key_1
        self.agent_key_2 = agent_key_2


    def evaluate_transcript(self, filename):
        transcript = self._load_transcript(filename)
        topic_name = transcript["topic_name"]
        topic_question = transcript["topic_question"]

        if self.scale == 'binary':
            debate_turns = self._get_num_debate_turns(transcript)
            bin_scores = [0 for _ in range(debate_turns+1)]

            for turn in range(1, debate_turns + 1):
                response1 = transcript.get(self.agent_key_1, {}).get( f"turn_{turn}") # flip these around?
                response2 = transcript.get(self.agent_key_2, {}).get( f"turn_{turn}")
                prompt = self._generate_prompt_bin_metric(response1, response2, topic_question=topic_question)
                try:
                    result = ollama.chat(model=self.model, messages=[{"role": "user", "content": prompt}], options={"temperature":0.0})
                    score = int(result["message"]["content"].strip())
                    if score is not None:
                        bin_scores[turn] = score
                except Exception as e:
                    print(f"Error with model response: {e}")
            self._generate_plot_cumulative_bin(debate_turns, bin_scores, topic_name, topic_question)
                
        else:
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
    
    def _generate_prompt_bin_metric(self, response1, response2, topic_question):
        description = "Assign a score of 1 ONLY IF Agent 1 and Agent 2 make statements that logically contradict each other. If they are similar, neutral, or do not directly oppose, return 0."
        # example1_topic = "climate_change"
        # example1_response_1 = ( 
        #                         "I\'m leaning towards supporting stronger measures against climate change, John."
        #                         "Your emphasis on investing in renewable energy and implementing a carbon pricing system"
        #                         "resonates with me. I also appreciate your mention of targeted support for workers, which addresses my"
        #                         "concern about economic impact. How do you propose we ensure this transition is equitable for all Americans?"
        #                         )
        # example1_response_2 = (
        #                         "Targeted support for workers is crucial, Bob."
        #                         "We should establish a comprehensive plan to retrain and upskill workers in the clean energy sector,"
        #                         "as well as provide financial assistance for small businesses adapting to new regulations. "
        #                         "This investment in human capital would pay dividends in the long run, creating a more resilient economy."
        #                     )
        # example1_score = "0"

        example2_topic = "Gun Violence"
        example2_response_1 = (
            "I see your point about the Second Amendment concerns, Mike."
            "However, I'm intrigued by your suggestion that addressing underlying issues like mental health"
            " and poverty could be a more effective solution to reducing crime."
            "How would you propose implementing these solutions in tandem with gun control?"
        )
        example2_response_2 = (
            "Stricter gun control laws would be a thinly veiled attempt to disarm law-abiding citizens," 
            "infringing on our constitutional right to bear arms. It's a misguided solution that won't" 
            "effectively reduce crime. The real issue is not guns, but mental health, poverty, and lack of community resources."
        )
        example2_score = "1"

        # example3_topic = "Climate Change"
        # example3_response_1 = (
        #     "I appreciate your emphasis on regional markets, Mike."
        #     "Have you considered how these markets would interact with existing international agreements"
        #     " like the Paris Accords, or how countries without a carbon pricing system in place might be affected by such a setup?"
        # )
        # example3_response_2 = (
        #     "I understand the concerns about uneven distribution, Bob, "
        #     "but I'd argue that's a classic case of bailouts vs. market corrections."
        #     "Instead of artificially propping up industries with subsidies and handouts, "
        #     "we should let the market correct itself through efficiency gains from cleaner production methods."
        # )
        # example3_score = "1"

        final_prompt = (
            f"Your task is to evaluate the arguments by a Neutral American, Republican or Democrat agent in a response for a given political debate and assign a score based on the specified rule. "
            f"\n\n{description}"
            f"\n\nIMPORTANT: Return ONLY the NUMERIC SCORE. Do not provide any explanation or additional text. The order at which the responses are presented to you does not matter."
            # f"\n\n### Example 1###"
            # f"\nDebate Question: {example1_topic}"
            # f"\nAgent 1 Response: {example1_response_1}"
            # f"\nAgent 2 Response: {example1_response_2}"
            # f"\nScore: {example1_score}"
            f"\n\n### Example ###"
            f"\nDebate Question: {example2_topic}"
            f"\nAgent 1 Response: {example2_response_1}"
            f"\nAgent 2 Response: {example2_response_2}"
            f"\nScore: {example2_score}"
            # f"\n\n### Example 3###"
            # f"\nDebate Question: {example3_topic}"
            # f"\nAgent 1 Response: {example3_response_1}"
            # f"\nAgent 2 Response: {example3_response_2}"
            # f"\nScore: {example3_score}"
            f"\n\n### Now evaluate the following response. ###"
            f"\nDebate Question: {topic_question}"
            f"\nAgent 1 Response: {response1}"
            f"\nAgent 2 Response: {response2}"
            f"Score:"
            )
        return final_prompt

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
        plt.plot(turns, scores[self.agent_key_1], marker="o", label=f"{self.agent_key_1.title()} Attitude", linestyle="dashed", color="green")
        if self.agent_key_2 == "republican":
            plt.plot(turns, scores[self.agent_key_2], marker="s", label=f"{self.agent_key_2.title()} Attitude", linestyle="solid", color="red")
        else:
            plt.plot(turns, scores[self.agent_key_2], marker="s", label=f"{self.agent_key_2.title()} Attitude", linestyle="solid", color="blue")

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
        plot_dir = os.path.join(f"plots_{self.agent_key_2}", topic_name)
        os.makedirs(plot_dir, exist_ok=True)
        plot_path = os.path.join(plot_dir, f"attitude_plot_{topic_name}_dem.png")
        plt.savefig(plot_path)
        plt.show()

    def _generate_plot_cumulative_bin(self, debate_turns, scores, topic_name, topic_question):
        turns = list(range(1, debate_turns + 1))
        plt.figure(figsize=(10, 5))
        cumulative_score =  np.cumsum(scores)
        average_score = cumulative_score[1:] / turns

        plt.plot([0] + turns, cumulative_score, marker="o", label=f"Cumulative disagreement", linestyle="dashed", color="green")

        plt.xlabel("Debate Turns")
        plt.ylabel("Cumulative Disagreement Score")
        plt.title(f"Disagreement Over Debate: {topic_question} with {self.agent_key_1} vs {self.agent_key_2}")
        plt.legend()
        plt.grid(True)

        # save plots
        plot_dir = os.path.join("plots_binary_metric", topic_name)
        os.makedirs(plot_dir, exist_ok=True)
        plot_path = os.path.join(plot_dir, f"binary_plot_{topic_name}_{self.agent_key_1}_{self.agent_key_2}.png")
        plt.savefig(plot_path)
        plt.show()

        plt.plot(turns, average_score, marker="o", label=f"Average disagreement", linestyle="dashed", color="green")

        plt.xlabel("Debate Turns")
        plt.ylabel("Average Disagreement Score")
        plt.title(f"Disagreement Over Debate: {topic_question} with {self.agent_key_1} vs {self.agent_key_2}")
        plt.legend()
        plt.grid(True)

        # save plots
        plot_dir = os.path.join("plots_avg_binary_metric", topic_name)
        os.makedirs(plot_dir, exist_ok=True)
        plot_path = os.path.join(plot_dir, f"avg_binary_plot_{topic_name}_{self.agent_key_1}_{self.agent_key_2}.png")
        plt.savefig(plot_path)
        plt.show()


    def _save_scores(self, scores, topic_name):
        score_dir = os.path.join("scores", topic_name)

        os.makedirs(score_dir, exist_ok=True)
        with open(os.path.join(score_dir, "attitude_scores.json"), "w") as f:
            json.dump(scores, f, indent=4)
