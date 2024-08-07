from random import randint
from sys import argv
from json import loads
from gtts import gTTS
import moviepy.editor as editor
from moviepy.video.fx.resize import resize
from moviepy.audio.fx.volumex import volumex
from pilmoji import Pilmoji
from PIL import ImageFont, Image, ImageDraw
import numpy as np
from country_emojis import country_emojis

EMOJI_FONT_PATH = "/Library/Fonts/NotoColorEmoji.ttf"
SIZE = (1080, 1920)
emojis = {"capitals": "🌍", "math": "🧠"}
titles = {"capitals": "Test Your Geography IQ!", "math": "Test Your Math IQ!"}


class Question:
    title: str
    answers: list[str]
    correct_answer: int

    def __init__(self):
        self.answers = []


def get_country_emoji(title):
    title_split = title.replace("?", "").split(" ")
    country_name = title_split[-1]
    if country_name in country_emojis:
        return country_emojis[country_name]
    else:
        if " ".join(title_split[-2:]) in country_emojis:
            return country_emojis[" ".join(title_split[-2:])]
        else:
            return country_emojis[" ".join(title_split[-3:])]


def make_emoji_image(emoji, font_path, font_size):
    emoji_font = ImageFont.truetype(font_path, font_size)
    # Create an empty image with a size that's slightly larger than the text
    image = Image.new("RGBA", (font_size * 2, font_size * 2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Use Pilmoji to draw the emoji
    with Pilmoji(image) as pilmoji:
        pilmoji.text((0, 0), emoji.strip(), (0, 0, 0), emoji_font)

    # Crop the image to the size of the text
    bbox = image.getbbox()
    image = image.crop(bbox)
    return np.array(image)


def create_emoji_clip(position, emoji_image, duration, start_time):
    return (
        editor.ImageClip(emoji_image, duration=duration)
        .set_start(start_time)
        .set_position(position)
    )


def create_emoji_clips(vertical_margins, positions, emoji_image, duration, start_time):
    clips = []
    for vertical_margin in vertical_margins:
        for position in positions:
            clips.append(
                create_emoji_clip(
                    (position, vertical_margin), emoji_image, duration, start_time
                )
            )
    return clips


def generate_speech(text, filename):
    tts = gTTS(text=text, lang="en")
    tts.save(filename)


def produce_short(
    category: str,
    questions: list[Question],
    background: str,
    music: str,
    font: str,
    output: str,
):
    clip_durations = {"question": 7, "answer": 2}
    if category == "math":
        clip_durations["question"] = 8

    full_question_duration = sum(clip_durations.values())
    question_count = len(questions)

    background_duration = editor.VideoFileClip(background).duration
    background = resize(
        (
            editor.VideoFileClip(background)
            .cutout(0, randint(1, round(background_duration) - 65))
            .set_duration(full_question_duration * question_count)
            .set_position(("center", "center"))
        ),
        height=1920,
    )

    music_duration = editor.AudioFileClip(music).duration
    music = volumex(
        editor.CompositeAudioClip(
            [
                editor.AudioFileClip(music)
                .cutout(
                    0,
                    randint(
                        1, int(music_duration - full_question_duration * question_count)
                    ),
                )
                .set_end(full_question_duration * question_count)
            ]
        ),
        0.6,
    )

    clips = []
    speech_clips = []

    text_clip = (
        editor.TextClip(
            titles[category],
            fontsize=85,
            color="white",
            font="Arial-Bold",
            stroke_width=1,
        )
        .set_position(("center", 0.03 * SIZE[1]))
        .set_duration(full_question_duration * question_count)
    )
    bg_box = (
        editor.ColorClip(size=(SIZE[0], int(0.158 * SIZE[1])), color=(0, 0, 0))
        .set_opacity(0.5)
        .set_position(("center", 0.03 * SIZE[1]))
        .set_duration(full_question_duration * question_count)
    )

    emoji_size = 120
    globe_emoji_image = make_emoji_image(emojis[category], EMOJI_FONT_PATH, emoji_size)
    emoji_duration = full_question_duration * question_count
    emoji_start_time = 0

    buffer = 10
    num_emojis = SIZE[0] // (emoji_size + buffer)
    total_emoji_width = num_emojis * emoji_size + (num_emojis - 1) * buffer
    start_x = (SIZE[0] - total_emoji_width) / 2

    vertical_position = 0.035 * SIZE[1] + (bg_box.size[1] - emoji_size) / 2 + buffer

    emoji_clips = []
    for i in range(num_emojis):
        position_x = start_x + i * (emoji_size + buffer)
        emoji_clips.append(
            create_emoji_clip(
                (position_x, vertical_position),
                globe_emoji_image,
                emoji_duration,
                emoji_start_time,
            )
        )

    text_with_bg = editor.CompositeVideoClip([bg_box, text_clip, *emoji_clips])

    clips.append(text_with_bg)

    for question_index, question in enumerate(questions):
        question_text = (
            editor.TextClip(
                question["title"],
                fontsize=110,
                color="white",
                stroke_color="black",
                stroke_width=4,
                method="caption",
                size=(1080, None),
                font=font,
            )
            .set_position(("center", 0.28), relative=True)
            .set_start(question_index * full_question_duration)
            .set_duration(clip_durations["question"])
        )
        clips.append(question_text)
        if category == "capitals":
            emoji_width = 200
            duration = clip_durations["question"]
            start_time = question_index * full_question_duration
            emoji_image = make_emoji_image(
                get_country_emoji(question["title"]),
                EMOJI_FONT_PATH,
                emoji_width,
            )
            vertical_margins = [0.18 * SIZE[1], 0.85 * SIZE[1]]
            positions = [
                0.1 * SIZE[0],  # Left
                SIZE[0] - emoji_width - 0.1 * SIZE[0],  # Right
                (SIZE[0] - emoji_width) / 2,  # Center
            ]

            clips.extend(
                create_emoji_clips(
                    vertical_margins, positions, emoji_image, duration, start_time
                )
            )

        question_audio_filename = f"out/question_{question_index}.mp3"
        generate_speech(question["title"], question_audio_filename)
        question_audio_clip = editor.AudioFileClip(question_audio_filename).set_start(
            question_index * full_question_duration
        )
        speech_clips.append(question_audio_clip)

        answer_texts = [
            (
                editor.TextClip(
                    f"{list('ABCD')[i]} - {question['answers'][i]}",
                    fontsize=120 if len(question["answers"][i]) < 16 else 100,
                    color="white",
                    stroke_color="black",
                    stroke_width=4,
                    method="caption",
                    size=(1080, None),
                    font=font,
                    align="West",
                )
                .set_position((0.05 * SIZE[0], 0.50 * SIZE[1] + (i * 170)))
                .set_start(question_index * full_question_duration)
                .set_duration(clip_durations["question"])
            )
            for i in range(len(question["answers"]))
        ]
        clips += answer_texts

        countdown_texts = [
            (
                editor.TextClip(
                    str(clip_durations["question"] - i),
                    fontsize=120,
                    color="white",
                    stroke_color="black",
                    stroke_width=4,
                    method="caption",
                    size=(1080, None),
                    font=font,
                )
                .set_start(question_index * full_question_duration + i)
                .set_duration(1)
                .set_position(("center", 0.42), relative=True)
            )
            for i in range(clip_durations["question"])
        ]
        clips += countdown_texts

        correct_answer_text = (
            editor.TextClip(
                question["answers"][question["correct"]],
                fontsize=120,
                color="#00ff00",
                stroke_color="black",
                stroke_width=5,
                method="caption",
                size=(1080, None),
                font=font,
            )
            .set_start(
                question_index * full_question_duration + clip_durations["question"]
            )
            .set_duration(clip_durations["answer"])
            .set_position("center")
        )
        clips.append(correct_answer_text)

    result: editor.CompositeVideoClip = editor.CompositeVideoClip(
        [background, *clips], size=SIZE
    ).set_audio(editor.CompositeAudioClip([music, *speech_clips]))

    result.write_videofile(
        output,
        fps=24,
        audio_codec="aac",
        threads=4,
        temp_audiofile="out/TEMP_trivia.mp4",
    )


if __name__ == "__main__":
    args = loads(argv[1])

    produce_short(
        category=args["assets"]["category"],
        questions=args["questions"],
        background=args["assets"]["background"],
        music=args["assets"]["music"],
        font=args["assets"]["font"],
        output=args["output"],
    )
