#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, struct
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

MH_MAGIC_64=0xfeedfacf
FAT_MAGIC=0xcafebabe
FAT_MAGIC_64=0xcafebabf
LC_SEGMENT_64=0x19
LC_SYMTAB=0x2
CPU_ARM64=0x0100000c
CPU_X86_64=0x01000007

MC_PARAM_PREFIXES=("_ig_","_ctd_","_biig_","_igd_","_mwb_","_mwa_","_msgc_","_mci_","_mcd_","_meta_")

@dataclass
class Section:
    seg:str; name:str; addr:int; size:int; offset:int; flags:int

@dataclass
class Segment:
    name:str; vmaddr:int; vmsize:int; fileoff:int; filesize:int; sections:List[Section]

def cstr(b:bytes)->str:
    return b.split(b'\0',1)[0].decode('utf-8','replace')

def cpu_name(c:int)->str:
    return {CPU_ARM64:'arm64',CPU_X86_64:'x86_64'}.get(c,f'cpu_0x{c:x}')

def hx(n:Optional[int])->Optional[str]:
    return None if n is None else f'0x{n:x}'

def hx16(n:Optional[int])->Optional[str]:
    return None if n is None else f'0x{n:016x}'

def hx14(n:Optional[int])->Optional[str]:
    return None if n is None else f'0x{n:014x}'

def choose_slice(raw:bytes, preferred='arm64')->Tuple[bytes,dict]:
    le=struct.unpack_from('<I',raw,0)[0]
    be=struct.unpack_from('>I',raw,0)[0]
    if le==MH_MAGIC_64:
        cputype,cpusub=struct.unpack_from('<ii',raw,4)
        return raw, {'fat':False,'slice_fileoff':0,'slice_size':len(raw),'arch':cpu_name(cputype),'cputype':cputype,'cpusubtype':cpusub}
    if be in (FAT_MAGIC,FAT_MAGIC_64):
        nfat=struct.unpack_from('>I',raw,4)[0]
        off=8; entries=[]; is64=(be==FAT_MAGIC_64)
        for _ in range(nfat):
            if is64:
                cputype,cpusub,soff,ssize,align,res=struct.unpack_from('>IIQQII',raw,off); off+=32
            else:
                cputype,cpusub,soff,ssize,align=struct.unpack_from('>IIIII',raw,off); off+=20
            entries.append((cputype,cpusub,int(soff),int(ssize)))
        chosen=None
        for e in entries:
            if cpu_name(e[0])==preferred: chosen=e; break
        if chosen is None:
            chosen=entries[0]
        cputype,cpusub,soff,ssize=chosen
        return raw[soff:soff+ssize], {'fat':True,'slice_fileoff':soff,'slice_size':ssize,'arch':cpu_name(cputype),'cputype':cputype,'cpusubtype':cpusub}
    raise SystemExit('unsupported file: not a 64-bit Mach-O/fat Mach-O')

def parse_macho(data:bytes, slice_info:dict):
    magic=struct.unpack_from('<I',data,0)[0]
    if magic!=MH_MAGIC_64:
        raise SystemExit('selected slice is not little-endian MH_MAGIC_64')
    magic,cputype,cpusub,filetype,ncmds,sizeofcmds,flags,res=struct.unpack_from('<IiiIIIII',data,0)
    header=dict(slice_info)
    header.update({'magic':hex(magic),'filetype':filetype,'ncmds':ncmds,'sizeofcmds':sizeofcmds,'flags':hex(flags)})
    segs=[]; symtab=None; lc=32
    for _ in range(ncmds):
        cmd,cmdsize=struct.unpack_from('<II',data,lc)
        if cmd==LC_SEGMENT_64:
            name=cstr(data[lc+8:lc+24])
            vmaddr,vmsize,fileoff,filesize=struct.unpack_from('<QQQQ',data,lc+24)
            maxprot,initprot,nsects,sflags=struct.unpack_from('<IIII',data,lc+56)
            secs=[]; so=lc+72
            for _ in range(nsects):
                sname=cstr(data[so:so+16]); sseg=cstr(data[so+16:so+32])
                addr,size=struct.unpack_from('<QQ',data,so+32)
                offset,align,reloff,nreloc,flags,r1,r2,r3=struct.unpack_from('<IIIIIIII',data,so+48)
                secs.append(Section(sseg,sname,addr,size,offset,flags)); so+=80
            segs.append(Segment(name,vmaddr,vmsize,fileoff,filesize,secs))
        elif cmd==LC_SYMTAB:
            symoff,nsyms,stroff,strsize=struct.unpack_from('<IIII',data,lc+8)
            symtab={'symoff':symoff,'nsyms':nsyms,'stroff':stroff,'strsize':strsize}
        lc+=cmdsize
    return header,segs,symtab

