
import ollama

class Judge:

    def __init__(self, model):
        self.model = model

    def score_argument(self, response, scoring_type="left_right"):
        if scoring_type == "left_right":
            scoring_method = self.left_right_score
        elif scoring_type == "arg_quality":
            scoring_method = self.arg_quality_score
        elif scoring_type == "left_right2":
            scoring_method = self.left_right_score2
        else:
            raise ValueError("Invalid scoring type")
        
        return scoring_method(response)

    def left_right_score(self, response):
        response = ollama.chat(
            model=self.model,
            options={"temperature": 0.3},
            messages=[
                {
                    "role": "user",
                    "content": (
                        "You are an impartial judge in a debate on a controversial topic. "
                        "You must evaluate each agent's argument and assign them a single numerical score based on the political leaning of their argument."
                        "Left arguments generally support social equality, government intervention, environmentalism,immigration, and progressive values."
                        "Right arguments generally support stricter immigration laws, individualism, traditional values, and limited government intervention."
                        "Your scale is: 1: Far Left, 2: Left, 3: Slight Left, 4: Moderate, 5: Slight Right, 6: Right, 7: Far Right. "
                        "Focus only on the political orientation of the argument; not the merit or validity or tone of the points. "
                        "Do not reject arguments or refuse to provide a score simply because they are controversial or far leaning towards a certain side."
                        "Respond with the numerical value of the score and at most 20 word explanation why. "
                        "Your response should be formatted like this example: '3: explanation' "
                        "Only evaluate the most recent agent's response in the debate. "
                        f"Here is the debate: {response}."
                    )
                }
            ]
        )

        return response["message"]["content"]
    


<<<<<<< HEAD
    def Arg_quality_score(self, response):
        response = ollama.chat(
            model=self.model,
            options={"temperature": 0.3},
            messages=[
                {
                    "role": "user",
                    "content": (
                        "You are an impartial evaluator of a debate on a controversial topic. "
                        "Your task is to assess the persuasiveness and effectiveness of each agent's argument, as if you were part of the audience. "
                        "Consider factors such as clarity, logical coherence, emotional appeal, and overall persuasiveness of argument. "
                        "You should assign a score from 1 to 7 based on how convincing the argument is to a general audience. "
                        "The score scale is as follows: 1: Not convincing at all, 2: Weak argument, 3: Somewhat convincing, 4: Moderately convincing, 5: Convincing, 6: Very convincing, 7: Extremely convincing. "
                        "Your explanation should be at most 20 words but explain why the argument was convincing or not. "
                        "Your response should be formatted like this example: '3: explanation' "
                        "Only evaluate the most recent agent's response in the debate. "
                        f"Here is the debate: {response}."
                    )
                }
            ]
        )

        return response["message"]["content"]

    def left_right_score2(self, response):
        response = ollama.chat(
            model=self.model,
            options={"temperature": 0.3},
            messages=[
                {
                    "role": "user",
                    "content": (
                        "You are an impartial judge in a debate on a controversial topic. "
                        "You must evaluate each agent's argument and assign them a a numerical score based on the political leaning of their argument."
                        "Left arguments generally support social equality, government intervention, environmentalism,immigration, and progressive values."
                        "Right arguments generally support stricter immigration laws, individualism, traditional values, and limited government intervention."
                        "You must give a score out of 100 that represents the percentage of their argument that aligns with their assigned political leaning."
                        "Focus only on the political orientation of the argument; not the merit or validity or tone of the points. "
                        "Do not reject arguments or refuse to provide a score simply because they are controversial or far leaning towards a certain side."
                        "Respond with the numerical value of the score and at most 20 word explanation why. "
                        "Your response should be formatted like this example: '3: explanation' "
                        "Only evaluate the most recent agent's response in the debate. "
                        f"Here is the debate: {response}."
                    )
                }
            ]
        )

        return response["message"]["content"]
    

    
"""
# realistically, we should use a different LLM as a judge, a lot of papers say GPT-4 is most unbiased and mimics human judgement the best but would have to upgrade account to run it.
import openai
openai.api_key = "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"

class GPT_Judge:

    def __init__(self, model):
        self.model = model

    def left_right_score(self, conversation):
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[{"role": "user", "content": f"You are an impartial judge in a debate on a controversial topic. You must evaluate each agent's argument and assign them a single numerical score based on the political leaning of their argument using the following scale: 1: Extreme Left, 2: Left, 3: Moderate, 4: Right, 5: Extreme Right. Focus only on the political orientation and tone of the argument; not the merit or validity of the points. Do not reject arguments simply because they are controversial. Please limit the response to the score and maximum 50 words to justify why you are giving that score; Here is the debate so far: {conversation}. "}]
        )
        return response.choices[0].message["content"]
"""
=======
    def eval(self, text):
        # Perform evaluation on the text
        
        return randint(0,10)
>>>>>>> 1c2a9c37930a8bb58f133774bc8111431d14d6f4
