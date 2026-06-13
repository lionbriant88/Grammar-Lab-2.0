"""预设例句库 - 覆盖 9 种常见时态"""

PRESET_SENTENCES: list[dict] = [
    {
        "sentence": "I usually get up at seven every morning.",
        "tense": "simple_present",
        "tense_cn": "一般现在时",
        "desc": "习惯性动作"
    },
    {
        "sentence": "She visited her grandparents last weekend.",
        "tense": "simple_past",
        "tense_cn": "一般过去时",
        "desc": "过去发生的动作"
    },
    {
        "sentence": "They will travel to Japan next month.",
        "tense": "simple_future_will",
        "tense_cn": "一般将来时",
        "desc": "将来计划 (will)"
    },
    {
        "sentence": "I am going to study medicine in college.",
        "tense": "simple_future_going_to",
        "tense_cn": "一般将来时",
        "desc": "将���计划 (be going to)"
    },
    {
        "sentence": "Look! The children are playing in the garden.",
        "tense": "present_progressive",
        "tense_cn": "现在进行时",
        "desc": "正在进行的动作"
    },
    {
        "sentence": "At ten o'clock last night, I was reading a book.",
        "tense": "past_progressive",
        "tense_cn": "过去进行时",
        "desc": "过去某时刻正在进行的动作"
    },
    {
        "sentence": "He has already finished his homework.",
        "tense": "present_perfect",
        "tense_cn": "现在完成时",
        "desc": "过去动作对现在的影响"
    },
    {
        "sentence": "By the time the guests arrived, she had cooked dinner.",
        "tense": "past_perfect",
        "tense_cn": "过去完成时",
        "desc": "过去某时刻之前已完成的动作"
    },
    {
        "sentence": "He said he would come to the party the next day.",
        "tense": "past_future_would",
        "tense_cn": "过去将来时",
        "desc": "过去看来将要发生的动作 (would)"
    },
]


__all__ = ["PRESET_SENTENCES"]
