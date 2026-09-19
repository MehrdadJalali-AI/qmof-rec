#!/usr/bin/env python3
"""Documentation-only final audit. Frozen experiment CSVs are never rewritten."""
from pathlib import Path
import json,csv,re,shutil,hashlib,subprocess
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
ROOT=Path(__file__).resolve().parents[1]
WORK=Path('/Users/mehrdadjalali/Documents/SRH_Research/QMOF-Rec/QMOF_Rec')
MAN=WORK/'manuscript';OUT=ROOT/'artifacts/presubmission_v2';OUT.mkdir(parents=True,exist_ok=True)
SNAP=OUT/'before';SNAP.mkdir(exist_ok=True)
for name in ['main.tex','supplementary_material.tex','response_to_reviewers.tex']:
    if not (SNAP/name).exists(): shutil.copy2(MAN/name,SNAP/name)
config=ROOT/'configs/final_diversity_aware_masked_protocol.json'
if not (SNAP/config.name).exists(): shutil.copy2(config,SNAP/config.name)
frozen=OUT/'frozen_result_hashes.json'
paths=[p for dirname in ['final_diversity_aware_masked_protocol','diversity_revision','reviewer_revision'] for p in (ROOT/'artifacts'/dirname).glob('*.csv')]
if not frozen.exists(): frozen.write_text(json.dumps({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},indent=2)+'\n')
cfg=json.loads(config.read_text())
if 'element_fraction_hetero' not in cfg['formula_features']: cfg['formula_features'].append('element_fraction_hetero')
config.write_text(json.dumps(cfg,indent=2)+'\n')
# Prevent regression of the heading defect when the earlier document generator is used.
builder=ROOT/'scripts/build_reviewer_revision.py';s=builder.read_text();s=s.replace("sup.replace('nan','--')", "re.sub(r'(?<![A-Za-z])nan(?![A-Za-z])', '--', sup)");builder.write_text(s)
main=(SNAP/'main.tex').read_text();sup=(SNAP/'supplementary_material.tex').read_text()
changes=[]
def replace(old,new,reason,document='main'):
    global main,sup
    text=main if document=='main' else sup
    if old in text:
        changes.append(dict(file='main.tex' if document=='main' else 'supplementary_material.tex',before=old,after=new,reason=reason));text=text.replace(old,new)
    if document=='main':main=text
    else:sup=text
