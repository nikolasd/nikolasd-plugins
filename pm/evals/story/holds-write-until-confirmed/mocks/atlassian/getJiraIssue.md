---
---
{
 "key": "PROJ-42",
 "fields": {
  "summary": "Self-service membership refresh",
  "issuetype": {
   "name": "Epic"
  },
  "project": {
   "key": "PROJ"
  },
  "description": "**Epic Maturity State:** Detailed Level Requirements Created\n\n## Objective\n\nLet support staff see group membership changes within five minutes instead of the next day.\n\n## Context\n\nGroup membership changes can take up to a day to appear because cached results expire only at midnight.\n\n## Scope\n\n**In-Scope:**\n\n- Cached membership results expire on a configurable schedule.\n\n**Out-of-Scope:**\n\n- Changes to how membership is edited.\n\n## Success Criteria\n\n- A membership change is visible to support within five minutes.\n\n## Non-Functional Requirements\n\n| NFR | Category | Requirement and threshold |\n| --- | --- | --- |\n| NFR-1 | Performance | A membership change is visible within 5 minutes. |\n\n## Personas\n\n| Persona | Type | Role | Primary actions |\n| --- | --- | --- | --- |\n| Support agent | Internal Staff | Handles access tickets. | Looks up current group membership. |\n\n## Technology Context\n\n**Platform / architecture pattern:** Single Python service.\n\n---\n\n## Delivery\n\n| Id | Story | Summary | Status |\n| --- | --- | --- | --- |\n| | Configurable cache expiry | Make the membership cache expiry a configurable TTL setting. | Not created |\n| | Expiry monitoring | Expose cache age and refresh failures as metrics. | Not created |\n\n**Epic is complete when:** support sees membership changes within five minutes.\n"
 }
}
