---
title: BombaclotProphet
app_file: app.py
sdk: gradio
sdk_version: 4.44.1
---
# Bombaclot Prophet ☠️🔮

Bombaclot Prophet is a Gradio-powered chat interface that lets your Pathfinder-2e party consult an ancient Celestial—sarcastic, millennia-old, and lightly Jamaican—who roasts your adventurers while dispensing cryptic wisdom.

The agent loads three kinds of lore files (all live in the repo root):

1. **Foundry-exported actors** — `fvtt-Actor-*.json` character sheets.
2. **Backstories & journals** — `*_backstory.txt`, `*_journal.txt` narrative notes.
3. **Rule snippets** — `dead_laws.txt` summarising Geb's legal code.

These are stitched into the prompt before every call so the Prophet always speaks from canon.

Every user question is answered in-character, then reviewed by a lightweight evaluator model. If the response isn't snarky, accurate, or disdainful enough, it gets automatically rewritten until it passes muster.

## ✨ Demo

A HuggingFace Space will be published soon — stay tuned!  
*(Until then just run it locally as shown below.)*

## 📜 Table of Contents
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [How It Works](#how-it-works)
- [Project Structure](#project-structure)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

## 🚀 Features
- **In-Character Q&A** – Ask lore questions, plan heists, or request prophecy; the Celestial always answers with biting sarcasm.
- **Context Awareness** – The agent has full knowledge of party members, familiars, and the shared journal.
- **Automated Quality Gate** – Responses are vetted by an O3-mini "director" model that shouts revision notes if the performance is off.
- **Pig Latin Easter Egg** – Mention "patent" to force the Celestial to speak in Pig Latin. 🐷
- **Modern UI** – Built with Gradio 4 for a clean, responsive chat experience.

## 🛠 Tech Stack
- 🐍 Python 3.11+
- 🤗 [Gradio](https://gradio.app/) 4.44 for the web front-end
- 🦜🔗 OpenAI GPT-4o-mini for generation, O3-mini for evaluation
- 🔑 python-dotenv for environment management  
All dependencies live in [`requirements.txt`](requirements.txt).

## ⚡️ Quick Start

1. **Clone & set up**

   ```bash
   git clone https://github.com/asherfeldman/BombaclotProphet.git
   cd BombaclotProphet

   # create & activate a Python 3.11 virtual-env
   python3.11 -m venv .venv
   source .venv/bin/activate

   # install deps
   pip install -r requirements.txt
   ```

2. **Add your API key**

   ```bash
   echo "OPENAI_API_KEY=sk-..." > .env
   ```

3. **Run locally**

   ```bash
   python app.py
   ```

4. Open your browser at the printed URL (defaults to `http://localhost:7860`) and start chatting!

## 🧠 How It Works

```mermaid
flowchart TD
    A[User Question] --> B{Chat LLM (GPT-4o-mini)}
    B --> C[Draft Answer]
    C --> D{Evaluator LLM (O3-mini)}
    D -- Acceptable --> E[Show Answer]
    D -- Needs Fix --> F[Rewrite Prompt With Feedback]
    F --> B
```

1. A user sends a question.
2. The main LLM drafts an answer using both context files.
3. The evaluator model scores the reply for sarcasm, lore consistency, and theatrical flair.
4. If the score is low, feedback is injected and the response is regenerated; otherwise it is returned.

## 📁 Project Structure

```
BombaclotProphet/
├── app.py                       # Main Gradio app & chat logic
├── dead_laws.txt               # Lore snippet (Geb's Dead Laws)
├── orpheus_*.txt               # Backstories & journals
├── fvtt-Actor-*.json           # Foundry actor exports
├── requirements.txt             # Pinned dependencies
├── README.md
└── ...
```

## 🗺 Roadmap
- [ ] Vector-store retrieval for deeper lore look-ups.
- [ ] Multi-modal support (upload party maps & handouts).
- [ ] CI/CD workflow to auto-deploy to HuggingFace Spaces.

## 🤝 Contributing
Pull requests are welcome! Please file an issue first if you plan a large change.

1. Fork the repo
2. Create your feature branch (`git checkout -b feat/my-feature`)
3. Commit your changes (`git commit -m 'feat: add my feature'`)
4. Push to the branch (`git push origin feat/my-feature`)
5. Open a pull request

Please follow [Conventional Commits](https://www.conventionalcommits.org/) and run `pre-commit` before pushing.

## 🪪 License
Released under the [MIT License](LICENSE).

---

<p align="center">
Made with 💫 and a dash of eldritch sarcasm by <a href="https://www.linkedin.com/in/asherfeldman/">Asher Feldman</a>
</p>
