# Message transport and recovery

## Native

1. Discover actually callable list_threads/read_thread/send_message_to_thread. Inspect the chosen existing ChatGPT target, including idle status. After an account switch, if the saved target disappeared, use an existing idle `kind=chatgpt` chat, perform a harmless exact-reply roundtrip, and rebind it automatically. Record ordinary Chat/model proof separately when visible; native tools may leave both unconfirmed and must not supply guessed labels.
2. Save the complete actual `read_thread` JSON (no hand-invented transcript) and run `bridge begin JOB --input baseline.json`. This claims the target against duplicate dispatch. Forward the exact `bridge prompt JOB` output to send_message_to_thread, omitting model/thinking. Save the actual receipt and run `bridge sent JOB --input receipt.json`.
3. Current observed wait_threads rejects ChatGPT targets. Only use it if the current tool explicitly supports this target; otherwise read_thread roughly every 20–30 seconds with maxOutputCharsPerItem=20000, interruptible waits and progress updates. Ten minutes per active turn is a bound, not evidence of failure. Leave the job pending if generation continues.
4. Save the complete actual response JSON; `bridge collect JOB --input response.json`. Pagination may be needed. A native exact matching turn may omit the requested marker when `read_thread` itself reports the turn completed and the thread idle; the job records `completion_proof: native_completed_turn`. Browser collection still requires the marker because page observation cannot provide the same completion contract. Truncated or incomplete results are rejected. Uncertain sends stay dispatching: inspect the same chat instead of resending. A collected job persists analysis.md and source response JSON.

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