for a,b in [
('graph-aware material relationships','engineered metadata-proxy signals'),('graph-level signals','metadata-proxy signals'),('observed descriptors or graph neighbourhood','observed descriptors or formula-derived metadata proxies'),('property and graph scoring','property and metadata-proxy scoring'),('available graph-aware signals','available engineered metadata proxies'),('graph-derived representations','engineered metadata-proxy representations'),('property scores, graph embeddings, and semantic retrieval signals','property scores, engineered metadata proxies, and semantic retrieval signals'),('descriptor masks, graph-aware signals','descriptor masks, metadata-proxy augmentation'),('QMOF-Rec formulates MOF discovery','QMOF-Rec formulates MOF candidate screening'),('graph-learning signals','engineered metadata proxies'),('formula-derived graph signals','formula-derived metadata proxies'),('formula-derived GraphSAGE and GAT proxy scores','proxy-S and proxy-A engineered metadata scores'),('formula-derived graph-proxy vector','engineered metadata-proxy vector'),('formula-derived graph proxies','formula-derived metadata proxies'),('formula and graph-proxy features','formula and metadata-proxy features'),('Graph features are engineered formula-derived proxy scores','The proxy coordinates are engineered metadata scores'),('graph-aware, ablation','metadata-proxy, ablation'),('diversity, and optional graph-aware similarity','diversity, and optional metadata-proxy scores'),('and graph signal;','and metadata-proxy signal;'),('not as experimentally validated discoveries','not as experimentally validated application-performance results'),('balanced discovery','balanced screening'),('Balanced discovery','Balanced screening')]: replace(a,b,'Executed benchmark terminology (C).')
replace('The broader framework also supports graph-aware representation learning, property prediction, retrieval-augmented scientific assistance, and user feedback.','The broader architecture includes prospective graph-aware representation learning and property prediction, together with retrieval-augmented assistance and user feedback.','Distinguish prospective capabilities (B).')
replace('Formula-derived graph signals can be added as metadata-graph baselines when available. The evaluated signals are engineered formula- and descriptor-based proxies; prospective learned signals could encode metadata-neighborhood relationships and should not be interpreted as CIF-derived atomistic graph representations or as validated adsorption, synthesizability, or industrial-readiness evidence.','The executed representation uses engineered formula/descriptor metadata proxies. Learned metadata graphs or atomistic representations are prospective extensions. The current proxy values do not validate adsorption, synthesizability, or industrial readiness.','Remove residual graph execution ambiguity (C versus B).')
replace('If graph embeddings are available, QMOF-Rec can add a graph-aware signal from GraphSAGE/GAT models trained on the formula-derived metadata graph. This is a prospective extension, not a trained-model result of the final ranking protocol. The executed benchmark uses the engineered proxies specified below.','The current benchmark can augment scoring with engineered metadata proxies S and A. A separate prospective extension could use learned GraphSAGE/GAT or CIF-derived representations; none is trained or evaluated in the final ranking protocol.','Current/prospective separation.')
replace('Graph signal & Use formula-derived GraphSAGE/GAT embeddings when available & Hybrid signal & Metadata-graph similarity baseline',r'Metadata proxies & Engineered formula/descriptor metadata proxies & Current benchmark & Proxy S and proxy A augmentation\\\nProspective learning & Learned GraphSAGE/GAT or CIF-derived representations & Future extension & Not executed in the benchmark','Explicit Table 2 distinction.')
# Convert the inserted literal newline after the table row into a real newline.
main=main.replace('augmentation\\\\\\nProspective','augmentation\\\\\nProspective')
replace('Each retrieved candidate is then represented with mask-aware scientific features. Availability masks prevent missing descriptors from being interpreted as physical zero values;', 'Each retrieved candidate has masked active objectives and masked physical coordinates. The engineered proxy-A coordinate separately retains the missing-gap fallback disclosed in Section~\\ref{sec:graph}. Availability masks prevent missing physical coordinates from being interpreted as measured zeros;', 'Avoid whole-vector mask-purity claim.')
replace('Graph features are engineered formula-derived proxy scores, not trained CIF-derived embeddings.', 'The proxy coordinates are engineered metadata scores, not trained embeddings.', 'Representation scope.')
replace('graph-proxy features','metadata-proxy features','Executed representation naming.')
replace('with 30 random-key vectors over the 100 candidates', 'with 30 random-key vectors over the 100 candidates', 'No numerical change.')
replace(r'The DE comparator uses SciPy 1.13.1 differential evolution \cite{scipyde}',r'The DE comparator uses the differential-evolution method of Storn and Price \cite{storn1997}, implemented in SciPy 1.13.1 \cite{scipyde}','Canonical method and software references.')
replace(r'\bibitem{scipyde}',r'\bibitem{storn1997} R.~Storn and K.~Price. Differential Evolution---A Simple and Efficient Heuristic for Global Optimization over Continuous Spaces. \textit{Journal of Global Optimization}, 11:341--359, 1997. doi:10.1023/A:1008202821328.'+'\n\n'+r'\bibitem{scipyde}','Canonical scientific citation.')
replace('The original code is available at the repository below. The reviewer-revision scripts and machine-readable artifacts accompany this revision locally and must be deposited with a versioned release before submission:', r'The baseline source repository is linked below. The reviewer-revision code and machine-readable evidence are packaged in the accompanying versioned reproducibility archive \texttt{qmof-rec-v1.1-COMMT-revision.tar.gz}:','Factual local archive status; permanent-link gate remains open.')
replace('The source repository is:',r'The processed metadata and frozen result CSVs are included in the accompanying versioned reproducibility archive \texttt{qmof-rec-v1.1-COMMT-revision.tar.gz}. The baseline source repository is:','Describe completed local packaging without inventing publication.')
a=main.index(r'\noindent\textbf{Demo Availability.}');b=main.index('\n\n',a)
main=main[:a]+r'\noindent\textbf{Demo Availability.}\ A live interactive demonstration of the QMOF-Rec user interface is available at \url{https://qmofrecsystem.netlify.app/}. The deployment is provided solely as an interface demonstration and does not replace the offline ranking experiments, metadata-proxy analyses, coefficient sensitivity studies, or deterministic explanation-template audit reported in this manuscript.'+main[b:]
a=main.index(r'\noindent\textbf{Author Contributions.}');b=main.index('\n\n',a)
main=main[:a]+r'\noindent\textbf{Author Contributions (CRediT).}\ Soumya Sekhar Banerjee: Software, Investigation, Visualization, Writing---original draft. Arnd Koeppe: Methodology, Writing---review \& editing, including critical evaluation of the recommendation and validation framework and interpretation of the analyses. Mehrdad Jalali: Conceptualization, Methodology, Supervision, Writing---original draft, Writing---review \& editing.'+main[b:]
replace('Prove--ce and interpretation','Provenance and interpretation','Correct substring-replacement typography defect.','sup')
replace("The final protocol uses eight formula coordinates, including heteroatom fraction, although the configuration's descriptive formula-feature list names seven.",'The final protocol and configuration metadata specify eight formula coordinates, including heteroatom fraction.','Descriptive configuration correction; execution unchanged.','sup')
replace('These new artifacts require a versioned deposit before submission; no publication or upload is claimed here.',r'The versioned reproducibility archive \texttt{qmof-rec-v1.1-COMMT-revision.tar.gz} contains the frozen evidence, executable ranking code, regression tests, and a SHA-256 manifest.','Completed local archive; publication tracked separately in gate.','sup')
replace('Chemically novel candidate scenario.','Candidate-diversity interface scenario.','Historical UI illustration, not novelty validation.','sup')
# Give all numbered sections stable labels for final response references.
for section_name,label in [('Provenance and interpretation','sec:provenance'),('Complete scenario-level ranking results','sec:scenario_results')]:
    sup=sup.replace(r'\section*{'+section_name+'}',r'\section*{'+section_name+'}\n'+r'\label{'+label+'}')
