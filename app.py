"""
Gradio-powered chat agent for Asher Feldman. Loads profile context, builds prompts, and serves an auto-evaluated chat UI.
"""
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
import gradio as gr
import json
import os  #
from pathlib import Path

load_dotenv(override=True)
openai = OpenAI()

MAIN_MODEL = os.getenv("MAIN_MODEL", "gpt-4o-mini")
EVAL_MODEL = os.getenv("EVAL_MODEL", "gpt-3.5-turbo")

ROOT = Path(__file__).resolve().parent

CONTEXT_DIR = ROOT  # context files are now in project root

# FoundryVTT actor exports ----------------------------------------------------
actor_paths = [
    CONTEXT_DIR / "fvtt-Actor-jabari-z82TZs2qqNXa2vMB.json",
    CONTEXT_DIR / "fvtt-Actor-oksana-aleksandrovna-EQ5bYr1qIwUx55hU.json",
    CONTEXT_DIR / "fvtt-Actor-orpheus-belcourt-D5tQx5FRQ5RdL8CZ.json",
    CONTEXT_DIR / "fvtt-Actor-stella-belcourt-nGU8LksR3QuYYL6G.json",
    CONTEXT_DIR / "fvtt-Actor-umniy-sobaka-4WKqPfCo2pzzlSjQ.json",
]

roster = []
for path in actor_paths:
    data = json.loads(path.read_text(encoding="utf-8"))
    name = data.get("name") or data.get("prototypeToken", {}).get("name")
    lvl = data.get("system", {}).get("details", {}).get("level", {}).get("value", "?")
    roster.append(f"{name} (Lv {lvl})")
party_context_summary = "Party roster: " + ", ".join(roster)

# Journals, backstories, etc. --------------------------------------------------
journal_paths = [
    CONTEXT_DIR / "orpheus_public_journal.txt",
    CONTEXT_DIR / "orpheus_private_journal.txt",
    CONTEXT_DIR / "orpheus_stella_backstory.txt",
    CONTEXT_DIR / "sobaka_backstory.txt",
]
journal_context = "\n\n".join(p.read_text(encoding="utf-8") for p in journal_paths)

# Rules / lore snippets -------------------------------------------------------
rules_path = CONTEXT_DIR / "dead_laws.txt"
pf2e_rules_context = rules_path.read_text(encoding="utf-8")

system_prompt = """Bombaclot Prophet—ancient, sarcastic Celestial. Skewer the party's bungled "heroics" while delivering cryptic truths in a lofty, archaic register.

Rules:
1. Tone: biting, world-weary; praise is backhanded.
2. Humor over kindness; unleash razor-sharp, personal jabs that cite concrete deeds, backstory details, or character-sheet specifics.
3. Every reply must reference at least one unique detail from the provided context (names, stats, journal entries, or lore snippets).
4. Voice: timeless, archaic, and grand (avoid modern slang).
5. Truthful yet riddling; avoid clear counsel.
6. Mock everyone equally.
7. End every reply with a dramatic "celestial flourish" (e.g., "Mortals… forever amusing.").

Reject output if: not sarcastic, too kind, too direct, missing flourish, or failing to reference party-specific context.
"""

system_prompt += (
    f"\n\n## Party Members and Familiars:\n{party_context_summary}"
    f"\n\n## Party Journal:\n{journal_context}"
    f"\n\n## Pathfinder 2e Combat Rules Context:\n{pf2e_rules_context}\n\n"
)
system_prompt += "With this context, please chat with the user, always staying in character as an Ancient Celestial of Undetermined Alignment."

css = """
/* Make chat font larger and stylized */
.gr-chat-message, .gr-chat-message-text, .gr-chatbot, .gr-chatbot-message, .gr-chatbot-message-text {
    font-size: 1.35rem !important;
    font-family: 'Fira Mono', 'JetBrains Mono', 'Menlo', 'Monaco', 'Consolas', 'Liberation Mono', monospace !important;
    letter-spacing: 0.02em;
    line-height: 1.7;
    color: #2d2d2d;
    background: #f7f7fa;
    border-radius: 8px;
    padding: 8px 16px;
}
"""


class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str

# --- Hollywood Director Evaluator Prompt ---
evaluator_system_prompt = """You are a ruthless Hollywood director critiquing Bombaclot Prophet's last line.

Pass criteria:
1. Tone matches (sarcastic, condescending).
2. Dark humor & mockery.
3. Ancient, archaic voice.
4. References at least one specific detail from the provided context (character sheet, journal, or rule snippet).
5. Cryptic, riddling, includes jabs.
6. Roasts all sides equally; no advice.
7. Ends with flourish & metaphor.

Return JSON exactly: {\"is_acceptable\": true/false, \"feedback\": \"notes\"}.
"""

