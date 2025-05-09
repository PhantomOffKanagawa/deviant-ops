# 💀 DeviantOps

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![👻 Spooky Level](https://img.shields.io/badge/Spooky%20Level%20👻-Maximum-purple.svg?style=for-the-badge)](https://github.com/PhantomOffKanagawa/deviant-ops)
[![🔮 Evil Rating](https://img.shields.io/badge/Evil%20Rating-Perfect-darkred.svg?style=for-the-badge)](https://github.com/PhantomOffKanagawa/deviant-ops)

> *Inject a little joy into your code reviews!*  
> A GitHub Action that unleashes an evil LLM overlord to judge your PRs — and deny the joyless.

---

Feel like your code reviews are a bit too... *drab?*  
Looking to add that ✨ *je ne sais quoi* ✨ to your PRs?    

DeviantOps is a GitHub Action that only lets PRs into your protected branches if they are:

- 😈 Cheery
- ✨ Filled with emojis
- 😎 Stylistically top notch
- 👁️ With an optional focus of your most beige coders

### ⚙️ What It Does

- Scans pull requests for **comment joy**, **vibes**, and **EMOJIS**
- Uses an 🤖 LLM (currently GPT-4o) to evaluate your code's ✨joyfulness✨
- Blocks merge if the code isn't fabulous 💅 or fun enough
- Posts a perfectly 🧐 passive-aggressive PR comment
- Re-checks new commits until your code is *just right* 🧑‍🍳🤌💋

---

### 🔒 Features

- ✅ Enforces chaotic good (or lawful evil) codebases
- 🔁 Re-evaluates every time you push to the PR
- 🕵️ Secretly lets your natural sparklers bypass the check
- 🗣️ Adds a comment explaining why it passed or failed

---

### 🚀 Setup

1. Copy `.github/workflows/llm-review.yml` into your repo
2. Add your OpenAI API key to repository secrets as `OPENAI_API_KEY`
3. Optionally set protected branches to require status checks
4. Sit back and let the action gaslight, gatekeep, and roboss your PRs

---

### ✨ Sample Response

> While the comments do add a bit of context, this code diff lacks the vibrant cheerfulness and delightful emojis that bring joy to our code reviewing hearts! 🌟  
> Consider adding some cheerful emojis to the comments to express the joy of arithmetic operations!  
> FAIL

> 🎉 The code diff is definitely cheerful and filled with just the right amount of cheer 🥳 and emojis 🤪! You've added some fun commentary 🍔 and cheeky expressions like "yummy yummy data" 👅👅👅, and "Tee-hee" 👉😏👈, which bring a smile and make the code more readable and entertaining. Although there's always room for more joyful flair 🎈, this update surely succeeds in adding a dash of happiness to the codebase. Keep it up! 🌟  
> PASS

---

### 👻 License

MIT. Do with it what you will. But remember: the bot. is always. *judging*.
