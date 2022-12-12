from autocorrect import Speller

spell = Speller('pl')


def correct_question(question: str):
    return spell(question.lower()).upper()
