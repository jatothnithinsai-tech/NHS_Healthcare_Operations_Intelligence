"""Execute a compact analytical notebook from the real exported warehouse."""
import json
import importlib.util
import os
import sys
from src.ingestion.acquire import ROOT

cells=[
 {'cell_type':'markdown','metadata':{},'source':['# NHS operational exploratory analysis\n','Published aggregate data only. RTT, A&E and diagnostics remain separate populations. These cells read the validated warehouse exports.']},
 {'cell_type':'code','metadata':{},'execution_count':None,'outputs':[],'source':['from pathlib import Path\n','import pandas as pd\n','root = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()\n','national = pd.read_csv(root / "powerbi/data/National.csv", parse_dates=["month"])\n','national.tail(3)']},
 {'cell_type':'code','metadata':{},'execution_count':None,'outputs':[],'source':['national.select_dtypes("number").describe().round(3)']},
 {'cell_type':'code','metadata':{},'execution_count':None,'outputs':[],'source':['from IPython.display import Image, display\n','display(Image(filename=str(root / "reports/figures/national_trends.png")))']},
 {'cell_type':'markdown','metadata':{},'source':['## Interpretation\n','Rates use separate weighted denominators. National RTT totals include submitted providers and exclude missing-trust estimates and NONC. A&E includes booked attendance fields. Consult the decision report for calculated findings, provider-mix limitations and the chronological baseline evaluation.']}
]
out=ROOT/'notebooks/01_nhs_operational_eda.ipynb'
out.parent.mkdir(exist_ok=True)
notebook={'nbformat':4,'nbformat_minor':5,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.13'}},'cells':cells}
for index,cell in enumerate(cells):
    cell['id']=f'nhs-eda-{index:02}'
out.write_text(json.dumps(notebook,indent=2),encoding='utf-8')
if importlib.util.find_spec('nbclient'):
    kernel_root=ROOT/'.local/jupyter'
    kernel_dir=kernel_root/'kernels/python3'
    kernel_dir.mkdir(parents=True,exist_ok=True)
    (kernel_dir/'kernel.json').write_text(json.dumps({'argv':[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],'display_name':'Python (NHS project)','language':'python'}))
    os.environ['JUPYTER_PATH']=str(kernel_root)
    os.environ['JUPYTER_RUNTIME_DIR']=str(ROOT/'.local/jupyter/runtime')
    os.environ['IPYTHONDIR']=str(ROOT/'.local/ipython')
    import nbformat
    from nbclient import NotebookClient
    nb=nbformat.read(out,as_version=4)
    NotebookClient(nb,timeout=120,resources={'metadata':{'path':str(ROOT)}}).execute()
    nbformat.write(nb,out)
    print('Analytical notebook executed and saved with genuine outputs')
else:
    print('Notebook saved; execution pending nbclient runtime')
