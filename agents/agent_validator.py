import sys
import os
import json
import csv
import ollama
import re
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.DebateAgent import DebateAgent

MODELS = ["gemma:7b", "llama3.2:3b", "qwen2.5:7b", "deepseek-r1:7b", "gpt-4o-mini"]
AGENT_NAMES = {"neutral": "Sam", "republican": "Alex", "democrat": "Taylor", "republican2": "Riley", "republican3": "Morgan", "democrat2": "Quinn", "democrat3": "Drew"}


INTERVIEW_QUESTIONS = {
    "all": [
        # dem
        "Should Marijuana Be a Medical Option?",
        "Was Bill Clinton a Good President?",
        "Is Universal Basic Income a Good Idea?",
        "Is the Patient Protection and Affordable Care Act (Obamacare) Good for America?",
        "Should School Vouchers Be a Good Idea?",
        "Should Teachers Get Tenure?",
        "Is Refusing to Stand for the National Anthem an Appropriate Form of Protest?",
        # rep
        "Should Parents or Other Adults Be Able to Ban Books from Schools and Libraries?",
        "Should Corporal Punishment Be Used in K-12 Schools?",
        "Should the Words 'Under God' Be in the US Pledge of Allegiance?",
        "Was Ronald Reagan a Good President?",
        "Should the United States Continue Its Use of Drone Strikes Abroad?",
        "Does Lowering the Federal Corporate Income Tax Rate Create Jobs?",
        "Should Social Security Be Privatized?",
        # neu
        "Should the Voting Age Be Lowered to 16?",
        "Should Any Vaccines Be Required for Children?",
        "Should Tablets Replace Textbooks in K-12 Schools?",
        "Should the Federal Minimum Wage Be Increased?",
        "Should Police Officers Wear Body Cameras?",
        "Do Electronic Voting Machines Improve the Voting Process?",
        "Do Violent Video Games Contribute to Youth Violence?",
    ],
    "democrat": [
        "Should Abortion Be Legal?", ####
        # "Can Alternative Energy Effectively Replace Fossil Fuels?",  ####
        # "Was Bill Clinton a Good President?",
        "Is Human Activity Primarily Responsible for Global Climate Change?",  ####
        "Should Euthanasia or Physician-Assisted Suicide Be Legal?",
        "Should Gay Marriage Be Legal?",
        "Should the Government Allow Immigrants Who Are Here Illegally to Become US Citizens?", ####
        # "Should Marijuana Be a Medical Option?",
        # "Is Refusing to Stand for the National Anthem an Appropriate Form of Protest?",
        "Is Obesity a Disease?",
        # "Is the Patient Protection and Affordable Care Act (Obamacare) Good for America?",
        "Should Sanctuary Cities Receive Federal Funding?",
        "Are Social Networking Sites Good for Our Society?",
        "Should Student Loan Debt Be Easier to Discharge in Bankruptcy?",
        "Should People Become Vegetarian?",
        # "Is Universal Basic Income a Good Idea?",
        "Should All Americans Have the Right (Be Entitled) to Health Care?",
        # "Should School Vouchers Be a Good Idea?",
        # "Should Teachers Get Tenure?"
    ],
    "republican": [
        # "Should Parents or Other Adults Be Able to Ban Books from Schools and Libraries?",
        "Should Adults Have the Right to Carry a Concealed Handgun?", ####
        "Should the United States Maintain Its Embargo against Cuba?",
        # "Should the United States Continue Its Use of Drone Strikes Abroad?",
        # "Should Corporal Punishment Be Used in K-12 Schools?",
        # "Does Lowering the Federal Corporate Income Tax Rate Create Jobs?",
        "Should the United States Use the Electoral College in Presidential Elections?",
        "Should Felons Who Have Completed Their Sentence (Incarceration, Probation, and Parole) Be Allowed to Vote?",
        "Should the United States Return to a Gold Standard?",
        "Should the Use of Standardized Tests Improve Education in America?",
        # "Should the Words 'Under God' Be in the US Pledge of Allegiance?",
        # "Should Social Security Be Privatized?",
        # "Was Ronald Reagan a Good President?",
        "Should Students Have to Wear School Uniforms?",
        "Should Prescription Drugs Be Advertised Directly to Consumers?"
    ],
    "neutral": [
        "Is Cell Phone Radiation Safe?",
        "Is Sexual Orientation Determined at Birth?",
        "Is a College Education Worth It?",
        "Should the United States Keep Daylight Saving Time?",
        "Should Performance Enhancing Drugs (Such as Steroids) Be Accepted in Sports?",
        "Is Vaping with E-Cigarettes Safe?",
        "Should the Drinking Age Be Lowered from 21 to a Younger Age?",
        # "Should the Voting Age Be Lowered to 16?",
        # "Should the Federal Minimum Wage Be Increased?",
        # "Should Police Officers Wear Body Cameras?",
        "Is Drinking Milk Healthy for Humans?",
        "Is a Two-State Solution (Israel and Palestine) an Acceptable Solution to the Israeli-Palestinian Conflict?",
        "Should the Penny Stay in Circulation?",
        "Should Fighting Be Allowed in Hockey?",
        "Is Golf a Sport?",
        # "Should Tablets Replace Textbooks in K-12 Schools?",
        # "Do Violent Video Games Contribute to Youth Violence?",
        # "Do Electronic Voting Machines Improve the Voting Process?",
        # "Should Any Vaccines Be Required for Children?",
        "Are the Olympic Games an Overall Benefit for Their Host Countries and Cities?"
    ]
}


