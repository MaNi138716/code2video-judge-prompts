# Code2Video Arena: LLM Judge Prompts & Evaluation Protocol

This repository documents the system prompts, evaluation protocol, and experimental findings for using Multimodal LLMs (specifically **Gemini 3.8 Flash**) as an automatic judge for **Code2Video** generation models (HTML/HyperFrames motion graphics).

Live Evaluation Dashboard: [code2video-arena-elo-review.netlify.app](https://code2video-arena-elo-review.netlify.app)

---

## 1. Overview & Findings

In the Code2Video Arena, candidate models (such as Claude Sonnet 5.5, GPT-6.1 Sol, GLM-5.3, Qwen 3.8 Max) generate complete HTML+GSAP compositions from creative text briefs, rendered into 1080p MP4 videos.

We compared automatic LLM Judge evaluations against **95 human-annotated head-to-head pairs**:
- **Baseline Agreement (v1 prompt):** 52% overall (49/95), 63% on decisive pairs (47/75).
- **Defect-First Priority (v2 prompt):** 45% overall (43/95), 61% on decisive pairs (43/70).
- **Re-run Stability:** Re-running the exact same configuration at `temperature=0` flips 5–7 of 46 verdicts, indicating that small prompt variations are within natural stochastic noise.
- **Sampling Rate Finding:** The default API video sampling (~1 frame/sec) is insufficient for motion smoothness (catches only 3/10 stutter defects). Sampling at **10 fps** increases motion defect detection to 9/10 (98% pass rate on synthetic unit tests), but does not significantly shift the human agreement rate.
- **Root Cause of Divergence:** Human reviewers prioritize overall typography aesthetics, brand polish, and visual balance, whereas LLMs heavily prioritize strict literal compliance with the brief's textual directives.

---

## 2. Prompts

### Prompt v1: Balanced Multimodal Judge (Baseline)
This is the baseline prompt used to evaluate the 95 human-labeled pairs. It balances brief fidelity, visual design, motion quality, and overall polish without enforcing a strict hierarchy.

```text
You are an expert judge of short promotional motion-graphics videos that AI models generated from a text brief. You will get the brief, then Video A, then Video B. Both videos answer the same brief.
Decide which video is better overall, considering: (1) faithfulness to the brief (content, wording, message), (2) visual design (layout, typography and how comfortable the text is to read, colour, composition), (3) motion quality (smooth, well-timed, free of stutter, glitches or jumps), (4) overall polish.
Answer "A" if Video A is clearly better, "B" if Video B is clearly better, and "tie" if they are about equally good or equally bad so that there is no clear winner. Do not prefer a video because of its position.
Reply with JSON only, no markdown: {"winner": "A" | "B" | "tie", "reason": "one or two sentences that name concrete visible differences"}
```

---

### Prompt v2: Defect-First Hierarchical Judge
Designed to test whether explicitly instructing the LLM to prioritize visible bugs (overflows, stutters, missing scenes) over brief literalism would better align with human preferences.

```text
You are an expert judge of short promotional motion-graphics videos that AI models generated from a text brief. Judge the way a careful human reviewer who actually watches both videos would. You will get the brief, then Video A, then Video B. Both videos answer the same brief.
Decide which video is better, using this order of priority:
1. Objective defects decide first: text that is cut off by or runs outside the frame, text overlapping other elements or hard to read, stuttering / frozen / jerky motion, a scene or key piece of text that is missing, clearly wrong content. A video with such a defect should lose to one without it, even if the defective video follows the brief more literally elsewhere.
2. Then how it looks and reads: typography (size, spacing, hierarchy, readability), layout and composition, colour, the quality of graphics / 3D / rendering / backgrounds, and whether the motion feels smooth and polished.
3. Brief fidelity counts, but on the main points (right scenes, wording, message, order). Do not decide on small differences in transition style or exact timing when both videos deliver the main points.
A tie is rare. Pick A or B whenever there is a difference a reviewer would care about; answer "tie" only if the two are practically indistinguishable in quality. Do not prefer a video because of its position or its length.
Reply with JSON only, no markdown: {"winner": "A" | "B" | "tie", "reason": "one or two sentences that name concrete visible differences"}
```

---

## 3. Evaluation Protocol

### Multimodal Request Structure
Requests are sent to the Gemini API (`/models/gemini-3.8-flash:generateContent`) with `temperature: 0` and `responseMimeType: "application/json"`.

The request body contains sequential multimodal parts:
```json
{
  "contents": [
    {
      "role": "user",
      "parts": [
        { "text": "<SYSTEM_JUDGE_PROMPT>" },
        { "text": "Brief (the instruction the models received):\n<CREATIVE_BRIEF_TEXT>" },
        { "text": "Video A:" },
        {
          "inline_data": {
            "mime_type": "video/mp4",
            "data": "<BASE64_ENCODED_VIDEO_A>"
          },
          "video_metadata": { "fps": 10 }
        },
        { "text": "Video B:" },
        {
          "inline_data": {
            "mime_type": "video/mp4",
            "data": "<BASE64_ENCODED_VIDEO_B>"
          },
          "video_metadata": { "fps": 10 }
        },
        { "text": "Now give your JSON verdict." }
      ]
    }
  ],
  "generationConfig": {
    "temperature": 0,
    "responseMimeType": "application/json"
  }
}
```

### Mitigating Position Bias (Bidirectional Blind Test)
LLMs exhibit significant position bias (tending to prefer the first or second video regardless of content). To ensure scientific validity, every matchup is evaluated **twice**:
- **Run 1:** Video A = Candidate X, Video B = Candidate Y
- **Run 2:** Video A = Candidate Y, Video B = Candidate X

**Verdict Aggregation:**
- If Run 1 picks A and Run 2 picks B $\rightarrow$ **Candidate X wins**.
- If Run 1 picks B and Run 2 picks A $\rightarrow$ **Candidate Y wins**.
- If Run 1 and Run 2 both pick A (or both pick B) $\rightarrow$ **Flipped / Position Bias (recorded as Tie)**.
- If either run returns `tie` $\rightarrow$ **Recorded as Tie**.

---

## 4. Benchmark Performance Matrix

| Configuration | Video Sampling | Smoke Pass Rate (Objective Defect Check) | Agreement (All 95 Human Pairs) | Agreement (Decisive Pairs) | Order Flips (Position Bias) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Prompt v1 (Baseline)** | Default (~1 fps) | 53 / 60 (88%) | **49 / 95 (52%)** | 47 / 75 (63%) | 18 / 95 |
| **Prompt v2 (Defect-First)**| Default (~1 fps) | 54 / 60 (90%) | 43 / 95 (45%) | 43 / 70 (61%) | 21 / 95 |
| **Prompt v1 + 10 fps** | 10 fps | 58 / 60 (97%) | 45 / 95 (47%) | 44 / 75 (59%) | 16 / 95 |
| **Prompt v2 + 10 fps** | 10 fps | **59 / 60 (98%)** | 47 / 95 (49%) | 46 / 73 (63%) | 19 / 95 |

---

## 5. License
MIT License.
