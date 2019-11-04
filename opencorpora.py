import lxml.etree as et
import re
import sys

parts_of_speech_opencorpora = {'POST': 'NI', 'NOUN': 'S', 'ADJF': 'A', 'ADJS': 'A', 'COMP': 'A', 'VERB': 'V',
                               'INFN': 'V', 'PRTF': 'V', 'PRTS': 'V', 'GRND': 'V', 'NUMR': 'NI', 'ADVB': 'ADV',
                               'NPRO': 'NI', 'PRED': 'NI', 'PREP': 'PR', 'CONJ': 'CONJ', 'PRCL': 'ADV',
                               'INTJ': 'ADV', 'Prnt': 'ADV'}

# read from xml with lxml

opencorpora_file = "files/dict.opcorpora.xml"


class DictionaryEntry:
    def __init__(self, text, original_form, part_of_speech):
        self.text = text
        self.original_form = original_form
        self.part_of_speech = part_of_speech

    def token(self, word=None):
        if word is None:
            word = self.text
        return word + "{" + f"{self.original_form}={self.part_of_speech}" + "}"


opencorpora_dictionary = {}

propositions = ['посереди', 'посреди', 'прежде', 'против', 'сверху', 'снизу', 'согласно', 'спереди', 'супротив', 'у',
                'благодаря', 'вблизи', 'вдоль', 'взамен', 'включая', 'вне', 'внутри', 'внутрь', 'во', 'возле', 'вокруг',
                'до', 'из', 'на', 'напротив', 'о', 'около', 'под', 'подле', 'подобно']
conjunctions = ['и', 'а', 'абы', 'али', 'будто', 'ведь', 'да', 'или', 'иначе', 'кабы', 'как', 'когда', 'но',
                'однако', 'отчего', 'пока', 'покуда', 'причем', 'хотя', 'хоть']

particles = ['аж', 'ан', 'всего', 'все-таки', 'даже', 'ж', 'же', 'ишь', 'ладно', 'ли', 'лишь', 'ль', 'мол', 'нет',
             'нешто', 'ни', 'пускай', 'пусть', 'разве', 'так', 'так-то', 'того', 'эк']
verb_on_hold = None


def get_special_token(word):
    lowercase_word = word.lower()
    if lowercase_word in propositions:
        return word + "{" + f"{lowercase_word}=PR" + "}"
    elif lowercase_word in conjunctions:
        return word + "{" + f"{lowercase_word}=CONJ" + "}"
    elif lowercase_word in particles:
        return word + "{" + f"{lowercase_word}=ADV" + "}"
    return None


def parse_xml():
    context = et.iterparse(opencorpora_file, tag='lemma')

    for (_, elem) in context:
        text = elem[0].attrib['t'].lower().replace('ё', 'е')
        part_of_speech = elem[0][0].attrib['v']
        if part_of_speech not in parts_of_speech_opencorpora:
            elem.clear()
            continue

        global verb_on_hold
        if part_of_speech == 'VERB':
            verb_on_hold = elem
            continue
        elif part_of_speech == 'INFN':
            if verb_on_hold is not None:
                part_of_speech = parts_of_speech_opencorpora[part_of_speech]
                if text not in opencorpora_dictionary:
                    opencorpora_dictionary[text] = DictionaryEntry(text, text, part_of_speech)
                for i in range(1, len(verb_on_hold)):
                    key = verb_on_hold[i].attrib['t'].replace('ё', 'е')
                    if key not in opencorpora_dictionary:
                        opencorpora_dictionary[key] = \
                            DictionaryEntry(key, text, part_of_speech)
                verb_on_hold.clear()
                verb_on_hold = None
                elem.clear()
                continue

        part_of_speech = parts_of_speech_opencorpora[part_of_speech]
        if text not in opencorpora_dictionary:
            opencorpora_dictionary[text] = DictionaryEntry(text, text, part_of_speech)
        for i in range(1, len(elem)):
            key = elem[i].attrib['t'].replace('ё', 'е')
            if key not in opencorpora_dictionary:
                opencorpora_dictionary[key] = DictionaryEntry(key, text, part_of_speech)

        elem.clear()


parse_xml()


def get_token(word):
    processed_word = word.replace('ё', 'е').lower()
    token = get_special_token(word)
    if token is None:
        if processed_word in opencorpora_dictionary:
            token = opencorpora_dictionary[processed_word].token(word)
        elif processed_word.startswith('не'):
            processed_word = processed_word[2:]
            if processed_word in opencorpora_dictionary:
                token = opencorpora_dictionary[processed_word].token(word)
    if token is None:
        token = word + "{" + f"{processed_word}=NI" + "}"
    return token


for line in sys.stdin:
    words = list(filter(lambda x: x and not x.isspace(), re.split("[.,?! ]", line)))
    for word in words:
        print(get_token(word.strip()), end=' ')
    print()