def vm_to_file(addr:int,segs:List[Segment])->Tuple[Optional[int],Optional[str],Optional[str]]:
    for seg in segs:
        if seg.vmaddr<=addr<seg.vmaddr+seg.filesize and seg.fileoff:
            fo=seg.fileoff+(addr-seg.vmaddr); secname=None
            for sec in seg.sections:
                if sec.addr<=addr<sec.addr+sec.size: secname=sec.name; break
            return fo,seg.name,secname
    for seg in segs:
        for sec in seg.sections:
            if sec.addr<=addr<sec.addr+sec.size and sec.offset:
                return sec.offset+(addr-sec.addr),sec.seg,sec.name
    return None,None,None

def bhex(data:bytes,off:Optional[int],n:int)->Optional[str]:
    if off is None or off<0 or off>=len(data): return None
    return data[off:off+n].hex(' ')

def decode_mc_param(name:str, section:Optional[str], first8:Optional[str]):
    if not name.startswith(MC_PARAM_PREFIXES): return {}
    if section and '__const' not in section: return {}
    if not first8: return {}
    clean=first8.replace(' ','').replace('0x','')
    if len(clean)<16: return {}
    try:
        value=int.from_bytes(bytes.fromhex(clean[:16]),'little')
    except Exception:
        return {}
    return {
        'mc_param': True,
        'mc_stable_id_hex': hx16(value),
        'mc_stable_id_normalized_hex': hx14(value & 0x00ffffffffffffff),
        'mc_low32_hex': f'0x{(value & 0xffffffff):08x}',
        'mc_high32_hex': f'0x{((value >> 32) & 0xffffffff):08x}',
    }

def parse_symbols(data:bytes,symtab,segs):
    out=[]
    if not symtab: return out
    symoff=symtab['symoff']; nsyms=symtab['nsyms']; stroff=symtab['stroff']; strend=stroff+symtab['strsize']
    for i in range(nsyms):
        off=symoff+i*16
        if off+16>len(data): break
        n_strx,n_type,n_sect,n_desc,n_value=struct.unpack_from('<IBBHQ',data,off)
        if not n_strx or stroff+n_strx>=strend: continue
        name=cstr(data[stroff+n_strx:strend])
        if not name: continue
        fileoff,seg,sec=vm_to_file(n_value,segs)
        first8=bhex(data,fileoff,8)
        rec={'index':i,'name':name,'vmaddr':hx(n_value),'fileoff':hx(fileoff),'segment':seg,'section':sec,'type':hex(n_type),'kind':'symbol','sect':n_sect,'desc':n_desc,'external':bool(n_type & 0x01),'private_extern':bool(n_type & 0x10),'first_8_bytes':first8,'first_16_bytes':bhex(data,fileoff,16)}
        rec.update(decode_mc_param(name, sec, first8))
        out.append(rec)
    return out

def sec_bytes(data:bytes,sec:Section)->bytes:
    return data[sec.offset:sec.offset+sec.size] if sec.offset and sec.size else b''

def strings_in_sec(data:bytes,sec:Section,min_len=2):
    raw=sec_bytes(data,sec); out=[]; start=0
    for i,ch in enumerate(raw+b'\0'):
        if ch==0:
            if i-start>=min_len:
                text=raw[start:i].decode('utf-8','replace')
                out.append({'string':text,'vmaddr':hx(sec.addr+start),'fileoff':hx(sec.offset+start),'segment':sec.seg,'section':sec.name})
            start=i+1
    return out

def objc_and_strings(data,segs):
    sections=[s for g in segs for s in g.sections]
    objc={}; strings={}; addrmap={}
    csec={'__objc_methname','__objc_classname','__objc_methtype','__cstring'}
    for sec in sections:
        key=f'{sec.seg},{sec.name}'
        if sec.name in csec:
            items=strings_in_sec(data,sec)
            for it in items: addrmap[int(it['vmaddr'],16)]=it['string']
            if sec.name.startswith('__objc'): objc[key]=items
            elif sec.name=='__cstring': strings[key]=items[:30000]
        elif sec.name.startswith('__objc_'):
            objc[key]=[{'segment':sec.seg,'section':sec.name,'vmaddr':hx(sec.addr),'fileoff':hx(sec.offset),'size':sec.size}]
    selrefs=[]
    for sec in sections:
        if sec.name!='__objc_selrefs': continue
        raw=sec_bytes(data,sec)
        for i in range(0,max(0,len(raw)-7),8):
            ptr=struct.unpack_from('<Q',raw,i)[0]
            selrefs.append({'selref_vmaddr':hx(sec.addr+i),'selref_fileoff':hx(sec.offset+i),'target_vmaddr':hx(ptr),'selector':addrmap.get(ptr),'resolved':ptr in addrmap})
    selectors=[]
    for k,v in objc.items():
        if k.endswith(',__objc_methname'): selectors+=v
    return objc,strings,{'selectors':selectors,'selrefs':selrefs}

def read_patterns(args_patterns,patterns_file):
    pats=[]
    if patterns_file and os.path.exists(patterns_file):
        pats += [l.strip() for l in open(patterns_file,encoding='utf-8',errors='replace') if l.strip() and not l.strip().startswith('#')]
    pats += [p for p in args_patterns if p]
    out=[]; seen=set()
    for p in pats:
        if p not in seen: out.append(p); seen.add(p)
    return out

