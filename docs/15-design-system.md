# Design system

A design system is a knowledge-plane artifact, not a design deliverable. In a factory where
agents write the user interface, it is the only place a human designer's intent survives after
the designer leaves the room. This document says what the artifact contains, where it sits in
the four layers of [04-knowledge-plane](04-knowledge-plane.md), how it enters the build loop,
and what the kvart adoption measured on 2026-09-07.

## Why this is a knowledge-plane layer and not a style guide

Three separate readers need it, and only one of them is a person.

- **The builder reads it before writing a screen.** Without it, an agent asked for "an
  apartments page" reconstructs the visual language from whichever three pages it happened to
  open. That is the same cost specs exist to remove ([04-knowledge-plane](04-knowledge-plane.md)),
  applied to the frontend: current state has to be readable without being re-derived per ticket.
  Re-derivation does not just cost tokens, it drifts. Two agents reconstructing "how a card
  looks" from different samples produce two card styles, and neither is wrong locally.
- **The verify gate reads it to have something to check against.** The browser QA pass of
  [06-verify-gate](06-verify-gate.md) walks every UI surface a diff touches. A QA pass with no
  declared standard can only find crashes, console errors and untranslated strings. With one, it
  can find "this page invented a modal where the standard says drawer" and "this table has no
  empty state". The finding class changes from broken to wrong.
- **The intent survives its author.** A design decision made once, in a review, in a canvas, or
  in a chat message, is gone by the next session. Written next to the value it explains, with
  its date, it is still there in six months. kvart's card radius went 8px in the canvas, 32px in
  the implementation, then down to 24px because the owner judged 32px too aggressive. Only the
  last number is in the code. All three are in the design system, and the middle one is why
  nobody re-raises the first `[measured 2026-09-07]`.

Which layer it sits in: the team layer. It describes one product across its repos, it is written
by agents and merged by the code owner, and code repos bind to it rather than carry it. Same
topology as the spec store and the memory store.

