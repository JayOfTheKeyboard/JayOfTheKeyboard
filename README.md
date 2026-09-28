# Jeremy Levartovsky

I build small tools for AI coding agents: Claude Code, Codex, MCP servers and agent skills.

By day I look after systems and infrastructure, and manage open source projects, for a not-for-profit in Australia. Everything here is personal work.

## Start here

- [ai-quota-meter](https://github.com/sigiletlabs/ai-quota-meter): shows your remaining Claude Code quota on the status line, using Anthropic's own numbers, and switches on Codex's built-in quota display. A single static binary with no network access.

New tools are released under [Sigilet Labs](https://github.com/sigiletlabs).

## Upstream work

Merged:

- [neuledge/context#125](https://github.com/neuledge/context/pull/125): only skip repo-meta filenames at the scan root
- [neuledge/context#126](https://github.com/neuledge/context/pull/126): Go module support for the docs registry
- [neuledge/context#166](https://github.com/neuledge/context/pull/166): skip test and example directories only at the repo root
- [yetone/magpie#88](https://github.com/yetone/magpie/pull/88): the gateway reports a Claude reply cut off by the context window as cut off
- [yetone/magpie#128](https://github.com/yetone/magpie/pull/128): gateway ids made in the same clock tick stay unique
- [Yeachan-Heo/oh-my-claudecode#4152](https://github.com/Yeachan-Heo/oh-my-claudecode/pull/4152): the git guardrail hook also catches `git --no-pager push` and other global options

In review:

- [NVIDIA/SkillEvaluator#168](https://github.com/NVIDIA/SkillEvaluator/pull/168): the PII scan stops reporting Chrome User-Agent versions as IP addresses
- [NVIDIA/SkillSpector#653](https://github.com/NVIDIA/SkillSpector/pull/653): piping plain data into an interpreter is rated low risk instead of remote code execution
- [microsoft/conductor#572](https://github.com/microsoft/conductor/pull/572): a `$` before a `{{ }}` expression no longer stops a workflow loading
- [stripe/link-cli#370](https://github.com/stripe/link-cli/pull/370): `--auth` without a path is refused instead of logging out the default session
- [vectorize-io/hindsight#4870](https://github.com/vectorize-io/hindsight/pull/4870): the MCP `recall` docs say what `max_tokens` counts
- [ahmad-a0/silverbullet-mcp#19](https://github.com/ahmad-a0/silverbullet-mcp/pull/19): the note-editing tools only write `.md` notes

Issues filed: [SkillSpector#638](https://github.com/NVIDIA/SkillSpector/issues/638), [#639](https://github.com/NVIDIA/SkillSpector/issues/639), [#640](https://github.com/NVIDIA/SkillSpector/issues/640), [SkillEvaluator#167](https://github.com/NVIDIA/SkillEvaluator/issues/167), [silverbullet-mcp#20](https://github.com/ahmad-a0/silverbullet-mcp/issues/20), [chrome-agent#12](https://github.com/captivus/chrome-agent/issues/12).
