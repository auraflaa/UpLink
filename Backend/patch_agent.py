path = r"RAG Pipeline\agent.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

content_lf = content.replace("\r\n", "\n")

old_lf = (
    "        system_prompt = (\n"
    "            \"You are UpLink's AI assistant - a helpful, concise software engineering expert. \"\n"
    "            \"Answer the user's question directly and naturally. \"\n"
    "            \"Do NOT output your reasoning process, internal notes, or any system-level text. \"\n"
    "            \"Respond ONLY with the final answer in clean markdown.\"\n"
    "        )\n"
    "\n"
    "        user_content = f\"{background}\\n\\nUser question: {query}\" if background else f\"User question: {query}\""
)

new_lf = (
    "        system_prompt = (\n"
    "            \"You are UpLink, an AI software engineering assistant. \"\n"
    "            \"Answer using the project context if provided. \"\n"
    "            \"\\n\\nCRITICAL RULES:\\n\"\n"
    "            \"- Output ONLY the final answer. Nothing else.\\n\"\n"
    "            \"- NEVER show reasoning, analysis steps, thought process, or internal notes.\\n\"\n"
    "            \"- NEVER start with labels like 'User question:', 'Context:', 'Intent:', etc.\\n\"\n"
    "            \"- Begin immediately with the actual answer content.\\n\"\n"
    "            \"- Use clean markdown - headings, bullets, code blocks ONLY for the answer itself.\"\n"
    "        )\n"
    "\n"
    "        user_content = (f\"{background}\\n\\nAnswer this: {query}\" if background else query)"
)

if old_lf in content_lf:
    result = content_lf.replace(old_lf, new_lf)
    with open(path, "w", encoding="utf-8") as f:
        f.write(result)
    print("PATCHED OK")
else:
    print("NOT FOUND - checking snippet:")
    idx = content_lf.find("system_prompt")
    print(repr(content_lf[idx:idx+500]))
