# Message transport and recovery

## Native

1. Discover actually callable list_threads/read_thread/send_message_to_thread. Inspect the chosen existing ChatGPT target, including idle status. After an account switch, if the saved target disappeared, use an existing idle `kind=chatgpt` chat, perform a harmless exact-reply roundtrip, and rebind it automatically. Record ordinary Chat/model proof separately when visible; native tools may leave both unconfirmed and must not supply guessed labels.
2. Save the complete actual `read_thread` JSON (no hand-invented transcript) and run `bridge begin JOB --input baseline.json`. This claims the target against duplicate dispatch. Forward the exact `bridge prompt JOB` output to send_message_to_thread, omitting model/thinking. Save the actual receipt and run `bridge sent JOB --input receipt.json`.
3. Prefer a target-specific event wait only when the current tool explicitly supports this target. The observed wait_threads rejects ChatGPT targets; do not repeatedly retry it. Otherwise probe with read_thread using turnLimit=1 and maxOutputCharsPerItem=1000. After the first probe, space unchanged checks about 45–60 seconds apart using interruptible waits; keep each blocking call at most 60 seconds and follow the host's progress-update requirements. Keep raw results outside model context where the tool permits; return only target status, turn/message IDs, truncation flags and whether a final candidate is visible. Do not print the prior answer or full request on every check. A compact probe is only a wake-up hint, never completion evidence. Ten minutes per active turn is a bound, not evidence of failure. Leave the job pending if generation continues; do not imply background polling without an explicit user request.
4. When idle or a final marker is observed, fetch the complete actual matching turn with maxOutputCharsPerItem=20000 (increase or paginate if needed) and save the actual response JSON; `bridge collect JOB --input response.json`. Pagination may be needed to locate the exact request and all its assistant messages. Do not assemble an invented completion transcript from compact probes. The collector selects the last assistant candidate after the exact request and before another user message, not the first progress update. A standalone final BRIDGE_DONE marker proves the marker path; without it, only a single unambiguous new assistant candidate in an exact completed native turn with an idle thread can pass (`completion_proof: native_completed_turn`). Multiple unmarked candidates, truncated pages/turns/messages, or missing exact requests remain pending. Browser collection still requires the marker because page observation cannot provide the same completion contract. Uncertain sends stay dispatching: inspect the same chat instead of resending. A collected job persists analysis.md and source response JSON.

These settings reduce repeated transcript handling and polling frequency; they do not establish a measured token-saving percentage. Report actual usage separately from estimates and never trade away exact-request or completeness checks to claim savings.

## Browser

Use the currently available browser tool and its documented API. Prefer the in-app browser unless the user selected a different browser. Do not require a particular obsolete skill/runtime. Use an existing ordinary chat the user authorized; create a new chat only when requested. Login/2FA/CAPTCHA is a user action.

Use one tab and its observed actual URL. Verify ordinary Chat and visible model label, bind the conversation ID from the URL. Save a browser observation JSON using ONLY the actual visible DOM/accessibility content:

```json
{
  "source": "browser-ui",
  "url": "https://chatgpt.com/c/observed-id",
  "generating": false,
  "messages": [
    {"id": "observed-message-id", "role": "user", "text": "exact observed text"},
    {"id": "observed-answer-id", "role": "assistant", "text": "exact observed text"}
  ]
}
```

IDs must come from the page. If the surface does not expose stable IDs or complete text, this strict adapter cannot verify the result: report the limitation and offer an explicitly manual handoff, never synthesize native-tool receipts. These files are operator observations, not cryptographic browser attestations.

Before sending use `bridge begin-browser JOB --input baseline-ui.json`. Paste/send the exact prompt once. Confirm it is visible. Leave state dispatching until collection; this avoids fabricating a native send receipt. Re-read the same tab after uncertain actions/timeouts. Poll generation with short bounded observations; do not resend, create extra chats, or change the model while pending. When complete, save actual UI text and run `bridge collect-browser JOB --input response-ui.json`.

Native ↔ browser recovery is allowed for the SAME conversation and job only after matching the original request. Do not redirect a sent job to another chat. Use cancel with an explicit reason only after deciding to abandon that job.
