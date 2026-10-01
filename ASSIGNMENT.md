# Assignment: Domain-Specific Tool-Calling Agent on Google Cloud Run

Build a domain-specific agent that calls tools, and deploy it to Google Cloud Run.

## What you're building

Think of a target user and problem for your agent to solve. There are no strict limitations on what this can be; take inspiration from your own life.

Build a web-based chat agent that uses tools to assist the user. Use `gemini-web-tool-calling.zip` as a starting point.

Your agent must:

- Remember the conversation across the session.
- Have at least three tools.
- Have at least one tool that makes a request for external data, such as an API or database.
- Have original tools. You need **one original tool per team member** that no other team in the class built. Every submission's tools will be compared against each other.
- Follow the tool-writing guidance from the lecture: name and describe your tools and their arguments well, and handle errors gracefully, relaying actionable information to the model.
- Show its tool calls. Keep the starter's `/chat` response shape: `response`, `session_id`, and `tool_calls` with the `name`, `args` and `result` of every call. Showing tool calls in your UI is encouraged.
- Have a frontend that is different from the base `gemini-web-tool-calling.zip` and makes it clear what the agent is and how to use it.

The exact requirements are vague by design. The most important part of this assignment is being creative with it.

## README

Each agent must come with a `README.md` that describes the project and lists **three sample queries** for the grader to test with.

## How it's graded

Course Assistants will clone your repo and use your deployed agent in a browser.

| Section | Points | What we assess |
| --- | --- | --- |
| Basics | 1 | A README and a valid `submission.json`. |
| Functionality | 11 | Deployed and reachable. Clear purpose. Answers example queries correctly. Calls tools when it should. Follows the conversation and keeps sessions separate. |
| Tools | 8 | At least one tool uses external data. Tools are well written and called appropriately. |
| Creativity | 5 | At least three tools. Original tools no other team built. A frontend changed from the starter. The agent does something interesting. |

Larger groups come with larger expectations: one original tool per team member.

## How to submit

Submit your GitHub repo URL on Courseworks. One person submits per group.

### Repo

At the root of the repo:

- `app.py`, `pyproject.toml` and `uv.lock`
- `README.md`
- `submission.json`, listing every team member's Columbia UNI or email in `authors`, including your own:

```json
{"deploy_url": "https://your-agent.example.run.app", "authors": ["abc1234", "xyz9876"]}
```

Private repos are fine. Add these GitHub accounts as collaborators (Settings > Collaborators > Add people): `codeboi07`, `bhuvighosh3`, `nniishhh`, `x`.

### Deployment

- Deploy to Cloud Run with continuous deploy from GitHub, following "Deploying to Cloud Run from GitHub".
- Keep it running until grades are released.

## Use of coding agents

Coding agents are encouraged, but you are expected to understand the code you submit, and it should reflect the style of agents covered in class so far.

## Peer review rubric (non-credit, peer-style critique only; 15 pts)

| Criterion | What it asks | 5 | 4 | 3 | 2 | 1 |
| --- | --- | --- | --- | --- | --- | --- |
| Experience & Usefulness | USE THE AGENT. Did it actually work for you? Focus on your real experience, not what you imagine it could do with more polish. | **Wow**: immediately intuitive, results made me think or see something differently. | **Impressed**: smooth, results genuinely useful or interesting. | **Functional**: understood it, got it working, results okay but not memorable. | **Bumpy**: got the general idea, but struggled to get useful results. | **Lost**: couldn't figure out what it does or how to use it. |
| Risk-Taking & Ambition | READ THE CODE. Did the creator push beyond what was comfortable or expected? Ambitious failures count more than safe successes. | **Full send**: genuinely bold, even if rough around the edges. | **Real swing**: clearly difficult or unfamiliar, made real progress. | **Solid push**: meaningfully outside their comfort zone, mixed results. | **Toe in the water**: one small stretch beyond the requirements, mostly safe. | **Safe bet**: did exactly what was asked, nothing more. |
| Originality & Voice | Does this project feel like the creator made it their own? | **One of a kind**: no one else in the class would have built this; reflects real curiosity and a distinct perspective. | **Their own thing**: clear point of view, deliberate personal choices. | **Getting there**: some creative choices hint at a perspective. | **Light touch**: one or two personal choices, mostly the obvious path. | **Off the shelf**: feels like a template; could be anyone's project. |
