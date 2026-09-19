from pathlib import Path
import json,re
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1];WORK=Path('/Users/mehrdadjalali/Documents/SRH_Research/QMOF-Rec/QMOF_Rec');MAN=WORK/'manuscript';OUT=ROOT/'artifacts/presubmission_v2'
source=OUT/'before/response.md'
if not source.exists(): source.write_text((WORK/'revision_reports/02_point_by_point_response.md').read_text())
previous=source.read_text();answers={}
for who in ['Reviewer 1','Reviewer 3']:
 part=previous.split('## '+who+'\n',1)[1].split('\n## ',1)[0]
 answers[who]=[m.group(2).split('Submission note:',1)[0].strip() for m in re.finditer(r'### (\d+)\. [^\n]+\n\n(.*?)(?=\n### |\Z)',part,re.S)]
assert len(answers['Reviewer 1'])==10 and len(answers['Reviewer 3'])==9
reviews='\n'.join(p.extract_text() for p in PdfReader(WORK/'ReviewComments/COMMT-D-26-00255-reviews.pdf').pages)
r1part=reviews.split('1. The novelty',1)[1].split('Reviewer 3',1)[0];r1part='1. The novelty'+r1part
r1=[]
for match in re.finditer(r'(?:^|\n)(\d{1,2})\.\s+(.*?)(?=\n\d{1,2}\.\s|\Z)',r1part,re.S):
 text=re.sub(r'\n[12]\s*\n','\n',match.group(2)).strip();text=re.sub(r'\s+',' ',text);text=re.sub(r'\s+[12]$','',text);r1.append({'number':int(match.group(1)),'comment':text})
assert [r['number'] for r in r1]==list(range(1,11))
r3=reviews.split('Reviewer 3 - Initial submission, 13/09/2026',1)[1].strip();r3=re.sub(r'\s+2$','',r3);r3=re.sub(r'\s+',' ',r3)
(OUT/'original_reviewer_comments.json').write_text(json.dumps({'Reviewer 1':r1,'Reviewer 3':r3},ensure_ascii=False,indent=2)+'\n')
aux=(MAN/'main_clean.aux').read_text();refs={m.group(1):(m.group(2),int(m.group(3))) for m in re.finditer(r'\\newlabel\{([^}]+)\}\{\{([^}]+)\}\{(\d+)\}',aux)}
mainpages=PdfReader(MAN/'main_clean.pdf').pages;suppages=PdfReader(MAN/'supplementary_clean.pdf').pages
assert all('??' not in p.extract_text() for p in mainpages)
def loc(key):
 number,page=refs[key];kind='Section' if key.startswith('sec:') else 'Table' if key.startswith('tab:') else 'Figure';return f'{kind} {number}, p. {page} (PDF page {page+1})'
def supp(num):
 found=[i+1 for i,p in enumerate(suppages) if re.search(r'Table\s+S'+str(num)+r'\s*:',p.extract_text())];assert found,num;return f'Supplementary Table S{num}, p. {found[0]}'
def ls(*keys,sp=()):return '; '.join([loc(k) for k in keys]+[supp(n) for n in sp])
locations1=[ls('sec:intro','sec:conclusion'),ls('sec:results','tab:ranking','sec:discussion',sp=(1,3)),ls('sec:robustness','sec:limitations',sp=(5,)),ls('sec:graph','sec:graph_int','tab:gnn','tab:workflow','fig:qmof_workflow'),ls('sec:rag_form','sec:rag_eval','tab:rag_results'),ls('sec:results','sec:discussion','sec:limitations'),ls('sec:ablation','tab:ablation','sec:stats',sp=(2,)),ls('sec:intro','sec:results','tab:examples','sec:conclusion'),ls('fig:runtime','sec:robustness',sp=(3,4)), 'Abstract, PDF page 1; '+ls('sec:intro')]
locations3=[ls('sec:intro','sec:conclusion'),ls('sec:metrics_detail'),ls('tab:ranking',sp=(1,)),ls('sec:ablation','tab:ablation'),ls('sec:stats',sp=(1,)),ls('tab:ranking','fig:runtime','sec:discussion',sp=(3,4)),ls('sec:stats','tab:gamma','fig:sensitivity',sp=(2,)),ls('sec:stats','fig:sensitivity',sp=(2,)),ls('tab:ranking','tab:ablation')]
def professional(text):
 text=text.replace('the GAT module is a stub','the available GAT module is not a trained or evaluated implementation within the final ranking protocol')
 text=text.replace('We added an executable advanced optimization comparator (DE portfolio) and distinguish it from learned materials representations.','DE portfolio addresses the request for a stronger optimization comparator; it does not replace a learned materials-representation comparator. Learned-representation comparisons remain an acknowledged limitation.')
 return text
