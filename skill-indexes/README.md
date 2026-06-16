# Skill Indexes

Skill indexes are routing helpers, not skills.

They should curate which skills are useful for a category of task when automatic skill selection is fuzzy or underspecified.

Current expected use case:

- one conventional YAML index file points at multiple private, global, or environment-specific skills outside this repo or curates a personal skill bundle for use here

Current example artifact:

- `skill-index.example.yaml` demonstrates the current contract and schema
- `skill-index.yaml` is the untracked working copy used by the runtime when present

Discovery should be by convention, not config:

- runtime should only read `skill-index.yaml`
- `skill-index.example.yaml` is documentation and bootstrap material only
- if it does not exist, future tooling should ignore it and continue normally

Committed shared indexes are not a default requirement. Add them later only if the repository gains enough repo-owned skills that curated shared bundles become useful.
