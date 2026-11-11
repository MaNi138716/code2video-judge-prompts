"""
Minimal example demonstrating how to run bidirectional LLM judge evaluation using Gemini 3.8 Flash.
"""
import base64
import json
import os
import re
import urllib.request

PROMPTS = json.load(open("prompts.json", encoding="utf-8"))["prompts"]


def encode_video_b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def call_judge(api_key, brief, video_a_path, video_b_path, prompt_version="v1", fps=10):
    prompt_text = PROMPTS[prompt_version]["text"]
    part_a = {"inline_data": {"mime_type": "video/mp4", "data": encode_video_b64(video_a_path)}}
    part_b = {"inline_data": {"mime_type": "video/mp4", "data": encode_video_b64(video_b_path)}}
    if fps:
        part_a["video_metadata"] = {"fps": fps}
        part_b["video_metadata"] = {"fps": fps}

    body = {
        "contents": [{
            "role": "user",
            "parts": [
                {"text": prompt_text},
                {"text": "Brief (the instruction the models received):\n" + brief},
                {"text": "Video A:"}, part_a,
                {"text": "Video B:"}, part_b,
                {"text": "Now give your JSON verdict."}
            ]
        }],
        "generationConfig": {"temperature": 0, "responseMimeType": "application/json"}
    }

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    req = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        m = re.search(r"\{.*\}", text, re.S)
        return json.loads(m.group(0)) if m else {}


if __name__ == "__main__":
    print("Example ready. Set GEMINI_API_KEY and call call_judge().")
