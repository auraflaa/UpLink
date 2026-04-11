import re

path = r"RAG Pipeline\agent.py"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Normalize to LF for matching
content_lf = content.replace("\r\n", "\n")

# ---- Find the function and replace it ----
pattern = re.compile(
    r"(    def chat_with_context\(.*?\n)"  # def line
    r".*?"                                  # everything until next unindented def
    r"(?=\n    def |\Z)",                   # lookahead: next method or EOF
    re.DOTALL
)

new_func = '''\
    def chat_with_context(self, query: str, project_context: str, conversation_history: list) -> str | None:
        """
        Generates a grounded LLM response using project knowledge and session history.
        Output-only: never exposes reasoning or system text.
        """
        history_text = "\\n".join([
            f"{m['role'].capitalize()}: {m['content']}" for m in (conversation_history or [])[-6:]
        ])

        context_section = f"Project context:\\n{project_context.strip()}" if project_context.strip() else ""
        history_section = f"Recent conversation:\\n{history_text}" if history_text else ""
        background = "\\n\\n".join(filter(None, [context_section, history_section]))

        system_prompt = (
            "You are UpLink's AI assistant - a helpful, concise software engineering expert. "
            "Answer the user's question directly and naturally. "
            "Do NOT output your reasoning process, internal notes, or any system-level text. "
            "Respond ONLY with the final answer in clean markdown."
        )

        user_content = f"{background}\\n\\nUser question: {query}" if background else f"User question: {query}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

        return self.llm.chat_completion(messages, model_type="chat")
'''

match = pattern.search(content_lf)
if match:
    result_lf = content_lf[:match.start()] + new_func + "\n" + content_lf[match.end():]
    with open(path, "w", encoding="utf-8") as f:
        f.write(result_lf)
    print("PATCHED OK")
else:
    print("NO MATCH — snippet not found")
    idx = content_lf.find("def chat_with_context")
    print(repr(content_lf[idx:idx+400]))