That is the shape kvart has: the design system is derived from the code and the code is the only
thing that ships. When the design system is its own repository with its own commits (a package
the product repos install, a home for design-tool exports a product repo reads, a structural
catalogue), it is a repo in the loop as well as a knowledge layer. See
[the design-system repo in the loop](#the-design-system-repo-in-the-loop).

## The rule that makes it true rather than aspirational

**A token that no code reads is not a standard, it is a suggestion.**

Two thirds of kvart's original 2026-08-09 canvas token file was never implemented, and nothing
noticed for a month `[measured 2026-09-07]`. The mechanism that prevents a repeat is an ordering
rule with a check behind it:

1. The value changes in the application code first.
2. The same pull request mirrors it into the design-standards repo, into both token formats,
   which must always agree.
3. The dated rationale travels with it. A token change without its reason is how the system lost
   its history the first time.

The check, for the one rule that had a mechanical form worth building: kvart swept 942 hardcoded
corner-radius classes into a single CSS card primitive and left a build gate behind that fails
when the hand-rolled pattern regrows `[measured 2026-08-11]`. It is wired into the project's
validation script, so an agent-built page cannot silently replant the forest that was just
cleared. Everything else in the catalogue is advisory: it will look wrong, and the QA pass may
say so, but nothing refuses.

That asymmetry is the honest state of the layer. One rule out of 28 is enforced. The rest rely
on being read.

## Repo shape

| Part | Contents | Why it exists separately |
|---|---|---|
| `tokens/tokens.css` | CSS custom properties: colour scales, semantic tones, typography, radius, elevation, motion, spacing, control sizes, each block citing its source file and dated reason | what a stylesheet can include directly |
| `tokens/tokens.json` | the same values as structured data, each with `value` (shipped), `canvas` (the design-file value where it differs) and `shipped: false` where a canvas token was never implemented | what a tool can read: a prototype generator, a linter, a future diff |
| `patterns.md` | 28 numbered layout and behaviour conventions in plain language, plus "planned but not shipped" and "anti-goals" | how a screen is arranged, readable by a PM |
| `components.md` | the catalogue: 31 entries covering one layout shell, 9 design-system primitives, the CSS card primitive, 5 console shell components and 15 cross-cutting components, with everything else listed by path | what already exists, so a new page composes instead of inventing |
| `demo/demo.css` | one self-contained stylesheet, tokens inlined plus utility classes for buttons, inputs, cards, badges, tables, page headers and empty states | a throwaway prototype that looks like the product with no framework and no build step |
| `origin.md` | lineage from the design canvas through the refresh rounds to the owner's adjustments, plus the divergence log | why the values are what they are |
| `origin/design-handoffs/` | the recovered canvas artifacts: the original token file and two 2026-08-09 handoff bundles with their artboard prototypes | provenance, kept verbatim |

Counts as of 2026-09-07: 28 patterns, 31 catalogued component entries, 20 divergences, 14 canvas
tokens marked `shipped: false`.

### Why both token formats are kept

They serve different readers and neither subsumes the other. The CSS file is what a page or a
prototype includes. The JSON file is what a program reads, and it carries a field the CSS cannot:
the canvas-versus-shipped split.

That split is the interesting part. Each token records what shipped and, where it differs, what
the design file said. A token the canvas defined and the code never implemented is present and
marked `shipped: false` rather than deleted. Deleting it would lose the information that someone
intended it; keeping it unmarked would make the file lie about the product. The marked form makes
the gap queryable: 14 tokens in kvart's case, mostly an alias layer the canvas added so that dark
mode would be a one-line swap, on a product that later closed the door on dark mode deliberately.

The cost of two formats is that they can disagree. That is why the update rule says both files or
neither, in the same pull request.

### The origin bundles

The design work started on a canvas in a design tool, which exported handoff bundles: a spec
written against the product's stack, an artboard prototype as HTML, and a runtime file to open it.
Those exports were zipped into a documentation folder and git-ignored, which is the normal fate of
a design handoff and the reason design intent usually evaporates.

They were recovered on 2026-09-07 and are kept verbatim as provenance: two bundles from
2026-08-09 plus the canvas token file `[measured 2026-09-07]`. They are explicitly not the source
of truth. Where they disagree with the implemented CSS, the implementation wins and the canvas
value is recorded beside it as history.

Keeping them costs a few hundred kilobytes and answers a question that is otherwise unanswerable:
was this value a decision or an accident. The live canvas URLs were not recorded anywhere, and the
repo carries an explicit gap for the owner to fill. A design system that cannot point back at its
canvas has already lost half its provenance.

### The divergence log

A divergence is one difference between what the design file specified and what the code shipped.
Not a bug and not a violation. It is a fact with three possible readings, and the log's job is to
force the reading to be chosen rather than left ambiguous:

- **the implementation is right** and the canvas is superseded (kvart: the base radius was raised
  so the derived scale would land on round pixel values; the font is self-hosted because the
  content security policy would have blocked the canvas's font import outright)
- **the canvas is right** and the code has drift to fix
- **the canvas value was never load-bearing**, so it is recorded and closed (kvart: an eight-step
  type scale as tokens, against an app that defines no size tokens at all)

kvart's log holds 20 divergences as of 2026-09-07: 12 changed in implementation, 5 defined in the
canvas and never implemented, 3 added by the implementation with no canvas equivalent
`[measured 2026-09-07]`. The palette itself survived contact with the code apart from one shade,
which is the log's most useful single finding: it says the disagreements are about structure, not
about taste, so the next canvas should spend its effort on the alias layer and the type scale
rather than re-picking colours.

Who resolves one: the code owner, in the role that owns the visual product. Not the agent that
found it. An agent may open a divergence and propose the reading; adopting one is a decision, and
it lands as a line in the log with its date. This is the same authority split as accepting a
quality-ratchet site into a baseline ([05-sensor-stack](05-sensor-stack.md)): the machine reports
the difference, a person decides what it means.

## How it enters the loop

| Stage | What happens | Class |
|---|---|---|
| SPEC | a ticket touching UI names the patterns and components it expects to use, so the reviewer can tell invention from reuse, and carries the agreed prototype as an attachment so the builder reads arrangement, states and copy from it rather than inventing them (decided 2026-09-09) | `designed` |
| BUILD | the builder reads `patterns.md` before planning a screen and `components.md` before writing one; the token files supply exact values | `measured 2026-09-07` |
| BUILD (prototype) | a PM workspace prototype skill includes `demo/demo.css`, reads `patterns.md` for arrangement and `components.md` for naming, and produces a throwaway page that looks like the product with no build step | `measured 2026-09-07` |
| VERIFY | the browser QA pass checks the walked surfaces against the patterns, not only against crashes and console errors; the page tree the CLI runtime writes per surface (roles, names, heading order) is the input for that check (adr/0008) | `designed` |
| VERIFY (mechanical) | the card-primitive gate fails the build when the hand-rolled pattern regrows | `measured 2026-08-11` |
| LEARN | a UI-changing pull request carries the token mirror in the same diff; pattern and component text may follow after | `designed` |

The write-back rule is the same one specs follow, with one difference worth naming. Specs are
derived from the code by retro-generation. Design tokens are derived from the code too, but their
*intent* comes from a canvas that is not in the code, so the artifact has two upstreams and can be
hand-edited in neither. The value comes from the implementation. The reason comes from the canvas
or from the owner's recorded adjustment. Editing the design-standards repo directly, without
either upstream moving, produces exactly the failure the whole layer exists to prevent: a standard
that no code reads.

## What kvart measured

All on 2026-09-07 unless the row says otherwise.

| What | Number | Note |
|---|---|---|
| When the repo was created | Day 1 of the context-standard bootstrap, 2026-09-07 | same day as the spec and decision-record bootstrap |
| Method | reverse-engineered from the implemented frontend | every token value read out of 3 named source files; every relative path checked to exist before it was written |
| Patterns catalogued | 28 | plus a "planned but not shipped" section and an anti-goals section |
| Components catalogued | 31 entries | 1 layout shell, 9 primitives, 1 CSS primitive, 5 console components, 15 cross-cutting |
| Divergences logged | 20 | 12 changed in implementation, 5 never implemented, 3 implementation-only |
| Canvas tokens never implemented | 14 | marked `shipped: false` rather than deleted |
| Handoff bundles recovered | 2, from 2026-08-09 | recovered from git-ignored archives in the product's docs folder |
| Rules with mechanical enforcement | 1 of 28 | the card primitive gate, from 2026-08-11 |
| Debt the gate was built to hold back | 942 hardcoded radius classes swept into 1 primitive | `[measured 2026-08-11]` |
| Frontend inventory behind the refresh | 59 pages, 121 components | `[measured 2026-08-11]` |
| The refresh's load-bearing finding | the app declared a font family and shipped no webfont at all | the content security policy would have blocked the remote import anyway; resolved by self-hosting 8 variable subsets |

The font finding deserves a note beyond its size. It sat in the code for months, invisible in
every screenshot, because the fallback stack rendered something plausible. No test asserts a
typeface. A design system built by reading the code is an audit of the code, in the same way that
spec retro-generation is ([04-knowledge-plane](04-knowledge-plane.md)): the act of writing down
what is true finds the places where nobody had checked.

## Designed versus measured

**Measured.** The repo exists and was built on Day 1 by reading the shipped frontend. Its counts
are counts of what is in it. Builders and the prototype skill read it. The card gate runs in the
project's validation script and has been failing regrowth since 2026-08-11.

**Designed, not yet exercised.** The QA pass checking against `patterns.md` rather than only
against rendering and console output. The same-PR token mirror as a habit that survives a busy
week: it is a written rule with no check, and the divergence log is what a broken week looks like
after the fact.

**Not built.** A mechanical token diff between the design-standards repo and the application's
stylesheet, which would turn the mirror rule from etiquette into a gate. That is the obvious next
piece: the values are already in a structured file with named source paths, so the check is a
comparison, not an inference. Until it exists, this layer holds one gate and 27 conventions, and
the honest description is a knowledge artifact with a single ratchet attached, not an enforced
system.

## The design-system repo in the loop

A design-system repository is part of the flywheel. Every repository whose changes reach a
product gets the same loop as the product repo: a ticket at the head of the work, the context
standard and the memory binding, the sensors, the verify gate, the ledger, and a spec write-back. A repository outside the loop is where changes land with no ticket,
no review and no record, and a design system is the worst place for that: one change reaches
every product that installs it.

### Four shapes, one rule

The group runs three shapes next to kvart's, checked on 2026-11-09 `[measured 2026-11-09]`:

| Shape | What the repo holds | Where a value comes from | What ships |
|---|---|---|---|
| derived (kvart) | tokens, patterns, components written by reading the shipped frontend | the product code | nothing; the product repo ships |
| package | a token package and a component package, synced from the design tool, released with versioned changesets, with a generated-output check and visual tests | the design tool, through a sync step | a versioned package; product repos install or vendor a copy |
| export home | the design tool's exports pulled on a weekly schedule, an inventory, tests on the pull | the design tool | the exports; one product repo reads them |
| structural catalogue | categories, rules and past decisions as machine-readable files beside the design tool | the design tool for values, the repo for structure | nothing; designers and agents read it |

The rule from the top of this document holds in every shape: a value nothing reads is a
suggestion. What changes is the direction of the mirror. In the derived shape the product code
moves first and the design-standards repo mirrors it in the same pull request. In the package
shape the design-system repo moves first, releases a version, and each product repo adopts that
version in a pull request of its own. Writing kvart's ordering rule into a package repo would
invert it: the product would edit a value the next sync overwrites.

### What the loop looks like in a package repo

| Stage | In the product repo | In the design-system repo |
|---|---|---|
| ticket | the product ticket that needs the change | its own ticket, linked from the product ticket; the product ticket is blocked on it, not merged around it |
| BUILD | adopts the released version, never edits the vendored copy | the sync from the design tool, then the component change; the generated-output check proves the committed output matches the sync |
| VERIFY | browser QA against the patterns | the visual tests are the browser QA leg; the consort panel and the scanner run as on any code repo |
| SHIP | merge and deploy | the release step publishes a version; done for the design-system ticket means released, not merged |
| LEARN | the product spec names the version it depends on | the component catalogue is the spec layer: `retrogenerate-specs` treats each component as a feature |

Two failure modes this shape adds, with the check each one needs:

- **Edited vendored copy.** A product repo that vendors the package can edit the copy in place,
  and the next adoption silently reverts the edit. Check: the vendored directory is a no-touch
  zone in the product repo's `AGENTS.md`, and a fence fails a diff that touches it outside an
  adoption pull request `[designed]`.
- **Version drift.** Each product repo pins its own version, so the same component can differ
  between products for months. Check: the divergence log gains a second axis, released version
  against each consumer's pinned version, written at each release `[designed]`.

### Which team context it binds to

A design-system repo serves more than one team. It binds to the team context of the team that
owns it, and its tickets live in that team's tracker project. Each consuming team's front-door
`CLAUDE.md` names the design-system repo and the version it pins, so a builder in a product repo
can find the source without guessing. A change a consuming team needs is a ticket in the owner's
tracker, linked from theirs; a direct pull request from the consuming team goes through the same
gate and the owner merges it.

### Onboarding it

Scaffold it with [deploy/02-scaffold-a-project.md](../deploy/02-scaffold-a-project.md) like any
code repo, in the same Day 1 as the product repos it serves. The project checker needs no special
case for the package and export shapes: run against the three group repos on 2026-11-09 it reported 18, 21 and 20 MISSING lines,
every one an unwired loop artifact (header, binding, sensors, hooks, ruleset, gate jobs, ledger)
and none a design-specific false alarm `[measured 2026-11-09]`. A structural catalogue with no
build still gets the header, the binding, the ruleset, the ledger and the panel; the sensors that
read source code (cleat, enola) have nothing to read there. Record that skip in its ADR 0001; the
checker still prints those two lines as MISSING, because it has no flag for a repo without source
code, so the run record names them as the expected residue.

## For an adopter

The minimum useful version is not the kvart shape. It is three files:

1. The tokens, in whatever format the code already reads, with a source path and a dated reason
   per block.
2. The patterns, numbered, in plain language, including the anti-goals. Anti-goals do more work
   than rules here, because an agent asked to make something look good will add decoration unless
   told not to.
3. The component catalogue, so the builder composes instead of inventing.

Add the divergence log the first time a design tool and the code disagree, which will be the first
week. Add the canvas artifacts before someone deletes the zip. Add a gate for the one convention
whose violation you can express as a pattern match, and accept that the rest are advisory until a
QA pass reads them.
