# Evidence contract

## What counts as evidence

A result counts only when the local `socai` command returned a JSON record with
a public HTTP(S) source URL. A search result is discovery evidence, not proof
that the post body, comments, or media were opened.

The compact projection may contain:

- public source URL;
- title, caption, description, or visible text;
- public author or account label;
- visible engagement counts;
- public media type.

## What must stay private

Never reproduce API keys, tokens, environment values, executable paths,
browser-profile paths, local artifact paths, run directories, command arrays,
or the unfiltered CLI payload. The script deliberately projects a small
allowlist of public fields.

## Claim limits

- A platform result is not independent verification of its claims.
- Missing visible metrics are unknown, not zero.
- An empty search can reflect the query, login state, a challenge, a rate
  limit, or live-site behavior; preserve the reported limitation.
- Do not infer popularity, identity, endorsement, or a broad trend from a
  small result set.
- Do not say a post was read in full when only its search card was captured.

## Access boundary

Stop on login gates, CAPTCHAs, challenges, and rate limits. Do not change an
account, publish, engage, message, switch browser profiles, or attempt an access
bypass. The bundled script exposes search only.
