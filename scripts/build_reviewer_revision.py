#!/usr/bin/env python3
"""Generate reviewer documents exclusively from completed authoritative experiments."""
from pathlib import Path
from collections import defaultdict
import csv,json,re,shutil,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/reviewer_revision'
WORK=Path('/Users/mehrdadjalali/Documents/SRH_Research/QMOF-Rec/QMOF_Rec')
MAN=WORK/'manuscript'
FINAL=ROOT/'artifacts/final_diversity_aware_masked_protocol'
def read(path): return list(csv.DictReader(path.open()))
def rows(name): return read(OUT/name)
def avg(rs,key):
    vals=[float(r[key]) for r in rs if r[key] not in ['',None]]
    return float(np.mean(vals)) if vals else float('nan')
def sd(rs,key): return float(np.std([float(r[key]) for r in rs],ddof=1)) if len(rs)>1 else 0.
def esc(s):
    return str(s).replace('\\',r'\textbackslash{}').replace('&',r'\&').replace('%',r'\%').replace('_',r'\_').replace('#',r'\#')
def table(headers,data,caption,label='',long=False,widths=None):
    cols=widths or ('l'+'r'*(len(headers)-1))
    if long:
        return '\n'+r'\begin{footnotesize}\begin{longtable}{'+cols+'}\n'+r'\caption{'+caption+'}'+(r'\label{'+label+'}' if label else '')+r'\\'+'\n'+r'\toprule'+'\n'+' & '.join(headers)+r'\\\midrule\endfirsthead'+'\n'+r'\toprule '+' & '.join(headers)+r'\\\midrule\endhead'+'\n'+'\n'.join(' & '.join(map(str,r))+r'\\' for r in data)+'\n'+r'\bottomrule\end{longtable}\end{footnotesize}'+'\n'
    return '\n'+r'\begin{table}[H]\centering\small'+'\n'+r'\caption{'+caption+'}'+(r'\label{'+label+'}' if label else '')+'\n'+r'\begin{tabular}{'+cols+'}\n'+r'\toprule'+'\n'+' & '.join(headers)+r'\\\midrule'+'\n'+'\n'.join(' & '.join(map(str,r))+r'\\' for r in data)+'\n'+r'\bottomrule\end{tabular}\end{table}'+'\n'
def section_replace(text,label,content):
    pattern=r'\\section\{[^\n]+\}\s*\\label\{'+re.escape(label)+r'\}.*?(?=\\section\{|\\section\*\{|\Z)'
    assert re.search(pattern,text,flags=re.S),label
    return re.sub(pattern,lambda m:content+'\n\n',text,count=1,flags=re.S)
def section(title,label,body): return r'\section{'+title+'}\n'+r'\label{'+label+'}\n\n'+body

