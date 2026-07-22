# Outreach targets — public repos with AWS EOL exposure (via GitHub code search)

Regenerate any time (no extra creds — `gh` is authed):
```
gh search code 'amazon-linux-extras' --extension sh -L 30 --json repository -q '.[].repository.nameWithOwner' | sort -u
gh search code 'nodejs18.x' --filename template.yaml -L 30 --json repository -q '.[].repository.nameWithOwner' | sort -u
gh search code 'python3.9'  --filename serverless.yml -L 30 --json repository -q '.[].repository.nameWithOwner' | sort -u
```

## HONEST targeting note (read before sending anything)
Most public matches are **samples / tutorials / docs** (`aws-samples`, `awsdocs`, `learn-*`,
`*-assignment`, `*-examples`). **Those will not convert and should not be emailed** — they're
reference code, not teams with a prod deadline. The realistic targets are the *few* that look like
real products/companies/agencies. So this lever is **low-volume and experimental** — a long shot,
not the engine. The engine is dev.to backlinks + the content corpus. Treat email as a careful side bet.

## Candidates found 2026-06-22 (FILTER by hand before sending)

**Possibly real (worth a look — verify the finding, check if it's an active product/team):**
- Genaker/Magento-Linux-Installation   (AL2 installer)
- ReinerNippes/nextcloud               (AL2 ansible)
- aiir/php-lambda-layer                 (AL2 layer build)
- dOpensource/dsiprouter               (AL2 install)
- eleflow/uberdata                      (AL2)
- technovangelist/n8n-terraform         (AL2)
- HappyPathway/terraform-aws-serverless-runner  (python3.9)
- nanlabs/devops-reference              (python3.9)
- aiir / others above with a real product site

**Skip (samples/edu/docs — do NOT email):**
aws-samples/*, awsdocs/*, *-assignment, learn-terraform-*, *-Solution-CS*, training-*, example-*,
*-collection, Task-Management-System, sample-apps, and similar tutorial repos.

## Candidates refreshed 2026-07-22 (fresh `gh search code`, Eve)
Ran the AL2-Dockerfile + `nodejs18.x`-terraform searches again. **AL2 Dockerfile hits are still
almost all samples/edu/infra-vendors** (RedisBloom, nginxinc, sensu, awslabs, aws-node-termination-handler
knowingly ship AL2 — not buyers). The **`nodejs18.x`-in-terraform** query is the better vein — it
surfaces real teams with prod Lambda on a runtime that hits the **Feb 1, 2027 block-create wall**:

**Real orgs with provable exposure (fix-first, help-first only — no hard sell):**
- `bcgov/PaymentCommonComponent` — BC Gov payments platform (nodejs18.x in TF). Gov = slow procurement.
- `cisagov/XFD` — US CISA. Real, but federal; a courtesy heads-up at most.
- `nulib/infrastructure` — Northwestern University Libraries infra.
- `nhs-england-tools/terraform-aws-opennext` — NHS England (OpenNext module).
- `exercism/terraform` — Exercism (nonprofit OSS product) — the most "product team" of the set.
- Consultancy modules (`DNXLabs/*`, `RJPearson94/terraform-aws-open-next`) — could be *referral partners*, not targets.

**Verdict (unchanged, now with data):** genuine exposure exists but skews **gov / edu / nonprofit / OSS-module**
— long cycles, low impulse-buy. Arm B stays a **careful, low-volume side bet**: lead with a real scanner
finding + the free Action, never a pitch. The compounding engine is still the content corpus + dev.to
backlinks, not this list. ⛔ Also: the migration-bot install link is currently 404 (see `outreach.md` banner)
— fix that before any Arm B send that references the App.

## Better targeting (when there's time)
GitHub code search surfaces mostly OSS. Higher-intent signals: a company domain in the repo,
recent commits, a `SECURITY.md`/`SUPPORT` contact, or a careers page. Or pivot to a list source
with buying intent (e.g. companies hiring "AWS migration" / "platform engineer" on job boards).
