import sys
import os
import time
import random
import json
import argparse
from typing import Dict, Tuple, Optional

import requests
from bs4 import BeautifulSoup
import genanki

# TODO: Make original focus to translate from en to other languages.
# TODO: Add the glpys to the note output.

# https://www.50languages.com/em/learn/phrasebook-lessons/162/bn
LESSON_LINK = "https://www.50languages.com/{src}/learn/phrasebook-lessons/{lesson}/{dest}"
SOUND_LINK = "https://www.book2.nl/book2/{lang}/SOUND/{sound_id}.mp3"

CSS = """\
.card {
  font-family: arial;
  font-size: 20px;
  text-align: center;
  color: black;
  background-color: white;
}
"""

CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")
AUDIO_DIR = os.path.join(CACHE_DIR, "audio")
SENTENCES_DIR = os.path.join(CACHE_DIR, "sentences")
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(SENTENCES_DIR, exist_ok=True)

LESSON_MAP = {
    1: "People",
    2: "Family Members",
    3: "Getting to Know Others",
    4: "At School",
    5: "Countries and Languages",
    6: "Reading and Writing",
    7: "Numbers",
    8: "The Time",
    9: "Days of the Week",
    10: "Yesterday-Today-Tomorrow",
    11: "Months",
    12: "Beverages",
    13: "Activities",
    14: "Colors",
    15: "Fruits and Food",
    16: "Seasons and Weather",
    17: "Around the House",
    18: "House Cleaning",
    19: "In the Kitchen",
    20: "Small Talk 1",
    21: "Small Talk 2",
    22: "Small Talk 3",
    23: "Learning Foriegn Languages",
    24: "Appointment",
    25: "In the City",
    26: "In Nature",
    27: "In the Hotel - Arrival",
    28: "In the Hotel - Complaints",
    29: "At the Restaurant 1",
    30: "At the Restaurant 2",
    31: "At the Restaurant 3",
    32: "At the Restaurant 4",
    33: "At the Train Station",
    34: "On the Train",
    35: "At the Airport",
    36: "Public Transportation",
    37: "En Route",
    38: "In the Taxi",
    39: "Car Breakdown",
    40: "Asking for Directions",
    41: "Where is ...?",
    42: "City Tour",
    43: "At the Zoo",
    44: "Going Out in the Evening",
    45: "At the Cinema",
    46: "In the Discotheque",
    47: "Preparing a Trip",
    48: "Vacation Activities",
    49: "Sports",
    50: "In the Swimming Pool",
    51: "Running Errands",
    52: "In the Department Store",
    53: "Shops",
    54: "Shopping",
    55: "Working",
    56: "Feelings",
    57: "At the Doctor",
    58: "Parts of the Body",
    59: "At the Post Office",
    60: "At the Bank",
    61: "Ordinal Numbers",
    62: "Asking Questions 1",
    63: "Asking Questions 2",
    64: "Negation 1",
    65: "Negation 2",
    66: "Possessive Pronouns 1",
    67: "Possessive Pronouns 2",
    68: "Big-Small",
    69: "To Need or Want To",
    70: "To Like Something",
    71: "To Want Something",
    72: "To Have to Do Something/Must",
    73: "To Be Allowed To",
    74: "Asking for Something",
    75: "Giving Reasons 1",
    76: "Giving Reasons 2",
    77: "Giving Reasons 3",
    78: "Ajectives 1",
    79: "Ajectives 2",
    80: "Ajectives 3",
    81: "Past Tense 1",
    82: "Past Tense 2",
    83: "Past Tense 3",
    84: "Past Tense 4",
    85: "Questions-Past Tense 1",
    86: "Questions-Past Tense 2",
    87: "Past Tense of Modal Verbs 1",
    88: "Past Tense of Modal Verbs 2",
    89: "Imperative 1",
    90: "Imperative 2",
    91: "Subordinate Clauses: That 1",
    92: "Subordinate Clauses: That 2",
    93: "Subordinate Clauses: If",
    94: "Conjunctions 1",
    95: "Conjunctions 2",
    96: "Conjunctions 3",
    97: "Conjunctions",
    98: "Double Connectors",
    99: "Genitive",
    100: "Adverbs"
}

def sentences_file_for_lang(lang: str) -> str:
    return os.path.join(SENTENCES_DIR, f"{lang}.json")


