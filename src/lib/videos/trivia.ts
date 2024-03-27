import { readdirSync } from "fs";
import { sample } from "lodash";

import { renderVideo } from "../video";
import { TriviaVideoOptions } from "../types/options";
import { TriviaQuestion, TriviaCategory } from "../types/trivia";

import triviaQuestions from "../../resources/trivia/questions.json";

export async function produceTriviaShort(output: string, questionCount: number) {

    // Pick a random category of trivia questions
    const questionsCategory = sample(Object.keys(triviaQuestions)) as TriviaCategory;
    if (!questionsCategory) {
        throw Error("trivia questions file has no defined catgories.");
    }

    // Pick a random set of questions from that category
    const questions: TriviaQuestion[] = [];
    for (let i = 0; i < questionCount; i++) {
        const question = sample(triviaQuestions[questionsCategory]);
        if (!question) {
            throw Error(`the trivia category '${questionsCategory}' has no defined questions.`);
        }

        questions.push(question);
        triviaQuestions[questionsCategory].splice(
            triviaQuestions[questionsCategory].indexOf(question),
            1
        );
    }

    // Pick a random lofi music track
    const lofiTrackFile = sample(
        readdirSync("src/resources/music/lofi")
    );
    if (!lofiTrackFile) {
        throw Error("there are no defined lofi music tracks.");
    }

    // Render video
    renderVideo<TriviaVideoOptions>(
        "trivia",
        {
            output: output,
            questions: questions,
            assets: {
                background: "src/resources/parkour.mp4",
                font: "src/resources/default.ttf",
                music: "src/resources/music/lofi/" + lofiTrackFile
            }
        }
    );

}