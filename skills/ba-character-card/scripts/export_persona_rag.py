#!/usr/bin/env python3
"""Export persona RAG from normalized BA JSONL; standard library, no network."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re
import sys

LANGUAGES = {'zh_tw': '官方繁中（须由源数据核实）', 'zh_cn_community': '社区简中',
             'ja': '日文', 'ko': '韩文', 'en': '英文'}


def within(root, relative):
    path = Path(relative)
    if path.is_absolute():
        raise ValueError(f'Expected relative input path: {relative}')
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root):
        raise ValueError(f'Input escapes project root: {relative}')
    return resolved


def rows_at(path):
    rows = []
    with path.open(encoding='utf-8-sig') as stream:
        for number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict) or not isinstance(row.get('texts'), dict):
                raise ValueError(f'{path.name}:{number}: expected object with texts mapping')
            rows.append(row)
    return rows


def text_of(row, languages):
    for language in languages:
        text = row['texts'].get(language)
        if isinstance(text, str) and text.strip():
            # Keep choice tokens and all other script annotations visible.
            return text.replace('#n', ' / ').replace('\r', '').replace('\n', ' / ').strip(), language
    return '', ''


def has_choices(row):
    script = row.get('raw', {}).get('ScriptKr', '')
    return bool(re.search(r'(?m)^#s;', script)) or any(
        isinstance(text, str) and re.search(r'\[(?:ns|s)\d*\]', text)
        for text in row['texts'].values())


def speaker_of(row, cfg):
    if row.get(cfg.get('joint_flag', 'joint_speaking')):
        names = row.get('speaker_aliases') or []
        return '共同发言：' + ('／'.join(cfg.get('speaker_names', {}).get(n, n) for n in names)
                             or cfg['character_name'] + '与其他角色')
    if row.get(cfg.get('target_flag', 'character_speaking')):
        return cfg['character_name']
    if row.get('speaker'):
        return cfg.get('speaker_names', {}).get(row['speaker'], row['speaker'])
    if row.get('speaker_aliases'):
        return '／'.join(cfg.get('speaker_names', {}).get(n, n) for n in row['speaker_aliases'])
    if has_choices(row):
        return '老师回复／可选项（多选不视作同时发生）'
    return '旁白／未标注说话人'


def provenance(row, file_name):
    source = row.get('source') or {}
    details = [f'input={file_name}']
    for key in ('local_path', 'table', 'array_index', 'url'):
        if source.get(key) is not None:
            details.append(f'{key}={source[key]}')
    return '; '.join(details)


def blockify(prefix, items, limit):
    blocks, batch, size = [], [], 0
    for item in items:
        if batch and size + len(item) > limit:
            blocks.append(prefix + '\n' + '\n'.join(batch))
            # One preceding line provides context. Avoid carrying an oversized row.
            batch = batch[-1:] if len(batch[-1]) < limit // 2 else []
            size = sum(map(len, batch))
        batch.append(item)
        size += len(item)
    if batch:
        blocks.append(prefix + '\n' + '\n'.join(batch))
    return blocks


def export(root, cfg, out, overwrite=False):
    if not isinstance(cfg.get('character_name'), str) or not cfg['character_name'].strip():
        raise ValueError('character_name is required')
    if '\n' in cfg['character_name']:
        raise ValueError('character_name must be one line')
    languages = cfg.get('language_priority', ['zh_tw', 'zh_cn_community', 'ja'])
    if not languages or not all(isinstance(x, str) for x in languages):
        raise ValueError('language_priority must contain language keys')
    limit = cfg.get('chunk_chars', 1000)
    if type(limit) is not int or limit < 200:
        raise ValueError('chunk_chars must be an integer >= 200')
    flags = [cfg.get('target_flag', 'character_speaking'), cfg.get('joint_flag', 'joint_speaking')]
    input_paths = {key: within(root, cfg[key]) for key in ('context_file', 'dialogue_file', 'momo_file') if cfg.get(key)}
    if not input_paths:
        raise ValueError('At least one input file is required')
    outputs = [out / name for name in ('official_story.txt', 'daily_dialogues.txt', 'export_manifest.json')]
    if any(path in input_paths.values() for path in outputs):
        raise ValueError('Output would overwrite an input file')
    if not overwrite and any(path.exists() for path in outputs):
        raise ValueError('Output exists; choose a new directory or use --overwrite')
    story, daily, source_rows, matched_groups = [], [], {}, []
    stage_map = {str(k): str(v) for k, v in cfg.get('stages', {}).items()}
    if 'context_file' in input_paths:
        rows = rows_at(input_paths['context_file'])
        groups = collections.defaultdict(list)
        for row in rows:
            if 'group_id' not in row or type(row.get('order')) is not int:
                raise ValueError('Each context row requires group_id and integer order')
            if flags[0] not in row or type(row[flags[0]]) is not bool:
                raise ValueError(f'Each context row requires boolean target flag {flags[0]}')
            if flags[1] in row and type(row[flags[1]]) is not bool:
                raise ValueError(f'Joint flag {flags[1]} must be boolean when present')
            groups[row['group_id']].append(row)
        source_rows['context'] = len(rows)
        chosen = set(map(str, cfg['groups'])) if 'groups' in cfg else None
        for gid, group in groups.items():
            if chosen is not None and str(gid) not in chosen:
                continue
            group.sort(key=lambda row: row['order'])
            if len({r['order'] for r in group}) != len(group):
                raise ValueError(f'Duplicate order values in group {gid}; normalize partitions first')
            keep = {j for i, row in enumerate(group) if any(row.get(f) for f in flags)
                    for j in range(max(0, i-2), min(len(group), i+3))}
            if not keep:
                continue
            matched_groups.append(gid)
            prefix = (f"【{cfg['character_name']}原作语境】GroupId={gid}; "
                      f"阶段={stage_map.get(str(gid), '未标定，按具体场景核实')}; "
                      '保留其他说话人与分支，不把备选项视作连续经历。')
            run, previous = [], -2
            for i in sorted(keep):
                if i != previous+1 and run:
                    story.extend(blockify(prefix, run, limit)); run = []
                row = group[i]
                text, language = text_of(row, languages)
                if text:
                    run.append(f"[{speaker_of(row, cfg)} | {language} | order={row['order']} | "
                               f"branch={row.get('selection_group', 0)}] {text} "
                               f"〔{provenance(row, cfg['context_file'])}〕")
                previous = i
            story.extend(blockify(prefix, run, limit))
    if 'dialogue_file' in input_paths:
        rows = rows_at(input_paths['dialogue_file'])
        source_rows['dialogue'] = len(rows)
        groups = collections.defaultdict(list)
        categories = set(cfg.get('extra_categories', ['日常与节日语音']))
        for row in rows:
            if row.get('category') in categories:
                # Source adapter must already have selected the target character.
                groups[(row.get('variant', ''), row.get('cv_group') or row.get('id', ''))].append(row)
        for (variant, voice_group), group in groups.items():
            prefix = f"【{cfg['character_name']}日常语音】服装={variant}; 语音组={voice_group}; 依对应情景使用。"
            items = []
            for row in group:
                text, language = text_of(row, languages)
                if text:
                    items.append(f"[{speaker_of(row,cfg)} | {language} | {row.get('id','')}] {text} "
                                 f"〔{provenance(row,cfg['dialogue_file'])}〕")
            daily.extend(blockify(prefix, items, limit))
    if 'momo_file' in input_paths:
        rows = rows_at(input_paths['momo_file'])
        source_rows['momo'] = len(rows)
        groups = collections.defaultdict(list)
        for row in rows:
            groups[(row.get('variant',''), row.get('character_id',''))].append(row)
        for (variant, cid), group in groups.items():
            prefix = (f"【{cfg['character_name']}MomoTalk】服装={variant}; character_id={cid}; "
                      '以下保留消息跳转图，不假定这些消息都连续发生。')
            items = []
            for row in group:
                if any(key not in row for key in ('speaker', 'message_group_id', 'next_group_id')):
                    raise ValueError('MomoTalk rows require speaker, message_group_id and next_group_id')
                text, language = text_of(row, languages)
                if text:
                    items.append(f"[{speaker_of(row,cfg)} | {language} | {row.get('id',row.get('message_id',''))} | "
                                 f"group={row['message_group_id']} -> next={row['next_group_id']}] {text} "
                                 f"〔{provenance(row,cfg['momo_file'])}〕")
            daily.extend(blockify(prefix, items, limit))
    if not story and not daily:
        raise ValueError('No text matched; check flags, categories, languages and selected groups')
    payloads = {'official_story.txt': '\n\n'.join(story), 'daily_dialogues.txt': '\n\n'.join(daily)}
    out.mkdir(parents=True, exist_ok=True)
    manifest = {'character_name': cfg['character_name'], 'source_rows': source_rows,
                'matched_context_groups': matched_groups, 'language_labels': LANGUAGES,
                'language_priority': languages, 'files': [],
                'notes': 'Local export only, not proof of live RAG activation. Single long source lines may exceed chunk_chars.'}
    for name, text in payloads.items():
        data = (text + ('\n' if text else '')).encode('utf-8')
        (out/name).write_bytes(data)
        manifest['files'].append({'local_path': name, 'bytes': len(data),
                                  'sha256': hashlib.sha256(data).hexdigest(),
                                  'blocks': len([x for x in text.split('\n\n') if x.strip()])})
    (out/'export_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args()
    try:
        cfg = json.loads(args.config.read_text(encoding='utf-8-sig'))
        result = export(args.root.resolve(), cfg, args.out.resolve(), args.overwrite)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f'Export failed: {exc}', file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