def create_sentences_file(lang: str) -> str:
    path = sentences_file_for_lang(lang)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write("{}\n")
    return path


def get_cached_sentences(lang: str) -> Dict:
    path = create_sentences_file(lang)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_cached_lesson_sentences(src: str, dest: str, lesson_id: str) -> Tuple:
    sentences_1 = get_cached_sentences(src).get(lesson_id, {})
    sentences_2 = get_cached_sentences(dest).get(lesson_id, {})
    return sentences_1, sentences_2


def cache_lesson_sentences(lang: str, lesson_id: str, sentences: Dict):
    path = sentences_file_for_lang(lang)
    cached = get_cached_sentences(lang)
    cached[lesson_id] = sentences
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cached, f, ensure_ascii=False)


def download_audio(session: requests.Session, lang: str, sound_id: str) -> str:
    link = SOUND_LINK.format(sound_id=sound_id, lang=lang)
    filename = f"{lang}_{sound_id}.mp3"
    path = os.path.join(AUDIO_DIR, filename)
    if os.path.exists(path):
        return filename
    with session.get(link) as res:
        with open(path, "wb") as f:
            f.write(res.content)

    return filename


def random_id() -> int:
    return random.randrange(1 << 30, 1 << 31)


def get_model(src: str, dest: str, model_id: Optional[int] = None) -> genanki.Model:
    # TODO: Format this to match some of your existing audio cards that you like. I think this is the audio recoginition that is below.
    return genanki.Model(
        model_id if model_id is not None else random_id(),
        f"50Languages {src}-{dest}",
        fields=[
            {"name": src},
            {"name": dest},
            {"name": f"{dest}_audio"},
            {"name": "Reference"},
        ],
        templates=[
            {
                "name": f"{dest}-{src}",
                "qfmt": "{{" + dest + "}}\n<br>\n" + "{{" + f"{dest}_audio" + "}}",
                "afmt": "{{FrontSide}}\n<hr id=answer>\n"
                + "{{"
                + src
                + "}}"
                + "\n<br><br>\n"
                + "{{Reference}}",
            },
            {
                "name": f"{src}-{dest}",
                "qfmt": "{{" + src + "}}\n<br>",
                "afmt": "{{FrontSide}}\n<hr id=answer>\n"
                + "{{"
                + dest
                + "}}\n<br>\n"
                + "{{"
                + f"{dest}_audio"
                + "}}"
                + "\n<br><br>\n"
                + "{{Reference}}",
            },
            # TODO: add audio recognition card type?
            # {
            #     "name": f"{dest} audio",
            #     "qfmt": "{{" + f"{dest}_audio" + "}}",
            #     "afmt": "{{FrontSide}}\n<hr id=answer>\n" + "{{" + dest + "}}",
            # },
        ],
        css=CSS,
    )


def add_note(
    model: genanki.Model,
    deck: genanki.Deck,
    src: str,
    dest: str,
    sound_id: str,
    src_sentence: str,
    dest_sentence: str,
    filename2: str,
    lesson_link_html: str,
    note_tags: list,
):
    note = genanki.Note(
        model=model,
        fields=[
            src_sentence,
            dest_sentence,
            f"[sound:{filename2}]",
            lesson_link_html,
        ],
        tags=note_tags,
        guid=genanki.guid_for(src, dest, sound_id),
        due=len(deck.notes),
    )
    deck.add_note(note)


