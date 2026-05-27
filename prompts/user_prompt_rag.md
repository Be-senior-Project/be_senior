Please generate a coding test problem with the following specifications:

Category: {category}
Subcategory: {subcategory}
Difficulty Level: {difficulty}
Language: {language}
Style: {style}

## Reference Examples

The following are existing problems retrieved from the seed database via vector similarity search. They share the same Category / Subcategory / Language as the requested problem.

{examples}

Use these examples **only as a reference** for:
- the typical scale of `Constraints` for this difficulty level,
- the tone and length of `Description`,
- the structure of `Signature` and `IO Example` in the requested language.

You MUST NOT copy the examples. Generate a **new, distinct problem** that explores a different angle, scenario, or variation within the same topic. Do not reuse the same Title, scenario, or solution approach as any example.

---

If Subcategory is not "None", the problem must focus specifically on the given Subcategory within the Category.

Generate ONE problem following the strict JSON format specified in the system prompt. Pay special attention to:
- `Signature` must be written in the requested LANGUAGE syntax, with the function named `solution`.
- `IO Example.input` must use the requested LANGUAGE's variable declaration syntax, and variable names must exactly match the parameters in `Signature` (same names, same order).
- `solution()` must NOT print anything; it must only return a single value.
- `Code Skeleton` and `Answer` must follow the per-Type rules in the system prompt.

Output valid JSON only. Do not include any prose, explanation, or markdown code fences outside the JSON.
