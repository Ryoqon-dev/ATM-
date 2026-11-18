from pathlib import Path
import olefile, struct, zlib, json

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '.artifacts' / 'analysis' / '원문분석'
OUT.mkdir(parents=True, exist_ok=True)
source = next((ROOT / '.artifacts' / 'originals').glob('*.hwp'))
ole = olefile.OleFileIO(source)
print('Streams:', ole.listdir())
header = ole.openstream('FileHeader').read()
compressed = bool(struct.unpack_from('<I', header, 36)[0] & 1)
text=[]
for stream in ole.listdir():
    if stream[0] == 'BodyText':
        data=ole.openstream(stream).read()
        if compressed: data=zlib.decompress(data,-15)
        pos=0
        while pos+4<=len(data):
            value=struct.unpack_from('<I', data,pos)[0]; pos+=4
            tag=value&1023; level=(value>>10)&1023; size=value>>20
            if size==4095: size=struct.unpack_from('<I',data,pos)[0];pos+=4
            record=data[pos:pos+size];pos+=size
            if tag==67:
                units=list(struct.unpack('<'+'H'*(len(record)//2),record))
                clean=[];i=0
                while i<len(units):
                    c=units[i]
                    if c in (1,2,3,11,12,14,15,16,17,18,21,22,23): i+=8;continue
                    if c==9: clean.append(32);i+=8;continue
                    if c in (10,13): clean.append(10)
                    elif c>=32: clean.append(c)
                    i+=1
                s=struct.pack('<'+'H'*len(clean),*clean).decode('utf-16-le',errors='replace').strip()
                if s:text.append(s)
    if stream[0] == 'BinData':
        data=ole.openstream(stream).read()
        try:data=zlib.decompress(data,-15)
        except zlib.error:pass
        (OUT / stream[-1]).write_bytes(data)
(OUT/'원문.txt').write_text('\n'.join(text),encoding='utf-8')
print('\n'.join(text))
