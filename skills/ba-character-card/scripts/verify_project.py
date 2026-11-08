#!/usr/bin/env python3
"""Verify local source manifests, JSONL and ZIP integrity without changing inputs."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile


def within(root, value):
    path = Path(value)
    if path.is_absolute():
        raise ValueError(f'Expected relative path: {value}')
    result = (root/path).resolve()
    if not result.is_relative_to(root):
        raise ValueError(f'Path escapes project: {value}')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--manifest', action='append', default=[])
    parser.add_argument('--jsonl', action='append', default=[])
    parser.add_argument('--zip', action='append', default=[])
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    if not any((args.manifest, args.jsonl, args.zip)):
        parser.error('Supply at least one --manifest, --jsonl or --zip')
    root = args.root.resolve()
    results, input_paths = [], set()
    def record(kind, path, action):
        try:
            resolved = within(root, path)
            input_paths.add(resolved)
            extra = action(resolved)
            results.append({'kind':kind, 'path':path, 'ok':True, **(extra or {})})
        except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile, RuntimeError) as exc:
            results.append({'kind':kind, 'path':path, 'ok':False, 'error':str(exc)})
    def check_file(path, row):
        data = path.read_bytes()
        if type(row.get('bytes')) is not int or len(data) != row['bytes']:
            raise ValueError('Size missing or mismatched')
        actual = hashlib.sha256(data).hexdigest()
        if not isinstance(row.get('sha256'), str) or actual != row['sha256'].lower():
            raise ValueError('SHA256 missing or mismatched')
        return {'bytes':len(data), 'sha256':actual}
    for name in args.manifest:
        try:
            path = within(root, name); input_paths.add(path)
            data = json.loads(path.read_text(encoding='utf-8-sig'))
            rows = data['files']
            if not isinstance(rows, list) or not rows:
                raise ValueError('Manifest files must be a nonempty list')
            results.append({'kind':'manifest', 'path':name, 'ok':True, 'entries':len(rows)})
            for row in rows:
                if not isinstance(row, dict) or not isinstance(row.get('local_path'), str):
                    raise ValueError('Each manifest entry needs local_path')
                record('source', row['local_path'], lambda p, r=row:check_file(p,r))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            results.append({'kind':'manifest', 'path':name, 'ok':False, 'error':str(exc)})
    def check_jsonl(path):
        count = 0
        with path.open(encoding='utf-8-sig') as stream:
            for number, line in enumerate(stream,1):
                if not line.strip():continue
                try:json.loads(line)
                except ValueError as exc:raise ValueError(f'line {number}: {exc}') from exc
                count += 1
        if not count:raise ValueError('Empty JSONL')
        return {'records':count}
    def check_zip(path):
        with zipfile.ZipFile(path) as archive:
            bad = archive.testzip()
            if bad:raise ValueError(f'CRC failed: {bad}')
            return {'members':len(archive.namelist())}
    for name in args.jsonl:record('jsonl',name,check_jsonl)
    for name in args.zip:record('zip',name,check_zip)
    report = {'ok':all(row['ok'] for row in results),'checks':results}
    text = json.dumps(report,ensure_ascii=False,indent=2)+'\n'
    if args.report:
        dest = args.report.resolve()
        if dest in input_paths:
            print('Report path would overwrite an input',file=sys.stderr);return 1
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(text,encoding='utf-8')
    print(text,end='')
    return 0 if report['ok'] else 1

if __name__ == '__main__':
    sys.exit(main())
