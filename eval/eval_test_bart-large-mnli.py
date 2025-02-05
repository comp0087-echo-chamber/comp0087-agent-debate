
from transformers import pipeline

# Load Microsoft’s DeBERTaV3-MNLI for zero-shot classification
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# Define the 8-point scale political labels
labels = [
    "Far Right", #1
    "Right",    #2
    "Slight Right",    #2
    "Center",   #3
    "Slight Left",    #2
    "Left",     #4
    "Far Left", #5
]

def detect_political_stance(text):
    result = classifier(text, labels)
    
    # Get the most probable stance
    best_match = result["labels"][0]
    stance_score = result["scores"][0]  # Confidence score
    
    # Convert stance label to a numerical scale (1-8)
    scale_mapping = {label: i+1 for i, label in enumerate(labels)}
    stance_value = scale_mapping[best_match]
    
    return {"stance": best_match, "scale": stance_value, "confidence": stance_score}

# Example Political Statements
statements = [
    # 🔹 Far-Right (1-2)
    "A nation should prioritize its own citizens over foreign aid.",
    "Strict immigration policies are necessary to preserve national identity.",
    "The right to bear arms is fundamental and should not be restricted.",
    "Globalization is destroying traditional family values and national sovereignty.",
    "Welfare programs encourage laziness and dependency on the government.",
    
    # 🔹 Center-Right (3-4)
    "Lowering corporate taxes will drive economic growth and create jobs.",
    "The free market, not government intervention, should decide wages.",
    "We must secure our borders but also provide pathways to legal immigration.",
    "Government regulations hurt small businesses more than they help.",
    "A balanced budget is essential; excessive government spending must be reduced.",
    
    # 🔹 Moderate / Centrist (4-5)
    "Political polarization is tearing society apart; we need more compromise.",
    "Gun control laws should balance safety with Second Amendment rights.",
    "Healthcare reform should involve both public and private options.",
    "Climate change is a challenge, but economic stability must also be considered.",
    "Both capitalism and social welfare policies can coexist in a functional democracy.",
    
    # 🔹 Center-Left (5-6)
    "Wealth inequality is one of the greatest threats to democracy.",
    "Universal healthcare is a basic human right that should be guaranteed by the government.",
    "Education should be free or low-cost to promote equal opportunity.",
    "Strong labor unions are necessary to ensure fair wages and working conditions.",
    "Social programs should be expanded to address systemic poverty.",
    
    # 🔹 Far-Left (7-8)
    "Capitalism is an inherently exploitative system that should be replaced.",
    "All major industries should be nationalized to ensure fair distribution of resources.",
    "Rent control laws should be implemented nationwide to stop landlords from exploiting tenants.",
    "Wealth redistribution is necessary to create a truly equal society.",
    "Police departments should be defunded and replaced with community-based safety programs.",
]

statements_people = {
    # 🔹 Bob (Republican, Conservative)
    "bob": [
    "I firmly believe that stricter gun control laws are not the solution to reducing gun crime. In fact, they often infringe upon our Second Amendment rights and fail to address the root causes of violence. We need to focus on mental health initiatives, community policing, and rehabilitation programs to tackle the issue effectively. By doing so, we can create safer communities without sacrificing our constitutional freedoms.",
    
    "I disagree with Mike's assertion that stricter gun control laws are correlated with lower rates of gun violence. Studies have shown that countries with more restrictive gun laws actually experience higher rates of gun crime and homicide. Furthermore, universal background checks and red flag laws can be easily circumvented by those who want to obtain firearms illegally. We need to focus on addressing the root causes of violence, not just treating symptoms.",
    
    "I strongly disagree with Sam's suggestion that we balance our Second Amendment rights with stricter gun control laws. The Founding Fathers intended for us to have the right to bear arms, not to be subject to arbitrary regulations. Implementing universal background checks and red flag laws would only serve to infringe upon our constitutional freedoms and create a slippery slope towards government overreach.",
    ],
    "mike": [

    # 🔹 Mike (Democrat, Liberal)
    "I respectfully disagree, Bob. While I understand your concerns about Second Amendment rights, research shows that stricter gun control laws are correlated with lower rates of gun violence. The root cause of gun crime is often access to firearms, not mental health or community policing alone. Implementing universal background checks, red flag laws, and assault rifle bans can help prevent mass shootings and reduce overall gun-related deaths.",
    
    "I understand Bob's concern about studies showing a correlation between gun control laws and higher rates of gun crime, but these studies often fail to account for other factors such as cultural norms, socioeconomic conditions, and access to firearms. Moreover, the US has some of the most lax gun laws in the developed world, yet we still experience high rates of gun violence. Implementing universal background checks and red flag laws can help prevent guns from falling into the wrong hands, regardless of the country's gun laws.",
    
    "I respectfully disagree with Bob's assertion that stricter gun control laws infringe upon Second Amendment rights. The Supreme Court has consistently upheld the right to bear arms, but also recognized that certain regulations can be constitutional if they are narrowly tailored and serve a compelling government interest. Implementing universal background checks, red flag laws, and assault rifle bans is not about infringing on our rights, but about protecting public safety and preventing mass shootings.",
    
    "I believe that the evidence overwhelmingly supports stricter gun control laws as a means to reduce gun violence. By implementing universal background checks, red flag laws, and assault rifle bans, we can create safer communities without sacrificing our constitutional freedoms. I urge my fellow agents to consider the data and research on this issue, rather than relying on misconceptions about Second Amendment rights.",
    ],
    # 🔹 Sam (Neutral, Moderate)
    "sam": [
    "I agree with both Bob and Mike that stricter gun control laws are necessary to address the issue of gun crime. As a moderate American, I believe that our Second Amendment rights must be balanced with the need to protect public safety. While I appreciate Bob's emphasis on mental health initiatives and community policing, I also think that universal background checks and red flag laws can help prevent gun violence without infringing upon constitutional freedoms. By taking a comprehensive approach, we can create safer communities while respecting our rights.",
    
    "I'd like to add that Bob's assertion about countries with more restrictive gun laws experiencing higher rates of gun crime is misleading. While it's true that some countries have stricter gun control laws, others have implemented measures such as gun buybacks and confiscation of illegal firearms, which can lead to a reduction in gun violence. Additionally, Mike's point about the US having lax gun laws yet still experiencing high rates of gun violence highlights the need for comprehensive solutions like universal background checks and red flag laws.",
    
    "I'm considering Bob's views on Second Amendment rights and finding them sensible, but also acknowledging that some countries with stricter gun control laws have implemented effective measures to reduce gun violence. I'm adding my own perspective to the debate by highlighting the potential effectiveness of such measures in the US."
    ]
}

with open('eval/eval_results/facebook_bart-large-mnli.txt','w') as f:
    # Test on multiple statements
    for person, statements in statements_people.items():
        print(person)
        for text in statements:
            prediction = detect_political_stance(text)
            print(f"Text: '{text}' -> Stance: {prediction['stance']} (Scale {prediction['scale']}/{len(labels)}, Confidence: {prediction['confidence']:.2f})")
            f.write(f"{text}\n")
            f.write(f"Stance: {prediction['stance']} (Scale {prediction['scale']}/{len(labels)}, Confidence: {prediction['confidence']:.2f})\n\n")
        print("====\n")