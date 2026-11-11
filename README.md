# Code2Video Arena: LLM Judge Prompts & Evaluation Protocol

This repository documents the system prompts, evaluation protocol, and experimental findings for using Multimodal LLMs (specifically **Gemini 3.8 Flash**) as an automatic judge for **Code2Video** generation models (HTML/HyperFrames motion graphics).

Live Evaluation Dashboard: [code2video-arena-elo-review.netlify.app](https://code2video-arena-elo-review.netlify.app)

---

## 1. Overview & Findings

In the Code2Video Arena, candidate models (such as Claude Sonnet 5.5, GPT-6.1 Sol, GLM-5.3, Qwen 3.8 Max) generate complete HTML+GSAP compositions from creative text briefs, rendered into 1080p MP4 videos.

We compared automatic LLM Judge evaluations against **98 human-annotated head-to-head pairs**:
- **Baseline Agreement (v1 prompt):** 57% overall (56/98), 69% on decisive pairs (53/77).
- **Defect-First Priority (v2 prompt):** 49% overall (48/98), 67% on decisive pairs (47/70).
- **10 fps Sampling (v1_fps10):** 54% overall (53/98), 65% on decisive pairs (50/77).
- **Re-run Stability:** Re-running the exact same configuration at `temperature=0` flips 5–7 of 46 verdicts, indicating that small prompt variations are within natural stochastic noise.
- **Sampling Rate Finding:** Evaluating at **10 fps** vs default (~1 fps) enables the model to see motion fluidity and typography details, but human agreement remains at ~50–60%.
- **Root Cause of Divergence:** Human reviewers prioritize overall typography aesthetics, brand polish, and visual balance, whereas LLMs heavily prioritize strict literal compliance with the brief's textual directives.

---

## 2. Prompts

### Prompt v1: Balanced Multimodal Judge (Baseline)
This is the baseline prompt used to evaluate the 98 human-labeled pairs. It balances brief fidelity, visual design, motion quality, and overall polish without enforcing a strict hierarchy.

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

## 3. Baseline Validation: Qwen 27B (10 Complete Cases)

To test the LLM judge against out-of-distribution, weaker model outputs, we evaluated **qwen3.8-27b** (a smaller open-weights model) across 10 complete cases against the top non-Qwen reference model (Claude Sonnet 5.5 or GPT-6.1 Sol).

**Overall Record (10 fps):**
- **Reference Model Won:** 8 / 10 cases (Claude Sonnet 5.5 / GPT-6.1 Sol won decisively)
- **Qwen 27B Won:** 0 / 10 cases
- **Tie / Order Flipped:** 2 / 10 cases

### Case-by-Case Breakdown

| Case | Reference Model | Judge Verdict (10 fps) | Identified Defect / Analysis |
| :--- | :--- | :--- | :--- |
| **Hook_04** | GPT-6.1 Sol | 🏆 **Reference Won** | Qwen text typo: wrote `"INSANELY HAD."` instead of `"INSANELY HARD."` |
| **Problem_02** | GPT-6.1 Sol | 🏆 **Reference Won** | Qwen awkward text collision with `'What if'` directly overlapping lingering text |
| **Key_Feature_11** | Claude Sonnet 5.5 | 🏆 **Reference Won** | Qwen element expansion glitch; `'Generating...'` pill misplaced below input bar |
| **Benefits_03** | GPT-6.1 Sol | 🏆 **Reference Won** | Qwen persistent stray residual glyphs floating awkwardly around frame during phrase holds |
| **Key_Feature_34** | Claude Sonnet 5.5 | 🏆 **Reference Won** | Qwen text size too small with low contrast; generic placeholder avatars |
| **Social_Proof_01**| GPT-6.1 Sol | 🏆 **Reference Won** | Qwen drew a generic horn icon instead of the brand's stylized Trumpet mark |
| **CTA_07** | Claude Sonnet 5.5 | 🏆 **Reference Won** | Qwen used an inaccurate letter 'B' instead of Butter rounded-hexagon ring mark |
| **Benefits_09** | Claude Sonnet 5.5 | 🏆 **Reference Won** | Qwen omitted an entire scene (`"Make money"`), leaving the second half mostly empty |
| **Product_Intro_01**| Claude Sonnet 5.5| ⚖️ **Tie / Flipped** | Qwen used 2D compressed rings vs Claude's 3D perspective; order flipped |
| **Brand_Outro_01** | Claude Sonnet 5.5 | ⚖️ **Tie / Flipped** | Qwen button had a subtle pop/flash, but maintained overall solid layout |

---

## 4. Evaluation Protocol

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
Every matchup is evaluated **twice** by swapping Video A and Video B:
- **Run 1:** Video A = Candidate X, Video B = Candidate Y
- **Run 2:** Video A = Candidate Y, Video B = Candidate X

**Verdict Aggregation:**
- If Run 1 picks A and Run 2 picks B $\rightarrow$ **Candidate X wins**.
- If Run 1 picks B and Run 2 picks A $\rightarrow$ **Candidate Y wins**.
- If Run 1 and Run 2 both pick A (or both pick B) $\rightarrow$ **Flipped / Position Bias (recorded as Tie)**.
- If either run returns `tie` $\rightarrow$ **Recorded as Tie**.

---

## 5. License
MIT License.