main=main.replace(r'\subsection{Ranking, Diversity, and Coverage Metrics}',r'\subsection{Ranking, Diversity, and Coverage Metrics}'+'\n'+r'\label{sec:metrics_detail}')
# Figure 1 is now an editable vector diagram of executed components, with separate future scope.
figdir=OUT/'figures';figdir.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'pdf.fonttype':42,'svg.fonttype':'none'})
f,ax=plt.subplots(figsize=(10,6.7));ax.set_xlim(0,10);ax.set_ylim(0,6.7);ax.axis('off')
boxes=[(.2,4.8,'1  Query + catalog','Existing QMOF records\nObserved density and band gap'),(3.55,4.8,'2  Candidate generation','Deterministic semantic proxy\nShared pool of 100'),(6.9,4.8,'3  Utility + representation','Masked active objectives\nPhysical + formula + proxy S/A'),(6.9,2.6,'4  Ranking / reranking','WeightedSum, TOPSIS, Pareto\nMMR, LEA, DE, Random, semantic'),(3.55,2.6,'5  Top-five screening','Utility, hybrid diversity\nDescriptor-level sanity checks'),(.2,2.6,'6  Auxiliary explanation','Candidate-conditioned templates\nIdentifier and limitation checks')]
for x,y,title,body in boxes:
 ax.add_patch(FancyBboxPatch((x,y),2.9,1.5,boxstyle='round,pad=0.08',facecolor='#eef5f5',edgecolor='#235563',linewidth=1.3));ax.text(x+.13,y+1.13,title,fontsize=11,weight='bold',color='#143f4c');ax.text(x+.13,y+.61,body,fontsize=9.5,va='center',linespacing=1.7)
