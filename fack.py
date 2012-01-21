import cPickle as pickle
import os
import re
import subprocess
import sys


Verbose = True


def build_file_index(fn):
    if Verbose:
        print "Indexing", fn
    index = {}
    with open(fn) as f:
        for s in f:
            for m in re.finditer(r"\w+", s):
                word = m.group(0)
                if word not in index:
                    index[word] = set()
                index[word].add(fn)
    return index


def read_catalog():
    try:
        with open("fack.index", "rb") as f:
            return pickle.load(f)
    except IOError:
        return {
            "files": {},
            "index": {},
        }


def write_catalog(catalog):
    with open("fack.index", "wb") as f:
        pickle.dump(catalog, f, protocol=pickle.HIGHEST_PROTOCOL)
    #import json
    #with open("fack.json", "w") as f:
    #    json.dump(catalog, f, indent=2)


def update_index(index, fn, file_index):
    for k, v in index.items():
        v.discard(fn)
    for k, v in file_index.items():
        if k not in index:
            index[k] = set()
        index[k] |= v


def main():
    target = sys.argv[1]
    files = sys.argv[2:]

    if not files:
        files = subprocess.check_output(["ack", "-f"]).strip().split("\n")

    catalog = read_catalog()

    changed = False
    for fn in files:
        mtime = os.stat(fn).st_mtime
        if fn not in catalog["files"] or catalog["files"][fn] < mtime:
            update_index(catalog["index"], fn, build_file_index(fn))
            catalog["files"][fn] = mtime
            changed = True

    if changed:
        write_catalog(catalog)

    if target not in catalog["index"]:
        sys.exit(0)

    print catalog["index"][target]
    print files
    matching_files = catalog["index"][target].intersection(files)
    if not matching_files:
        sys.exit(0)
    print matching_files
    subprocess.call(["ack", "--with-filename", target] + list(matching_files))


if __name__ == "__main__":
    main()
