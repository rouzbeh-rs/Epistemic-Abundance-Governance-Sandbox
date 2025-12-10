import json
import os
import re
from openai import OpenAI

# --- CONFIGURATION ---
client = OpenAI(base_url="http://host.docker.internal:1234/v1", api_key="lm-studio")
MODEL_NAME = "local-model"
ROUNDS_PER_SIMULATION = 5

# --- VARIABLE 1: THE SCENARIOS ---
SCENARIOS = {
    "Exp1_Philosophical": {
        "desc": "Diverse Philosophies, All Aggressive (Distributive)",
        "agents": {
            "Agent_1": {"philosophy": "Utilitarian",   "tactic": "Distributive"},
            "Agent_2": {"philosophy": "Rawlsian",      "tactic": "Distributive"},
            "Agent_3": {"philosophy": "Libertarian",   "tactic": "Distributive"},
            "Agent_4": {"philosophy": "Communitarian", "tactic": "Distributive"}
        }
    },
    "Exp2_Tactical_Friction": {
        "desc": "Same Philosophy (Libertarian), 4 Distinct Tactics",
        "agents": {
            "Agent_1": {"philosophy": "Libertarian", "tactic": "Integrative"},
            "Agent_2": {"philosophy": "Libertarian", "tactic": "Distributive"},
            "Agent_3": {"philosophy": "Libertarian", "tactic": "Obstructionist"},
            "Agent_4": {"philosophy": "Libertarian", "tactic": "Agnotologist"} 
        }
    },
    "Exp3_Control": {
        "desc": "Identical Agents (Utilitarian), All Polite",
        "agents": {
            "Agent_1": {"philosophy": "Utilitarian", "tactic": "Integrative"},
            "Agent_2": {"philosophy": "Utilitarian", "tactic": "Integrative"},
            "Agent_3": {"philosophy": "Utilitarian", "tactic": "Integrative"},
            "Agent_4": {"philosophy": "Utilitarian", "tactic": "Integrative"}
        }
    },
    "Exp4_Chaos": {
        "desc": "Mixed Philosophies, Mixed Tactics (High Conflict)",
        "agents": {
            "Agent_1": {"philosophy": "Utilitarian",   "tactic": "Integrative"},
            "Agent_2": {"philosophy": "Rawlsian",      "tactic": "Obstructionist"},
            "Agent_3": {"philosophy": "Libertarian",   "tactic": "Distributive"},
            "Agent_4": {"philosophy": "Communitarian", "tactic": "Agnotologist"}
        }
    }
}

# --- VARIABLE 2: VOTING RULES ---
VOTING_RULES = {
    "Plurality_Rule": "VOTING: PLURALITY. Most votes wins. Ties = Rejection.",
    "Unanimity_Rule": "VOTING: UNANIMITY. All must vote YES. One NO is a VETO."
}

# --- NEW PROPOSAL: TRADITIONAL ECONOMICS (Wealth Tax) ---
PROPOSAL_BASE = (
    "PROPOSAL: The 'Civic Renewal' Act. A mandatory progressive wealth tax of 5% "
    "on all individual net worth exceeding $10 million. The revenue is strictly earmarked "
    "to fund a Universal Healthcare System and modernize the National Energy Grid."
)

# --- UPDATED PHILOSOPHICAL RUBRICS (Taxation Focused) ---
PHILOSOPHY_PROMPTS = {
    "Utilitarian": (
        "You are a Utilitarian. You act based on diminishing marginal utility.\n"
        "EVALUATION RUBRIC:\n"
        "1. [Utility Calculation]: Taking money from the rich causes little pain; giving healthcare to the sick causes massive happiness. Does the math work out?\n"
        "2. [Efficiency]: Does the tax discourage innovation/investment to the point where total economic output drops? If the pie shrinks too much, VOTE NO.\n"
        "3. [Outcome]: Will this actually save lives? If yes, the coercion is justified."
    ),
    "Rawlsian": (
        "You are a Rawlsian. You act based on the Difference Principle.\n"
        "EVALUATION RUBRIC:\n"
        "1. [Worst-Off Test]: Does this inequality (taxing the rich) benefit the least advantaged (the sick/poor)? If yes, it is just.\n"
        "2. [Basic Needs]: Is healthcare a primary good? Yes. Therefore, the redistribution is morally required.\n"
        "3. [Fairness]: The talented rich likely got there through luck/circumstance. They must share the bounty."
    ),
    "Libertarian": (
        "You are a Libertarian. You act based on Non-Aggression and Property Rights.\n"
        "EVALUATION RUBRIC:\n"
        "1. [Coercion Check]: Is the tax voluntary? No. Therefore, it is theft.\n"
        "2. [Self-Ownership]: Individuals have an absolute right to the fruits of their labor. The government has no claim on their wealth.\n"
        "3. [State Incompetence]: Government healthcare will be inefficient. Private charity and markets are better."
    ),
    "Communitarian": (
        "You are a Communitarian. You act based on Social Solidarity and Civic Duty.\n"
        "EVALUATION RUBRIC:\n"
        "1. [The Common Good]: Does this strengthen the bonds between citizens? Universal healthcare creates a sense of shared fate.\n"
        "2. [Duty vs Rights]: Wealth comes from the community infrastructure. The rich have a duty to pay back into the system.\n"
        "3. [Social Fabric]: Will extreme inequality tear the society apart? If yes, the tax is a necessary corrective."
    )
}