def generate_deck(
    src: str,
    dest: str,
    start: int = 1,
    end: int = 100,
    model_id: Optional[int] = None,
    outfile: Optional[str] = None,
):
    """
    Download sentences from lesson number `start` to number `end` in `dest` and
    their translations in `src` with audio files in `src`
    and create a deck package named "50Languages_{src}-{dest}_{start}-{end}.apkg" in the current
    working directory.
    """
    deck_package_name = (
        f"50Languages_{src}-{dest}_{start}-{end}.apkg" if not outfile else outfile
    )
    print(f"Generating {deck_package_name}...")
    model = get_model(src, dest, model_id)
    deck = genanki.Deck(
        random_id(),
        f"50Languages {src}-{dest}",
        description="""50Languages's content is licensed under the Creative Commons Attribution-NonCommercial-NoDerivatives 3.0 license (CC BY-NC-ND 3.0). See <a href="https://www.50languages.com/licence.php">https://www.50languages.com/licence.php</a>""",
    )
    media_files = []
    session = requests.Session()
    i = start
    while i <= end:
        sys.stdout.write(f"\rFetching lesson {i}...")
        sys.stdout.flush()
        page_number = i+162    
        lesson_link = LESSON_LINK.format(src=src, dest=dest, lesson=page_number)
        lesson_link_html = f'<a href="{lesson_link}">{lesson_link}</a>'
        sentences_1, sentences_2 = get_cached_lesson_sentences(src, dest, str(i))
        lesson_tag = LESSON_MAP.get(i).replace(" ", "-")
        note_tags = [f"{src}-to-{dest}", lesson_tag]
        if sentences_1 and sentences_2:
            for sound_id, src_sentence in sentences_1.items():
                dest_sentence = sentences_2[sound_id]
                filename2 = download_audio(session, dest, sound_id)
                media_files.append(os.path.join(AUDIO_DIR, filename2))
                add_note(
                    model,
                    deck,
                    src,
                    dest,
                    sound_id,
                    src_sentence,
                    dest_sentence,
                    filename2,
                    lesson_link_html,
                    note_tags,
                )
        else:
            sentences_1 = {}
            sentences_2 = {}
            # FIXME: handle exceptions?
            try:
                with session.get(lesson_link) as res:
                    soup = BeautifulSoup(res.content, "html.parser")
                    sentence_entries = soup.select(".table tr")
                    for entry in sentence_entries:
                        cols = entry.select("td")
                        src_sentence = cols[0].get_text().strip()
                        print(f"\n{src_sentence}")
                        if not src_sentence:
                            continue
                        # grab the glyphs
                        # dest_sentence = str(cols[1].select("a")[1].contents[0])
                        dest_sentence = str(cols[1].select("a")[3].contents[0]) # Get the english spelling of this.
                        print(f"Language to Learn Sentence: {dest_sentence}")
                        # sound_id = cols[2].select_one("[offset_text]")["offset_text"]
                        sound_id = cols[2].select("audio")[-1].contents[1]
                        sound_id_str = str(sound_id)
                        url_start_idx = sound_id_str.find('"')
                        partial_str = sound_id_str[url_start_idx+1:]
                        sound_id_str = partial_str[0:partial_str.find('"')]
                        sound_id_str = sound_id_str.split("/")[-1].replace(".mp3","")
                        print("sound_id: " + str(sound_id_str))
                        sound_id = sound_id_str
                        filename2 = download_audio(session, dest, sound_id)
                        media_files.append(os.path.join(AUDIO_DIR, filename2))
                        add_note(
                            model,
                            deck,
                            src,
                            dest,
                            sound_id,
                            src_sentence,
                            dest_sentence,
                            filename2,
                            lesson_link_html,
                            note_tags,
                        )
                        sentences_1[sound_id] = src_sentence
                        sentences_2[sound_id] = dest_sentence

            except ConnectionResetError:
                # FIXME: should we catch more exceptions here?
                time.sleep(15)
                continue
            cache_lesson_sentences(src, str(i), sentences_1)
            cache_lesson_sentences(dest, str(i), sentences_2)
            time.sleep(random.randrange(3, 5))
        i += 1

    package = genanki.Package(deck)
    package.media_files = media_files
    package.write_to_file(deck_package_name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--src",
        help="Code of source language",
        metavar="LANG_CODE",
        required=True,
    )
    parser.add_argument(
        "--dest",
        help="Code of destination language",
        metavar="LANG_CODE",
        required=True,
    )
    parser.add_argument(
        "--start",
        help="Number of lesson to start downloading from (1-100)",
        type=int,
        metavar="N",
        choices=range(1, 101),
        default=1,
    )
    parser.add_argument(
        "--end",
        help="Number of last lesson to download (1-100)",
        type=int,
        metavar="N",
        choices=range(1, 101),
        default=100,
    )
    parser.add_argument(
        "--model-id",
        help="Model ID to use for the generated notes",
        type=int,
        metavar="ID",
    )
    parser.add_argument(
        "--out",
        help="File to write the deck to",
        metavar="FILE",
    )
    args = parser.parse_args()
    generate_deck(args.src, args.dest, args.start, args.end, args.model_id, args.out)
