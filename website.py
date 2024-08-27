import streamlit as st
from text_generate import *
from os import path, system
import os


def button_click():
    if uploaded_file and path.exists(uploaded_file.name):
        st.write('Пожалуйста, переименуйте файл')

    elif uploaded_file:
        files_to_del = [uploaded_file.name]
        file_name = uploaded_file.name
        save_audio(file_name, uploaded_file)

        # Проверка на дурака (юзер загрузил не аудиофайл)
        try:
            a = pd.AudioSegment.from_file(file_name)
        except IndexError:
            st.write('Пожалуйста, загрузите аудио')

        audio_convert(file_name)
        file_name = path.splitext(file_name)[0] + '.mp3'

        files_to_del.append(file_name)

        try:
            st.write(audio_to_text(file_name, hard_words))
            remove_rest(files_to_del)
        except MoreThan25Error:
            st.write('Загрузите файл с меньшим битрейтом (максимальный допустимый - 320 kbps')

    else:
        st.write('Пожалуйста, сначала загрузите файл')


def save_audio(path_to_save, file):
    bytes_data = file.getvalue()
    with open(path_to_save, 'wb') as audiofile:
        audiofile.write(bytes_data)


def remove_rest(orig_files):
    """
    Функция для аудиофайлов
    :param orig_files: Пути к файлам источников
    :return: None
    """
    n = 0
    while True:
        if path.exists(f"segment_{n}.mp3"):
            os.remove(f"segment_{n}.mp3")
        else:
            break
        n += 1
    for elem in orig_files:
        os.remove(elem)


st.write('Загрузите аудиофайл (до гигабайта размером)')
uploaded_file = st.file_uploader('Audiofile')
st.write('Напишите в поле ниже список "сложных" слов (жаргонизмы, профессионализмы, названия компаний и.т.п),'
         ' т.к. программа может ошибиться в их транскрибировании. ')
hard_words = st.text_input('Hard words')
st.button("Транскрибировать текст", on_click=button_click)