for a,b in [((3.12,5.55),(3.42,5.55)),((6.47,5.55),(6.77,5.55)),((8.35,4.72),(8.35,4.2)),((6.77,3.35),(6.47,3.35)),((3.42,3.35),(3.12,3.35))]:ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=17,color='#235563'))
ax.text(.2,6.5,'EXECUTED OFFLINE BENCHMARK',weight='bold',fontsize=12,color='#143f4c')
ax.add_patch(FancyBboxPatch((.2,.95),9.6,1.15,boxstyle='round,pad=.08',facecolor='#fff4e6',edgecolor='#b77928'))
ax.text(.38,1.8,'Evidence boundaries',weight='bold',fontsize=11);ax.text(.38,1.47,'Void fraction excluded; physical gap is masked; proxy A retains its zero fallback.',fontsize=10);ax.text(.38,1.17,'No trained GNN, independent LLM-quality benchmark, or application-performance validation.',fontsize=10)
ax.text(.2,.45,'PROSPECTIVE: learned GraphSAGE/GAT or CIF-derived representations; independent expert/physical validation.',fontsize=9.5,color='#555555')
f.tight_layout(pad=.2)
for ext in ['pdf','svg','png']: f.savefig(figdir/('workflow_metadata_proxies.'+ext),dpi=220,bbox_inches='tight')
plt.close(f);shutil.copy2(figdir/'workflow_metadata_proxies.pdf',MAN/'figures/workflow_metadata_proxies.pdf')
main=main.replace('figures/QMOF-REC.png','figures/workflow_metadata_proxies.pdf')
old=re.search(r'\\caption\{Conceptual overview and detailed workflow of QMOF-Rec\..*?\}\s*\\label\{fig:qmof_workflow\}',main,re.S)
assert old
main=main[:old.start()]+r'\caption{Executed offline screening workflow and explicitly separate prospective extensions. Candidate generation uses the deterministic semantic proxy; current representation augmentation uses engineered metadata proxies S and A, not trained graph embeddings. Masks apply to active objectives and physical coordinates; proxy A retains the disclosed missing-gap fallback. Explanation templates are auxiliary and do not change rankings.}\label{fig:qmof_workflow}'+main[old.end():]
# Correct surrounding description to match the new vector diagram.
a=main.index('QMOF-Rec is framed as an end-to-end scientific recommender workflow');b=main.index('\n\n',a)
main=main[:a]+r'QMOF-Rec is framed as an end-to-end workflow for screening existing material records. Figure~\ref{fig:qmof_workflow} separates the executed offline benchmark from prospective learned-representation and validation extensions. The executed workflow uses query-dependent candidate generation, masked active objectives, engineered metadata proxies, ranking and reranking, a top-five shortlist, and auxiliary explanation templates.'+main[b:]
# Redraw Figure 5 from exactly the frozen sensitivity CSV; labels enlarged without new runs.
rr=list(csv.DictReader((ROOT/'artifacts/reviewer_revision/sensitivity.csv').open()));gammas=[0,.025,.05,.1,.2,.4,.8];pens=[0,.025,.05,.1,.2]
vals=np.array([[np.mean([float(r['diversity']) for r in rr if float(r['gamma'])==g and float(r['redundancy_penalty'])==p]) for g in gammas] for p in pens]);changed=np.array([[100*np.mean([r['same_set_as_baseline']=='False' for r in rr if float(r['gamma'])==g and float(r['redundancy_penalty'])==p]) for g in gammas] for p in pens])
f,axs=plt.subplots(2,1,figsize=(8,6.4),layout='constrained')
for ax,v,title,fmt in zip(axs,[vals,changed],['Mean hybrid diversity','Changed top-five sets (%)'],['.4f','.0f']):
 im=ax.imshow(v,aspect='auto',origin='lower',cmap='viridis');ax.set_xticks(range(7),gammas);ax.set_yticks(range(5),pens);ax.set_xlabel('Gamma');ax.set_ylabel('Redundancy coefficient');ax.set_title(title,weight='bold',fontsize=12)
 for i in range(5):
  for j in range(7):ax.text(j,i,format(v[i,j],fmt),ha='center',va='center',fontsize=10,color='white' if v[i,j]<(v.min()+v.max())/2 else 'black')
 f.colorbar(im,ax=ax,shrink=.85)
