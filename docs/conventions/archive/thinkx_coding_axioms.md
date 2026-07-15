> **原本(非規範・D-19)。正規化版が規範の材料。**
> この文書は「Coding Guide」(2022, wiki)の原本コピーである。編集しない。
> 正規化・層分解の結果は `docs/conventions/AXIOMS.md` / `SKILLS_INDEX.md` と
> 各リポジトリの `CLAUDE.md`、および `docs/conventions/NORMALIZATION_REPORT.md` に反映済み。

---

Coding Guide

Kazuki Otsuka edited this page on Feb 11, 2022 · 4 revisions
*must read it all

Axioms

1. Minimalism - A small number of principles to satisfy all

Physics explains a lot of things with a few laws.
The functionality of a framework will inevitably increase to satisfy more user levels.
And there are many ways to do the same thing.
But out of these, choose a basic and versatile way and use it only as long as it satisfies all your needs.

2. Uniqueness - The interface is the brand.

A product's interface is like a person's face, voice, or expression.
By being unique, people accumulate a brand in their cognitive identity.
In most cases, we avoid using ready-made goods and implement them originally.
Implement animations that move smoothly and naturally, like a living organism.

3. Speed - Fast response is the greatest feature.

The greatest advantage of a computer is that it can respond to a human request for something faster than the human can to return the same result.
A slow computer deteriorates the human brain.
A fast computer makes people want to ask for something again.
Being fast must be given priority over everything else in many cases.

Basics

Python Style Guide (Very Basic)

Google Python Style Guide *

Naming

Naming is super important.

・must be both necessary and sufficient.
・type/object must be clear. (eg. user_age, is_valid, dogs(=suggests a list), dog(=suggests a single dog object))
・subject/predicate must not be confusing. (eg. managed_account, blocking_user)
・past/future must not be confusing. (eg. saved_password, visiting_page)
・abbreviation is bad except special cases. (eg. item_dsc -> bad, lat/lon -> ok)
・write like an english sentence. (eg. if password.is_valid)
・be consistent.
・be clear that the role is "to be", "to do", "how" or "what".

main-qimg-5eec62f54a828e4d0ff7af16210aa7a9