from openai import OpenAI, NotGiven
from os.path import getsize, splitext, exists
import pydub as pd


class MoreThan25Error(Exception):
    def __str__(self):
        return 'File is more than 25 MB'


def audio_convert(path):
    """
    Конвертирует аудио в формат mp3
    :param path: Путь к файлу
    :return: None
    """

    output_file = splitext(path)[0] + '.mp3'
    audio = pd.AudioSegment.from_file(path)
    audio.export(output_file, format="mp3")

    print("Аудио успешно конвертировано")


def split_big_audio(path_to_audiofile):
    """
    Разделяет большие аудиофайлы (больше 25 мб) на несколько маленьких.
    Маленькие файлы будут длиться по 10 минут. (10 минут аудио с битрейтом 320 кбит/сек примерно равны 25 мегабайт)
    :param path_to_audiofile: Файл, который нужно разделить
    :return: Список путей к файлам
    """

    ten_min = 10 * 60 * 1000  # milliseconds
    start = 0
    stop = ten_min
    n = 0
    res = []

    ext = splitext(path_to_audiofile)[1]
    audio = pd.AudioSegment.from_file(path_to_audiofile)
    audio_len = audio.duration_seconds * 1000

    while stop <= audio_len:
        segment = audio[start:stop]
        segment.export(f"segment_{n}{ext}")
        if getsize(f"segment_{n}{ext}") > 26214400:
            raise MoreThan25Error
        start = stop
        stop += ten_min
        res.append(f"segment_{n}{ext}")

        print(f"Сегмент {n} успешно создан")
        n += 1

    # Вдруг все таки файл длится кратное кол-во времени
    if start < audio_len:
        segment = audio[start:]
        segment.export(f"segment_{n}{ext}")
        res.append(f"segment_{n}{ext}")

        print(f"Сегмент {n} успешно создан")

    print("Разделение файла проведено успешно")
    return res


def audio_to_text(path, hard_words, prompt=None):
    """
    :param path: Путь к аудиофайлу
    :param hard_words: Тяжелые для распознавания слова
    :param prompt: Промпт
    :return: Текст, произнесенный в аудиофайле
    """

    if getsize(path) > 26214400:  # Если размер файла больше 25 МБ

        audios = split_big_audio(path)
        corr_trans_prev = audio_to_text(audios[0], hard_words)
        res = corr_trans_prev

        for i in range(1, len(audios)):
            corr_trans_ong = audio_to_text(audios[i], hard_words, prompt=corr_trans_prev)
            res += corr_trans_ong
            corr_trans_prev = corr_trans_ong

        return res

    else:
        audio_file = open(path, "rb")
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text",
            prompt=prompt if prompt else NotGiven
        )

        system_prompt = get_system_prompt(hard_words)
        print("Фрагмент успешно транскрибирован")
        return generate_corrected_transcript(system_prompt, transcription)


def get_system_prompt(hard_words):
    """
    Задает системный промпт для функции улучшения текста
    :param hard_words: Слова, в которых нейронка может ошибиться
    :return: Системный промпт
    """

    return f"""
    You are responsible for transcribing audio files. Your task is to correct all spelling inaccuracies in the
    transcribed text. Make sure the following names are spelled correctly: {', '.join(hard_words)}
    """ if hard_words else f"""
    You are responsible for transcribing audio files. Your task is to correct all spelling inaccuracies in the
    transcribed text.
    """


def generate_corrected_transcript(system_prompt, transcript_text, temperature=0):
    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=temperature,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": transcript_text
            }
        ]
    )
    return response.choices[0].message.content


client = OpenAI(api_key='value')
