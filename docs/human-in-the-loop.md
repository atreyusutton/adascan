# The human aspect

The part everyone underestimates.

## The arithmetic that forces the issue

`[E]` At 20% of pages needing review at 3 minutes each, a **10,000-page job is 100 hours
of human work.**

You cannot do that yourself while finishing a degree. So one of two things has to be
true:

1. The pass rate is high enough that the number drops, or
2. You have help.

**Plan for both.**

## Your first hire is not a salesperson

It's a **reviewer** — someone who knows Acrobat's accessibility tooling. These people
exist; the remediation industry trains them, and you can hire contract hourly.

**Your job is to build a review tool good enough that a reviewer clears a page in
30 seconds instead of 3 minutes.**

That tool is a **product surface, not an internal script**. Every minute shaved off it
goes straight to gross margin — it moves the single most important variable in
[`economics.md`](economics.md) without improving the model at all.

## Hire a screen reader user for final QA

Someone blind or low vision who actually uses **JAWS or NVDA** daily, reviewing samples
from every batch.

Three reasons, all of them real:
- It is the **best quality signal available** — nothing else tells you whether the
  output is actually usable
- It is the **right thing to do**
- In a sales conversation about accessibility it is **worth more than any certification
  you could put on a slide**

## A human signs off on every delivered batch

Not because the machine is necessarily wrong, but because **when a resident files a
complaint, someone accountable needs to have looked.**

That's the liability posture, and it's what separates this from an overlay vendor. The
sign-off is recorded in the audit log (Stage 6 in [`architecture.md`](architecture.md))
along with what changed on which document and who approved it.

## What this means for the product

The review tool is not a back-office afterthought. It is:
- the lever on gross margin
- the mechanism of accountability
- the thing that makes the honest hybrid pitch credible instead of a hedge

Build it like a product.
