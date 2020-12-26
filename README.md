[![codecov](https://codecov.io/gh/romantolkachyov/yaaccu/branch/master/graph/badge.svg?token=T3GB8PGG4E)](https://codecov.io/gh/romantolkachyov/yaaccu)

# Yet another accounting

Fast-api based service implementing base accounting functionality
like creating an accounts and transfer funds between them.

Features:

* 100% coverage (TBD!)
* strong consistency guarantees
* fast transactions (minimal lock design using "two-step commit")
* RSA key-pair based auth
* account ownership; only the owner of the private key can transfer funds (FIXME)
* transaction signing; allowing clients to prove transaction origin and check data integrity (TBD)
* integrity audit; allowing clients to check data corruption or identify possible attacks on the storage (TBD)
* accounting rules (TBD)
* yeh, we use Decimal for calculations; but it should not surprise you, really

## Why?

1. It is a critical part of the common functionality of the many products
2. It is hard to share your accounting package when it becomes amateur (because of p.1)
3. It is hard to improve it in the production environment (because of p.1)
4. It is boring stuff, but there is the p.1

So, many products has bad accounting because of these reasons. And, because existing solution doesn't 
meet requirements.

Yaaccu is a simple but powerful service you can use in your infrastructure. It is not a library/package
because the service form limits your intention to make things complex. Yaaccu is business-agnostic, 
so you should store business-specific information in the application db etc.

## Getting started

There is a docker-compose way for a while.

```shell
docker-compose up -d
```

will do the job.

* Service url: http://localhost:8000/
* Swagger: http://localhost/docs/
* ReDoc: http://localhost/redoc/

## Concept

__Account__ — main entity of the accounting holding balances for each system currency and 
defining main balance rule. There are three types of account defining possible balance:

* `active` — the balance of the account should be always greater or equal to 0
* `passive` — only negative balance or the balance equal to 0 allowed
* `normal` — any balance allowed

Operations will fail if any of these checks on involved accounts have fail. Every account associated
with public key or can be used by the client.

__Document__ — is a primary accounting document. It holds a set of operations and commitment status. The closest
analogy is a ledger record, but we can hold more than single transfer, and we're not limited with exactly
two involved accounts.

__Operation__ — is a part of a document describing balance change of a single account in a single document.

__Currency__ — is a unit of measurement for account balances. It is not a classic currency like USD and might be
something like "legs count" if have such a buisness need to count legs (and control their count never drops below zero).
There is no built-in way to convert one currency to another, you should implement this in a separate service.

### Two-step commit

We use so-called "two-step commit" technic to prevent heavy db locks and allowing high api throughput.
It means it is not enough to commit document and all it's operations to apply balance changes. There is also
a `committed` flag on the Document which should be set to `True` before balance changes will be applied.

Between the first (document and operations creation) and the second step (commit) application must exit any
transactions and check consistency of the document against new documents, and against committed 
only, then. The first check is required to ensure there is no conflicting documents created while we were
isolated in our transaction (it is why we need to exit any transactions first): we must rollback our document
because the other client may be passed consistency check before we created our record, so we will introduce 
an inconsistency if we will commit. And, we need the second check against only committed documents (including
our one) to ensure we don't relying on uncommitted changes.

This way we can overcome heavy table-wide locks caused by consistency check if we were relied on single-step
schema involving db-transaction only.
