import os
import re

import lxml.etree as et
from nltk.tokenize import RegexpTokenizer

opencorpora_file = "files/dict.opcorpora.xml"
names = set()
organizations = set()
locations = set()
regular_words = set()

organizations_full = []
organizations_train = set()

collection_directory = "files/Collection3"
dialogue_directory = "files/testset"

organizations_file = "files/organizations.txt"
train_sentences_enhanced_file = "files/train_sentences_enhanced.txt"

quotes = ["\"", "\'", "«", "»", "“", "„"]
organization_types = ["фонд", "организация", "компания", "предприятие", "ооо", "зао", "оао", "компаний", "концерн",
                      "центр", "издательство", "партия"]


def parse_orglist():
    with open(organizations_file) as f:
        for line in f.readlines():
            organizations.add(line.strip().lower().replace('ё', 'е'))


def parse_train_sentences_enhanced():
    person_regexp = r"\w+{PERSON}"
    org_regexp = r"\w+{ORG}"
    with open(train_sentences_enhanced_file) as f:
        for line in f.readlines():
            res = re.findall(person_regexp, line)
            for r in res:
                names.add(r[:r.find("{")].lower().replace('ё', 'е'))
            res = re.findall(org_regexp, line)
            for r in res:
                organizations_train.add(r[:r.find("{")].lower().replace('ё', 'е'))


def parse_dialogue_testset():
    for filename in os.listdir(dialogue_directory):
        if filename[-7:] == "objects":
            with open(dialogue_directory + os.sep + filename) as f:
                for line in f.readlines():
                    if 'Person' in line:
                        names.add(line[line.rfind('#') + 1:].strip().lower().replace('ё', 'е'))
                    elif 'Location' in line:
                        locations.add(line[line.rfind('#') + 1:].strip().lower().replace('ё', 'е'))
                    elif 'LocOrg' in line or 'Org' in line:
                        organizations.add(line[line.rfind('#') + 1:].strip().lower().replace('ё', 'е'))


def parse_collection():
    for filename in os.listdir(collection_directory):
        if filename[-3:] == "ann":
            with open(collection_directory + os.sep + filename) as f:
                for line in f.readlines():
                    if '\tLOC' in line:
                        last_tab = line.rfind('\t')
                        locations.add(line[last_tab + 1:].strip().lower().replace('ё', 'е'))
                    elif '\tPER' in line:
                        last_tab = line.rfind('\t')
                        names.add(line[last_tab + 1:].strip().lower().replace('ё', 'е'))
                    elif '\tORG' in line:
                        last_tab = line.rfind('\t')
                        organizations.add(line[last_tab + 1:].strip().lower().replace('ё', 'е'))


def parse_xml_opencorpora():
    context = et.iterparse(opencorpora_file, tag='lemma')

    for (_, elem) in context:
        text = elem[0].attrib['t'].lower().replace('ё', 'е')
        if len(elem[0]) > 3 and (elem[0][3].attrib['v'] == 'Name' or elem[0][3].attrib['v'] == 'Surn' or
                                 elem[0][3].attrib['v'] == 'Patr'):
            names.add(text)
            for i in range(1, len(elem)):
                key = elem[i].attrib['t'].replace('ё', 'е')
                names.add(key)
        elif len(elem[0]) > 3 and (elem[0][3].attrib['v'] == 'Orgn' or elem[0][3].attrib['v'] == 'Abbr' or
                                   elem[0][3].attrib['v'] == 'Trad'):
            organizations.add(text)
            for i in range(1, len(elem)):
                key = elem[i].attrib['t'].replace('ё', 'е')
                organizations.add(key)
        elif len(elem[0]) > 3 and elem[0][3].attrib['v'] == 'Geox':
            locations.add(text)
            for i in range(1, len(elem)):
                key = elem[i].attrib['t'].replace('ё', 'е')
                locations.add(key)
        else:
            regular_words.add(text)
            for i in range(1, len(elem)):
                key = elem[i].attrib['t'].replace('ё', 'е')
                regular_words.add(key)

        elem.clear()


def parse_xml_names(filename, tag):
    result = []
    context = et.iterparse(filename, tag=tag, recover=True)

    for (_, elem) in context:
        result.append(elem.text)
        elem.clear()

    return result


with open("files/dataset_40163_1.txt") as f:
    sentences = f.readlines()

russian_names = parse_xml_names("files/russian_names.xml", "Name")
russian_surnames = parse_xml_names("files/russian_surnames.xml", "Surname")
foreign_names = parse_xml_names("files/foreign_names.xml", "name")

