"""Verify this package's staged LFS pointers against working files and local objects."""
import hashlib,json,subprocess
from pathlib import Path

root=Path(__file__).resolve().parents[2]
prefixes=[f'art/{kind}/qingxi-water-report-c/' for kind in ('references','source','exports','previews')]+['tools/qingxi-water-report-c/']
def git(*args):
    return subprocess.check_output(['git',*args],cwd=root).decode('utf-8').strip()
files=git('ls-files','--',*prefixes).splitlines()
verified=[]
for name in files:
    if not name.endswith(('.png','.glb','.blend','.webm')):
        continue
    pointer=git('show',':'+name)
    assert pointer.startswith('version https://git-lfs.github.com/spec/v1\n'),name
    oid=next(line.split('sha256:')[1] for line in pointer.splitlines() if line.startswith('oid '))
    size=int(next(line.split()[1] for line in pointer.splitlines() if line.startswith('size ')))
    working=root/name
    obj=root/'.git/lfs/objects'/oid[:2]/oid[2:4]/oid
    for candidate in (working,obj):
        assert candidate.stat().st_size==size,str(candidate)
        assert hashlib.sha256(candidate.read_bytes()).hexdigest()==oid,str(candidate)
    verified.append({'path':name,'sha256':oid,'size':size})
assert len(verified)>=30,len(verified)
report={'scope':prefixes,'note':'Package staged files only; baseline repository LFS objects were not all downloaded. Not a full repository fsck.','pass':True,'count':len(verified),'files':verified}
(root/'art/previews/qingxi-water-report-c/lfs-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('WATER_REPORT_LFS_PASS',len(verified))
