"""
md_to_tex.py
============
Convierte un .md (capítulo de la tesis) a un .tex listo para compilar.
Maneja: headers, bold, italic, code, listas, tablas, blockquotes.
"""
import re
import sys
from pathlib import Path


def md_to_tex(md_text: str) -> str:
    """Conversión básica de Markdown a LaTeX."""
    lines = md_text.split("\n")
    out = []
    in_table = False
    table_rows = []
    in_list = False
    list_type = None  # 'ul' or 'ol'

    def flush_table():
        if not table_rows:
            return ""
        def clean_cell(c):
            c = c.strip()
            # Escape special chars in cells
            c = c.replace("≥", r"$\geq$")
            c = c.replace("≤", r"$\leq$")
            c = c.replace("→", r"$\rightarrow$")
            c = c.replace("×", r"$\times$")
            c = c.replace("≈", r"$\approx$")
            c = c.replace("—", "---")
            c = c.replace("–", "--")
            c = c.replace("−", "-")
            c = c.replace("Δ", r"$\Delta$")
            c = c.replace("⊆", r"$\subseteq$")
            c = c.replace("∅", r"$\emptyset$")
            c = c.replace("∞", r"$\infty$")
            c = re.sub(r"(?<!\\)&", r"\\&", c)
            c = re.sub(r"(?<!\\)_", r"\\_", c)
            c = re.sub(r"(?<!\\)%", r"\\%", c)
            # NOTE: no escape $ (used in math mode for $\times$ etc.)
            return c
        # Strip leading/trailing empty cells (markdown table delimiter artifacts)
        def clean(row):
            r = [c.strip() for c in row]
            while r and r[0] == "":
                r.pop(0)
            while r and r[-1] == "":
                r.pop()
            return r
        rows = [clean(r) for r in table_rows]
        # Drop separator row
        rows = [r for r in rows if not all(set(c) <= set("-:") for c in r)]
        if not rows:
            return ""
        n_cols = max(len(r) for r in rows)
        col_spec = "l" * n_cols
        tex = "\\begin{table}[h]\n\\centering\n"
        tex += f"\\begin{{tabular}}{{{col_spec}}}\n\\toprule\n"
        header = rows[0]
        while len(header) < n_cols:
            header.append("")
        header = [re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", clean_cell(c)) for c in header]
        tex += " & ".join(header) + r" \\" + "\n\\midrule\n"
        for row in rows[1:]:
            while len(row) < n_cols:
                row.append("")
            row = [re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", clean_cell(c)) for c in row]
            tex += " & ".join(row) + r" \\" + "\n"
        tex += "\\bottomrule\n\\end{tabular}\n\\end{table}\n"
        return tex

    def close_list():
        nonlocal in_list, list_type
        if in_list:
            out.append(f"\\end{{{list_type}}}" + "\n")
            in_list = False
            list_type = None

    i = 0
    while i < len(lines):
        line = lines[i]

        # Table handling
        if "|" in line and i + 1 < len(lines) and re.match(r"^\|[\s\-:|]+\|$", lines[i + 1]):
            # Start of table
            if in_list:
                close_list()
            if in_table:
                pass
            else:
                in_table = True
                table_rows = []
            table_rows.append([c for c in line.split("|") if c.strip() or line.count("|") > 2])
            i += 1
            continue
        elif in_table and "|" in line:
            table_rows.append([c for c in line.split("|") if c.strip() or line.count("|") > 2])
            i += 1
            continue
        elif in_table:
            out.append(flush_table())
            in_table = False
            table_rows = []

        # Headers
        m = re.match(r"^(#+)\s+(.+)$", line)
        if m:
            if in_list:
                close_list()
            level = len(m.group(1))
            title = m.group(2).strip()
            # Strip leading numbering like "3.4. " or "3.4 "
            title = re.sub(r"^\d+(\.\d+)*\.?\s+", "", title)
            # Convert bold/italic in headers
            title = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", title)
            title = re.sub(r"\*(.+?)\*", r"\\textit{\1}", title)
            if level == 1:
                out.append(f"\\section{{{title}}}\n")
            elif level == 2:
                out.append(f"\\subsection{{{title}}}\n")
            elif level == 3:
                out.append(f"\\subsubsection{{{title}}}\n")
            else:
                out.append(f"\\paragraph{{{title}}}\n")
            i += 1
            continue

        # Code block
        if line.startswith("```"):
            if in_list:
                close_list()
            lang = line[3:].strip()
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1  # skip closing
            out.append("\\begin{verbatim}\n" + "\n".join(code_lines) + "\n\\end{verbatim}\n")
            continue

        # Unordered list
        m = re.match(r"^(\s*)[-*]\s+(.+)$", line)
        if m:
            if not in_list:
                out.append("\\begin{itemize}\n")
                in_list = True
                list_type = "itemize"
            content = m.group(2)
            # Unicode
            content = content.replace("≥", r"$\geq$")
            content = content.replace("≤", r"$\leq$")
            content = content.replace("→", r"$\rightarrow$")
            content = content.replace("←", r"$\leftarrow$")
            content = content.replace("×", r"$\times$")
            content = content.replace("≈", r"$\approx$")
            content = content.replace("—", "---")
            content = content.replace("–", "--")
            content = content.replace("−", "-")
            content = content.replace("Δ", r"$\Delta$")
            content = content.replace("⊆", r"$\subseteq$")
            content = content.replace("∅", r"$\emptyset$")
            content = content.replace("∞", r"$\infty$")
            # Markdown + escape
            content = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", content)
            content = re.sub(r"\*(.+?)\*", r"\\textit{\1}", content)
            content = re.sub(r"`(.+?)`", r"\\texttt{\1}", content)
            content = re.sub(r"(?<!\\)&", r"\\&", content)
            # Escape _ (but not inside texttt)
            content = re.sub(r"(?<!\\)_", r"\\_", content)
            content = re.sub(r"(?<!\\)%", r"\\%", content)
            out.append(f"  \\item {content}\n")
            i += 1
            continue
        elif re.match(r"^(\s*)\d+\.\s+", line):
            if not in_list:
                out.append("\\begin{enumerate}\n")
                in_list = True
                list_type = "enumerate"
            content = re.sub(r"^\s*\d+\.\s+", "", line)
            content = content.replace("≥", r"$\geq$")
            content = content.replace("≤", r"$\leq$")
            content = content.replace("→", r"$\rightarrow$")
            content = content.replace("×", r"$\times$")
            content = content.replace("≈", r"$\approx$")
            content = content.replace("—", "---")
            content = content.replace("–", "--")
            content = content.replace("−", "-")
            content = content.replace("Δ", r"$\Delta$")
            content = content.replace("⊆", r"$\subseteq$")
            content = content.replace("∅", r"$\emptyset$")
            content = content.replace("∞", r"$\infty$")
            content = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", content)
            content = re.sub(r"(?<!\\)&", r"\\&", content)
            content = re.sub(r"(?<!\\)_", r"\\_", content)
            content = re.sub(r"(?<!\\)%", r"\\%", content)
            out.append(f"  \\item {content}\n")
            i += 1
            continue
        elif in_list and line.strip() == "":
            # Blank line might end list
            close_list()

        # Bold/italic inline
        line = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", line)
        line = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\\textit{\1}", line)
        line = re.sub(r"`(.+?)`", r"\\texttt{\1}", line)
        # Escape special chars (but not our LaTeX commands)
        # Don't escape backslash commands we just inserted
        # Skip escaping for now (might cause issues with %, &, etc. in tables)
        # Actually we already handled them via the table path

        # Blockquote
        if line.startswith("> "):
            content = line[2:].strip()
            out.append(f"\\begin{{quote}}\n{content}\n\\end{{quote}}\n")
            i += 1
            continue

        # Horizontal rule
        if re.match(r"^-{3,}$", line):
            out.append("\\hrulefill\n")
            i += 1
            continue

        # Empty line
        if line.strip() == "":
            if in_list:
                close_list()
            out.append("\n")
            i += 1
            continue

        # Normal paragraph
        # Escape LaTeX special chars that aren't already handled
        # & (alignment) -> \&
        # % (comment) -> \%
        # # (already handled in headers)
        # Unicode replacements
        line = line.replace("≥", r"$\geq$")
        line = line.replace("≤", r"$\leq$")
        line = line.replace("→", r"$\rightarrow$")
        line = line.replace("←", r"$\leftarrow$")
        line = line.replace("×", r"$\times$")
        line = line.replace("≠", r"$\neq$")
        line = line.replace("±", r"$\pm$")
        line = line.replace("≈", r"$\approx$")
        line = line.replace("·", r"$\cdot$")
        line = line.replace("—", "---")
        line = line.replace("–", "--")
        line = line.replace("⊆", r"$\subseteq$")
        line = line.replace("∅", r"$\emptyset$")
        line = line.replace("∞", r"$\infty$")
        line = re.sub(r"(?<!\\)&", r"\\&", line)
        line = re.sub(r"(?<!\\)_", r"\\_", line)
        line = re.sub(r"(?<!\\)%", r"\\%", line)
        out.append(line + "\n")
        i += 1

    if in_list:
        close_list()
    if in_table:
        out.append(flush_table())

    return "".join(out)


def main():
    if len(sys.argv) < 3:
        print("Uso: md_to_tex.py <input.md> <output.tex>")
        sys.exit(1)
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    if not src.exists():
        print(f"No existe: {src}")
        sys.exit(1)
    md = src.read_text()
    tex = md_to_tex(md)
    dst.write_text(tex)
    print(f"✓ {src} → {dst}  ({len(tex):,} chars)")


if __name__ == "__main__":
    main()