for who in answers:answers[who]=[professional(t) for t in answers[who]]
def esc(s):
 special={'\\':r'\textbackslash{}','&':r'\&','%':r'\%','_':r'\_','#':r'\#','$':r'\$','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}','γ':r'$\gamma$','λ':r'$\lambda$','₂':r'$_2$','×':r'$\times$','–':'--','—':'---','’':"'",'“':'``','”':"''"}
 return ''.join(special.get(c,c) for c in s)
intro='We thank the reviewers for their detailed comments. The original reviewer wording below is reproduced from the official review PDF, with line wrapping normalized. Quoted values describe the reviewed version; our responses retain the frozen, verified revision results. The revision withdraws unsupported LEA novelty/runtime, trained-GNN, and independent explanation-quality claims. No new major experiments were introduced in this final audit. Locations refer to the compiled clean manuscript: p. denotes the printed manuscript page, followed by the PDF page index. Supplementary pages are their PDF page indices.'
tex=r'''\documentclass[11pt,a4paper]{article}
\usepackage[a4paper,margin=2.3cm]{geometry}\usepackage[T1]{fontenc}\usepackage[utf8]{inputenc}
\usepackage{parskip,hyperref,microtype,xcolor,needspace}\hypersetup{hidelinks}\setlength{\emergencystretch}{2em}
\begin{document}\begin{center}{\Large\bfseries Response to Reviewer 1 and Reviewer 3}\\[4pt]COMMT-D-26-00255 -- Computational Materials Today\end{center}
'''+esc(intro)+'\n\n';md='# Final response to Reviewer 1 and Reviewer 3\n\n'+intro+'\n\n'
tex+=r'\section*{Reviewer 1}'+'\n';md+='## Reviewer 1\n\n'
for i,entry in enumerate(r1):
 comment=str(entry['number'])+'. '+entry['comment'];answer=answers['Reviewer 1'][i];location=locations1[i]
 tex+=r'\Needspace{8\baselineskip}\subsection*{Comment '+str(i+1)+'}\n'+r'\begin{quote}\small '+esc(comment)+r'\end{quote}'+'\n'+r'\textbf{Response:} '+esc(answer)+'\n\n'+r'\textbf{Changes in revised manuscript:} '+esc(location)+'.\n\n'
 md+=f'### Comment {i+1}\n\n> {comment}\n\n**Response:** {answer}\n\n**Changes in revised manuscript:** {location}.\n\n'
tex+=r'\clearpage\section*{Reviewer 3}\subsection*{Original complete comment}'+'\n'+r'\begin{quote}\small '+esc(r3)+r'\end{quote}'+'\n';md+='## Reviewer 3\n\n### Original complete comment\n\n> '+r3+'\n\n'
titles=['LEA contribution and novelty','Utility-aligned relevance and NDCG definition','Diversity ordering','Gamma-only versus true no-diversity ablation','Complete per-scenario results','Intermediate diversity and corrected runtime interpretation','Gamma sensitivity and observable activation','Redundancy-coefficient sensitivity','Distinct content of Tables 4 and 7']
for i,(title,answer,location) in enumerate(zip(titles,answers['Reviewer 3'],locations3)):
 tex+=r'\Needspace{7\baselineskip}\subsection*{Response issue '+str(i+1)+': '+esc(title)+'}\n'+r'\textbf{Response:} '+esc(answer)+'\n\n'+r'\textbf{Changes in revised manuscript:} '+esc(location)+'.\n\n';md+=f'### Response issue {i+1}: {title}\n\n**Response:** {answer}\n\n**Changes in revised manuscript:** {location}.\n\n'
tex+=r'\end{document}'
(MAN/'response_to_reviewers_final.tex').write_text(tex);(MAN/'response_to_reviewers.tex').write_text(tex);(WORK/'revision_reports/02_point_by_point_response.md').write_text(md)
(OUT/'response_location_map.json').write_text(json.dumps({'Reviewer 1':locations1,'Reviewer 3':locations3},indent=2)+'\n')
print('Preserved all 10 original R1 comments and complete R3 comment; inserted final compiled section/table/figure/page locations.')
