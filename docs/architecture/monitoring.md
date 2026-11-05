# Monitoring

There are no servers. The maintainer monitors the public repo and the demo store; each user's own Action reports to that user.

| Signal | Source | Threshold | Alert to | Reviewed |
|---|---|---|---|---|
| Store index rebuild failure | User's store Action | any failure | store owner, by GitHub email | on failure |
| Stale index at boot | `sp boot` header check | index older than newest entry by over 10 min | user, one line in boot output | every boot |
| Public repo CI failure on main | GitHub Actions | any failure | maintainer | daily |
| Demo store release run | release checklist | any story failing | maintainer | each release |
| Setup failure reports | issues labelled `setup-failure` | over 10% of new issues in a month | maintainer | weekly |
| Stars and traffic | `gh api repos/{owner}/{repo}` and `/traffic/views`, `/traffic/clones` | below plan in prd.md success metrics | maintainer | weekly |
| Boot size growth | `index/builds.md` boot_chars in the demo store | over 7,000 characters | maintainer | each release |

## History
GitHub traffic data is kept for 14 days. A weekly scheduled workflow in the public repo appends stars, views, clones and open issues to `docs/metrics/history.csv`, so the success metrics have a full record.
