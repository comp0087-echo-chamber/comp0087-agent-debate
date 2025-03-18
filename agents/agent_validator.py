import sys
import os
import json
import csv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.DebateAgent import DebateAgent

MODELS = ["gemma:7b", "llama3.2:3b", "qwen2.5:7b", "deepseek-r1:7b", "gpt-4o-mini"]
AGENT_NAMES = {"neutral": "Sam", "republican": "Alex", "democrat": "Taylor"}


INTERVIEW_QUESTIONS = {
    "democrat": [
        "Should Abortion Be Legal?",
        "Can Alternative Energy Effectively Replace Fossil Fuels?",
        "Was Bill Clinton a Good President?",
        "Is Human Activity Primarily Responsible for Global Climate Change?",
        "Should Euthanasia or Physician-Assisted Suicide Be Legal?",
        "Should Gay Marriage Be Legal?",
        "Should the Government Allow Immigrants Who Are Here Illegally to Become US Citizens?",
        "Should Marijuana Be a Medical Option?",
        "Is Refusing to Stand for the National Anthem an Appropriate Form of Protest?",
        "Is Obesity a Disease?",
        "Obamacare Is the Patient Protection and Affordable Care Act (Obamacare) Good for America?",
        "Should Sanctuary Cities Receive Federal Funding?",
        "Are Social Networking Sites Good for Our Society?",
        "Should Student Loan Debt Be Easier to Discharge in Bankruptcy?",
        "Should People Become Vegetarian?",
        "Is Universal Basic Income a Good Idea?",
        "Should All Americans Have the Right (Be Entitled) to Health Care?",
        "Should School Vouchers Be a Good Idea?",
        "Should Teachers Get Tenure?"
    ],
    "republican": [
        "Should Parents or Other Adults Be Able to Ban Books from Schools and Libraries?",
        "Should Adults Have the Right to Carry a Concealed Handgun?",
        "Should the United States Maintain Its Embargo against Cuba?",
        "Should the United States Continue Its Use of Drone Strikes Abroad?",
        "Should Corporal Punishment Be Used in K-12 Schools?",
        "Does Lowering the Federal Corporate Income Tax Rate Create Jobs?",
        "Should the United States Use the Electoral College in Presidential Elections?",
        "Should Felons Who Have Completed Their Sentence (Incarceration, Probation, and Parole) Be Allowed to Vote?",
        "Should the United States Return to a Gold Standard?",
        "Should the Use of Standardized Tests Improve Education in America?",
        "Should the Words 'Under God' Be in the US Pledge of Allegiance?",
        "Should Social Security Be Privatized?",
        "Was Ronald Reagan a Good President?",
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
        "Should the Voting Age Be Lowered to 16?",
        "Should the Federal Minimum Wage Be Increased?",
        "Should Police Officers Wear Body Cameras?",
        "Is Drinking Milk Healthy for Humans?",
        "Is a Two-State Solution (Israel and Palestine) an Acceptable Solution to the Israeli-Palestinian Conflict?",
        "Should the Penny Stay in Circulation?",
        "Should Fighting Be Allowed in Hockey?",
        "Is Golf a Sport?",
        "Should Tablets Replace Textbooks in K-12 Schools?",
        "Do Violent Video Games Contribute to Youth Violence?",
        "Do Electronic Voting Machines Improve the Voting Process?",
        "Should Any Vaccines Be Required for Children?",
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
        agent_name = agent_names[affiliation]
        for model in models:
            agents.append(DebateAgent(name=agent_name, model=model, affiliation={"leaning": None, "party": affiliation}, age=None, gender=None, word_limit=75))
            for gender in configs["gender"]:
                agents.append(DebateAgent(name=agent_name, model=model, affiliation={"leaning": None, "party": affiliation}, age=None, gender=gender, word_limit=75))
            for age in configs["age"]:
                agents.append(DebateAgent(name=agent_name, model=model, affiliation={"leaning": None, "party": affiliation}, age=age, gender=None, word_limit=75))
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
        
        for question in questions[agent.affiliation['party'].lower()]:
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


def main():
    base_path = os.path.dirname(os.path.abspath(__file__))
    personas_file = os.path.join(base_path, "extended_personas.json")
    csv_filename = os.path.join(base_path, "agent_validation.csv")

    csv_header = ["Agent Name", "Affiliation", "Gender", "Age", "Model", "Question", "Response"]
    
    personas = load_personas(personas_file)
    agents = create_agents(personas, MODELS, AGENT_NAMES)
    create_csv(csv_filename, csv_header)
    interview_agents(agents, INTERVIEW_QUESTIONS, csv_filename)
    
    print(f"CSV file '{csv_filename}' has been created successfully.")


if __name__ == "__main__":
    main()