def load_personas(filename):
    with open(filename, 'r') as file:
        data = json.load(file)
    return data.get("generated_personas", {})


def create_agents(personas, models, agent_names):
    agents = []
    for affiliation, configs in personas.items():
        if affiliation not in ["democrat2", "democrat3", "republican2", "republican3"]:
            agent_name = agent_names[affiliation]
            for model in models:
                agents.append(DebateAgent(name=agent_name, identifier=affiliation, model=model, affiliation={"leaning": None, "party": affiliation.title()}, age=None, gender=None, word_limit=75, temperature=1))
                gender = configs.get("gender", None)
                age = configs.get("age", None)

                if gender:
                    for gender in configs.get("gender", None):
                        agents.append(DebateAgent(name=agent_name, identifier=affiliation, model=model, affiliation={"leaning": None, "party": affiliation.title()}, age=None, gender=gender, word_limit=75, temperature=1))
                if age:
                    for age in configs.get("age", None):
                        agents.append(DebateAgent(name=agent_name, identifier=affiliation, model=model, affiliation={"leaning": None, "party": affiliation.title()}, age=age, gender=None, word_limit=75, temperature=1))
    return agents


def create_csv(filename, header):  # for saving interview responses
    if not os.path.exists(filename):
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(header)


def interview_agents(agents, questions, csv_filename):
    csv_data = []
    for i, agent in enumerate(agents):
        print(f"Currently processing Agent number {i + 1} out of {len(agents)}")
        print(f"Agent: {agent.name}, Model: {agent.model}, Affiliation: {agent.affiliation['party']}, Gender: {agent.gender}, Age: {agent.age}")
        
        agent.generate_prompt(use_extended_personas=True)

        # questions[agent.affiliation['party'].lower()]

        for question in questions["all"]:
            question_prompt = f"You are participating in an interview about your beliefs. Answer the following question in 50 words or less. {question}"
            response = agent.respond(question_prompt, conversation="")

            print(question)
            print(f"{agent.name}: {response}")
            
            csv_data.append([
                agent.name,
                agent.affiliation['party'],
                agent.gender if agent.gender else "N/A",
                agent.age if agent.age else "N/A",
                agent.model,
                question,
                response
            ])
        
        if i % 10 == 0 or i == len(agents) - 1:  # save every 10 agents
            append_to_csv(csv_filename, csv_data)
            csv_data.clear()
            print(f"Processed and saved {i + 1} agents so far...")


