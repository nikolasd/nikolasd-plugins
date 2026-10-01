# User Interface Mockups Section Template

Use this structure to build the `## User Interface Mockups` section that is
written into the Epic or Story description by the calling skill. Apply the content rules to all
text. Repeat the per-screen block once for every agreed screen, in the order
the user reviewed them.

The image files themselves are not embedded by the skill. Each screen ends with
one closing line, chosen by how the screens were shown:

- PNGs rendered: `_Attach: [screen-slug].png_`, naming the file the user should
  drag onto the Epic or Story.
- Claude Design canvas: `_Mockup: [design-url]_`, the same link on every screen.
- Neither: `_No image is available for this screen; the description and
  annotations above are the record._`

Use the matching intro sentence below: attached images, the canvas link, or no
images.

```
## User Interface Mockups

_These mockups were produced for business review. They show the intended layout
and behaviour of each screen.
[Choose one: The screen images are attached to this [Epic or Story]. | The screens are in
a Claude Design canvas linked under each screen; the canvas is private until its
owner shares it. | No images accompany these mockups; the descriptions and
annotations are the record.]_

### Screen 1 - [Screen name]

**Primary persona:** [persona name and one-line role]

**Purpose:** [one or two sentences, written for a business reader, describing
what the user accomplishes on this screen]

**Description:** [a short paragraph describing the layout and the main content
of the screen as a business reader would understand it]

**Annotations:**

1. [Element or region] - [what it is and what it does]
2. [Element or region] - [what it is and what it does]
3. [Element or region] - [what it is and what it does]

**States shown:** [list the states that matter for this screen, for example
populated, empty, loading, error, and one line on how each differs. Omit this
line if only the populated state applies.]

[Closing line for the rung used: _Attach: [screen-slug].png_ | _Mockup: [design-url]_ | the no-image line]

---

### Screen 2 - [Screen name]

[Repeat the same block for each screen.]

---

### UI Open Questions

[Numbered list of any open UI questions the user could not resolve during the
session, stating what is undecided and which screen it affects. If there are
none, write "No open UI questions at this stage."]
```
