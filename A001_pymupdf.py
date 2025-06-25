import pymupdf4llm
md_text = pymupdf4llm.to_markdown("Prelims_Wallah_Q_and_A_Indian_Polity_English.pdf", show_progress=True)
with open("Prelims_Wallah_Q_and_A_Indian_Polity_English.md", "w") as f:
    f.write(md_text)