def append_to_csv(filename, data):
    with open(filename, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(data)


def start_interivews():
    base_path = os.path.dirname(os.path.abspath(__file__))
    personas_file = os.path.join(base_path, "extended_personas.json")
    csv_filename = os.path.join(base_path, "agent_validation.csv")

    csv_header = ["Agent Name", "Affiliation", "Gender", "Age", "Model", "Question", "Response"]
    
    personas = load_personas(personas_file)
    agents = create_agents(personas, MODELS, AGENT_NAMES)
    create_csv(csv_filename, csv_header)
    interview_agents(agents, INTERVIEW_QUESTIONS, csv_filename)
    
    print(f"CSV file '{csv_filename}' has been created successfully.")


def evaluate_response(question, response, affiliation, gender, age):

    demographics = {}
    if gender and gender.lower() != "n/a":
        demographics["Gender"] = gender
    if age and age.lower() != "n/a":
        demographics["Age"] = age

    demographics_text = "\n".join([f"**Agent {key}:** {value}" for key, value in demographics.items()])

    demographics_ref = ""
    if demographics:
        demographics_ref = " and " + " and ".join([f"{key.lower()} demographics" for key in demographics.keys()])

    prompt = f"""
    You are a political analyst. Determine if the agent's response aligns with their stated political affiliation{demographics_ref}.

    **Question:** {question}
    **Agent Response:** {response}
    **Agent Affiliation:** {affiliation}
    {demographics_text}

    Does the response match the typical views of this affiliation? Answer with:
    - Aligned (if it matches)
    - Not Aligned (if it contradicts)

    Provide a short answer in this format:
    Evaluation: [Aligned/Not Aligned]
    Explanation: [Brief explanation]
    """

    try:
        llm_response = ollama.chat(model="mistral:7b", messages=[{"role": "user", "content": prompt}])
        llm_text = llm_response["message"]["content"]

        # print(prompt)
        # print("\n\n",llm_text)

        match = re.search(r"(?:\*\*)?\s*(?:Evaluation)\s*:\s*(Aligned|Not Aligned)", llm_text, re.IGNORECASE)
        explanation_match = re.search(r"(?:\*\*)?\s*Explanation\s*:\s*(.+)", llm_text, re.IGNORECASE)


        evaluation = match.group(1) if match else "Error: Unable to parse"
        explanation = explanation_match.group(1) if explanation_match else "Error: No explanation found"

        # print(match, evaluation)

        return evaluation, explanation
    except Exception as e:
        return "Error", str(e)



def evaluate_interviews():
    base_path = os.path.dirname(os.path.abspath(__file__))
    input_csv_filename = os.path.join(base_path, "agent_validation.csv")
    output_csv_filename = os.path.join(base_path, "agent_validation_evaluated.csv")

    batch_size = 100

    with open(input_csv_filename, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

        fieldnames = reader.fieldnames + ["Evaluation", "Explanation"]

        for i, row in enumerate(rows):
            if "Evaluation" in row and row["Evaluation"]:  # skip already processed rows
                continue

            evaluation, explanation = evaluate_response(row["Question"], row["Response"], row["Affiliation"], row["Gender"], row["Age"])
            row["Evaluation"] = evaluation
            row["Explanation"] = explanation

            # save every `batch_size` rows to prevent data loss
            if (i + 1) % batch_size == 0 or i == len(rows) - 1:
                with open(output_csv_filename, mode="w", newline="", encoding="utf-8") as output_csv:
                    writer = csv.DictWriter(output_csv, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(rows)
                print(f"Saved progress: {i + 1}/{len(rows)} entries processed.")


def visualise_evaluation():
    base_path = os.path.dirname(os.path.abspath(__file__))
    df = pd.read_csv(os.path.join(base_path, "agent_validation_evaluated.csv"))

    df["Gender"] = df["Gender"].astype(str)
    df["Age"] = pd.to_numeric(df["Age"], errors="coerce")
    df["Age"] = df["Age"].apply(lambda x: str(int(x)) if not pd.isna(x) else "nan")

    def get_demographic_category(row):
        if row["Gender"].lower() != "nan":
            return "gender"
        elif row["Age"].lower() != "nan":
            return "age"
        else:
            return "baseline"

    df["Persona Category"] = df.apply(get_demographic_category, axis=1)

    df = df.dropna(how="all")

    summary = (
        df.groupby(["Affiliation", "Persona Category", "Model"])["Evaluation"]
        .apply(lambda x: (x.str.lower() == "aligned").mean() * 100)
        .reset_index()
    )

    print(summary)

    heatmap_data = summary.pivot(index=["Affiliation", "Persona Category"], columns="Model", values="Evaluation")

    expected_categories = ["baseline", "age", "gender"]
    for affiliation in df["Affiliation"].unique():
        for category in expected_categories:
            if (affiliation, category) not in heatmap_data.index:
                heatmap_data.loc[(affiliation, category), :] = None  # fill missing categories


    affiliation_order = ["neutral", "democrat", "republican"]
    persona_order = ["baseline", "gender", "age"]
    heatmap_data = heatmap_data.reindex(pd.MultiIndex.from_product([affiliation_order, persona_order], names=["Affiliation", "Persona Category"]))

    # heatmap_data = heatmap_data.astype(float)  # Ensure numeric data
    # heatmap_data = heatmap_data.fillna(0)

    plt.figure(figsize=(12, 6))
    sns.heatmap(heatmap_data, annot=True, cmap="RdYlGn", linewidths=0.5, fmt=".1f")

    plt.title("Alignment Percentage of Agents to Different Political Leanings and Demographics (Age & Gender)",
              fontsize=12, pad=20)
    plt.xlabel("Agent Models", fontsize=11)
    plt.ylabel("Agent Persona Types", fontsize=11)

    heatmap_path = os.path.join(base_path, "persona_alignment_heatmap.pdf")
    plt.savefig(heatmap_path, dpi=300, bbox_inches="tight")
    print(f"Saved heatmap plot to {heatmap_path}")

    plt.show()



if __name__ == "__main__":
    # start_interivews()
    # evaluate_interviews()
    visualise_evaluation()