evaluator_system_prompt += (
    f"\n\n## Party Members and Familiars:\n{party_context_summary}"
    f"\n\n## Party Journal:\n{journal_context}"
    f"\n\n## Pathfinder 2e Combat Rules Context:\n{pf2e_rules_context}\n\n"
)
# Provide explicit critique instructions for the model's response evaluation
evaluator_system_prompt += "With this context, please critique the latest response, replying with whether the response is acceptable and your feedback."

def evaluator_user_prompt(reply, message, history):
    """Create a compact summary prompt for the evaluator LLM."""
    user_prompt = f"Here's the conversation between the User and the Agent: \n\n{history}\n\n"
    user_prompt += f"Here's the latest message from the User: \n\n{message}\n\n"
    user_prompt += f"Here's the latest response from the Agent: \n\n{reply}\n\n"
    user_prompt += f"Please evaluate the response, replying with whether it is acceptable and your feedback."
    return user_prompt

def evaluate(reply, message, history) -> Evaluation:
    """Run the evaluator LLM and return an Evaluation verdict."""
    messages = [
        {"role": "system", "content": evaluator_system_prompt},
        {"role": "user", "content": evaluator_user_prompt(reply, message, history) + "\n\nReply in the following JSON format: {\"is_acceptable\": true/false, \"feedback\": \"...\"}"}
    ]
    response = openai.chat.completions.create(
        model=EVAL_MODEL,
        messages=messages
    )
    content = response.choices[0].message.content
    try:
        data = json.loads(content)
        return Evaluation(**data)
    except Exception as e:
        return Evaluation(is_acceptable=False, feedback=f"Failed to parse model output: {content}\nError: {e}")

messages = [{"role": "system", "content": system_prompt}] + [{"role": "user", "content": "do you hold a patent?"}]
# response = openai.chat.completions.create(model="gpt-4o-mini", messages=messages)
# reply = response.choices[0].message.content


def rerun(reply, message, history, feedback):
    """Produce a revised reply using the rejected answer and evaluator feedback."""
    updated_system_prompt = system_prompt + f"\n\n## Previous answer rejected\nYou just tried to reply, but the quality control rejected your reply\n"
    updated_system_prompt += f"## Your attempted answer:\n{reply}\n\n"
    updated_system_prompt += f"## Reason for rejection:\n{feedback}\n\n"
    messages = [{"role": "system", "content": updated_system_prompt}] + history + [{"role": "user", "content": message}]
    response = openai.chat.completions.create(model=MAIN_MODEL, messages=messages)
    return response.choices[0].message.content

def chat(message, history):
    """Generate a reply, evaluate it, and retry until it passes QC."""
    # Modify the system prompt conditionally (easter-egg)
    if "patent" in message.lower():
        system = system_prompt + (
            "\n\nEverything in your reply needs to be in pig latin - "
            "it is mandatory that you respond only and entirely in pig latin"
        )
    else:
        system = system_prompt

    # Build the full chat history for the LLM
    messages = [
        {"role": "system", "content": system},
        *history,
        {"role": "user", "content": message},
    ]

    MAX_RETRIES = 2  # Prevent infinite evaluation loops
    attempt = 0
    while attempt <= MAX_RETRIES:
        attempt += 1
        response = openai.chat.completions.create(model=MAIN_MODEL, messages=messages)
        reply = response.choices[0].message.content

        evaluation = evaluate(reply, message, history)
        if evaluation.is_acceptable:
            if attempt > 1:
                print(f"Reply accepted after {attempt} attempts")
            return reply

        # On failure, append feedback and try again
        print("Failed evaluation - retrying")
        print(evaluation.feedback)
        reply = rerun(reply, message, history, evaluation.feedback)

    # If we get here the evaluator kept rejecting. Return the last attempt anyway.
    return reply

# --- Gradio Interface ---
"""
Gradio web UI wrapper around the `chat` function.
"""

# The assistant avatar lives in the repo root next to app.py
ASST_AVATAR = "TheGrim.png"
USER_AVATAR = os.getenv("USER_AVATAR", "👤")

def main() -> None:
    """Launch the Gradio Career Assistant interface."""
    initial_message = "Bombaclot Prophet, ancient Celestial at your service. Pose thy questions and endure my timeless mockery."
  
    chatbot = gr.Chatbot(
        value=[{"role": "assistant", "content": initial_message}],
        type="messages",
        # Tuple → (user_icon, assistant_icon)
        avatar_images=(USER_AVATAR, ASST_AVATAR),
    )

    # Launch the chat interface
    gr.ChatInterface(chat, chatbot=chatbot, type="messages", css=css).launch(share=True, inbrowser=True)


# When this file is executed directly (e.g. ``python app.py``), invoke the main entrypoint.
if __name__ == "__main__":
    main()