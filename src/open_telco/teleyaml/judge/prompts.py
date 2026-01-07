from textwrap import dedent


SCORE_PATTERN = r"(?i)\$FINAL_SCORE\s*:\s*([0-9]+(?:\.[0-9]+)?)"

# Templates are based on:
# https://github.com/openai/evals/blob/main/evals/registry/modelgraded/closedqa.yaml


JUDGE_TEMPLATE = dedent("""
    You are comparing a submitted answer to an expert answer on a given question. Here is the data:
    [BEGIN DATA]
    ************
    [Task]: {question}
    ************
    [Rubric]: {rubric}
    ************
    [Submission]: {answer}
    ************
    [END DATA]

    Evaluate the submission based on the rubric.

    {instructions}
""").strip()


JUDGE_INSTRUCTIONS = dedent("""
    Based on the rubric, reply with '$FINAL_SCORE: $NUMBER' (without quotes) where NUMBER is the final score.

    First, write out in a step by step manner your reasoning about the criterion to be sure that your conclusion is correct. Avoid simply stating the correct answers at the outset. Then, end with your final score formatted as '$FINAL_SCORE: $NUMBER' (without quotes) where NUMBER is the final score.
""").strip()
