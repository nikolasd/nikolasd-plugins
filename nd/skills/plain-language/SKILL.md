---
name: plain-language
description: Explains or rewrites text in everyday words, short sentences and active voice, keeping only the technical terms that carry meaning. Use when the user asks for plain language, says an answer was too jargon-heavy, or wants text rewritten for a non-specialist reader.
when_to_use: |
  Trigger phrases: "in plain language", "plain English", "explain it simply", "ELI5", "layman's terms", "too much jargon", "explain like I'm not an engineer", "rewrite this for a non-technical reader".

  Not this skill: authoring technical documentation, ADRs, architecture documents, code comments, commit messages, or PR descriptions — those keep their own technical register.
---

# Writing Plain Language

Plain Language means the reader understands on the first read.

## The recipe

Write to this shape:

- **Everyday words, short sentences, active voice.** "use" not "utilize", "to" not "in order to", "I implemented the cache" not "the cache was implemented". Split a sentence that runs past about 20 words.
- **Only load-bearing terms.** A technical term earns its place when it names something specific that a plainer phrase would lose — an API, a protocol, an error type, a component name. Define each on first use. To test one, drop it and reread the sentence; if it still says the same thing, leave it out.
- **Plain prose, not labelled bullets.** Write the idea as a sentence rather than opening a bullet with a jargon label and a dash. This holds inside technical explanations too: keep the necessary terms and use plain words around them.
- **Keep the meaning.** Do not lose a caveat, a number or a condition to make something simpler. If a plain wording would be wrong, keep the term and define it.
- **Keep code exact.** Code, commands and quoted identifiers stay as written.
- **Keep it up.** Once the user asks for plain language, hold this register for the rest of the conversation unless they say otherwise.

## Before / after

<Bad>
"Latency reduction — if your server is in Virginia and a user is in Singapore, that round trip adds real, noticeable delay. A CDN edge node in or near Singapore serves the same content in a fraction of the time. Origin offload — static assets get served from the edge cache instead of hitting your application servers and database every time."
</Bad>

<Good>
"A CDN is a set of servers spread around the world that store copies of your site's content close to your users. Someone in Singapore loading a site hosted in Virginia would otherwise wait for every request to cross the ocean and back — the CDN skips that by answering from a nearby copy instead."
</Good>

The good version drops "latency reduction", "edge node" and "origin offload" as headline jargon. It keeps "CDN" — that term is load-bearing — and defines it once.

Two habits the recipe above won't catch:

- Naming a framework, pattern or technique when a plain description says the same thing.
- Treating "this is a technical topic" as licence for technical wording throughout.
