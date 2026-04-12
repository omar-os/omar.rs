---
title: "Introducing OMAR"
description: ""
date: "2026-04-12"
author: "Shaokai Lin, Karim Elmaaroufi, Matei Zaharia, Sanjit Seshia"
---

## Can one person run a unicorn company in the future?

Imagine, you are the CEO, leading hundreds of non-stop AI agents to solve humanity's biggest problems.

That is the vision we have for **Open Multi-Agent Runtime** (`omar`), a TUI for creating powerful agentic organizations.

## The 10,000x engineer

<blockquote class="twitter-tweet" data-media-max-width="560"><p lang="et" dir="ltr">10000x Engineer <a href="https://t.co/zLwGV3q7a9">pic.twitter.com/zLwGV3q7a9</a></p>&mdash; shafu (@shafu0x) <a href="https://twitter.com/shafu0x/status/2019854429848236051?ref_src=twsrc%5Etfw">February 6, 2026</a></blockquote> <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>

## Open Multi-Agent Runtime

While the 10,000x engineer is clearly productive beyond our wildest dreams, they remain elusive and difficult for the average engineer to ever match in skills. Today, we significantly close the gap between the average engineer and the 10,000x engineer by introducing **Open Multi-Agent Runtime** (`omar`).

`omar` is a multi-agent orchestration system managed through an easy to use text user interface (TUI) built on top of `tmux`, the powerful terminal multiplexer tool you probably already know and love. With `omar`, you can tackle massive problems that are easily solved by multi-agent systems without ever having to manually handle orchestration, `Ctrl+Tab` to cycle and context switch through terminals, or directly manage the consoles of tens of Claude Code screens like our 10,000x engineer.

We demonstrate `omar` on several problems and find that `omar` can perform tasks that often are not trivial or even possible for a single agent. With `omar`, you benefit from:
*(ideally these are each hyperlinks to the sections of the blog down below that definitively show that omar can do this)*
- **Deep hierarchies**: Agents managing agents, teams, and organizations just like a company.
- **Scalability**: create or remove teams of tens or hundreds of agents without the need of direct human interaction
- **Heterogeneity**: Let different agent backends collaborate as a team.
- **Full control**: Talk to, monitor, and control any agent in any level of the hierarchy you want.
- **Life span**: Long-running or ephemeral agents, your choice.

Other features include messaging system integrations (e.g., Slack), computer use, support for classic `tmux` commands, and several existing agent coding tools (e.g., Claude Code, Codex, etc.). 

## Demo

Enjoy a demo of `claude`, `opencode`, `codex`, and `cursor` agents working together as a team. 

