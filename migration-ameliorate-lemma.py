#!/usr/bin/env python3
"""
Ameliorate the lemma forms in migration-step1.json to create migration-step2.json
"""
import json
import sys

# When the lemma is a noun, place an acute accent in the third-from-last mora (if shorter than 3, at the initial mora)
# When it is a verb:
#   vowel-stem verbs such as "ata-lu" should be made into "áta-": strip the final "lu" and place the accent at the penultimate vowel
#   consonant-stem verbs such as "mogakug-u" should be made into "mogakúg-": strip the final "u" and place the accent at the ultimate vowel
#   "c-u" and "(a)c-u" should be "ć-" and "(á)c-".

VOWELS = 'aeiou'
ACCENT_MAP = {'a': 'á', 'e': 'é', 'i': 'í', 'o': 'ó', 'u': 'ú'}

def vowel_positions(s):
    """Return list of char indices where a vowel occurs in s."""
    return [i for i, c in enumerate(s) if c in VOWELS]

def accent_nth_vowel(s, vi):
    """Accent the vi-th vowel (0-indexed) in string s."""
    positions = vowel_positions(s)
    if not positions:
        return s
    idx = positions[vi]
    return s[:idx] + ACCENT_MAP[s[idx]] + s[idx + 1:]

def ameliorate_noun(base):
    """3rd-from-last vowel (or initial vowel if fewer than 3)."""
    positions = vowel_positions(base)
    n = len(positions)
    if n == 0:
        return base
    vi = max(0, n - 3)
    return accent_nth_vowel(base, vi)

def ameliorate_vowel_stem(stem):
    """Penultimate vowel of the stem (or the sole vowel if only one)."""
    positions = vowel_positions(stem)
    n = len(positions)
    if n == 0:
        return stem
    vi = max(0, n - 2)
    return accent_nth_vowel(stem, vi)

def ameliorate_consonant_stem(stem):
    """Ultimate (last) vowel of the stem."""
    positions = vowel_positions(stem)
    n = len(positions)
    if n == 0:
        return stem
    vi = n - 1
    return accent_nth_vowel(stem, vi)

PARTICLE_POS = {'noun particle', 'verb particle', 'sentence particle'}

def ameliorate_id(entry_id, pos, conj_class):
    """Return the accented lemma form for a single entry id."""
    # Split off the homophone suffix (#2, #3, …) — process the base only.
    if '#' in entry_id:
        base, homo = entry_id.rsplit('#', 1)
        homo = '#' + homo
    else:
        base, homo = entry_id, ''

    if conj_class == 'c-irregular':
        if base == 'c-u':
            return 'ć-' + homo
        elif base == '(a)c-u':
            return '(á)c-' + homo
        else:
            print(f"WARNING: unhandled c-irregular form: {base!r}", file=sys.stderr)
            return entry_id

    elif conj_class == 'vowel-stem':
        if not base.endswith('-lu'):
            print(f"WARNING: vowel-stem does not end in -lu: {base!r}", file=sys.stderr)
            return entry_id
        stem = base[:-3]          # strip '-lu'
        return ameliorate_vowel_stem(stem) + '-' + homo

    elif conj_class == 'consonant-stem':
        if not base.endswith('-u'):
            print(f"WARNING: consonant-stem does not end in -u: {base!r}", file=sys.stderr)
            return entry_id
        stem = base[:-2]          # strip '-u'
        return ameliorate_consonant_stem(stem) + '-' + homo

    elif pos in PARTICLE_POS:
        # Particles are not accented.
        return entry_id

    else:
        # Noun, prenominal — accent as a noun.
        return ameliorate_noun(base) + homo


def ameliorate_lemma(src):
    with open(src, encoding='utf-8') as f:
        data = json.load(f)

    for entry in data['entries']:
        old_id = entry['id']
        pos = entry.get('pos', '')
        conj_class = entry.get('conjugation_class')   # None for non-declinables
        new_id = ameliorate_id(old_id, pos, conj_class)
        entry['id'] = new_id
        if new_id == old_id:
            print(f"INFO: id unchanged: {old_id!r}", file=sys.stderr)

    return data


if __name__ == '__main__':
    src = 'migration-step1.json'
    result = ameliorate_lemma(src)
    print(json.dumps(result, ensure_ascii=False, indent=2))
