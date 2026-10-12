# Reading a Confluence PRD

Read this in Phase 2 only when the PRD is a Confluence page. A local file, another URL or a written brief needs no Atlassian call, so a failed or denied call here must never block them.

## Resolve the cloud ID

Call `mcp__atlassian__getAccessibleAtlassianResources` once. If it returns one resource, use it. If it returns several, use the one whose `url` contains `site`; if `site` is `(unset)`, list them and ask which to use. Hold the chosen resource's `id` as `<cloud_id>`. If the call fails but `site` is set, use `site` as `<cloud_id>`.

## Read the page

Call `mcp__atlassian__getConfluencePage` with `<cloud_id>` and `contentFormat: markdown`.

## A server under another name

The tool names above are those of the official Atlassian MCP server registered as `atlassian`. If the session has the Atlassian server under another name, or with other tool names (for example `mcp__jira__getAccessibleAtlassianResources` and `mcp__jira__getConfluenceContent`), use that server's equivalent read-only tools the same way. If no Atlassian tool can read the page, say so and ask the user to paste the PRD text instead.