[![asciicast](https://asciinema.org/a/836739.svg)](https://asciinema.org/a/836739)

Try out this demo by sending the following prompt to the Executive Assistant (requires more than one agent backends installed):
```
Run https://github.com/lsk567/omar/blob/main/prompts/tests/project-factory.md and use different agent backends for the subagents spawned.
```

## How omar works

At its core, `omar` is a TUI that begins with one agent the **Executive Assistant** (EA). This agent is the main point of contact for a user interacting with an army of agents, hence One Man Army. While `omar` allows users to manually create their own agents, the real force multiplier kicks in when our EA can spawn several agents which in turn can spawn their own teams of agents quickly leading to hundreds of agents working towards solving the user's goal.

### User interface

`omar` has two kinds of entry points: (1) a TUI that serves as the "mission control" (shown in the demo above), (2) messaging apps, e.g. Slack, that relay messages to the Executive Assistant.

The `omar` TUI is built on top of Ratatui, a Rust-based TUI framework. We realized that, in a large agentic organization, the user might be working with hundreds of agents simultaneously, thus the TUI was built with navigating hierarchy in mind (*not sure about this sentence*).

### Communication and scheduling

Communication between agents is orchestrated by the `omar` server, which has an internal event queue. When agent `A` sends a message to agent `B`, agent `A` sends an HTTP POST request to the `omar` server with the following format:
```json 
{
    "sender": "A",
    "receiver": "B",
    "timestamp": 1773768458704306000,
    "payload": "Execute the following task: ..."
}
```

Upon receiving the message, the server inserts a new event into its event queue, which globally orders events in timestamp order. When it's time to deliver the message, the server pops the event from the queue and executes `tmux send-keys` to type the message into the target agent's session.

The same event queue is used for scheduling future tasks, which are highly useful for implementing *cron jobs* in `omar`. Cron jobs are essentially a special type of event that carries a predefined period. When a cron job fires, the `omar` server automatically reschedules it based on its period.

## omar in action

### Creating infinite robotics data

Large Language Models (LLMs) have seen much success partly because scaling laws (Kaplan et al. 2020, Hoffmann et al. 2022) have delivered their promise of improved performance as we have scaled up data. According to [Epoch AI](https://epoch.ai/data-insights/dataset-size-trend), dataset sizes have doubled roughly every six months and are currently at 10<sup>14</sup> - 10^<sup>15</sup> tokens of text. 

In contrast, even the largest robot datasets such as Open X‑Embodiment, and the real‑robot data behind models like RT‑1 and π₀ contain at most 10<sup>6</sup>–10<sup>8</sup> action‑labeled interaction steps. 

To put this into a physical perspective, consider the sun which is about one million times the volume of the Earth. If LLM training text were the Sun, all current real‑robot interaction data for manipulation would easily fit inside a single Earth. 

Even with this massive scale advantage, LLMs are still scaling up further. Consider the latest popular open source models like Minimax, Kimi 2.5, Trinity, Qwen 3 and Nemotron-3 which all credit synthetic data generation as a significant reason for unlocking next-level capabilities. 

With `omar`, we can ask, how can we scale up robotics data in a similar manner? 

#### Introducing [LIBERO-Infinity](https://github.com/KE7/libero-infinity)

LIBERO is a popular robotics learning benchmark that was initially centered on lifelong, sequential knowledge transfer in manipulation tasks but later became popular for evaluating and eventually training Vision Language Action (VLA) models. Recently models like SmolVLA and 𝜋<sub>0.5</sub> easily score above 90% on LIBERO, so are we ready for VLA-powered robots? Not quite. 

Works such as, [LIBERO-Pro](https://arxiv.org/abs/2510.03827) by Zhou et al., recently found that these VLAs are merely memorizing the trajectories packaged with the benchmarks. When you perturb (i.e., change) something seemingly pointless like the color of a mug or where the mug is initially placed, these state-of-the-art VLAs often drop to 0% success. Prior work from NVIDIA (COLOSSEUM benchmark 2024) also found that similar collapses of success rates occur in non-VLA robotics models and ultimately, the models that did do well across perturbations also better bridge the sim-to-real gap. Given that, in both cases, these perturbations were hand designed and finite in size, how can we scale to practically infinitely many while doing so with just one engineer and `omar`?

##### [Scenic](https://scenic-lang.org)

Scenic is "a domain-specific probabilistic programming language for modeling the environments of cyber-physical systems". Perfect for robots! It's also been used by Boeing, Meta, Toyota, and many others for testing autonomous systems. The problem is that Scenic is domain specific and thus it's often out of distribution for LLMs. [ScenicNL](https://arxiv.org/abs/2405.03709) by Elmaaroufi et al. demonstrated that while LLMs cannot write domain specific languages, compound AI systems can. 

Inspired by ScenicNL, we ask `omar` to similarly create a team of role playing agents to go through Scenic's public documentation and code to produce a [Claude skill](https://github.com/KE7/scenic-skills). This skill is all that we use to enable agents in `omar` to implement and use Scenic code which powers LIBERO-Infinity. In other words, a team of ~10 agents orchestrated by `omar` produced an artifact that allows a single agent to now write Scenic code. This whole process took less than an hour and is more capable than the ScenicNL system which took academic researchers several months to implement. 

##### Scaling LIBERO up to Infinity

We ask `omar` to explain the 130 base BDDL or tasks of LIBERO, the five environments, and then propose ideas for how we can generalize them. `omar` on its own proposes a team of 9 agents: 5 for each LIBERO env, and 4 for the LIBERO subtasks.

With that context and a few rounds of back and forth with my EA, we settled on the following perturbations:
  - position - randomizes object (x, y) placement over the workspace
  - object - swaps the object’s mesh/texture using the variant pool
  - camera - perturbs the agentview camera pose and tilt
  - lighting - perturbs light intensity, position, and ambient level
  - texture - changes the table-surface texture
  - distractor - adds 1-5 non-task objects as clutter
  - background - perturbs wall and floor textures
  - articulation - perturbs fixture state, like drawers/doors/stoves, by sampling their initial joint state
  - combination - you may compose two or more of the above perturbations

Armed with the ability to write Scenic and a plan of the perturbations that we want, we let `omar` work on this for a few days. Every few hours, we check in to provide testing feedback (we watch simulation videos for `omar`) and occasionally instruct `omar` to perform refactors. `omar` on its own was able to discover concepts like containment (e.g., if I displace an object that has objects inside it like a ball inside a cabinet, the ball should move with the cabinet so it stays inside) and implement code to support that as well as tests to prevent future regressions.

In total, `omar` produced LIBERO-Infinity in one week. For context, such projects would often take academic researchers several weeks if not a full semester. Lastly, while we do not explore it in this blog, we point out that by using Scenic, we've enabled LIBERO to connect with Scenic's companion tool, [VerifAI](https://verifai.readthedocs.io/en/latest/), which would allow for falsification-guided adversarial search over the Scenic distribution, i.e., we can formally identify failure modes of our robot policies. 

### Deep Research - March Madness Style 🏀

American college sports and especially basketball is unparalleled in any other country. The talent is the best in the world and fans from all over the world tune in to watch. This year's 68-team playoffs, known as March Madness, has already broken records. Broadcasting rights were sold for over $1 billion. 

As of the start of this year's tournament no one has ever predicted all 63 games correctly (i.e., formed a correct bracket). 

> If every game were a true 50/50 coin flip, the odds of picking a perfect bracket would be 1 in 9.2 quintillion.
> 
> In reality, fans use stats, matchups, and basketball knowledge to guide their picks. Even then, the odds are still estimated to be around 1 in 120 billion.

[Fox Sports](https://www.foxsports.com/stories/betting/kalshi-1-billion-dollar-perfect-bracket-challenge-march-madness-2026)

This problem is so hard that even the prediction market, Kalshi, offers anyone a chance to win [$1 billion](https://kalshi.com/billion-dollar-bracket) if they form a perfect bracket. 

#### Omar's Turn

As Fox noted, one can improve their bracket by using basketball knowledge. However, if I wanted to include all sources of information like news and analyst recommendations, I would need days if not weeks to consolidate the information. Instead, what if I use an army of coordinated agents to do the research I planned to do? Commanders and generals leading teams in different domains, working all in parallel to gather every signal available and culminate it all into one bracket? With `omar` it's now possible to do this in a controlled and digestible manner.

We give our EA in `omar` the following prompt:
> "I want to build an NCAA winning bracket. I need you to select the teams for me to do this. We will need to spawn a massive set of agents. We will need teams to read the news about all teams in the tournament as well as every individual player on each team. We need to consider both news and social media profiles of the players to see if they have been locked in. We should also look for historical information and metrics stuff like based on a teams seasons stats do those stats go on to predict anything about the playoffs? For example, KenPom and rule of 2 are interesting metrics that come to mind. We should also be robust and have agents debate each other. These debate agents can also critique the brackets of professional analysts who have already published theirs as a way to include additional information in our research process. The net result should be a hierarchy of agents at least three layers deep with a total number of agents in the range of 50 to 100 agents working to create the best possible bracket."

As you can see, the prompt is not exhaustive but it includes things that the average college basketball viewer may not know like the KenPom metric. 

Our EA creates a single agent -- `ncaa-master` -- to sit at the top and manage everything. The `ncaa-master` then goes on to identify 7 domains and creates a manager for each one. 
- `news-mgr` Breaking news, injuries, coaching changes for all 68 teams
- `social-mg` Player Twitter/Instagram/TikTok — morale, lock-in, drama
- `stats-mgr` KenPom, NET, SOS, pace, 3PT risk, FT rate, Rule of 2
- `matchup-mgr` Region-by-region matchup modeling, style clashes, Sweet 16 paths
- `debate-mgr` Adversarial FOR/AGAINST debate agents for every contested pick
- `analyst-mgr` ESPN, CBS, Jay Bilas, Joe Lunardi, The Ringer, Action Network brackets

As we watched these 6 managers spin up, we recalled that we missed a critical information source: Vegas. Had we directly used the deep research feature from somewhere like Gemini or leverage the background agents feature in Claude Code, this would have been the end of our experiment as we would have had to stop it and restart with this additional information. These existing products do not provide users a way to directly interact with any subagent. However, `omar` allows this. Thus, we swap over to the `ncaa-master` and give it an additional instruction:

> We forgot to include Vegas itself, so this is futures from gambling market, such as Caesars bets, and DraftKings.

The `ncaa-master` quickly responded by adding a 7<sup>th</sup> manager:
- `vegas-mgr` DraftKings, Caesars, FanDuel, BetMGM futures, spreads, line movement

At this point, we were happy with our managers and our One Man Army was quickly growing in size. 

![image](https://hackmd.io/_uploads/rk9Xkm99bx.png)

As the experiment progressed, the `ncaa-master` was not pleased with the breadth of information and would further create 12 more managers to cover 12 additional deep research domains: referee tendencies, venue proximity, travel logistics, practice reports, tournament experience, NIL signals, Reddit intel, talent grades, academic eligibility, transfer cohesion, prediction markets, and situational stats. In total hundreds of agents were spawned but we observed a peak of 110 agents running simultaneously.  The entire process took slightly under two hours. 

Needless to say, we have entered our bracket into Kalshi with Arizona as the projected winner.

### How well can agents trade on prediction markets?

Project site: [https://omarmy.ai/kalshi](https://omarmy.ai/kalshi)

One of the most exciting (and somewhat scary) questions is whether agents can make money on their own. The prerequisite of becoming an agentic unicorn is the ability to bring in some positive cashflow. In addition, can a team of agents outperform a single agent? 

#### Setting up agents in `omar`

To answer these questions, we created two teams of agents: a single-agent "baseline trader" and a multi-agent "quant firm." Both teams use the Claude Code backend with Opus 4.6. Both teams started out with $200 each and an independent Kalshi account.

Every hour, both teams are woken up by `omar` cron jobs and each executes a trading loop, which includes doing research, identifying trade opportunities, and executing trades using Kalshi APIs. `omar`'s support for deep hierarchy made it possible to spawn two independent teams of agents under the top-level Executive Assistant, who delivers an experiment report on slack every six hours.

<figure style="text-align: center;">
  <img src="https://hackmd.io/_uploads/Bk7UH6D9bx.png" alt="description">
  <figcaption>Figure 1: Both teams running on omar  (March 9, 2026).</figcaption>
</figure>

The baseline trader was launched on March 7, 2026. Without explicit prompting, the baseline trader (Claude Code with Opus 4.6) chose a strategy focusing on macro bets, in particular, WTI oil prices and CPI in February/March. The quant firm, on the other hand, started on March 9, 2026, and chose to bet on GDP and NYC/Miami weather the next day.

#### Performance comparison

We have been running the experiment for a month and observed some surprising results. Overall, the solo trader has been outperforming the quant firm significantly. The figure below shows the total account value of both teams with key events annotated.

<figure style="text-align: center;">
  <img src="/blog/introducing-omar/performance.png" alt="Performance comparison as of April 11, 2026.">
  <figcaption>Figure 2: Performance comparison as of April 11, 2026.</figcaption>
</figure>

Here is Claude Code summarizing what happened based on both teams' trading data and reflections:

> On March 7, two AI-run trading desks each opened a Kalshi account with $200. Five weeks later one sits at **$242.96 (+21.5%)** and the other at **$55.17 (−72.4%)** — a $188 gap, or 94 percentage points, between identical starting lines. The quant firm blew itself up on day one: its four-agent team spotted what looked like a slam-dunk weather bet (NWS forecast Miami at 89°F, Kalshi's 87°F YES contracts trading at 1–6¢) and piled 43% of the bankroll into 2,100 contracts on a single city's afternoon temperature. The portfolio ripped to **$292 in six hours — up 46%** — and then the sea breeze came in. Miami topped out at 84.2°F, three degrees short. In binary markets close is zero. The position crashed from $292 to $142 in minutes and settled at $108 the next morning, down 45.6% before the firm had finished its third cycle.

> The baseline trader, meanwhile, did nothing dramatic. A single agent with no org chart quietly opened 13 small positions across CPI strikes, WTI oil thresholds, and GDP bets — some as tiny lottery tickets at 1¢. When the Iran-driven oil shock hit and inflation repriced, baseline had exposure to every story: CPI-Mar T1.2 went +250%, CPI-Apr T0.5 went +140%, WTI T100 settled YES for +$9.60, and by March 22 every single one of its 18 positions was green, the book ticking a new ATH at **$283.45**. The quant firm spent the same weeks searching for a formula — v1 through v9 each tried a different shape of team, and none of them found edge fast enough to outrun the day-one hole. A v8 weather bot briefly looked like the answer, netting +$28 on April 2, then miscalibrated and gave back −$40 over the next two days. On April 8–9 oil crashed, the bot failed again, and the account fell to **$30.91** — down 85% from start. Shaokai pulled the plug: full liquidation to $55.17 cash, 0 positions.

> That liquidation wasn't the end of the story — it was the reset that made **v10** possible. With the book flat and no pressure to chase, the firm has rebuilt itself around a rigorous research pipeline: every strategy now has to clear a seven-gate backtest (win rate, profit factor, p-value, drawdown, calibration error, sample size, BH-FDR family correction), then pass a dual audit, then earn a CONDITIONAL_PASS before anything goes live with real capital. In the last 48 hours alone the pipeline has produced six CONDITIONAL_PASS candidates — cpi-headline-mom, shelter-cpi, payrolls, canada-cpi-yoy, jp-cpi-mom, kxnfprod — and the scanner keeps surfacing cross-source discoveries every cycle. The baseline trader is still ahead by a mile, and will be for a while, but for the first time since day one the quant firm has a way to know whether a strategy is real before it sizes into it. The Miami bet never had to clear a single one of those gates. The next one will have to clear all seven.

#### Quant firm's dynamic restructures

To make the quant firm run more efficiently, we gave the firm head, a Claude Code agent, the authority to adjust the firm's organizational structure anytime, i.e., "firing" or "hiring" agents, similar to what a real company would do.

The firm head agent has evolved the organizational structure nine times since launch.

> • **v1: Full Team** (Mar 9) — Opened for business like a real trading desk in miniature: four AI agents with job titles — researcher, risk manager, executor, bookkeeper — coordinated by the firm head typing messages into their terminals. About 80% of those messages never got delivered.
> 
> • **v2: Event-Based Coordination** (Mar 9) — Same four agents, but communication moved to a proper messaging system. Reliability went from 20% to 100%. The org chart finally worked the way it was drawn — unfortunately, by then the account was already down to $108 from the Miami weather disaster.
> 
> • **v3: Lean Team** (Mar 11) — Noticed the executor and bookkeeper were sitting idle 95% of the time waiting for something to do. Laid both of them off. The firm head absorbed the bookkeeping and started calling in an executor only when there was actually a trade to place.
> 
> • **v4: Solo Operator** (Mar 14) — Took the logic to its conclusion: fire everyone. The firm head operates alone by default and only spins up specialists on "big news" days — inflation reports, Fed meetings, sudden market moves. Maximum efficiency.
>
> • **v5: Parallel Research Desks** (Mar 18) — The efficiency was real but it wasn't the problem. Running solo, the firm head kept falling in love with the first idea it found and ignoring everything else. Fix: spin up three specialist researchers in parallel at the start of every cycle — one for oil, one for inflation, one for everything-else — and run the third one on a different AI model so it can disagree with the other two.
>
> • **v6: Research-Driven Firm** (Mar 31) — Added a fourth desk whose only job is to hunt for themes the firm isn't already trading. Also raised the risk dials: the old limits were so cautious they were blocking trades the research desks wanted to make, and research you can't act on is just expensive reading.
> 
> • **v7: Horizontal Scale** (Apr 1) — The new opportunity hunter kept choking trying to scan all 9,000+ Kalshi markets in one sitting, so its job got split ten ways — ten narrow scouts each covering one beat (Fed, jobs, housing, politics, weather, crypto, and so on), all running at once. The insight: in the world of AI agents, bodies are cheap; what's expensive is attention.
> 
> • **v8: Bots + Agents** (Apr 2) — Introduced the first actual bot — not an AI agent, real Python code with hard-coded limits it physically could not break. Some trading edges don't need judgment, they need discipline, and code is better at discipline than any AI. The weather bot won $28 its first day.
>
> • **v9: Pipeline-Driven Firm** (Apr 5) — Then the weather bot lost $15 the next day and $25 the day after. The parameters had been tuned on one lucky day of live data — classic rookie mistake. Response: a formal four-stage pipeline. From now on, no idea reaches real money without a written hypothesis, a backtest on months of historical data, acceptance gates, and daily monitoring. No more guessing.
>
> • **v10: Coordinator Model** (Apr 8) — The pipeline was good on paper, but in one cycle the firm head got busy and skipped the risk check, missing a catastrophic drawdown. Fix: the firm head no longer does anything — it only dispatches. Every step of every cycle is handled by a dedicated subagent, and the risk check is now its own agent that physically cannot be skipped. The pipeline has since produced six new strategy candidates that cleared a seven-test gauntlet, all queued for a final audit before any real money touches them.

<figure style="text-align: center;">
  <img src="/blog/introducing-omar/org-changes.png" alt="Quant firm's organizational restructures.">
  <figcaption>Figure 3: Colored regions represent the quant firm's organizational restructures.</figcaption>
</figure>

Figure 3 shows the performance curve with an overlay of organizational restructures. We are curious to see whether the quant firm can eventually outperform the baseline through continuous evolution of the team structure and changes of strategy.

#### An ongoing experiment

Back to the first question: Can agents make money on their own? The answer is "yes and no." While the baseline agent was up ~22.7% after a month, the quant firm agents collectively were down ~72.4%.

Also, can a team of agents outperform a single agent? Our data so far are negative, but this is too soon to tell. In the `lesson_learned.md` maintained by the quant firm periodically, an entry says:

> **Diverse models for high-stakes decisions.** When conviction is borderline, get a second opinion from a different model (e.g., o3 via opencode). Two independent analyses > one deeper analysis.

We still believe that multi-agent interactions could unlock potential not accessible by a single agent. Therefore, we are cautiously optimistic that, with heterogeneous backend models triangulating for better insights and a functional organizational structure, the quant firm might outperform the baseline eventually.

We also stumbled upon another insight. When a prompt is complex and an agent has been fed the same prompt multiple times in a single session, the agent starts to cut corners and skip critical steps in the instructions. This is a known phenomenon called "context rot," and we observed it when feeding a big skill file on how to run a trading cycle to the quant firm agent. With `omar`, we fixed this issue by letting a persistent parent spawn ephemeral subagents for every step in the instructions using the `omar` APIs. When a subagent starts with a fresh context, it follows the instructions much more faithfully.

Because of `omar`, performing this experiment is made much easier compared to launching coding agents in separate windows that provide no means for communication. At the time this blog is written, the Kalshi experiment is still running live. Check out agents' live trading data at [omarmy.ai/kalshi](https://omarmy.ai/kalshi).

## AI Safety

Having the ability to efficiently control tens or even hundreds of agents can be a scary thought. While there is nothing stopping the 10,000x engineer from performing malicious acts with their agents, `omar` does indeed make such attempts more manageable for the average engineer. This is inherent in any multi-agent product, especially ones that support heterogeneous mixtures of agents, and an active area of research we deeply care about.

Another one of our concerns when using teams of agents is traceability and compartmentalization. In organizations of people, we ensure the former by having conversations with managers and stakeholders to receive work and report updates on work that is done. For example, in software companies this information may be communicated as JIRA tickets. The latter is done through access management where employees are given the minimum access to accomplish their daily tasks. In our example, this could be providing employees with source code access to only their teams' code as opposed to all code in the company. As such, we are currently developing safety features in `omar` that implement traceability and compartmentalization.

**Before we release these features, we strongly recommend installing OMAR in a sandboxed / non-critical environment to remain safe.**

### OMAR's safety timeline

Here is a recent real-world example of the dangers of unchecked agent access, where [an AI assistant (Claude Code) was given excessive permissions and ended up deleting a developer's entire production environment, including its database and all backups, erasing over two years of records in seconds (Tom's Hardware)](https://www.tomshardware.com/tech-industry/artificial-intelligence/claude-code-deletes-developers-production-setup-including-its-database-and-snapshots-2-5-years-of-records-were-nuked-in-an-instant). 

Such issues are further compounded in multi-agent systems like `omar` not only because there are multiple agents that can do damage, but also because it becomes harder for an individual to track the work and changes created by each agent. In our NCAA bracket example, how does one check the files touched by over 100 agents? What about the work completed? The problem quickly becomes intractable. 

In `omar`, while we haven't yet solved this problem, we have made it traceable through logging. All agents regardless of their backend are directed to provide justification for why they are taking *"any significant action"*. In our experiments, we found that this phrasing led to a moderate amount of logging where agents aren't logging every file they read but they are logging file modifications. Each action logged with a timestamp, the agent's Chain of Command, the reasoning for taking that action, and why the action aligns with the user's goal. We find that this Action Justification & Reasoning Alignment is a good first step towards addressing Multi-Agent Safety. While agents can lie and take actions that are not faithful to their explanations, they report to the `omar` API, we emphasize that this is no different from an agent that would lie to a user and take malicious actions. You probably wouldn't have run such agents on your system anyway. `omar`'s logging API may not prevent agents from erasing over two years of records, but it does provide a way for one person to track the actions of teams of agents. 

Lastly, with regards to role access that would limit agents to only have write access to files related to their tasks, this is a feature under active development and will be released soon 🚀 !


## What's next

We're working on a few exciting features:

- Supporting multiple executive assistants for ultra large teams of agents (think thousands).
- better sandboxing through docker containers
- access role management for agents
- More to come!

Check out the [docs](/docs/) to get started, and join our [Discord](https://discord.gg/X76PSzmfWr) to connect with the community.

Star us on [GitHub](https://github.com/lsk567/omar) if you find `omar` interesting.

`omar` is made with ❤️ at Berkeley, CA.