parse_collection()
parse_dialogue_testset()
parse_orglist()
parse_train_sentences_enhanced()

parse_xml_opencorpora()


def is_person(word, start=False):
    word = word.lower().replace('ё', 'е')
    return word in russian_names or word in russian_surnames or word in names or \
           not start and any(word in person.split() for person in names) \
           or word[:-1] in names or \
           not start and any(word[:-1] in person.split() for person in names)


def is_organization(word, start=False):
    word = word.lower().replace('ё', 'е')
    return word in organizations or word in organizations_train or not start and any(org.find(word) != -1 for org in organizations) or \
           not start and any(word in org.split() for org in organizations) or word[:-1] in organizations or \
           not start and any(word[:-1] in org.split() for org in organizations)


def is_location(word):
    word = word.lower().replace('ё', 'е')
    return word in locations or any(word in loc.split() for loc in locations)


def is_included(lst, entry):
    counted = False
    for r in lst:
        counted = r[0] <= entry[1][0] and r[0] + r[1] >= entry[1][1]
        if counted:
            break
    return counted


exceptions = ["Россия", "Украины", "Украина"]

organizations = set(w for w in organizations if len(w) > 3)

for sentence in sentences:
    results = []

    for org in organizations:
        idx = sentence.lower().find(org.lower())
        if idx == 0 or idx > 0 and (sentence[idx - 1] == " " or sentence[idx - 1] in quotes):
            words = org.split()
            offset = 0
            for word in words:
                results.append((idx + offset, len(word), "ORG"))
                offset += len(word) + 1

    tokenizer = RegexpTokenizer(r'(«[^»]+»)|(„[^“]+“)|(\"[^\"]+\")|(\'[^\']+\')|([«„\"\'\w-]+)|([\w»“\"\'-]+)')
    tokens = [(sentence[token[0]:token[1]].strip(), token) for token in tokenizer.span_tokenize(sentence)]
    potential_names = list(filter(lambda entry: entry[0][0].isupper() and re.search(r"[a-zA-Z]", entry[0]) is None,
                                  tokens))
    for name in potential_names:
        if name[0] in exceptions or name[1][0] == 0 and name[0].lower().replace('ё', 'е') in regular_words:
            continue
        if is_person(name[0]) and not is_included(results, name):
            results.append((name[1][0], len(name[0]), "PERSON"))
        elif is_location(name[0]):
            continue
        elif is_organization(name[0], start=(name[1][0] == 0)) and not is_included(results, name):
            idx = tokens.index(name)
            if idx > 0 and tokens[idx - 1][0] in organization_types:
                results.append((tokens[idx - 1][1][0], len(tokens[idx - 1][0]), "ORG"))
            results.append((name[1][0], len(name[0]), "ORG"))
        elif not sentence[name[1][0] - 1] in quotes:  # last resort
            results.append((name[1][0], len(name[0]), "PERSON"))

    potential_organizations = list(filter(lambda entry: any(quote in entry[0] for quote in quotes), tokens))
    for organization in potential_organizations:
        if organization[0][0] in quotes and organization[0][-1] not in quotes or \
                organization[0][-1] in quotes and organization[0][0] not in quotes:
            continue
        # is this direct speech? if so, not an organization
        prefix = sentence[:organization[1][0]]
        # if it's this long, it's probably direct speech
        if len(organization[0].split()) > 3:
            continue
        if re.search(r":\s*$", prefix) is not None and (
                '!' in organization[0] or '?' in organization[0] or sentence[organization[1][1]] == "."):
            continue
        organization_name = organization[0].strip("".join(quotes))
        if ' ' in organization_name:
            offset = 1
            words = organization_name.split()
            if words[0][0].isupper():
                for word in words:
                    # most likely only one quotation mark
                    results.append((organization[1][0] + offset, len(word), "ORG"))
                    # most likely only one space symbol
                    offset += len(word) + 1
        else:
            results.append((organization[1][0] + 1, len(organization[0]), "ORG"))
    
    potential_organizations = list(
        filter(lambda entry: re.search("[a-zA-Z]", entry[0]) is not None and entry[0][0].isupper() and entry[1][0] > 0,
               tokens))
    for organization in potential_organizations:
        # already done with the quotes
        if any(quote in organization[0] for quote in quotes) or is_included(results, organization):
            continue
    for entry in results:
        print(f"{entry[0]} {entry[1]} {entry[2]}", end=" ")
    print("EOL")