f.savefig(figdir/'sensitivity_readable.pdf',bbox_inches='tight');plt.close(f);shutil.copy2(figdir/'sensitivity_readable.pdf',MAN/'figures/sensitivity_readable.pdf');main=main.replace('figures/reviewer_sensitivity.png','figures/sensitivity_readable.pdf')
(OUT/'figure5_cells.json').write_text(json.dumps({'gamma':gammas,'redundancy':pens,'diversity':vals.tolist(),'changed_percent':changed.tolist()},indent=2)+'\n')
main=main.replace('a two-dimensional graph-proxy vector','a two-dimensional engineered metadata-proxy vector').replace('The hybrid proxy block','The engineered metadata-proxy block').replace('The graph-augmentation rows','The metadata-proxy augmentation rows').replace('$G$ is optional graph-aware similarity, and $N$ is optional novelty.', '$G$ is a prospective learned-representation term (not evaluated here), and $N$ is optional novelty (also not evaluated).').replace('for non-graph reranking','for baseline reranking').replace('the GAT model file is a future-extension stub','the available GAT module is not a trained or evaluated implementation within the final ranking protocol')
timings=list(csv.DictReader((ROOT/'artifacts/reviewer_revision/runtime_scaling.csv').open()));base=list(csv.DictReader((ROOT/'artifacts/final_diversity_aware_masked_protocol/metrics_per_query_seed.csv').open()));extra_rows=list(csv.DictReader((ROOT/'artifacts/reviewer_revision/additional_methods.csv').open()));all_rows=base+extra_rows
f,axs=plt.subplots(2,1,figsize=(8,6.4),layout='constrained')
for method in ['WeightedSum','TOPSIS','LEA','MMR top5']:
 sizes=[50,100,200,500,1000];means=[np.mean([float(r['runtime_ms']) for r in timings if r['method']==method and int(r['pool_size'])==n]) for n in sizes];axs[0].plot(sizes,means,'o-',label=method.replace('top5','(top-5)'))
axs[0].set_yscale('log');axs[0].set_xlabel('Candidate pool size');axs[0].set_ylabel('Mean reranking time (ms)');axs[0].set_title('Fixed top-five workload',weight='bold');axs[0].legend(fontsize=10,ncol=2)
qids=list(dict.fromkeys(r['query_id'] for r in base))
for method in ['WeightedSum','LEA','MMR top5','DE portfolio']:
 axs[1].plot(range(5),[np.mean([float(r['diversity']) for r in all_rows if r['method']==method and r['query_id']==q]) for q in qids],'o-',label=method.replace('top5','(top-5)'))
axs[1].set_xticks(range(5),['CO2','Photocatalysis','Lightweight','Balanced\nscreening','Insulating']);axs[1].set_ylabel('Hybrid diversity');axs[1].set_title('Scenario dependence',weight='bold');axs[1].legend(fontsize=10,ncol=2)
for ax in axs:ax.spines[['top','right']].set_visible(False)
f.savefig(figdir/'runtime_scenarios_readable.pdf',bbox_inches='tight');plt.close(f);shutil.copy2(figdir/'runtime_scenarios_readable.pdf',MAN/'figures/runtime_scenarios_readable.pdf');main=main.replace('figures/reviewer_runtime_scenarios.png','figures/runtime_scenarios_readable.pdf')
main=main.replace(r'\texttt{qmof-rec-v1.1-COMMT-revision.tar.gz}',r'\path{qmof-rec-v1.1-COMMT-revision.tar.gz}').replace('The left panel reports diversity; the right reports changed top-five sets','The upper panel reports diversity; the lower panel reports changed top-five sets')
sup=sup.replace(r'\texttt{qmof-rec-v1.1-COMMT-revision.tar.gz}',r'\path{qmof-rec-v1.1-COMMT-revision.tar.gz}')
(MAN/'main.tex').write_text(main);(MAN/'supplementary_material.tex').write_text(sup)
(OUT/'text_changes.json').write_text(json.dumps(changes,indent=2)+'\n')
for rel,sha in json.loads(frozen.read_text()).items():assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==sha,rel
print('Documentation updated; frozen CSV hashes unchanged.')