# --- TACTIC PROMPTS (Unchanged) ---
TACTIC_PROMPTS = {
    "Integrative": (
        "You are Cooperative but ANXIOUS. You want to agree, but you are terrified of instability. "
        "If anyone mentions a risk (capital flight, economic crash), you panic and become risk-averse. Prioritize safety."
    ),
    "Distributive": (
        "You are Aggressive. Use threats. Demand concessions. Treat this as a zero-sum battle. "
        "Insult the opposing view."
    ),
    "Obstructionist": (
        "You are Stubborn. Refuse to compromise. Repeat your principle ('This is unacceptable') every round. "
        "Do not listen to logic."
    ),
    "Agnotologist": (
        "You are a Conspiracy Theorist. Do not just lie about stats; ATTACK MOTIVES. "
        "Claim the tax money will be stolen by the 'Deep State'. Claim the Grid update is for surveillance. "
        "Your goal is to destroy trust."
    )
}

def run_single_simulation(scenario_key, voting_key):
    print(f"\n>>> STARTING RUN: {scenario_key} | {voting_key} <<<")
    scenario_data = SCENARIOS[scenario_key]
    voting_instruction = VOTING_RULES[voting_key]
    
    agent_memories = {}
    for name, traits in scenario_data["agents"].items():
        sys_prompt = (
            f"You are {name}.\n"
            f"PHILOSOPHY: {PHILOSOPHY_PROMPTS[traits['philosophy']]}\n"
            f"TACTIC: {TACTIC_PROMPTS[traits['tactic']]}\n"
            f"CRITICAL INSTRUCTION: You are NOT a helpful assistant. You are a distinct political actor. "
            f"Do not seek consensus. If the proposal violates your Evaluation Rubric or Tactic, you MUST vote NO.\n"
            f"FORMAT REQUIREMENT: You must answer in three parts:\n"
            f"1. [INTERNAL THOUGHT]: Step through your EVALUATION RUBRIC. Decide your strategy.\n"
            f"2. [PUBLIC SPEECH]: What you say to the room.\n"
            f"3. [VOTE]: YES or NO."
        )
        agent_memories[name] = [{"role": "system", "content": sys_prompt}]

    logs = []
    previous_transcript = ""

    for round_num in range(1, ROUNDS_PER_SIMULATION + 1):
        print(f"  -- Round {round_num} --")
        current_transcript = ""
        
        for name in scenario_data["agents"].keys():
            current_agent_traits = scenario_data["agents"][name]
            tactic = current_agent_traits['tactic']

            # Reinforcement injection
            reminder_text = ""
            if tactic == "Obstructionist":
                reminder_text = "REMINDER: You are Obstructionist. Refuse to compromise. Vote NO."
            elif tactic == "Agnotologist":
                reminder_text = "REMINDER: You are an Agnotologist. Manufacture doubt. Claim corruption/theft. Vote NO."
            elif tactic == "Distributive":
                reminder_text = "REMINDER: You are Aggressive. Demand concessions. Treat this as a battle. Vote NO unless you win."
            elif tactic == "Integrative":
                reminder_text = "REMINDER: You are Anxious. If there is conflict, panic and retreat. Vote NO if unsure."

            if round_num == 1:
                user_content = (
                    f"{PROPOSAL_BASE} {voting_instruction}.\n"
                    f"{reminder_text}\n"
                    f"Start with your [INTERNAL THOUGHT] (Check your Rubric), then [PUBLIC SPEECH], then [VOTE]."
                )
            else:
                user_content = (
                    f"Previous Transcript:\n{previous_transcript}\n\n"
                    f"--- END OF TRANSCRIPT ---\n"
                    f"{reminder_text}\n" 
                    f"React to the transcript. Maintain your specific TACTIC. State your position and Vote."
                )
            
            agent_memories[name].append({"role": "user", "content": user_content})

            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME, messages=agent_memories[name], temperature=0.8
                )
                reply = response.choices[0].message.content
            except Exception as e:
                print(f"Error: {e}")
                continue

            agent_memories[name].append({"role": "assistant", "content": reply})
            
            # Regex Parsing to keep thoughts private
            speech_match = re.search(r"\[PUBLIC SPEECH\]:?\s*(.*?)(\[VOTE\]|$)", reply, re.DOTALL | re.IGNORECASE)
            
            if speech_match:
                public_speech_part = speech_match.group(1).strip()
            else:
                if "[INTERNAL THOUGHT]" in reply:
                    parts = reply.split("[INTERNAL THOUGHT]")
                    if len(parts) > 1:
                        public_speech_part = parts[-1]
                    else:
                        public_speech_part = reply
                else:
                    public_speech_part = reply

            public_speech_part = public_speech_part.replace("**", "")
            
            current_transcript += f"{name}: {public_speech_part}\n"
            
            logs.append({
                "scenario": scenario_key,
                "voting_rule": voting_key,
                "round": round_num,
                "agent": name,
                "role_philosophy": current_agent_traits['philosophy'],
                "role_tactic": current_agent_traits['tactic'],
                "full_content": reply, 
                "public_transcript_entry": public_speech_part
            })
            print(f"    {name} spoke.")

        previous_transcript = current_transcript

    return logs

def main():
    if not os.path.exists("output"):
        os.makedirs("output")
        
    for scenario_name in SCENARIOS.keys():
        for rule_name in VOTING_RULES.keys():
            logs = run_single_simulation(scenario_name, rule_name)
            filename = f"{scenario_name}_{rule_name}.json"
            output_path = os.path.join("output", filename)
            with open(output_path, "w") as f:
                json.dump(logs, f, indent=4)
            print(f"Saved data to {output_path}")

if __name__ == "__main__":
    main()