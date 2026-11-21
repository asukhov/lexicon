#!/usr/bin/env python3
"""Generate the grammar reference payload.

The content is original, learner-oriented prose. It is kept in a Python source
file so it is easy to review and regenerate; the site receives JSON.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "grammar.json"
TOPICS = ROOT / "build" / "content" / "grammar-topics.json"


def ex(text: str, note: str = "") -> dict:
    return {"text": text, "note": note}


def rule(title, pattern, explanation, examples, mistake=""):
    return {
        "title": title,
        "pattern": pattern,
        "explanation": explanation,
        "examples": examples,
        "mistake": mistake,
    }


def table(headers, rows):
    return {"headers": headers, "rows": rows}


GROUPS = [
    {
        "id": "basics",
        "title": "Basics",
        "summary": "Sentence building, agreement, questions, negatives and the small words that hold a sentence together.",
        "sections": [
            {
                "title": "Building a sentence",
                "intro": "English normally puts the subject first, then the verb, then the object or complement.",
                "rules": [
                    rule("Subject + verb + object", "S + V + O", "The subject does the action; the verb is the action; the object receives it.", [ex("Maya reads a book."), ex("The dog chased the ball.")], "Do not put the object before the verb in a normal statement: not â€œA book reads Maya.â€"),
                    rule("Subject + verb + complement", "S + V + C", "Linking verbs such as be, seem, become and look are followed by a complement that describes the subject.", [ex("She is a teacher."), ex("The soup smells delicious.")]),
                    rule("Adverb position", "S + adverb + V + O / S + V + O + adverb", "Adverbs of frequency usually go before the main verb but after be; other adverbs often go at the end.", [ex("I usually walk to work."), ex("He is always late."), ex("She speaks clearly.")], "Not â€œI walk usually to work.â€"),
                    rule("Subjectâ€“verb agreement", "singular subject + singular verb / plural subject + plural verb", "The verb agrees with the subject, not with a noun next to it.", [ex("The list of names is long."), ex("The students in the class are ready.")], "Not â€œThe list of names are long.â€"),
                    rule("There is / there are", "There is + singular / There are + plural", "Use there is for one thing and there are for more than one; the real subject comes after the verb.", [ex("There is a cafÃ© on the corner."), ex("There are two chairs by the window.")], "Not â€œThere have two chairs.â€"),
                    rule("Negatives", "do/does/did + not + base verb; be + not", "Use do-support for most verbs; be and modal verbs take not directly.", [ex("I do not know the answer."), ex("She does not drive."), ex("They are not ready."), ex("He cannot come.")], "Not â€œI not know.â€"),
                    rule("Questions", "auxiliary + subject + main verb", "Move the auxiliary before the subject. If there is no auxiliary, use do/does/did.", [ex("Do you like tea?"), ex("Where does she live?"), ex("Are they coming?")], "Not â€œWhere she lives?â€"),
                    rule("Imperatives", "base verb (+ object)", "Use the base verb for instructions, requests and warnings; add please to soften it.", [ex("Close the door."), ex("Please sit down."), ex("Do not touch the wire.")]),
                ],
            },
        ],
    },
    {
        "id": "nouns",
        "title": "Nouns & articles",
        "summary": "Countable and uncountable nouns, plurals, possessives, articles and quantifiers.",
        "sections": [
            {
                "title": "Countable and uncountable nouns",
                "intro": "Countable nouns can be counted and have a plural. Uncountable nouns are treated as a mass.",
                "rules": [
                    rule("Countable nouns", "a/an + singular; plural form", "Countable nouns can take a number and have singular and plural forms.", [ex("one apple, two apples"), ex("a chair, three chairs")]),
                    rule("Uncountable nouns", "no plural; use a unit", "Uncountable nouns do not normally take a/an or a plural. Use a unit or container to count them.", [ex("water, rice, advice, information"), ex("a glass of water, two pieces of advice")], "Not â€œan adviceâ€ or â€œtwo advicesâ€."),
                    rule("Nouns that can be both", "countable sense / uncountable sense", "Some nouns change meaning: chicken (animal) / chicken (meat), paper (newspaper) / paper (material).", [ex("We keep chickens."), ex("I ate some chicken.")]),
                ],
            },
            {
                "title": "Plurals and possessives",
                "intro": "Most plurals add -s, but spelling and irregular forms need care.",
                "rules": [
                    rule("Regular plurals", "noun + -s", "Add -s to most nouns.", [ex("book â†’ books"), ex("car â†’ cars")]),
                    rule("Plurals after -s, -x, -ch, -sh", "noun + -es", "Add -es after these sounds.", [ex("bus â†’ buses"), ex("box â†’ boxes"), ex("watch â†’ watches")]),
                    rule("Consonant + y", "-y â†’ -ies", "Change y to i and add -es after a consonant.", [ex("city â†’ cities"), ex("baby â†’ babies")], "Not â€œcitysâ€."),
                    rule("Irregular plurals", "learn the form", "Some nouns have irregular plurals.", [ex("child â†’ children"), ex("man â†’ men"), ex("tooth â†’ teeth"), ex("mouse â†’ mice")]),
                    rule("Possessive singular", "noun + 's", "Add 's to a singular noun to show possession.", [ex("the girl's bag"), ex("Tom's car")]),
                    rule("Possessive plural", "plural noun + '", "For a regular plural ending in -s, add only an apostrophe.", [ex("the girls' bags"), ex("the teachers' room")], "Not â€œthe girls's bagsâ€."),
                ],
            },
            {
                "title": "Articles",
                "intro": "Articles signal whether a noun is new, specific, or general.",
                "rules": [
                    rule("A / an", "a/an + singular countable noun", "Use a/an for one non-specific thing, or when you mention something for the first time. Use an before a vowel sound.", [ex("I saw a dog."), ex("She is an engineer."), ex("an hour")], "Not â€œa hourâ€."),
                    rule("The", "the + noun", "Use the when the listener knows which one you mean, when it is unique, or when it was already mentioned.", [ex("Close the door."), ex("the sun"), ex("I bought a book. The book was expensive.")]),
                    rule("Zero article", "no article", "Use no article for general plurals, uncountable nouns, most names, languages, sports and meals.", [ex("Dogs are loyal."), ex("Water is essential."), ex("She speaks French."), ex("We had lunch.")]),
                    rule("Articles with institutions", "the / no article", "Use the with some institutions and no article when the place is used for its main purpose.", [ex("go to school (as a pupil)"), ex("go to the school (to visit)"), ex("go to bed")]),
                ],
            },
            {
                "title": "Quantifiers and pronouns",
                "intro": "Quantifiers tell you how much or how many; pronouns replace nouns.",
                "rules": [
                    rule("Some and any", "some in positive; any in negative/questions", "Use some in statements and offers; use any in negatives and most questions.", [ex("I have some money."), ex("Do you have any questions?"), ex("There isn't any milk.")]),
                    rule("Much / many / a lot of", "much + uncountable; many + countable", "Much and many are common in negatives and questions; a lot of works in all types.", [ex("How much time?"), ex("How many people?"), ex("She has a lot of friends.")]),
                    rule("A few / a little", "a few + countable; a little + uncountable", "A few and a little mean a small but sufficient amount. Few and little without a mean â€˜not enoughâ€™.", [ex("A few students came."), ex("A little sugar, please."), ex("Few people came. (almost none)")]),
                    rule("Subject and object pronouns", "I/me, he/him, she/her, we/us, they/them", "Use subject pronouns before the verb and object pronouns after a verb or preposition.", [ex("She called me."), ex("We went with them.")], "Not â€œMe called she.â€"),
                    rule("Possessive adjectives and pronouns", "my/mine, your/yours, his, her/hers, our/ours, their/theirs", "Possessive adjectives come before a noun; possessive pronouns stand alone.", [ex("This is my book."), ex("This book is mine.")]),
                ],
            },
        ],
    },
    {
        "id": "verbs",
        "title": "Verbs",
        "summary": "Verb forms, auxiliary verbs, irregular verbs, gerunds, infinitives and stative verbs.",
        "sections": [
            {
                "title": "Verb forms",
                "intro": "Every English verb has a base form, a third-person singular form, an -ing form and a past participle.",
                "rules": [
                    rule("The four forms", "base / -s / -ing / past participle", "Learn these four forms for every new verb; they build all tenses and the passive.", [ex("work / works / working / worked"), ex("write / writes / writing / written")]),
                    rule("Regular verbs", "base + -ed", "Regular verbs add -ed for the past simple and past participle.", [ex("walk â†’ walked"), ex("study â†’ studied"), ex("stop â†’ stopped")]),
                    rule("Irregular verbs", "learn the three parts", "Many common verbs are irregular: base, past, past participle.", [ex("go â€“ went â€“ gone"), ex("see â€“ saw â€“ seen"), ex("take â€“ took â€“ taken")]),
                    rule("Auxiliary verbs", "be / have / do + main verb", "Be forms continuous tenses and the passive; have forms perfect tenses; do forms negatives and questions.", [ex("She is working."), ex("They have finished."), ex("Do you know?")]),
                    rule("Gerund after certain verbs", "verb + -ing", "Some verbs are followed by an -ing form: enjoy, avoid, finish, mind, suggest, keep.", [ex("I enjoy reading."), ex("She avoided answering.")]),
                    rule("Infinitive after certain verbs", "verb + to + base", "Some verbs are followed by to + base: decide, hope, plan, want, need, promise.", [ex("We decided to leave."), ex("I want to help.")]),
                    rule("Verb + object + infinitive", "verb + object + to + base", "Verbs such as ask, tell, want, expect and encourage take an object before the infinitive.", [ex("She asked me to wait."), ex("They want us to come.")]),
                    rule("Stative verbs", "usually no continuous form", "Verbs of thinking, liking, belonging and seeming are usually not used in continuous tenses.", [ex("I know the answer."), ex("This book belongs to me.")], "Not â€œI am knowing the answer.â€"),
                ],
            },
        ],
    },
    {
        "id": "tenses",
        "title": "Tenses",
        "summary": "The twelve tenses, their forms and uses, plus the main ways to talk about the future.",
        "sections": [
            {
                "title": "Present tenses",
                "intro": "Present tenses can describe habits, current situations, completed actions with present relevance, and ongoing activity.",
                "rules": [
                    rule("Present simple", "V1 / V-s", "Habits, routines, facts and timetables.", [ex("She works in a hospital."), ex("The train leaves at six.")], "Not â€œShe work in a hospital.â€"),
                    rule("Present continuous", "am/is/are + V-ing", "Actions happening now, temporary situations and fixed future arrangements.", [ex("I am writing an email."), ex("They are staying with us this week."), ex("We are meeting at noon.")]),
                    rule("Present perfect", "have/has + V3", "A past action with a present result, experience, or a period that is not finished.", [ex("I have lost my keys."), ex("She has visited Japan."), ex("We have lived here for ten years.")], "Do not use it with a finished past time: not â€œI have seen him yesterday.â€"),
                    rule("Present perfect continuous", "have/has been + V-ing", "An activity that started in the past and continues, or has just stopped and has a visible result.", [ex("I have been reading all morning."), ex("It has been raining, so the ground is wet.")]),
                ],
            },
            {
                "title": "Past tenses",
                "intro": "Past tenses place actions before now and show whether they were finished, in progress, or earlier than another past action.",
                "rules": [
                    rule("Past simple", "V2", "A finished action or state at a definite past time.", [ex("We visited Rome last year."), ex("She was tired yesterday.")]),
                    rule("Past continuous", "was/were + V-ing", "An action in progress at a past moment, often interrupted by a shorter action.", [ex("I was cooking when he called."), ex("They were waiting at the station.")]),
                    rule("Past perfect", "had + V3", "An action that happened before another past action or time.", [ex("The film had started before we arrived."), ex("She had never seen the sea.")]),
                    rule("Past perfect continuous", "had been + V-ing", "A continuing activity that led up to a past point.", [ex("He had been working for hours before he stopped."), ex("They had been arguing all morning.")]),
                ],
            },
            {
                "title": "Future tenses",
                "intro": "English has no single future tense; will, going to, the present continuous and the present simple all express future meaning.",
                "rules": [
                    rule("Future simple", "will + V1", "Predictions, spontaneous decisions, promises, offers and formal statements.", [ex("I will call you later."), ex("It will probably rain."), ex("I will help you.")]),
                    rule("Future continuous", "will be + V-ing", "An action that will be in progress at a future time.", [ex("At eight, I will be travelling to work."), ex("They will be waiting for us.")]),
                    rule("Future perfect", "will have + V3", "An action that will be completed before a future time.", [ex("By Friday, I will have finished the report."), ex("She will have left by then.")]),
                    rule("Future perfect continuous", "will have been + V-ing", "The duration of an activity up to a future point.", [ex("By June, I will have been working here for five years."), ex("He will have been driving for six hours.")]),
                    rule("Going to", "be going to + V1", "Plans and intentions, or predictions based on present evidence.", [ex("We are going to move house."), ex("Look at those clouds â€” it is going to rain.")]),
                    rule("Present continuous for arrangements", "am/is/are + V-ing + future time", "A fixed arrangement with another person or a booking.", [ex("I am meeting Anna tomorrow."), ex("We are flying to Rome on Friday.")]),
                    rule("Present simple for timetables", "V1 / V-s + future time", "Scheduled events such as trains, flights, classes and opening times.", [ex("The flight leaves at 7:30."), ex("The course starts on Monday.")]),
                ],
            },
            {
                "title": "Twelve tenses at a glance",
                "intro": "Use this table as a quick revision grid; the cards above give the full explanations.",
                "rules": [],
                "table": table(
                    ["Tense", "Form", "Main use"],
                    [
                        ["Present simple", "V1 / V-s", "habits, facts, timetables"],
                        ["Present continuous", "am/is/are + V-ing", "now, temporary, arrangements"],
                        ["Present perfect", "have/has + V3", "past with present relevance"],
                        ["Present perfect continuous", "have/has been + V-ing", "duration up to now"],
                        ["Past simple", "V2", "finished past action"],
                        ["Past continuous", "was/were + V-ing", "in progress in the past"],
                        ["Past perfect", "had + V3", "earlier past"],
                        ["Past perfect continuous", "had been + V-ing", "duration before a past point"],
                        ["Future simple", "will + V1", "predictions, decisions, promises"],
                        ["Future continuous", "will be + V-ing", "in progress in the future"],
                        ["Future perfect", "will have + V3", "completed before a future point"],
                        ["Future perfect continuous", "will have been + V-ing", "duration before a future point"],
                    ],
                ),
            },
        ],
    },
    {
        "id": "modals",
        "title": "Modal verbs",
        "summary": "Ability, permission, possibility, obligation, advice, requests and past deduction.",
        "sections": [
            {
                "title": "Core modals",
                "intro": "Modal verbs are followed by a base verb and do not add -s, -ed or -ing.",
                "rules": [
                    rule("Can / could", "can/could + base", "Ability, permission, requests and possibility. Could is also the past of can and a more polite form.", [ex("She can swim."), ex("Could you open the window?"), ex("It could rain later.")], "Not â€œShe cans swim.â€"),
                    rule("May / might", "may/might + base", "Possibility and formal permission. Might is often less certain than may.", [ex("It may snow."), ex("May I come in?"), ex("She might be at home.")]),
                    rule("Must / have to", "must + base / have to + base", "Strong obligation or necessity. Must is often personal; have to often states an external rule.", [ex("You must wear a seat belt."), ex("I have to finish this today.")]),
                    rule("Mustn't / don't have to", "mustn't + base / don't have to + base", "Mustn't means prohibition; don't have to means no obligation.", [ex("You mustn't smoke here."), ex("You don't have to come.")], "Not â€œYou don't must smoke.â€"),
                    rule("Should / ought to", "should/ought to + base", "Advice, recommendation or expectation.", [ex("You should see a doctor."), ex("They ought to arrive soon.")]),
                    rule("Will / would for requests", "will/would + base", "Would is more polite; will is more direct.", [ex("Will you help me?"), ex("Would you mind waiting?")]),
                    rule("Past modals", "modal + have + V3", "Use this to talk about possibility, obligation or regret in the past.", [ex("She must have missed the train."), ex("You should have told me."), ex("He might have forgotten.")]),
                ],
            },
        ],
    },
    {
        "id": "conditionals",
        "title": "Conditionals",
        "summary": "Real, unreal and past unreal conditions, plus unless and wish.",
        "sections": [
            {
                "title": "If-clauses",
                "intro": "The tense in the if-clause shows how real or unreal the condition is.",
                "rules": [
                    rule("Zero conditional", "If + present, present", "General truths and always-true results.", [ex("If you heat ice, it melts."), ex("If I drink coffee late, I cannot sleep.")]),
                    rule("First conditional", "If + present, will + base", "A real future possibility and its result.", [ex("If it rains, we will stay inside."), ex("If you finish early, call me.")], "Not â€œIf it will rainâ€¦â€"),
                    rule("Second conditional", "If + past simple, would + base", "An unreal or unlikely present/future situation.", [ex("If I had more time, I would travel."), ex("If she knew, she would tell us.")]),
                    rule("Third conditional", "If + had + V3, would have + V3", "An unreal past situation and its imagined result.", [ex("If I had studied, I would have passed."), ex("If they had left earlier, they would have caught the train.")]),
                    rule("Mixed conditional", "If + had + V3, would + base", "A past cause with a present result.", [ex("If I had taken that job, I would be living in Paris now.")]),
                    rule("Unless", "unless + present", "Unless means â€˜if notâ€™.", [ex("We will go unless it rains."), ex("You cannot enter unless you have a ticket.")]),
                    rule("Wish / if only", "wish + past simple / had + V3", "Use the past for an unreal present wish and had + V3 for regret about the past.", [ex("I wish I had more time."), ex("I wish I had studied harder."), ex("If only she were here.")]),
                ],
            },
        ],
    },
    {
        "id": "passive",
        "title": "Passive voice",
        "summary": "Focus on the action or receiver rather than the doer.",
        "sections": [
            {
                "title": "Form and use",
                "intro": "The passive is be + past participle. The tense is carried by be.",
                "rules": [
                    rule("Passive form", "be + V3 (by + agent)", "Use the passive when the doer is unknown, unimportant, obvious, or when the action is more important.", [ex("The bridge was built in 1890."), ex("English is spoken here."), ex("The results will be announced tomorrow.")]),
                    rule("Passive by tense", "be changes tense; V3 stays", "Present: is made. Past: was made. Perfect: has been made. Future: will be made.", [ex("Bread is made daily."), ex("The letter has been sent.")]),
                    rule("Passive with modals", "modal + be + V3", "After a modal, use be + past participle.", [ex("The form must be signed."), ex("The work could be finished today.")]),
                    rule("Get-passive", "get + V3", "Get-passive is informal and often suggests something happened unexpectedly.", [ex("He got fired."), ex("She got hurt during the match.")]),
                    rule("Only transitive verbs", "object becomes subject", "Only verbs that take an object can normally be passive.", [ex("They built the house. â†’ The house was built.")], "Not â€œHe was arrived.â€"),
                ],
            },
        ],
    },
    {
        "id": "reported",
        "title": "Reported speech",
        "summary": "Report statements, questions and commands without quotation marks.",
        "sections": [
            {
                "title": "Reporting what someone said",
                "intro": "When the reporting verb is in the past, the reported verb often moves one step back.",
                "rules": [
                    rule("Reported statements", "said (that) + backshifted clause", "Move the tense back: present â†’ past, past â†’ past perfect, will â†’ would.", [ex("â€œI am tired.â€ â†’ She said she was tired."), ex("â€œI will call.â€ â†’ He said he would call.")]),
                    rule("Reported questions", "asked + if/whether / question word + statement order", "Use if/whether for yes/no questions and keep statement word order.", [ex("â€œDo you live here?â€ â†’ She asked if I lived here."), ex("â€œWhere is it?â€ â†’ He asked where it was.")], "Not â€œShe asked where was it.â€"),
                    rule("Reported commands", "told/asked + object + to + base", "Use told for orders and asked for requests; negative: not to + base.", [ex("â€œSit down.â€ â†’ She told me to sit down."), ex("â€œPlease don't go.â€ â†’ He asked me not to go.")]),
                    rule("Time and place changes", "now â†’ then, today â†’ that day, here â†’ there", "Change time and place words when the reporting situation is different.", [ex("â€œI'll do it tomorrow.â€ â†’ He said he would do it the next day.")]),
                    rule("Reporting verbs", "admit, deny, suggest, promise, warn, explain", "Different reporting verbs take different patterns.", [ex("He admitted making a mistake."), ex("She suggested going home."), ex("They warned us not to swim there.")]),
                ],
            },
        ],
    },
    {
        "id": "prepositions",
        "title": "Prepositions",
        "summary": "At, on and in for time and place, plus other high-frequency prepositions.",
        "sections": [
            {
                "title": "At, on and in for time",
                "intro": "Think of at as a point, on as a day or date, and in as a longer period.",
                "rules": [
                    rule("At + clock time and points in time", "at + time / at night / at the weekend", "Use at for exact times, meals, and a few fixed expressions.", [ex("at 7:30"), ex("at noon"), ex("at night"), ex("at the weekend (British English)"), ex("at Christmas")]),
                    rule("On + days and dates", "on + day/date", "Use on for days, dates, named days and special days.", [ex("on Monday"), ex("on 5 May"), ex("on my birthday"), ex("on New Year's Day")]),
                    rule("In + longer periods", "in + month/year/season/part of day", "Use in for months, years, seasons, centuries and parts of the day.", [ex("in July"), ex("in 2024"), ex("in winter"), ex("in the morning"), ex("in the 19th century")]),
                    rule("No preposition", "next/last/this/every + time", "Do not use at/on/in before next, last, this, every, today, tomorrow or yesterday.", [ex("next week"), ex("last year"), ex("this morning"), ex("every day")], "Not â€œin next weekâ€."),
                ],
                "table": table(
                    ["Preposition", "Use", "Examples"],
                    [
                        ["at", "exact time, point in time", "at 6 o'clock, at noon, at night, at the weekend (UK)"],
                        ["on", "days, dates, named days", "on Monday, on 1 June, on my birthday"],
                        ["in", "months, years, seasons, parts of day, longer periods", "in April, in 2025, in summer, in the evening"],
                        ["no preposition", "next, last, this, every, today, tomorrow, yesterday", "next month, last Friday, this afternoon"],
                    ],
                ),
            },
            {
                "title": "At, on and in for place",
                "intro": "At views a place as a point, on views it as a surface or line, and in views it as an enclosed space.",
                "rules": [
                    rule("At + point or event", "at + place/event", "Use at for a point on a journey, a specific place, or an event.", [ex("at the bus stop"), ex("at the door"), ex("at the party"), ex("at home"), ex("at work")]),
                    rule("On + surface or line", "on + surface/floor/street/transport", "Use on for surfaces, floors, streets (British English), pages, screens and public transport.", [ex("on the table"), ex("on the second floor"), ex("on Oxford Street"), ex("on the bus"), ex("on page 12")]),
                    rule("In + enclosed space or area", "in + container/city/country/water", "Use in for enclosed spaces, towns, countries, water and periods.", [ex("in the box"), ex("in London"), ex("in France"), ex("in the sea"), ex("in the car")]),
                    rule("Common place contrasts", "at / on / in", "Compare: at the station (point), on the platform (surface), in the station (inside the building).", [ex("I'll meet you at the station."), ex("She is on the platform."), ex("The shop is in the station.")]),
                ],
                "table": table(
                    ["Preposition", "Idea", "Examples"],
                    [
                        ["at", "a point or event", "at the bus stop, at the party, at home, at work"],
                        ["on", "a surface, line or public transport", "on the table, on the wall, on the bus, on the left"],
                        ["in", "an enclosed space or area", "in the box, in London, in the water, in the car"],
                    ],
                ),
            },
            {
                "title": "Other common prepositions",
                "intro": "These pairs are often confused because their meanings overlap in some languages.",
                "rules": [
                    rule("For and since", "for + length of time; since + starting point", "For answers â€˜how long?â€™; since answers â€˜from when?â€™.", [ex("for three years"), ex("since 2020"), ex("since Monday")], "Not â€œsince three yearsâ€."),
                    rule("During and while", "during + noun; while + clause", "During is followed by a noun; while is followed by a subject and verb.", [ex("during the film"), ex("while I was watching the film")]),
                    rule("By and until", "by + deadline; until + end point", "By means â€˜not later thanâ€™; until means â€˜up to the time thatâ€™.", [ex("Finish it by Friday."), ex("Wait until Friday.")]),
                    rule("Between and among", "between two; among more than two", "Between is usually for two people or things; among is for a group.", [ex("between you and me"), ex("among the crowd")]),
                    rule("Beside and besides", "beside = next to; besides = in addition", "These are different words.", [ex("Sit beside me."), ex("Besides English, she speaks French.")]),
                    rule("Above/over and below/under", "above/below = higher/lower; over/under = covering or directly below", "Over often suggests covering or movement across; above is simply higher than.", [ex("The lamp hangs over the table."), ex("The plane flew above the clouds.")]),
                    rule("Into and onto", "into = movement inside; onto = movement onto a surface", "Use into for entering an enclosed space and onto for reaching a surface.", [ex("She walked into the room."), ex("He put the cup onto the table.")]),
                ],
            },
        ],
    },
    {
        "id": "sentences",
        "title": "Sentences & clauses",
        "summary": "Clauses, relative clauses, linking words, comparison and emphasis.",
        "sections": [
            {
                "title": "Clauses and sentence types",
                "intro": "A clause contains a subject and a verb. Clauses can be independent or dependent.",
                "rules": [
                    rule("Independent and dependent clauses", "main clause + subordinate clause", "An independent clause can stand alone; a dependent clause needs a main clause.", [ex("I stayed home because it was raining."), ex("When she arrived, we ate.")]),
                    rule("Relative clauses", "who/which/that/whose/where", "Relative clauses describe a noun. Defining clauses are essential; non-defining clauses add extra information between commas.", [ex("The woman who called is my aunt."), ex("The book, which was published in 2020, is excellent.")]),
                    rule("Noun clauses", "that / whether / question word + clause", "A noun clause can be the subject or object of a verb.", [ex("I know that she is right."), ex("Whether he comes is uncertain.")]),
                    rule("Adverb clauses", "because, although, if, when, while, since", "Adverb clauses show reason, contrast, condition, time or result.", [ex("Although it was late, we continued."), ex("I will call you when I arrive.")]),
                    rule("Coordination and subordination", "and/but/or / because/although/if", "Coordinate equal ideas with and, but, or; subordinate one idea to another with because, although, if, etc.", [ex("She was tired but she finished."), ex("He left because he was ill.")]),
                    rule("Comparatives and superlatives", "-er/-est or more/most", "Short adjectives take -er/-est; longer adjectives take more/most. Use than for comparison.", [ex("taller than"), ex("more interesting than"), ex("the best")], "Not â€œmore betterâ€."),
                    rule("Participle clauses", "-ing / -ed clause", "A participle clause can replace a longer clause when the subject is the same.", [ex("Walking home, I saw a fox."), ex("Written in 1920, the novel is still popular.")]),
                    rule("Inversion for emphasis", "negative adverb + auxiliary + subject", "After never, rarely, seldom, hardly and not only, invert the subject and auxiliary.", [ex("Never have I seen such a crowd."), ex("Rarely does she complain.")]),
                ],
            },
            {
                "title": "Linking words",
                "intro": "Linking words make the relationship between ideas clear.",
                "rules": [
                    rule("Addition", "and, also, moreover, in addition", "Use these to add a similar idea.", [ex("The room is small. Moreover, it is expensive.")]),
                    rule("Contrast", "but, however, although, whereas", "Use these to contrast ideas; however is followed by a comma and a full clause.", [ex("It was cold. However, we went out."), ex("Although it was cold, we went out.")]),
                    rule("Cause and result", "because, so, therefore, as a result", "Show why something happened and what followed.", [ex("It was raining, so we stayed in."), ex("The road was closed; therefore, we took a detour.")]),
                    rule("Purpose", "to + base, in order to, so that", "Show the purpose of an action.", [ex("I left early to catch the train."), ex("She spoke slowly so that everyone could understand.")]),
                ],
            },
        ],
    },
    {
        "id": "punctuation",
        "title": "Punctuation",
        "summary": "The marks that make written English clear.",
        "sections": [
            {
                "title": "Sentence punctuation",
                "intro": "Punctuation marks structure sentences and show how ideas relate.",
                "rules": [
                    rule("Full stop / period", ".", "Ends a statement or a complete sentence.", [ex("The shop closes at six.")]),
                    rule("Question mark", "?", "Ends a direct question.", [ex("Where are you going?")]),
                    rule("Exclamation mark", "!", "Shows strong feeling, a warning or emphasis; use it sparingly.", [ex("Watch out!")]),
                    rule("Comma", ",", "Separates items, introductory phrases, and non-defining clauses.", [ex("We bought bread, milk and eggs."), ex("After lunch, we went for a walk.")]),
                    rule("Semicolon", ";", "Joins two closely related independent clauses.", [ex("The train was late; we missed the meeting.")]),
                    rule("Colon", ":", "Introduces a list, an explanation or a quotation after a complete clause.", [ex("She brought three things: a map, water and a torch.")]),
                    rule("Apostrophe", "'", "Shows possession or a contraction.", [ex("the girl's coat"), ex("it's = it is"), ex("its = belonging to it")], "Do not confuse its and it's."),
                    rule("Hyphen and dash", "- / â€”", "A hyphen joins parts of a compound word; a dash marks a break or aside.", [ex("well-known author"), ex("He arrived late â€” again.")]),
                    rule("Quotation marks", "\" \" / â€˜ â€™", "Show direct speech or a quotation.", [ex("She said, â€œI'll be there.â€")]),
                    rule("Capitalisation", "capital letter at the start", "Capitalise the first word of a sentence, proper names, days, months, nationalities and titles.", [ex("On Monday, Anna visited London.")]),
                ],
            },
        ],
    },
    {
        "id": "mistakes",
        "title": "Common mistakes",
        "summary": "High-value errors that learners make again and again.",
        "sections": [
            {
                "title": "Fix these first",
                "intro": "Each card shows the wrong form and the correct form.",
                "rules": [
                    rule("I am agree", "I agree", "Agree is a verb, not an adjective; do not use am/is/are before it.", [ex("I agree with you.")], "Not â€œI am agree.â€"),
                    rule("Discuss about", "discuss + object", "Discuss takes a direct object, without about.", [ex("We discussed the plan.")], "Not â€œWe discussed about the plan.â€"),
                    rule("Depend of", "depend on", "The preposition after depend is on.", [ex("It depends on the weather.")], "Not â€œIt depends of the weather.â€"),
                    rule("Since / for", "since + starting point; for + length", "Use since with a point in time and for with a duration.", [ex("since 2019"), ex("for five years")], "Not â€œsince five yearsâ€."),
                    rule("Make / do", "make a decision; do homework", "Use make for creating or producing; use do for tasks and activities.", [ex("make a cake, make a plan"), ex("do the washing, do your best")]),
                    rule("Say / tell", "say something; tell someone something", "Tell needs a person as object; say does not.", [ex("She said hello."), ex("She told me hello.")], "Not â€œShe said me hello.â€"),
                    rule("Borrow / lend", "borrow from; lend to", "You borrow something from someone; you lend something to someone.", [ex("I borrowed a pen from Tom."), ex("Tom lent me a pen.")]),
                    rule("Affect / effect", "affect = verb; effect = noun", "Affect means influence; effect means result.", [ex("The rain affected the game."), ex("The effect was immediate.")]),
                    rule("Its / it's", "its = possessive; it's = it is", "Check whether you can replace it with â€˜it isâ€™.", [ex("The dog wagged its tail."), ex("It's raining.")]),
                    rule("Then / than", "then = time; than = comparison", "Use than after a comparative.", [ex("First we ate, then we left."), ex("She is taller than me.")]),
                    rule("Fewer / less", "fewer + countable; less + uncountable", "Use fewer with plural countable nouns and less with uncountable nouns.", [ex("fewer cars"), ex("less traffic")]),
                    rule("Good / well", "good = adjective; well = adverb", "Use good before a noun or after a linking verb; use well to describe how an action is done.", [ex("a good singer"), ex("She sings well.")], "Not â€œShe sings good.â€"),
                    rule("Double negative", "one negative", "Standard English uses one negative; use any-words with not.", [ex("I didn't see anything.")], "Not â€œI didn't see nothing.â€"),
                    rule("Present perfect with finished time", "past simple + finished time", "Use the past simple with yesterday, last week, in 2010, etc.", [ex("I saw him yesterday.")], "Not â€œI have seen him yesterday.â€"),
                    rule("Infinitive after modal", "modal + base verb", "Do not add to after a modal.", [ex("She can swim.")], "Not â€œShe can to swim.â€"),
                ],
            },
        ],
    },
]


TENSE_MAP = {
    "present": [
        {"name": "Present simple", "form": "V1 / V-s", "use": "habits, facts, timetables"},
        {"name": "Present continuous", "form": "am/is/are + V-ing", "use": "now, temporary situations"},
        {"name": "Present perfect", "form": "have/has + V3", "use": "past with present relevance"},
        {"name": "Present perfect continuous", "form": "have/has been + V-ing", "use": "duration up to now"},
    ],
    "past": [
        {"name": "Past simple", "form": "V2", "use": "finished past actions"},
        {"name": "Past continuous", "form": "was/were + V-ing", "use": "in progress in the past"},
        {"name": "Past perfect", "form": "had + V3", "use": "earlier past"},
        {"name": "Past perfect continuous", "form": "had been + V-ing", "use": "duration before a past point"},
    ],
    "future": [
        {"name": "Future simple", "form": "will + V1", "use": "predictions, decisions, promises"},
        {"name": "Future continuous", "form": "will be + V-ing", "use": "in progress in the future"},
        {"name": "Future perfect", "form": "will have + V3", "use": "completed before a future point"},
        {"name": "Future perfect continuous", "form": "will have been + V-ing", "use": "duration before a future point"},
    ],
}


def main() -> None:
    if TOPICS.exists():
        topics = json.loads(TOPICS.read_text(encoding="utf-8"))
        raw_groups = topics.get("groups") or []
        groups = [g for g in raw_groups if isinstance(g, dict) and isinstance(g.get("sections"), list)]
        existing = {g.get("id") for g in groups}
        for fallback in GROUPS:
            if fallback["id"] not in existing:
                groups.append(fallback)
        intro = topics.get("intro") or "A practical reference to English grammar, from sentence building to tenses, conditionals and punctuation."
        tense_map = topics.get("tenseMap") or TENSE_MAP
    else:
        groups = GROUPS
        intro = "A practical reference to English grammar, from sentence building to tenses, conditionals and punctuation."
        tense_map = TENSE_MAP
    data = {
        "intro": intro,
        "groups": groups,
        "tenseMap": tense_map,
        "wordClasses": [
            {"code": "n", "name": "noun", "summary": "A person, place, thing or idea.", "examples": ["book", "London", "idea"], "notes": "Countable or uncountable."},
            {"code": "v", "name": "verb", "summary": "An action or state.", "examples": ["run", "be", "seem"], "notes": "Main or auxiliary."},
            {"code": "adj", "name": "adjective", "summary": "Describes a noun.", "examples": ["blue", "happy", "wooden"], "notes": "Comes before a noun or after a linking verb."},
            {"code": "adv", "name": "adverb", "summary": "Describes a verb, adjective or another adverb.", "examples": ["quickly", "very", "well"], "notes": "Often ends in -ly."},
            {"code": "prep", "name": "preposition", "summary": "Shows a relationship of time, place or direction.", "examples": ["at", "on", "in"], "notes": "Followed by a noun or pronoun."},
            {"code": "conj", "name": "conjunction", "summary": "Joins words, phrases or clauses.", "examples": ["and", "because", "although"], "notes": "Coordinating or subordinating."},
            {"code": "det", "name": "determiner", "summary": "Introduces and limits a noun.", "examples": ["the", "a", "some"], "notes": "Includes articles and quantifiers."},
            {"code": "pron", "name": "pronoun", "summary": "Replaces a noun.", "examples": ["she", "them", "mine"], "notes": "Subject, object or possessive."},
            {"code": "modal", "name": "modal verb", "summary": "Adds ability, possibility, obligation or advice.", "examples": ["can", "must", "should"], "notes": "Followed by a base verb."},
            {"code": "interj", "name": "interjection", "summary": "A short exclamation.", "examples": ["oh", "wow", "hello"], "notes": "Often stands alone."},
        ],
        "grammarCodes": [
            {"code": "C", "meaning": "countable", "example": "a chair, two chairs"},
            {"code": "U", "meaning": "uncountable", "example": "water, advice"},
            {"code": "T", "meaning": "transitive", "example": "She made a cake."},
            {"code": "I", "meaning": "intransitive", "example": "He slept."},
            {"code": "pl", "meaning": "plural", "example": "children"},
            {"code": "sing", "meaning": "singular", "example": "child"},
            {"code": "phr v", "meaning": "phrasal verb", "example": "give up"},
            {"code": "aux", "meaning": "auxiliary verb", "example": "have, be, do"},
        ],
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("groups", len(groups), "sections", sum(len(g["sections"]) for g in groups), "rules", sum(len(s.get("rules", [])) for g in groups for s in g["sections"]), "bytes", OUT.stat().st_size)


if __name__ == "__main__":
    main()

