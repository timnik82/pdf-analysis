# MCP Server Usage Guide

> **Purpose:** This document helps the AI assistant choose the optimal MCP server for documentation and code search tasks. Reference this guide when starting new sessions.

---

## Available MCP Servers

### 1. Context7 MCP

**Philosophy:** A curated, high-speed library of pre-processed code snippets from official documentation.

**Tools:**

- `resolve-library-id` - Converts library name to Context7-compatible ID (e.g., "Next.js" → `/vercel/next.js`)
- `query-docs` - Searches for code examples within the resolved library's documentation

**Strengths:**

- ✅ Fast, clean code snippets ready for immediate use
- ✅ Official documentation from popular libraries
- ✅ High-quality, curated content
- ✅ Minimal noise, highly token-efficient

**Limitations:**

- ❌ Limited to curated popular libraries only
- ❌ No private repo access
- ❌ No PDFs or custom documentation

---

### 2. Ref MCP

**Philosophy:** An iterative, research-focused tool for both public and private documentation.

**Tools:**

- `ref_search_documentation` - Searches web, GitHub, and private resources (repos, PDFs, Markdown files)
- `ref_read_url` - Reads URL content as Markdown with intelligent filtering

**Strengths:**

- ✅ Access to private GitHub repos and uploaded documents
- ✅ Reads PDFs and Markdown files
- ✅ Intelligent token filtering (e.g., 90K page → 5K relevant tokens)
- ✅ Session state remembers previous searches
- ✅ Deep-reads entire pages with full context

**Limitations:**

- ❌ Requires two-step process (search → read)
- ❌ More verbose output than pure snippet tools

---

### 3. Exa MCP

**Philosophy:** A neural search engine for the entire open web with specialized code context retrieval.

**Tools:**

- `web_search_exa` - General web search with content extraction
- `get_code_context_exa` - **Specialized** tool for finding code snippets across the web
- `deep_researcher_start/check` - Autonomous research agent for complex queries
- `crawling_exa` - Extract content from specific URLs
- `deep_search_exa` - Natural language web search

**Strengths:**

- ✅ Entire open web as source (not just docs)
- ✅ Finds real-world production code examples
- ✅ Neural/semantic search understands intent
- ✅ Configurable token budget (1K-50K)
- ✅ Deep research mode for complex topics
- ✅ Finds tutorials, blog posts, and GitHub implementations

**Limitations:**

- ❌ No private repo access
- ❌ May return non-official implementations

---

## Quick Decision Matrix

| Use Case | Best MCP |
|----------|----------|
| "How do I use X in [popular library]?" | **Context7** |
| Official syntax or API reference | **Context7** |
| Reading a specific URL deeply | **Ref** |
| Searching private repos or PDFs | **Ref** |
| Understanding internal/custom APIs | **Ref** |
| Finding real-world code examples | **Exa** |
| Troubleshooting obscure errors | **Exa** |
| Comparing tools or frameworks | **Exa** |
| Research on emerging technologies | **Exa** |
| "Show me how people implement X in production" | **Exa** |

---

## Code Snippet Capabilities Comparison

| Ability | Context7 | Ref | Exa |
|---------|----------|-----|-----|
| **Snippet Focus** | High | Medium | Very High |
| **Explanation Detail** | Concise | Detailed | Minimal |
| **Source Variety** | Curated libs only | Any URL/PDF/Repo | Entire Web + GitHub |
| **Real-World Examples** | Official docs only | Official + private | Best (production code) |
| **Token Efficiency** | Fixed snippet size | Adaptive filtering | Configurable budget |
| **Ready for AI** | Excellent | Good | Excellent |

---

## Example Queries by MCP

### Context7 Examples

```
"How do I use useEffect cleanup in React?"
"Supabase RLS policy syntax"
"Next.js 15 middleware authentication"
"Prisma findMany with relations"
```

### Ref Examples

```
"Search our internal API docs for rate limiting"
"Read this specific GitHub MDX file: [URL]"
"Find authentication patterns in our private repo"
"Extract info from this PDF manual"
```

### Exa Examples

```
"Find examples of WebSocket reconnection handling in production apps"
"Compare authentication patterns between Next.js and Remix"
"How are developers implementing Stripe Elements with Server Components?"
"Research current state of WebGPU support across browsers"
```

---

## Best Practices

1. **Start with Context7** for standard library questions - fastest and cleanest results
2. **Use Ref for depth** - when you need full context around a code snippet
3. **Use Exa for discovery** - when official docs don't have what you need
4. **Combine tools** - use Context7 for syntax, then Exa for real-world patterns
5. **All three can be active** - no performance penalty; AI chooses optimally

---

*Last updated: January 2026*