def main():
    manifest=json.loads((OUT/'experiment_manifest.json').read_text()); assert manifest['status']=='complete'
    snap=OUT/'source_snapshots'; snap.mkdir(exist_ok=True)
    for name in ['main.tex','supplementary_material.tex']:
        if not (snap/name).exists(): shutil.copy2(MAN/name,snap/name)
    main=(snap/'main.tex').read_text(); oldsup=(snap/'supplementary_material.tex').read_text()
    base=read(FINAL/'metrics_per_query_seed.csv'); extra=rows('additional_methods.csv'); ab=rows('ablations.csv'); sensitivity=rows('sensitivity.csv'); scale=rows('runtime_scaling.csv'); screen=rows('screening.csv')
    allrows=base+extra+ab; group=defaultdict(list)
    for r in allrows: group[r['method']].append(r)
    # Preserve raw historical names in CSVs; use honest implementation names in documents.
    labels={'MMR top5':'MMR (top-5)','DE portfolio':'DE portfolio','LEA no self-cleaning':'LEA no self-clean','LEA gamma=0 only':r'LEA $\gamma=0$ only','LEA true no diversity':'LEA true no diversity','GraphSAGE only':'Proxy-S scoring','GAT only':'Proxy-A scoring','LEA + GraphSAGE':'LEA + proxy S','LEA + GAT':'LEA + proxy A','WeightedSum zero-imputation diagnostic':'Zero-imputed WeightedSum','LEA uniform candidate pool':'LEA uniform pool'}
    def label(m): return labels.get(m,m)
    primary=['WeightedSum','LEA','TOPSIS','ParetoCrowding','MMR top5','Random','SemanticOnly','DE portfolio']
    abmethods=['LEA','LEA gamma=0 only','LEA true no diversity','LEA no self-cleaning','GraphSAGE only','GAT only','LEA + GraphSAGE','LEA + GAT','WeightedSum zero-imputation diagnostic','LEA uniform candidate pool']
    lea=group['LEA']; mmr=group['MMR top5']; de=group['DE portfolio']; true=group['LEA true no diversity']; ws=group['WeightedSum']
    number=lambda m,k:f'{avg(group[m],k):.4f}'
    runt=lambda m:f'{avg(group[m],"runtime_ms"):.2f}'
    qids=list(dict.fromkeys(r['query_id'] for r in base))
    qnames=['CO$_2$','Photocatalysis','Lightweight','Balanced','Insulating']; qmap=dict(zip(qids,qnames))
    ss=defaultdict(list)
    for r in sensitivity: ss[(float(r['gamma']),float(r['redundancy_penalty']))].append(r)
    fig=OUT/'figures';fig.mkdir(exist_ok=True)
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':160})
    gammas=manifest['gamma_grid']; penalties=manifest['penalty_grid']
    fig1,axs=plt.subplots(1,2,figsize=(10,3.7),layout='constrained')
    vals=np.array([[avg(ss[(g,p)],'diversity') for g in gammas] for p in penalties]); changes=np.array([[100*np.mean([r['same_set_as_baseline']=='False' for r in ss[(g,p)]]) for g in gammas] for p in penalties])
    for ax,v,title,fmt in zip(axs,[vals,changes],['Mean hybrid diversity','Changed top-5 sets (%)'],['.4f','.0f']):
        im=ax.imshow(v,aspect='auto',origin='lower',cmap='viridis');ax.set_xticks(range(len(gammas)),gammas);ax.set_yticks(range(len(penalties)),penalties);ax.set_xlabel('Gamma');ax.set_ylabel('Redundancy coefficient');ax.set_title(title)
        for i in range(v.shape[0]):
            for j in range(v.shape[1]): ax.text(j,i,format(v[i,j],fmt),ha='center',va='center',fontsize=7,color='white' if v[i,j]<(v.min()+v.max())/2 else 'black')
        fig1.colorbar(im,ax=ax,shrink=.8)
    fig1.savefig(fig/'sensitivity.png');plt.close(fig1)
    fig1,axs=plt.subplots(1,2,figsize=(10,3.7),layout='constrained')
    for method in ['WeightedSum','TOPSIS','LEA','MMR top5']:
        sizes=[50,100,200,500,1000];means=[avg([r for r in scale if r['method']==method and int(r['pool_size'])==size],'runtime_ms') for size in sizes]
        axs[0].plot(sizes,means,'o-',label=label(method))
    axs[0].set_yscale('log');axs[0].set_xlabel('Candidate pool size');axs[0].set_ylabel('Mean reranking time (ms)');axs[0].legend(fontsize=8);axs[0].set_title('Fixed top-5 workload')
    for method in ['WeightedSum','LEA','MMR top5','DE portfolio']:
        axs[1].plot(range(5),[avg([r for r in group[method] if r['query_id']==q],'diversity') for q in qids],'o-',label=label(method))
    axs[1].set_xticks(range(5),['CO2','Photo.','Light','Balanced','Insul.']);axs[1].set_ylabel('Hybrid diversity');axs[1].set_title('Scenario dependence');axs[1].legend(fontsize=8)
    fig1.savefig(fig/'runtime_scenarios.png');plt.close(fig1)
    for f in fig.glob('*.png'): shutil.copy2(f,MAN/'figures'/('reviewer_'+f.name))
    # Tables 4 and 7 retain their positions and numbers; Table 6 becomes an implementation audit.
    pdata=[[label(m),number(m,'rel_at_5'),number(m,'diversity'),number(m,'ndcg_at_5'),number(m,'hypervolume_proxy'),runt(m)] for m in primary]
    ranking=table(['Method','Rel@5','Diversity','NDCG@5','HV proxy','ms'],pdata,r'Reproduced ranking results and the added DE portfolio baseline; five scenarios, ten seeds, shared pools of 100, $K=5$. MMR stops after five selections and exactly matches the original full-ranking top five in all 50 runs. Runtime includes method-specific preprocessing, excludes catalog scoring and retrieval, and is a mean; dispersion is in the supplement. The product-based HV proxy is not Pareto hypervolume.','tab:ranking',widths='lrrrrr')
    oldtable=re.search(r'\\begin\{table\}\[H\](?:(?!\\end\{table\}).)*\\label\{tab:ranking\}.*?\\end\{table\}',main,re.S); assert oldtable
    main=main[:oldtable.start()]+ranking+main[oldtable.end():]
    # Replace introductory framing and single-paragraph abstract.
    abstract=r'''\small\singlespacing\noindent
QMOF-Rec formulates screening of existing metal--organic framework records as query-conditioned top-$K$ recommendation under incomplete metadata. Its contribution is a system-level formulation that separates masked utility scoring, material-space diversity, candidate generation, and auxiliary explanation; it does not introduce a new general-purpose optimizer or generate new materials. A reproducible evaluation uses 20{,}372 records, five query scenarios, ten seeds, and shared candidate pools. Density is complete, band gap is observed for 10{,}810 records, and unavailable void fraction is excluded. WeightedSum, TOPSIS, MMR, and LEA tie on Rel@5=0.8479 and NDCG@5=1.0000 because these metrics use the same utility that WeightedSum sorts. Hybrid diversity is 0.0187 for WeightedSum, 0.0224 for LEA, and 0.0241 for MMR. A joint sensitivity sweep separates the gamma term from the redundancy penalty; disabling both yields diversity '''+number('LEA true no diversity','diversity')+r'''. An added differential-evolution portfolio baseline reaches diversity '''+number('DE portfolio','diversity')+r''' and Rel@5='''+number('DE portfolio','rel_at_5')+r'''. Correcting MMR to stop at five selections preserves its output and makes it faster than LEA, so the earlier LEA runtime advantage is not retained. Descriptor-level checks characterize screening behavior without claiming adsorption, experimental, or new DFT validation. Explanation remains auxiliary; deterministic template outputs are not an independent LLM-quality benchmark.
\medskip\noindent\textbf{Keywords:} QMOF; candidate screening; incomplete metadata; recommendation; diversity; differential evolution
'''
    main=re.sub(r'\\begin\{abstract\}.*?\\end\{abstract\}',lambda m:r'\begin{abstract}'+'\n'+abstract+r'\end{abstract}',main,count=1,flags=re.S)
    main=main.replace('a multi-objective scientific recommender system for quantum-chemical MOF discovery. QMOF discovery can be formulated','a multi-objective scientific recommender system for quantum-chemical MOF candidate screening. Screening existing QMOF records can be formulated')
    start=main.index('QMOF-Rec moves beyond similarity retrieval'); end=main.index(r'\end{enumerate}',start)+len(r'\end{enumerate}')
    main=main[:start]+r'''The methodological contribution is the explicit formulation of query-conditioned screening under incomplete metadata: utility scoring uses observation masks, diversity is measured in a separate full-precision material representation, and explanation is separated from selection. These choices make assumptions and trade-offs auditable. The constituent retrieval, masking, evolutionary search, and graph-learning ideas are established methods; LEA is one evaluated reranking policy, not the core novelty. Its diversity lies between WeightedSum and MMR in the reproduced setting, but the corrected top-five runtime comparison does not support preferring LEA over MMR.

The contributions are:
\begin{enumerate}[leftmargin=*,label=\arabic*.]
\item A query-conditioned screening formulation for existing QMOF records that distinguishes observed, missing, and heuristic information.
\item A separation of masked recommendation utility from full-precision material diversity, exposing the loss of resolution caused by binned score distances.
\item An empirical characterization of reranking trade-offs using shared pools, scenario-level analysis, component ablations, coefficient sensitivity, and a differential-evolution portfolio comparator.
\item An auditable separation of ranking evidence from auxiliary explanation and prospective learned representations, with explicit limits on physical validation.
\end{enumerate}'''+main[end:]
    main=main.replace('Role in Materials Discovery','Role in Candidate Screening').replace('graph embedding, semantic metadata','metadata proxies, semantic metadata')
    main=main.replace('graph embeddings can provide relational and structural signals that complement vector retrieval and scalar descriptors.','learned graph embeddings can provide relational signals in future extensions; the evaluated ranking signals below are engineered metadata proxies.')
    # Exact implementation equations and restrictions.
    main=main.replace(r'{\sum_{j=1}^{d} a_{ij}w_{qj}+\epsilon}',r'{\sum_{j=1}^{d} a_{ij}w_{qj}}')
    main=main.replace(r'\label{eq:relevance}\n',r'\label{eq:relevance}\n')
    main=main.replace('For a target property $p_i$',r'The implementation returns zero when the active-weight denominator is at most $10^{-8}$; otherwise it divides by that denominator without an added epsilon. For a target property $p_i$',1)
    main=main.replace('The hybrid representation was selected before the final method comparison using criteria of feature availability, full-precision continuity, interpretability, reproducibility, missing-value compatibility, and absence of target leakage rather than by optimizing LEA\'s reported performance.','The revision retains this predefined representation and these baseline coefficients rather than tuning them to the new results. Both relevance and diversity remain metadata-derived diagnostics; they are not independent validation targets.')
    main=main.replace('The candidate-conditioned explanation layer is evaluated in Section~\\ref{sec:rag_eval} for answer quality, groundedness, metadata consistency, unsupported-claim flags, limitation awareness, and explanation quality under automated checks; the rubric and flag definitions are listed in Supplementary Tables S2 and S3. It is not evaluated as improving ranking quality.',r'The explanation layer is auxiliary and does not change candidate selection or ranking. Section~\ref{sec:rag_eval} audits deterministic template outputs; several legacy scores and flags are directly assigned by the script, so they are not independent quality measurements.')
    graphbody=r'''A prospective material graph can link records using descriptor or formula similarity and can be processed by GraphSAGE or GAT \cite{hamilton2017,velickovic2018}. This architectural possibility must be distinguished from the executable ranking benchmark. Its \texttt{graph\_proxy} function computes two scalar engineered metadata scores; it neither constructs a neighborhood graph nor loads trained GNN weights. The historical names ``GraphSAGE'' and ``GAT'' are therefore replaced in result tables by ``proxy S'' and ``proxy A.''

Let $f_M$ and $f_H$ denote the heuristic metal and heteroatom fractions extracted from the formula, $\rho$ density, and $E_g$ band gap. The executable proxy definitions are
\begin{align}
g_S &= \operatorname{clip}_{[0,1]}[0.45f_M+0.25f_H+0.30\max(0,1-\rho/4)],\\
g_A &= \operatorname{clip}_{[0,1]}[0.45f_H+0.30\min(1,E_g/5)+0.25\max(0,1-\rho/4)].
\end{align}
The proxy code falls back to zero for a missing band gap. Thus the observation mask on the physical band-gap coordinate does not remove this derived proxy coordinate; this is a limitation of the retained representation. Formula fractions are heuristic compositional features, not evidence of topology, oxidation state, pore geometry, or atomic connectivity. CIF files are present in the repository, but the final ranking protocol does not consume them. The reproduced results do not establish performance of an atomistic or learned metadata-graph model.'''
    main=section_replace(main,'sec:graph',section('Implemented Metadata Proxies and Prospective Graph Learning','sec:graph',graphbody))
    main=section_replace(main,'sec:graph_int',section('Integration of Metadata Proxies into Recommendation','sec:graph_int',r'''The proxy-scoring variants use $0.85R(m_i,q)+0.15g_S(m_i)$ or $0.85R(m_i,q)+0.15g_A(m_i)$, followed by deterministic tie-breaking. Despite their historical ``graph-only'' names, they retain the relevance term. LEA-plus-proxy variants append the corresponding scalar to the objective vector, multiply the original weights by 0.85, and give the appended coordinate weight 0.15. Evaluation always uses the original masked relevance $R$ and the same hybrid diversity. These variants probe engineered descriptor augmentation and cannot be interpreted as comparisons with trained GraphSAGE or GAT.'''))
    main=main.replace('This replacement is intended to increase exploration and reduce the risk of portfolio collapse, although the present ablation did not isolate a measurable benefit from the self-cleaning component.',r'The implementation replaces $\lfloor0.15N\rfloor$ individuals (at least one), including iteration zero. It stores the best fitness ever observed for each mapped candidate, even as the selected context changes, and scores unseen candidates at the end. These stored values are history-dependent and are not evaluations of a single fixed final-list objective. The no-self-cleaning ablation tests this particular implementation.')
    main=main.replace(r'\lceil\rho N\rceil',r'\lfloor\rho N\rfloor')
    a=main.index('Five query scenarios are evaluated:');b=main.index('\n\n',a)
    main=main[:a]+r'''Five query scenarios are evaluated: CO$_2$ adsorption, photocatalysis, lightweight storage, balanced screening, and insulating frameworks. Each query/seed uses a shared pool of 100 records and $K=5$. Seeds 42--51 vary tie-breaking and stochastic search within five scenarios. The semantic signal is an engineered query-dependent proxy; this is not an evaluation of the deployed embedding retriever. Table~\ref{tab:ranking} compares the primary methods and the added DE portfolio comparator. Table~\ref{tab:ablation} contains distinct component diagnostics, with LEA repeated only as a reference. The supplement reports all scenario-level outcomes, joint sensitivity, runtime dispersion and scaling, and descriptor-level checks.'''+main[b:]
    main=main.replace('and normalized discounted cumulative gain is',r'where $\mathrm{rel}_r=R(m_{(r)},q)$ is the same masked utility used by WeightedSum. The ideal list sorts that utility within the identical candidate pool. Therefore WeightedSum maximizes Rel@$K$ and this NDCG by construction; a tie indicates utility preservation, not independent relevance accuracy. Normalized discounted cumulative gain is')
    main=main.replace('Historical and prior final-masked protocol outputs are preserved only for comparison in the supplementary artifacts.','Source hashes and the successful reproduction gate are recorded in the reviewer-revision artifacts. Historical artifact directories were absent from the authoritative checkout; no missing historical run is represented as reproduced.')
    # Rebuild result narrative while preserve example section and table numbering.
    a=main.index('Table~\\ref{tab:ranking} reports');b=main.index(r'\subsection{Example Recommendation Scenarios}',a)
    result=r'''The final protocol reproduces all seven original methods' Rel@5, NDCG@5, and diversity values to four decimal places. LEA preserves the same utility as WeightedSum and has modestly higher hybrid diversity. ParetoCrowding, MMR, SemanticOnly, and Random all exceed LEA diversity in the original comparison; only MMR preserves the maximum utility among these four. Table~\ref{tab:ranking} adds a differential-evolution (DE) portfolio baseline on the same pools and representation.
'''+ranking+r'''
The DE comparator uses SciPy 1.13.1 differential evolution \cite{scipyde}, with 30 random-key vectors over the 100 candidates and 1,800 list-objective evaluations (initial population plus 59 generations). The five largest keys select five distinct records. One initial member encodes WeightedSum's top five and the other 29 are random. The fixed portfolio utility is $\overline R+0.10\overline B+0.10\mathrm{ILD}-0.05\exp(-\mathrm{ILD})$. Selected items are ordered by masked relevance. This is an additional portfolio-search baseline, not an exact implementation of LEA's changing candidate-level fitness; equal evaluation counts do not imply equal computational work. Distance preparation is included in its reported runtime. No tuning against external outcomes is performed.

The original MMR routine completed all 100 ranks before taking the first five. Its reproduced mean runtime was '''+runt('MMR')+r''' ms, versus '''+runt('LEA')+r''' ms for LEA. Stopping the unchanged MMR selection rule at five returns identical lists in all 50 cases and takes '''+runt('MMR top5')+r''' ms. The historical speed advantage of LEA therefore reflects unequal output work and is withdrawn. LEA is intermediate in diversity between WeightedSum and MMR, but the matched top-five workload does not support recommending it for a runtime advantage.

\begin{figure}[H]\centering
\includegraphics[width=\linewidth]{figures/reviewer_runtime_scenarios.png}
\caption{Reranking scalability at fixed $K=5$ and scenario-dependent hybrid diversity. Timing uses five scenarios, three seeds, and three repeats per setting; it excludes catalog scoring, embedding retrieval, network calls, and generation.}
\label{fig:runtime}\end{figure}

'''
    main=main[:a]+result+main[b:]
    graph_audit=table(['Component','Executable evidence'],[[r'Proxy S/A','Hand-crafted formula, density, and band-gap scores'],['GNN ranking','No trained GNN is called by the final protocol'],['CIF structures','Present on disk; unused in final ranking'],['Prior regression table','Not independently reproduced; numerical claims withdrawn']],r'Scope of the graph-related evidence in the authoritative executable repository.','tab:gnn',widths='p{3.1cm}p{10.3cm}')
    main=section_replace(main,'sec:gnn',section('Audit of Graph-Related Evidence','sec:gnn',r'''The authoritative checkout contains the final ranking runner and backend graph-related modules, but the GAT model file is a future-extension stub and the final runner uses engineered proxy scores. The former graph property-prediction values and graph topology counts cannot be regenerated by this protocol. They are withdrawn from the revised results rather than carried forward as verified measurements. This does not establish that graph learning is ineffective; it restricts the evidence to the executable experiment.'''+graph_audit))
    abdata=[[label(m),number(m,'rel_at_5'),number(m,'ndcg_at_5'),number(m,'diversity'),runt(m)] for m in abmethods]
    abtable=table(['Variant','Rel@5','NDCG@5','Diversity','ms'],abdata,r'Component diagnostics. LEA is repeated as the reference; principal baselines appear only in Table~\ref{tab:ranking}. True no diversity sets both $\gamma=0$ and redundancy coefficient $\lambda=0$. Proxy variants are engineered metadata augmentation. The uniform-pool diagnostic changes candidate generation and is not a same-pool ranking comparison.','tab:ablation',widths='lrrrr')
    main=section_replace(main,'sec:ablation',section('Component Ablations and Metadata-Proxy Augmentation','sec:ablation',abtable+r'''The historical ``no diversity'' row set only $\gamma=0$ while retaining $\lambda=0.05$ in $-\lambda e^{-D}$. It is now labeled ``gamma=0 only.'' Disabling both terms changes mean diversity from 0.0224 to '''+number('LEA true no diversity','diversity')+r''', showing that the two diversity-dependent terms must be distinguished. The gamma-only and no-self-cleaning variants retain the baseline aggregate metrics. This result supports an effect of the retained redundancy term under this implementation, not a universal advantage of the named optimizer. The zero-imputation diagnostic changes scoring on the same pools and evaluates selections using the original masked utility. Uniform-pool LEA tests the engineered candidate generator, not a trained retrieval model.'''))
    # Sensitivity and query-level interpretation.
    sdata=[]
    for g in gammas:
        rs=ss[(g,.05)];sdata.append([str(g),f'{avg(rs,"rel_at_5"):.4f}',f'{avg(rs,"diversity"):.4f}',str(sum(r['same_set_as_baseline']=='False' for r in rs))+'/50'])
    stable=all(r['same_set_as_baseline']=='True' for r in ss[(0,.05)])
    sensitivity_text=r'''The joint sweep uses gamma values 0, 0.025, 0.05, 0.10, 0.20, 0.40, and 0.80, and redundancy coefficients 0, 0.025, 0.05, 0.10, and 0.20 on all 50 query/seed pools: 1,750 runs. We define observable activation by a changed top-five set, order, or unrounded metric; a nonzero coefficient alone is not evidence of an output effect. Coefficients are retained at their predefined baseline, not selected from the sweep. The supplement reports every coefficient pair and scenario-level evidence, including null effects. Numerical fitness histories are also hashed in the artifacts.
'''+table([r'$\gamma$','Rel@5','Diversity','Changed sets'],sdata,r'Gamma sensitivity with redundancy coefficient fixed at 0.05. Changed sets are relative to baseline gamma=0.10.','tab:gamma',widths='rrrr')+r'''
\begin{figure}[H]\centering\includegraphics[width=\linewidth]{figures/reviewer_sensitivity.png}
\caption{Joint coefficient sensitivity. The left panel reports diversity; the right reports changed top-five sets relative to baseline. Changing the selected set is distinguished from changing the reported mean utility.}\label{fig:sensitivity}\end{figure}
'''
    stats=r'''The independent descriptive units are five query scenarios; ten seeds per scenario measure repeated algorithm behavior and do not create 50 independent scientific tasks. The LEA--WeightedSum diversity differences are 0.0125, 0.0000, 0.0028, 0.0029, and 0.0001 for CO$_2$, photocatalysis, lightweight, balanced, and insulating scenarios. The CO$_2$ scenario contributes approximately 68\% of the sum of these differences. We therefore report scenario dependence and no statistical superiority claim. Complete per-scenario results for all primary methods are given in Supplementary Table~S1.

'''+sensitivity_text
    main=section_replace(main,'sec:stats',section('Scenario-Level Analysis and Coefficient Sensitivity','sec:stats',stats)) if r'\label{sec:stats}' in main else main
    # Locate actual original statistics label if different.
    if r'\label{tab:gamma}' not in main:
        mat=re.search(r'\\section\{Statistical[^}]*\}\s*\\label\{([^}]+)\}',main);assert mat,'statistics section';main=section_replace(main,mat.group(1),section('Scenario-Level Analysis and Coefficient Sensitivity',mat.group(1),stats))
    rag=r'''Explanation is an auxiliary interface module; it has no effect on candidate generation, objective weights, or rankings in this benchmark. The reproduced runner emits 30 deterministic templates conditioned on seed-42 LEA candidate identifiers. It checks identifier presence and limitation phrases, but directly assigns metadata consistency, the nominal explanation-quality score, and all unsupported-claim flags. Those assigned values cannot demonstrate factual accuracy or a zero hallucination rate. We withdraw the former quality-score table as an independent evaluation and report the executable check scope instead.
'''+table(['Output/check','Interpretation'],[['30 candidate-conditioned templates','Reproducible local output; no live LLM call'],['Identifier inclusion','String-presence check against selected IDs'],['Limitation wording','Template/phrase check'],['Metadata and violation scores','Assigned in code; not independent measurements'],['Expert usefulness and faithfulness','Not evaluated']],r'Actual scope of the deterministic explanation routine.','tab:rag_results',widths='p{5.0cm}p{8.4cm}')+r'''A future explanation benchmark requires independent claim checking, source attribution, expert ratings, and adversarial prompts. The interface screenshots in the supplement illustrate historical UI behavior only.'''
    main=section_replace(main,'sec:rag_eval',section('Auxiliary Explanation: Template Audit and Limits','sec:rag_eval',rag))
    main=section_replace(main,'sec:robustness',section('Runtime, Scalability, and Descriptor-Level Screening','sec:robustness',r'''Reranking time was measured for WeightedSum, TOPSIS, LEA, and top-five MMR at pool sizes 50, 100, 200, 500, and 1,000, using five scenarios, seeds 42--44, and three repeats (45 measurements per method/size). These are serial wall-clock timings on one machine and exclude shared catalog scoring and retrieval. Mean and standard deviation, plus the raw measurements, are supplied in the supplement and artifacts. At fixed $K$, top-five MMR avoids the cubic distance-work growth of the original full-list scalar loop; its distance comparisons scale as $O(nK^2)$ in this implementation. LEA repeatedly remaps population vectors against the pool, with dominant work proportional to population size times iterations times pool size and objective dimension. These measurements establish local post-retrieval scaling only.

Descriptor-level screening compares catalog, candidate-pool, Random, WeightedSum, and LEA distributions for observed density and band gap, including missingness and prespecified bands. Because these descriptors also affect candidate generation and utility, their shifts are consistency checks, not independent discovery validation. Density thresholds are not porosity or uptake measurements; a favorable band gap alone does not demonstrate photocatalytic activity. The mean LEA shortlist density in the lightweight scenario is 0.890 g/cm$^3$, versus 1.696 in the catalog. Mean observed gaps are 2.804 eV for photocatalysis and 4.311 eV for insulating frameworks; all selected insulating gaps are at least 3.5 eV. These shifts support consistency with those descriptor-level intents, but not independent application performance. In the lightweight candidate pools, only 7 of 100 gaps are observed; selection favors those observed gaps, illustrating a completeness effect as well as a density preference.'''))
    discussion=r'''The evidence supports an auditable screening formulation under incomplete metadata, with established algorithms as components. Relevance and NDCG are aligned with the utility that WeightedSum optimizes, so their ties cannot validate scientific relevance independently. Full-precision hybrid distances resolve variation hidden by binned objectives, but the resulting diversity remains representation-dependent and partly heuristic.

LEA sits between WeightedSum and MMR in the original aggregate diversity comparison, with much of its difference concentrated in one scenario. The corrected ablation identifies a contribution from diversity-dependent fitness, chiefly the retained redundancy term at the baseline setting; gamma-only and self-cleaning ablations do not establish separate benefits. The added DE portfolio comparator broadens the optimization comparison but uses a fixed list objective, whereas LEA retains history-dependent candidate fitness. Neither comparison proves universal algorithm superiority.

The corrected top-five MMR is faster than LEA while preserving the higher original diversity and equal relevance. Accordingly, a runtime-based ``middle ground'' argument is not supported by the matched workload. The original ratio is retained only as an implementation audit, not as evidence for choosing LEA.

Learned atomistic GNNs and transformers answer a different representation-learning question from the present engineered-proxy benchmark. A fair learned comparison needs matched inputs, training splits, checkpoints, and targets. Although CIFs exist locally, the final protocol supplies none of these trained ranking comparisons. Bayesian optimization and active learning additionally require a sequential acquisition task and an oracle or held-out property target; the current deterministic utility is not such validation. These remain explicit gaps rather than artificial comparison rows.'''
    main=section_replace(main,'sec:discussion',section('Discussion','sec:discussion',discussion))
    main=section_replace(main,'sec:limitations',section('Limitations','sec:limitations',r'''Only five engineered query scenarios, $K=5$, incomplete descriptors, heuristic stability, and deterministic semantic proxies are evaluated. Band gap and density influence both selection and evaluation. The hybrid proxy block retains a zero fallback for missing band gap and is not fully mask-pure even though the physical coordinate is masked. No independent adsorption, synthesis, porosity, expert relevance, new DFT, online-user, or generative-discovery validation is provided. The graph-augmentation rows are engineered scores, not trained GNN predictions. Historical property-prediction numbers were not reproducible from the authoritative final protocol and are excluded. Explanation templates and assigned flags cannot establish LLM faithfulness. DE and LEA optimize differently defined utilities, and the limited search budget and query suite do not establish general optimizer rankings. Timing excludes retrieval, catalog scoring, and generation, and should not be read as production latency.'''))
    main=section_replace(main,'sec:conclusion',section('Conclusion','sec:conclusion',r'''QMOF-Rec provides a reproducible formulation for ranking existing QMOF records under incomplete metadata. The authoritative final protocol reproduces the reported primary ranking values. The revision adds complete scenario-level results, joint coefficient sensitivity, a true no-diversity ablation, a differential-evolution portfolio baseline, matched top-five timing and scalability, and descriptor-level screening checks. These tests support careful separation of masked utility, material diversity, and physical validation. They do not establish LEA as the core novelty or preferred optimizer: top-five MMR preserves its diversity advantage and runs faster in the corrected comparison. Learned graph models and independently evaluated LLM explanations remain future extensions; the present evidence consists of metadata-based screening and deterministic templates.'''))
    main=main.replace('Supplementary Figures S3--S12','the supplementary interface figures')
    main=main.replace('The processed metadata, scripts, and evaluation artifacts used in this study are available at:', 'The source repository is:')
    main=main.replace('The code and processed evaluation artifacts used for the reported offline ranking, graph-aware, ablation, and candidate-conditioned explanation evaluations are available at the same repository:', 'The original code is available at the repository below. The reviewer-revision scripts and machine-readable artifacts accompany this revision locally and must be deposited with a versioned release before submission:')
    main=main.replace('The authors reviewed, edited, verified, and approved the final text, code changes, figures, and response materials and take full responsibility for the manuscript content, analyses, and conclusions.','The authors are responsible for reviewing and approving the final text, code changes, figures, response materials, and scientific conclusions before submission.')
    main=main.replace(r'\begin{thebibliography}',r'\begin{thebibliography}',1)
    main=main.replace(r'\end{thebibliography}',r'\bibitem{scipyde} SciPy developers. Differential evolution, SciPy 1.13.1 reference manual. \url{https://docs.scipy.org/doc/scipy-1.13.1/reference/generated/scipy.optimize.differential_evolution.html}.'+'\n'+r'\end{thebibliography}')
    main=main.replace('The candidate-conditioned explanation layer is evaluated for answer quality, groundedness, metadata consistency, unsupported-claim flags, limitation awareness, and explanation quality in Section~\\ref{sec:rag_eval}; the scoring rubric and safeguard flags are listed in Supplementary Tables S2 and S3. It is not evaluated as improving ranking quality.',r'The auxiliary explanation routine is audited in Section~\ref{sec:rag_eval}; assigned scores are not independent quality evidence, and explanation does not alter ranking.')
    main=main.replace('Full pseudocode for retrieval/objective scoring, LEA reranking, and graph-aware explanation assistance is provided in the supplementary material.','The supplementary material gives the implementation scope and exact reproduction commands; executable control flow is preserved in the versioned runner.')
    main=main.replace('This signal is useful as a local graph-neighborhood baseline, but it should not be interpreted as a CIF-derived atomistic graph result or as a physically validated structure-aware adsorption model.','This is a prospective extension, not a trained-model result of the final ranking protocol. The executed benchmark uses the engineered proxies specified below.')
    main=main.replace('qmof-330a403 & Co$_2$C$_{58}$F$_{12}$H$_{32}$N$_8$O$_8$S$_2$', 'qmof-330a403 & {\\tiny Co$_2$C$_{58}$F$_{12}$H$_{32}$N$_8$O$_8$S$_2$}')
    main=main.replace('C{0.9cm} L{2.5cm} L{3.9cm}', 'C{1.1cm} L{2.5cm} L{3.9cm}')
    main=main.replace('These signals are derived from formula-level and metadata-neighborhood relationships', 'The evaluated signals are engineered formula- and descriptor-based proxies; prospective learned signals could encode metadata-neighborhood relationships')
    main=main.replace('The deterministic explanation evaluation reported below therefore checks groundedness and safeguard behavior rather than serving as a live LLM hallucination benchmark.', 'The deterministic routine below checks only identifier inclusion and limitation phrases; assigned flags do not independently establish safeguard behavior.')
    main=main.replace('deterministic candidate identifiers.', 'the seed-dependent candidate-pool order.')
    main=main.replace('computed from the product-like multi-objective footprint used by the reproducible evaluation script and should be interpreted as a comparative proxy only.', r'computed per list as $\mathrm{Rel}@5\times\mathrm{ILD}\times\overline{s}_{\mathrm{gap}}\times\overline{s}_{\mathrm{density}}\times\overline{s}_{\mathrm{stability}}$, then averaged over runs; it is a comparative proxy only.')
    main=main.replace(r'\medskip\noindent\textbf{Keywords:}',r'\par\medskip\noindent\textbf{Keywords:}')
    main=main.replace('The current graph-learning results are formula-derived metadata-graph baselines; CIF-derived, atomistic, and full structure-aware GNN evaluation remains future work.', 'The evaluated graph-named variants are engineered metadata proxies; trained metadata-graph, CIF-derived, and atomistic GNN comparisons remain future work.')
    main=main.replace('an end-to-end scientific recommender workflow for materials discovery rather than only a materials database or optimization script.', 'an end-to-end scientific recommender workflow for screening existing material records.')
    (MAN/'main.tex').write_text(main)
    # Supplement replaces unverifiable summaries with generated evidence; retains interface appendix.
    pre=r'''\documentclass[11pt,a4paper]{article}
\usepackage[a4paper,margin=2.2cm]{geometry}
\usepackage[T1]{fontenc}\usepackage[utf8]{inputenc}
\usepackage{amsmath,booktabs,longtable,array,graphicx,float,hyperref,caption,subcaption}
\usepackage{microtype}\usepackage{parskip}
\hypersetup{hidelinks}\renewcommand{\thetable}{S\arabic{table}}\renewcommand{\thefigure}{S\arabic{figure}}
\begin{document}
\begin{center}{\Large\bfseries QMOF-Rec: Revised Supplementary Material}\\[5pt]
Authoritative final protocol and reviewer experiments, 19 September 2026\end{center}
\section*{Provenance and interpretation}
The executable repository is \texttt{qmof-rec}, commit \texttt{10082124cf81a90ce40b4bd6306862416a46d2e6}. Source hashes, raw candidate pools, rankings, and reproduction comparisons accompany the artifacts. Twenty-one mask-aware regression tests pass. All seven primary methods reproduce Rel@5, NDCG@5, and diversity at the original four-decimal precision. There are five scenarios and ten seeds (42--51), not 50 independent scientific queries. Density is observed for 20,372 records, band gap for 10,810, and void fraction for none. Historical artifacts absent from this checkout are not asserted to have been reproduced.
\section*{Complete scenario-level ranking results}
Metrics are computed on the same pool of 100 for each query/seed. Values below are means over ten seeds. MMR (top-5) exactly matches the original MMR top five in all 50 runs. DE uses the same representation and evaluation but a fixed list objective and 1,800 portfolio evaluations. Relevance/NDCG are aligned utility diagnostics, not independent labels.
'''
    scenario=[]
    for q in qids:
        for m in primary:
            rs=[r for r in group[m] if r['query_id']==q]
            scenario.append([qmap[q],label(m),f'{avg(rs,"rel_at_5"):.4f}',f'{avg(rs,"ndcg_at_5"):.4f}',f'{avg(rs,"diversity"):.4f}',f'{sd(rs,"diversity"):.4f}',f'{avg(rs,"runtime_ms"):.2f}'])
    sup=pre+table(['Scenario','Method','Rel@5','NDCG','Diversity','SD','ms'],scenario,'Complete primary-method results by scenario. SD describes diversity across seeds.','tab:scenario',True,'llrrrrr')
    sup+=r'\section*{Joint gamma and redundancy sensitivity}'+'\n'+r'All 35 settings are rerun on all 50 pools. Changed sets and orders are counted relative to $(\gamma,\lambda)=(0.10,0.05)$. The true no-diversity ablation is $(0,0)$; setting only gamma to zero retains a diversity-dependent penalty. Full per-scenario, per-seed metrics and selected IDs are saved in \path{artifacts/reviewer_revision/sensitivity.csv}.'+'\n'
    sdata=[]
    for g in gammas:
        for pen in penalties:
            rs=ss[g,pen]; sdata.append([str(g),str(pen),f'{avg(rs,"rel_at_5"):.4f}',f'{avg(rs,"ndcg_at_5"):.4f}',f'{avg(rs,"diversity"):.4f}',str(sum(r['same_set_as_baseline']=='False' for r in rs)),str(sum(r['same_order_as_baseline']=='False' for r in rs))])
    sup+=table([r'$\gamma$',r'$\lambda$','Rel@5','NDCG','Diversity','Sets /50','Orders /50'],sdata,'Joint sensitivity; identical rounded metrics can conceal different selected sets.',long=True,widths='rrrrrrr')
    sup+=r'\section*{Runtime dispersion and scaling}'+'\n'+r'Reranking times are serial wall-clock measurements; they exclude shared catalog scoring, retrieval, networking, and explanations. Table S3 summarizes 50 query/seed runs. The original MMR full-list row is an audit comparator, not the matched top-five implementation. Scaling uses 45 measurements per method/size (five queries, three seeds, three repeats), with population 30 and 60 LEA iterations fixed.'+'\n'
    sup+=table(['Method','Mean ms','SD ms','Minimum','Maximum'],[[label(m),f'{avg(group[m],"runtime_ms"):.3f}',f'{sd(group[m],"runtime_ms"):.3f}',f'{min(float(r["runtime_ms"]) for r in group[m]):.3f}',f'{max(float(r["runtime_ms"]) for r in group[m]):.3f}'] for m in primary+['MMR']],'Primary-method runtime dispersion; MMR without the top-5 suffix computes the full 100 ranks.',widths='lrrrr')
    st=[]
    for size in [50,100,200,500,1000]:
        for m in ['WeightedSum','TOPSIS','LEA','MMR top5']:
            rs=[r for r in scale if int(r['pool_size'])==size and r['method']==m];st.append([str(size),label(m),str(len(rs)),f'{avg(rs,"runtime_ms"):.3f}',f'{sd(rs,"runtime_ms"):.3f}'])
    sup+=table(['Pool size','Method','Measurements','Mean ms','SD ms'],st,'Post-retrieval scalability at fixed top-five output.',long=True,widths='rlrrr')
    sup+=r'\section*{Descriptor-level screening sanity check}'+'\n'+r'Density is in g/cm$^3$ and band gap in eV. Means average the selected observed descriptors within each seed, then average across seeds with defined means; all-missing seed means are excluded, not zero-filled. A dash denotes an undefined summary. Catalog and pool are reference populations, not experimental control groups. Values are not adsorption capacity or evidence of synthesis feasibility. Missingness is reported separately; thresholds are descriptive. Formula and text heuristics can dominate the retained scenario definitions.'+'\n'
    descr=[]
    for q in qids:
        for g in ['catalog','candidate_pool','Random','WeightedSum','LEA']:
            dr=[r for r in screen if r['query_id']==q and r['group']==g and r['descriptor']=='density'];br=[r for r in screen if r['query_id']==q and r['group']==g and r['descriptor']=='band_gap']
            descr.append([qmap[q],esc(g.replace('_',' ')),f'{avg(dr,"mean"):.3f}',f'{avg(br,"mean"):.3f}',f'{100*avg(br,"missing_fraction"):.1f}',f'{100*avg(br,"fraction_observed_gap_at_least_3_5"):.1f}'])
    sup+=table(['Scenario','Group','Density','Gap','Gap missing \%','Gap $\geq$3.5 \%'],descr,'Observed descriptor means and band-gap completeness; the threshold percentage uses observed gaps as denominator.',long=True,widths='llrrrr')
    sup+=r'''\section*{Ablation scope and advanced optimizer}
Zero-imputed WeightedSum changes the missing-score convention on the same pools, with evaluation using the original masked relevance. If its top five are unchanged, that is a null effect in this pool, not a demonstration that masking is unnecessary. Uniform-pool LEA replaces candidate generation with random sampling from the catalog and therefore changes the feasible set and NDCG ideal. Its scores cannot be read as a same-pool optimizer comparison. Proxy S/A variants use 85\% relevance and 15\% engineered proxy, not trained GNN output.

The DE portfolio implementation uses SciPy 1.13.1, \texttt{best1bin}, differential weight dithering 0.5--1, crossover 0.7, immediate updating, no polishing, 30 members, and 59 generations after initialization. Random keys select exactly five unique IDs. One population member encodes WeightedSum, with 29 random members. Its fixed list objective is $\overline R+0.1\overline B+0.1D-0.05e^{-D}$. Cached pairwise distance construction is included in timing; outputs are ordered by relevance. Tests verify scalar/vectorized masked-distance agreement, unique outputs, 1,800 evaluations, and utility no worse than the initial WeightedSum portfolio. Equal nominal search budgets do not equate candidate-fitness evaluations with whole-portfolio evaluations, nor establish identical optimization problems.

\section*{Implementation consistency and missingness}
The final protocol uses eight formula coordinates, including heteroatom fraction, although the configuration's descriptive formula-feature list names seven. The executed hybrid vector contains two physical, eight formula, and two proxy dimensions, with block scaling $\sqrt{0.55/2}$, $\sqrt{0.30/8}$, and $\sqrt{0.15/2}$ before masked RMS distance. The missing physical gap coordinate is excluded, but proxy A has an internal zero fallback. This retained heuristic is disclosed rather than silently changed during reproduction. Objective remapping and hybrid diversity remain distinct. LEA retains best-ever candidate fitness across changing selected contexts; its trace is not convergence of a single fixed portfolio objective.

\section*{Explanation audit}
The runner emits 30 templates from saved seed-42 LEA selections. Groundedness uses identifier presence and limitation awareness uses phrases. Metadata consistency, nominal explanation-quality scores, and violation flags are assigned, rather than assessed by an independent evaluator. The former 5/5 and zero-hallucination claims are therefore excluded as evidence of explanation quality. No live LLM or expert-human benchmark has been run.

\section*{Reproduction commands and files}
Run from the authoritative repository:
\begin{verbatim}
PYTHONPATH=backend python3 -m pytest -q backend/tests
python3 scripts/run_final_diversity_aware_masked_protocol.py
python3 scripts/run_reviewer_revision.py
python3 scripts/build_reviewer_revision.py
\end{verbatim}
The baseline configuration is \path{configs/final_diversity_aware_masked_protocol.json}. New raw results, manifests, figures, and source snapshots are in \path{artifacts/reviewer_revision/}. The manuscript builder writes only the designated revision workspace and retains input sources under the executable repository's source snapshots. These new artifacts require a versioned deposit before submission; no publication or upload is claimed here.
'''
    appendix=oldsup[oldsup.index(r'\section*{CO$_2$ Adsorption Scenario}'):]
    appendix=appendix.replace('Chemically Novel Candidates','Interface Example: Candidate Diversity')
    sup+=r'\clearpage\section*{Historical interface illustrations}'+'\n'+r'The following screenshots are retained as interface illustrations. They are not new experiments, physical validation, or an independently assessed LLM benchmark.'+'\n'+appendix
    (MAN/'supplementary_material.tex').write_text(re.sub(r'(?<![A-Za-z])nan(?![A-Za-z])', '--', sup))
    # Audit summary used for the response and final report.
    summary={'LEA_diversity':avg(lea,'diversity'),'WeightedSum_diversity':avg(ws,'diversity'),'MMR_diversity':avg(mmr,'diversity'),'true_no_diversity':avg(true,'diversity'),'DE_diversity':avg(de,'diversity'),'DE_relevance':avg(de,'rel_at_5'),'LEA_ms':avg(lea,'runtime_ms'),'MMR_top5_ms':avg(mmr,'runtime_ms'),'MMR_full_ms':avg(group['MMR'],'runtime_ms'),'DE_ms':avg(de,'runtime_ms'),'sensitivity_runs':len(sensitivity),'gamma_zero_same_sets':stable,'gamma_08_changed_sets':sum(r['same_set_as_baseline']=='False' for r in ss[(.8,.05)])}
    (OUT/'revision_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    write_response(summary,MAN,OUT)
    write_audit(summary,OUT,WORK)
    print(json.dumps(summary,indent=2));print('Wrote manuscript, supplement, response, and audit')

def write_response(s,man,out):
    intro='We thank both reviewers. We reproduced the original primary ranking results from the authoritative repository before revising the manuscript. The revision adds 1,750 coefficient-sensitivity runs, a true no-diversity ablation, complete per-scenario results, a differential-evolution portfolio baseline, descriptor-level checks, and matched top-five runtime/scalability measurements. The new evidence also requires corrections: LEA is not the core novelty, the historical MMR runtime comparison performed unequal work, graph-named ranking rows are engineered proxies, and directly assigned explanation scores are not independent quality evidence.'
    r1=[
    ('Clarify the methodological contribution.', 'We agree that integration of established components alone should not be presented as a new optimization principle. The Introduction and four-item contribution list now identify the system-level formulation: query-conditioned screening under incomplete metadata, separate masked utility and material diversity, auditable portfolio trade-offs, and auxiliary explanation. We removed the LEA core-novelty and first-framework claims.'),
    ('Demonstrate LEA advantages and compare advanced optimization.',f'We added a SciPy differential-evolution portfolio baseline on identical pools, masks, and hybrid distances, with 30 members and 1,800 list-objective evaluations. It obtains Rel@5={s["DE_relevance"]:.4f} and diversity={s["DE_diversity"]:.4f}. The fixed list objective and initialization are disclosed in Methods and the supplement; it is not asserted to reproduce LEA\'s history-dependent fitness. Revised Table 4 does not claim universal LEA preference. Moreover, top-five MMR takes {s["MMR_top5_ms"]:.2f} ms versus LEA {s["LEA_ms"]:.2f} ms, with the same MMR selections. The previous speed-based preference is withdrawn.'),
    ('Add evidence of practical usefulness beyond ranking consistency.', 'We added scenario-level comparisons of observed density and band gap for the catalog, candidate pool, Random, WeightedSum, and LEA, with missingness and descriptor thresholds (supplementary descriptor table and raw screening.csv). These expose whether shortlist descriptors follow the stated screening intent. They use descriptors involved in scoring, so they are explicitly sanity checks, not independent materials-discovery validation. No adsorption uptake, porosity, synthesis, new DFT, or expert-label validation is claimed; that limitation remains unresolved by the available benchmark.'),
    ('Distinguish metadata graphs from atomistic structural representations.', 'The revised graph sections provide the actual formulas for proxies S and A and state that the benchmark neither constructs a graph nor loads trained GNN weights. The historical GraphSAGE-only/GAT-only labels are replaced by proxy scoring; these policies also retain 85% relevance, so they were not graph-only. CIF files are present but unused in this protocol. The old trained-property prediction numbers and graph topology counts could not be reproduced and have been withdrawn; Table 6 now audits implementation scope.'),
    ('Clarify whether LLM/RAG is core or auxiliary.', 'Explanation is now explicitly auxiliary and cannot alter candidate selection or ranking. Audit of the reproduced 30-template routine showed that several scores and all violation flags are directly assigned. We therefore replaced the nominal quality-score table with an implementation audit rather than describing perfect scores or zero flags as independent evidence. Live LLM, claim-checking, citation fidelity, and expert usefulness evaluation remain future work.'),
    ('Include modern AI materials-screening baselines.', 'We added an executable advanced optimization comparator (DE portfolio) and distinguish it from learned materials representations. We did not fabricate trained GNN or transformer comparison rows. A matched learned benchmark requires trained checkpoints, data splits, and comparable targets, which the final protocol does not supply; the GAT module is a stub. Bayesian optimization and active learning require a sequential acquisition objective and oracle, absent here. The Discussion states this remaining scope limitation rather than claiming that the requested learned-model comparison is complete.'),
    ('Quantify effects of individual components.',f'Revised Table 7 contains the LEA reference, gamma-only ablation, true no-diversity ablation, no-self-cleaning variant, proxy augmentation variants, a same-pool zero-imputation scoring diagnostic, and a uniform-candidate-pool diagnostic. Turning off both gamma and the redundancy penalty changes diversity from 0.0224 to {s["true_no_diversity"]:.4f}; the original gamma-only label was misleading. The uniform-pool row changes the feasible set and is not treated as a same-pool optimizer result. All coefficients and raw outputs are recorded.'),
    ('Refine materials-discovery terminology.', 'The evaluated task is now consistently framed as screening or prioritizing existing QMOF records. The Abstract and Introduction state that the system is not generative. Discovery terminology is retained only for the wider literature or future physical validation, and interface screenshots are not presented as evidence of novel materials.'),
    ('Report runtime and scalability.',f'The revision measures WeightedSum, TOPSIS, LEA, and top-five MMR for pools of 50, 100, 200, 500, and 1,000, with five scenarios, three seeds, and three repeats (45 measurements per method/size). Means, standard deviations, scope, and raw timings are provided. The original full-ranking MMR reproduced at {s["MMR_full_ms"]:.2f} ms, but its exactly matching top-five prefix needs {s["MMR_top5_ms"]:.2f} ms. We withdraw the approximately 25-fold LEA speed claim and discuss fixed-K complexity and excluded retrieval/generation costs.'),
    ('Use one abstract paragraph and revise contributions.', 'The abstract is now one paragraph. The contribution list is reduced to four scoped statements and separates the scientific formulation and empirical findings from general implementation capabilities. It incorporates the corrected ablation and runtime conclusions rather than repeating the previous stronger LEA claims.')]
    r3=[
    ('LEA is not supported as the core novelty.', 'We agree and removed that statement. The contribution is the auditable incomplete-metadata screening formulation. LEA is an evaluated policy with scenario-dependent behavior, not a newly established superior optimizer.'),
    ('Rel@K is aligned with WeightedSum; specify NDCG relevance.', 'The metrics section now defines rel_r = R(m_(r),q). IDCG sorts this same masked utility in the identical pool. WeightedSum maximizes both aligned metrics by construction; ties show utility preservation and are not independent evidence of relevance accuracy or physical discovery.'),
    ('Report diversity ordering accurately.', f'The original values reproduce: ParetoCrowding 0.0263, MMR 0.0241, SemanticOnly 0.0240, Random 0.0237, LEA 0.0224, and WeightedSum/TOPSIS 0.0187. We state explicitly that LEA is not the most diverse. The added DE portfolio comparator reaches {s["DE_diversity"]:.4f}, with its separate list objective disclosed.'),
    ('Explain the identical ablations and correct the no-diversity variant.',f'The original row disabled gamma but retained the 0.05 exponential redundancy penalty. It is renamed gamma=0 only. Setting both coefficients to zero gives diversity {s["true_no_diversity"]:.4f}, versus baseline 0.0224. Gamma-only and no-self-cleaning aggregate null effects are preserved and discussed. We do not attribute the baseline improvement to both mechanisms independently.'),
    ('Add all-method per-scenario results and discuss the CO2 concentration.', 'Supplementary Table S1 reports all seven original methods plus DE for all five scenarios. The reproduced LEA-minus-WeightedSum differences are 0.0125, 0.0000, 0.0028, 0.0029, and 0.0001. CO2 contributes about 68% of their sum. Five scenarios are treated as descriptive blocks; ten seeds per scenario are not 50 independent scientific tasks.'),
    ('Position LEA as a relevance-preserving middle ground.',f'The intermediate-diversity description is supported, but our additional matched-workload audit does not support the proposed runtime rationale. The original MMR computes all 100 ranks; stopping at five preserves every tested top-five list and reduces its mean runtime to {s["MMR_top5_ms"]:.2f} ms, below LEA\'s {s["LEA_ms"]:.2f} ms. We report this correction candidly and do not retain a misleading LEA speed advantage.'),
    ('Sweep gamma and identify activation.',f'The revision sweeps gamma=0, 0.025, 0.05, 0.10, 0.20, 0.40, 0.80, jointly with five penalty coefficients. At penalty 0.05, gamma=0 retains the baseline sets in all 50 runs; gamma=0.80 changes {s["gamma_08_changed_sets"]}/50 sets. We distinguish changes in sets, order, unrounded metrics, and recorded fitness-history hashes. The main sensitivity table and heatmap show where output effects appear, including null regions.'),
    ('Sweep the 0.05 redundancy coefficient.', 'The joint grid includes penalty coefficients 0, 0.025, 0.05, 0.10, and 0.20, for 35 settings and 1,750 query/seed runs. The supplement reports every pair, and sensitivity.csv includes scenario-level metrics and selected IDs. The baseline remains predefined; the grid is a robustness analysis and not outcome-driven retuning.'),
    ('Avoid duplicated principal rows in Tables 4 and 7.', 'Table 4 contains principal methods and DE. Table 7 contains component diagnostics, with only LEA repeated as the clearly identified reference row. SemanticOnly, WeightedSum, and MMR are no longer duplicated there; the zero-imputed WeightedSum row is a distinct labeled diagnostic.')]
    md='# Response to Reviewer 1 and Reviewer 3\n\n'+intro+'\n\n'
    tex=r'''\documentclass[11pt,a4paper]{article}\usepackage[a4paper,margin=2.4cm]{geometry}\usepackage[T1]{fontenc}\usepackage[utf8]{inputenc}\usepackage{parskip,hyperref,microtype}\hypersetup{hidelinks}\begin{document}\begin{center}{\Large\bfseries QMOF-Rec: Point-by-Point Response}\\COMMT-D-26-00255\end{center}'''+'\n'+esc(intro)+'\n'
    for reviewer,comments in [('Reviewer 1',r1),('Reviewer 3',r3)]:
        md+='## '+reviewer+'\n\n';tex+=r'\section*{'+reviewer+'}\n'
        if reviewer=='Reviewer 3':md+='The reviewer supplied a continuous comment; the points below separate its substantive requests for clarity.\n\n';tex+='The continuous reviewer comment is separated into its substantive requests below.\n\n'
        for i,(concern,answer) in enumerate(comments,1):
            md+=f'### {i}. {concern}\n\n{answer}\n\n';tex+=r'\subsection*{'+str(i)+'. '+esc(concern)+'}\n'+esc(answer)+'\n\n'
    end='Submission note: the new local scripts and artifacts must be included in a versioned repository/archive release, and the authors must review the revised claims and response before submission. No upload or publication has been performed.'
    md+=end+'\n';tex+=r'\end{document}'
    (WORK/'revision_reports/02_point_by_point_response.md').write_text(md);(man/'response_to_reviewers.tex').write_text(tex)

def write_audit(s,out,work):
    report=f'''# Phase 1 reproduction and reviewer revision — authoritative repository

Date: 2026-09-19. This report supersedes the prior blocked audit, which searched the wrong executable location.

## Outcome

**Primary ranking reproduction passed.** Executable repository: `/Users/mehrdadjalali/Documents/GitHub/qmof-rec`, baseline commit `10082124cf81a90ce40b4bd6306862416a46d2e6`. No older sibling implementation was used. All seven original methods reproduce Rel@5, NDCG@5, and hybrid diversity at four-decimal manuscript precision. Focused regression suite: **21 passed**.

Source hashes, descriptor coverage, environment, and the 21 individual comparisons are saved under `artifacts/reviewer_revision/reproduction/`. Density coverage is 20,372; finite band gap 10,810; void fraction 0. Original configuration, runner, objective utilities, mask-aware scoring, hybrid representation, and revised backend LEA are present. The three requested historical artifact directories were absent before execution. The final protocol regenerated final_diversity_aware_masked_protocol and diversity_revision. A new final_consistency_audit records this revision; no absent historical artifacts are invented.

## Completed extensions

- Complete all-method, all-scenario results: five scenarios, ten seeds.
- Gamma × redundancy sensitivity: 35 settings and {s['sensitivity_runs']} runs; selected IDs and history hashes retained.
- True no-diversity ablation: both coefficients zero, diversity {s['true_no_diversity']:.8f}.
- Same-pool zero-imputation and uniform-candidate-pool diagnostics.
- DE portfolio baseline: same pools and hybrid distances, 1,800 fixed-list utility evaluations; objective differs explicitly from historical LEA fitness.
- Runtime scaling: four methods × five sizes × five queries × three seeds × three repeats = 900 timings.
- Catalog/pool/Random/WeightedSum/LEA descriptor-level screening summaries.
- Revised main manuscript, supplement, and point-by-point response.

## Corrections that materially affect interpretation

1. Original full-list MMR: {s['MMR_full_ms']:.2f} ms; exactly matching top-five MMR: {s['MMR_top5_ms']:.2f} ms; LEA: {s['LEA_ms']:.2f} ms. The previous LEA runtime advantage is withdrawn.
2. Gamma=0 alone leaves the redundancy penalty active. True no diversity differs from the published mislabeled row.
3. Graph-named ranking rows are engineered proxy augmentation, not trained GNNs or graph-only policies. Prior graph-regression numbers/topology counts are not reproduced and have been removed from evidentiary results. CIF files exist but are not consumed by the final ranking protocol.
4. Several explanation scores and all violation flags are assigned by the runner. They are not independent quality or hallucination measurements; the former quality claims are withdrawn.
5. The physical band-gap coordinate is masked, but proxy A internally uses a zero fallback for absent gap. The configuration description lists seven formula features; executed code uses eight including heteroatom fraction. Both are disclosed; the baseline code was not silently changed.
6. LEA stores best-ever candidate fitness across changing contexts. Its trace is not a fixed final-list objective convergence proof.

## Limits and submission actions

No experimental/adsorption/porosity/new-DFT/expert validation, trained transformer or GNN ranking benchmark, live LLM evaluation, or sequential BO/active-learning experiment is claimed. New artifacts remain local and require a versioned deposit before submission. Author review is needed before external submission; no messages or files have been sent externally.
'''
    (out/'audit_report.md').write_text(report);(work/'revision_reports/01_reproduction.md').write_text(report)
    consistent=ROOT/'artifacts/final_consistency_audit';consistent.mkdir(exist_ok=True)
    (consistent/'reviewer_revision_audit.md').write_text(report)
    (out/'reproduction/source_manifest.json').write_text(json.dumps({**json.loads((out/'reproduction/source_manifest.json').read_text()),'reproduction_status':'passed','manuscript_edited':True},indent=2)+'\n')
    response=(work/'revision_reports/02_point_by_point_response.md').read_text()
    matrix=['# Reviewer request completion index','', 'Executable repository: `/Users/mehrdadjalali/Documents/GitHub/qmof-rec`. This supersedes the earlier wrong-location audit. Detailed responses are in `02_point_by_point_response.md`; evidence and caveats are in `01_reproduction.md`.','', '| Reviewer | Point | Concern | Status |','|---|---:|---|---|']
    reviewer=''
    for line in response.splitlines():
        if line.startswith('## Reviewer'): reviewer=line[3:]
        if line.startswith('### '):
            num,concern=line[4:].split('. ',1)
            status='Addressed with reproduced evidence and revised text'
            if reviewer=='Reviewer 1' and num=='3': status='Descriptor sanity check complete; independent physical validation unavailable'
            if reviewer=='Reviewer 1' and num=='6': status='Advanced optimizer added; trained GNN/transformer and sequential oracle baselines remain gaps'
            matrix.append(f'| {reviewer} | {num} | {concern} | {status} |')
    (work/'revision_reports/00_review_matrix.md').write_text('\n'.join(matrix)+'\n')
if __name__=='__main__': main()
