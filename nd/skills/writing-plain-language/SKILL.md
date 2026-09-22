---
name: plain-language
description: Use when the user asks for something explained in plain terms, says a previous answer was too jargon-heavy, or asks you to rewrite text for a non-specialist reader.
when_to_use: |
  Trigger phrases: "in plain language", "plain English", "explain it simply", "too much jargon", "explain like I'm not an engineer", "rewrite this for a non-technical reader".

  Not this skill: authoring technical documentation, ADRs, architecture documents, code comments, commit messages, or PR descriptions — those keep their own technical register.
---

# Writing Plain Language

Plain Language means the reader understands on the first read.

## The recipe

Write to this shape:

- **Short sentences.** Past roughly 20 words, split it.
- **Everyday words.** "use" not "utilize", "help" not "facilitate", "to" not "in order to".
- **Active voice.** "I implemented the cache", not "the cache was implemented".
- **Only load-bearing terms.** A technical term earns its place when it names something specific that a plainer phrase would lose — an API, a protocol, an error type, a component name. Define each on first use.
- **Plain prose, not labelled bullets.** Write the idea as a sentence rather than opening a bullet with a jargon label and a dash.

The last point applies inside technical explanations too: keep the necessary terms, and plain the connective tissue around them.

To test whether a term is load-bearing, drop it and reread the sentence. If it still says the same thing, leave it out.

## Before / after

<Bad>
"Latency reduction — if your server is in Virginia and a user is in Singapore, that round trip adds real, noticeable delay. A CDN edge node in or near Singapore serves the same content in a fraction of the time. Origin offload — static assets get served from the edge cache instead of hitting your application servers and database every time."
</Bad>

<Good>
"A CDN is a set of servers spread around the world that store copies of your site's content close to your users. Someone in Singapore loading a site hosted in Virginia would otherwise wait for every request to cross the ocean and back — the CDN skips that by answering from a nearby copy instead."
</Good>

The good version drops "latency reduction", "edge node" and "origin offload" as headline jargon. It keeps "CDN" — that term is load-bearing — and defines it once.

## Common swaps

| Reach for | Write instead |
|---|---|
| utilize, leverage | use |
| facilitate | help |
| in order to | to |
| robust solution | name the actual property — fast, tested, handles retries |

Two habits the swaps above won't catch:

- Naming a framework, pattern, or technique when a plain description says the same thing.
- Treating "this is a technical topic" as licence for technical wording throughout, instead of keeping only the load-bearing terms technical.
