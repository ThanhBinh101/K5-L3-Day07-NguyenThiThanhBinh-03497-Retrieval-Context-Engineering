"""Import Day 6 without writing to it; consistent SQLite backup of its vector index."""
import json
import logging
import shutil
import sqlite3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.common import DAY6, ROOT, PRIVATE, read_json, read_jsonl, write_json, sha, now
from pypdf import PdfReader

logging.getLogger('pypdf').setLevel(logging.ERROR)

def main():
    PRIVATE.mkdir(parents=True, exist_ok=True)
    for filename in ['entries.jsonl', 'chunks_B.jsonl', 'pages.jsonl']:
        shutil.copy2(DAY6/'data/processed'/filename, PRIVATE/filename)
    for filename in ['manifest.json']:
        shutil.copy2(DAY6/'data'/filename, PRIVATE/filename)
    shutil.copy2(DAY6/'data/raw/KANJI N2.pdf', PRIVATE/'source.pdf')
    shutil.copy2(DAY6/'data/handwriting/templates.json', PRIVATE/'templates.json')
    shutil.copy2(DAY6/'artifacts/model_snapshot.json', ROOT/'configs/embedding.json')
    # Keep the independent index stable after first import; do not reset it at server startup.
    target=ROOT/'.local/qdrant'
    if not (target/'meta.json').exists():
        target.mkdir(parents=True, exist_ok=True)
        meta=read_json(DAY6/'.local/qdrant/meta.json')
        meta['collections']={k:v for k,v in meta['collections'].items() if k=='kanji_B'}
        write_json(target/'meta.json',meta)
        dst=target/'collection/kanji_B/storage.sqlite';dst.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(f'file:{DAY6}/.local/qdrant/collection/kanji_B/storage.sqlite?mode=ro',uri=True) as src:
            with sqlite3.connect(dst) as out: src.backup(out)
    entries=read_jsonl(PRIVATE/'entries.jsonl')
    by_page={e['page']:e for e in entries}
    reader=PdfReader(PRIVATE/'source.pdf')
    images=PRIVATE/'images';images.mkdir(exist_ok=True)
    inventory=[]
    for n,p in enumerate(reader.pages,1):
        row={'page':n,'width':float(p.mediabox.width),'height':float(p.mediabox.height),'images':[],
             'text_indexed':True,'kind':'kanji_entry' if n in by_page else 'frontmatter_or_lesson_overview'}
        for i,img in enumerate(p.images):
            name=f'p{n:03}-{i}{Path(img.name).suffix}'
            (images/name).write_bytes(img.data)
            row['images'].append({'file':name,'region':'embedded image; original page available',
                'description_source':'Day 6 author-provided mnemonic, not a vision-generated observation',
                'caption':by_page.get(n,{}).get('mnemonic','')})
        if n in by_page:
            # Template coordinates as fractions of page: checked against rendered page 4.
            row['regions']={'illustration':[.39,.07,.95,.39],'table':[.06,.69,.94,.90],
                            'readings':[.05,.07,.38,.39],'mnemonic':[.06,.40,.94,.49]}
        inventory.append(row)
    write_json(PRIVATE/'inventory.json',inventory)
    manifest=read_json(PRIVATE/'manifest.json')
    write_json(ROOT/'results/data_audit.json',{
        'created_at':now(),'source_sha256':sha(PRIVATE/'source.pdf'),'physical_pages':len(reader.pages),
        'kanji_entries':len(entries),'indexed_text_pages':len(read_jsonl(PRIVATE/'pages.jsonl')),
        'vocabulary_rows':sum(len(e['vocabulary']) for e in entries),
        'pages_with_embedded_images':sum(bool(p['images']) for p in inventory),
        'image_count':sum(len(p['images']) for p in inventory),
        'embedding':read_json(ROOT/'configs/embedding.json'),'vector_store':'independent SQLite backup of Day 6 Qdrant kanji_B',
        'permissions':manifest['license_or_permission'],
        'bonus_status':'pending visual audit of charts; illustrations and vocabulary tables present',
        'image_extraction_failures':[]})
    print('Imported',len(entries),'Kanji;',sum(len(p['images']) for p in inventory),'images')

if __name__=='__main__':main()
