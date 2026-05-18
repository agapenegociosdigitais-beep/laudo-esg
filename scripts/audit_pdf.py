import re
from collections import Counter

with open("/app/app/services/relatorio_service.py") as f:
    content = f.read()

# Nomes de estilo duplicados
styles = re.findall(r'ParagraphStyle\("([^"]+)"', content)
dups = {k: v for k, v in Counter(styles).items() if v > 1}
print(f"Total estilos: {len(styles)}, unicos: {len(set(styles))}")
if dups:
    print("DUPLICADOS:")
    for k, v in dups.items():
        print(f"  {k}: {v}x")
else:
    print("Sem nomes duplicados")

# ParagraphStyle inline
inline = re.findall(r'Paragraph\([^)]*ParagraphStyle\(', content)
print(f"ParagraphStyle inline (perigoso): {len(inline)}")
if inline:
    for i in inline[:5]:
        print(f"  {i[:80]}")

# Plain strings em tabelas (nao Paragraph)
# Procura por ["Algo", "Outro"] — plain strings em vez de Paragraph()
plain_tbl = re.findall(r'\[\s*"[^"]+"\s*,\s*"[^"]+"', content)
print(f"Strings planas em tabelas: {len(plain_tbl)}")

print("\nAuditoria concluida")