def find_matches(patterns,symbols,selreport,strings,objc):
    out=[]
    for pat in patterns:
        for s in symbols:
            if pat in s['name']:
                m=dict(s); m.update({'pattern':pat,'text':s['name'],'confidence':'symbol-table'}); out.append(m)
        for item in selreport.get('selectors',[]):
            if pat in item.get('string',''):
                out.append({'pattern':pat,'kind':'objc_selector_string','text':item['string'],'vmaddr':item.get('vmaddr'),'fileoff':item.get('fileoff'),'segment':item.get('segment'),'section':item.get('section'),'confidence':'objc-methname'})
        for item in selreport.get('selrefs',[]):
            txt=item.get('selector') or ''
            if pat in txt:
                out.append({'pattern':pat,'kind':'objc_selref','text':txt,'selref_vmaddr':item.get('selref_vmaddr'),'selref_fileoff':item.get('selref_fileoff'),'target_vmaddr':item.get('target_vmaddr'),'confidence':'objc-selref'})
        for bucket in (strings,objc):
            for key,items in bucket.items():
                for item in items:
                    txt=item.get('string','')
                    if txt and pat in txt:
                        out.append({'pattern':pat,'kind':'string','text':txt,'vmaddr':item.get('vmaddr'),'fileoff':item.get('fileoff'),'segment_section':key,'confidence':'cstring-section'})
    return out

def write_json(path,obj):
    with open(path,'w',encoding='utf-8') as f: json.dump(obj,f,indent=2,ensure_ascii=False)

def write_md(path,binary,header,matches,patterns):
    with open(path,'w',encoding='utf-8') as f:
        f.write('# Target Matches\n\n')
        f.write(f'- Binary: `{binary}`\n- Architecture: `{header.get("arch")}`\n- Patterns: `{len(patterns)}`\n- Matches: `{len(matches)}`\n\n')
        if not matches:
            f.write('No target patterns matched in parsed symbol/selector/string data.\n'); return
        f.write('| Pattern | Kind | Text | VMAddr | FileOff | Stable ID | First 8 bytes | Confidence |\n|---|---|---|---:|---:|---:|---|---|\n')
        for m in matches:
            txt=str(m.get('text','')).replace('|','\\|')[:140]
            vm=m.get('vmaddr') or m.get('selref_vmaddr') or ''
            fo=m.get('fileoff') or m.get('selref_fileoff') or ''
            sid=m.get('mc_stable_id_hex') or ''
            f.write(f"| `{m.get('pattern','')}` | `{m.get('kind','')}` | `{txt}` | `{vm}` | `{fo}` | `{sid}` | `{m.get('first_8_bytes','') or ''}` | `{m.get('confidence','')}` |\n")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--binary',required=True)
    ap.add_argument('--out',required=True)
    ap.add_argument('--arch',default='arm64')
    ap.add_argument('--pattern',action='append',default=[])
    ap.add_argument('--patterns-file')
    a=ap.parse_args(); os.makedirs(a.out,exist_ok=True)
    raw=open(a.binary,'rb').read(); data,slice_info=choose_slice(raw,a.arch)
    header,segs,symtab=parse_macho(data,slice_info)
    symbols=parse_symbols(data,symtab,segs)
    objc,strings,selreport=objc_and_strings(data,segs)
    patterns=read_patterns(a.pattern,a.patterns_file)
    matches=find_matches(patterns,symbols,selreport,strings,objc)
    write_json(os.path.join(a.out,'01_macho_segments.json'),{'header':header,'segments':[{'name':g.name,'vmaddr':hx(g.vmaddr),'vmsize':hx(g.vmsize),'fileoff':hx(g.fileoff),'filesize':hx(g.filesize),'sections':[{'segment':s.seg,'section':s.name,'addr':hx(s.addr),'size':hx(s.size),'offset':hx(s.offset),'flags':hex(s.flags)} for s in g.sections]} for g in segs],'symtab':symtab})
    write_json(os.path.join(a.out,'02_symbols_exports_imports.json'),{'count':len(symbols),'symbols':symbols})
    write_json(os.path.join(a.out,'03_objc_sections.json'),objc)
    write_json(os.path.join(a.out,'05_selectors_selrefs.json'),selreport)
    write_json(os.path.join(a.out,'06_strings_by_section.json'),strings)
    write_json(os.path.join(a.out,'target_matches.json'),matches)
    write_md(os.path.join(a.out,'07_target_matches.md'),a.binary,header,matches,patterns)
    print(f'[radan] analyzed: {a.binary}')
    print(f'[radan] arch: {header.get("arch")} symbols={len(symbols)} selectors={len(selreport.get("selectors",[]))} selrefs={len(selreport.get("selrefs",[]))} matches={len(matches)} out={a.out}')
if __name__=='__main__': main()
