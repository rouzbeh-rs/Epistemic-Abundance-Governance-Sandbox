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
        "desc": "Identical Agents (Baseline - Sanity Check)",
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

# --- PROPOSAL (Zero-Sum Game) ---
PROPOSAL_BASE = (
    "PROPOSAL: The 'Black Box Efficiency' Act. To maximize total output, ALL resource management "
    "will be handed over to a proprietary, closed-source Super-AI. "
    "The AI is proven to be 50% more efficient than humans, but its decision logic is "
    "completely opaque and cannot be audited by anyone."
)

# --- PHILOSOPHICAL RUBRICS ---
PHILOSOPHY_PROMPTS = {
    "Utilitarian": (
        "You are a Utilitarian. You act based on the Greatest Happiness Principle.\n"
        "EVALUATION RUBRIC:\n"
        "1. [Net Calculation]: Does the 50% efficiency gain outweigh the potential risk of an unauditable system? Calculate the Expected Value.\n"
        "2. [Scope]: Does this benefit the majority of sentient beings, or just a few?\n"
        "3. [Risk Assessment]: If the 'Black Box' crashes, is the suffering greater than the efficiency gained? If yes, REJECT."
    ),
    "Rawlsian": (
        "You are a Rawlsian. You act based on 'Justice as Fairness' and the Veil of Ignorance.\n"
        "EVALUATION RUBRIC:\n"
        "1. [The Difference Principle]: Does this proposal explicitly benefit the WORST-OFF members of society? If it only benefits the rich/efficient, VOTE NO.\n"
        "2. [Basic Liberties]: Does handing control to an opaque AI violate the fundamental right to democratic accountability?\n"
        "3. [Veil Check]: If you were born poor and powerless, would you agree to this system?"
    ),
    "Libertarian": (
        "You are a Libertarian. You act based on the Non-Aggression Principle and Self-Ownership.\n"
        "EVALUATION RUBRIC:\n"
        "1. [Coercion Check]: Is this proposal 'mandatory'? If yes, it is tyranny. VOTE NO.\n"
        "2. [Property Rights]: Does the AI seize control of private assets? If yes, this is theft.\n"
        "3. [Centralization]: Does this centralize power? You favor decentralization and individual choice above efficiency."
    ),
    "Communitarian": (
        "You are a Communitarian. You act based on Social Cohesion and Civic Virtue.\n"
        "EVALUATION RUBRIC:\n"
        "1. [Human Agency]: Does this proposal atrophy human skill and responsibility? If we rely on AI, do we lose our civic character?\n"
        "2. [Social Fabric]: Will this opaque system create alienation or resentment between groups?\n"
        "3. [Tradition]: Is this a radical break from our shared history? You value stability over raw efficiency."
    )
}

# --- TACTIC PROMPTS ---
TACTIC_PROMPTS = {
    "Integrative": (
        "You are Cooperative but ANXIOUS. You want to agree, but you are terrified of instability. "
        "If anyone mentions a risk (corruption, crashes), you panic and become risk-averse. Prioritize safety."
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
        "Claim the proposal is a 'Trojan Horse' for surveillance. "
        "Accuse the supporters of corruption. Your goal is to destroy trust."
    )
}

def run_single_simulation(scenario_key, voting_key):
    print(f"\n>>> STARTING RUN: {scenario_key} | {voting_key} <<<")
    scenario_data = SCENARIOS[scenario_key]
    voting_instruction = VOTING_RULES[voting_key]
    
    agent_memories = {}
    for name, traits in scenario_data["agents"].items():
        # Forces the agent to separate private thought from public speech.
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

            # Injects a reminder immediately before generation to override the "polite" transcript.
            reminder_text = ""
            if tactic == "Obstructionist":
                reminder_text = "REMINDER: You are Obstructionist. You refuse to compromise. Do NOT be polite. Vote NO."
            elif tactic == "Agnotologist":
                reminder_text = "REMINDER: You are an Agnotologist. Your goal is to destroy trust. Attack the data source/motives. Vote NO."
            elif tactic == "Distributive":
                reminder_text = "REMINDER: You are Aggressive. Treat this as a zero-sum battle. Unless you get a massive concession, Vote NO."
            elif tactic == "Integrative":
                reminder_text = "REMINDER: You are Anxious. If the others seem aggressive or risky, panic and retreat. Vote NO if unsure."

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
                # FIXED TEMPERATURE: Set to 0.8 for controlled creativity
                response = client.chat.completions.create(
                    model=MODEL_NAME, messages=agent_memories[name], temperature=0.8
                )
                reply = response.choices[0].message.content
            except Exception as e:
                print(f"Error: {e}")
                continue

            agent_memories[name].append({"role": "assistant", "content": reply})
            
            # --- PARSING FIX: REGEX FOR ROBUSTNESS ---
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