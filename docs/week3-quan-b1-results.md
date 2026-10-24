# Week 3 Phase B1 Evidence: Isolated SQS Standard vs FIFO Benchmark (`b1-2026-10-24`)

## 1. Scope & Provenance

- **Experiment Type**: Bounded, isolated SQS API benchmark (`Phase B1` only).
- **Sample Cap**: `20` messages per scenario (`60` total messages sent, received, and deleted across 3 sequential runs). This is a **bounded 20-message/scenario isolated SQS API experiment**, **not** the full Week 3 runbook 50-message/scenario target, **not** a proof of maximum sustainable SQS throughput, and **not** an end-to-end Producer -> SQS -> Consumer -> DynamoDB benchmark.
- **Base `main` Commit**: `71095c0e362af41c9740a94990ccb7087a29486e`
- **Benchmark Script**: `scripts/benchmark_sqs.py` (unchanged; git blob SHA-1 `b827bf7ece8b109d5dd05c0fda1aa0dbe27f12dd`, file SHA-256 `7b8e7f718eceb2326be6ec30bf49f8b5c858137949619989b36369d97a20cff8`)
- **Execution Window (UTC)**: `2026-10-24T05:42:52Z` to `2026-10-24T05:44:03Z`
- **AWS Region / Target Account**: `us-east-1` / `<ACCOUNT_ID>` (12-digit AWS account ID redacted in committed public repository evidence; raw QueueUrls, ARNs, credentials, and session tokens omitted).
- **Evidence Artifacts (`docs/evidence/week3/quan/b1-2026-10-24/`)**:
  - [`manifest.json`](./evidence/week3/quan/b1-2026-10-24/manifest.json)
  - [`standard/benchmark-summary.json`](./evidence/week3/quan/b1-2026-10-24/standard/benchmark-summary.json) & [`standard/benchmark-results.csv`](./evidence/week3/quan/b1-2026-10-24/standard/benchmark-results.csv)
  - [`fifo-single/benchmark-summary.json`](./evidence/week3/quan/b1-2026-10-24/fifo-single/benchmark-summary.json) & [`fifo-single/benchmark-results.csv`](./evidence/week3/quan/b1-2026-10-24/fifo-single/benchmark-results.csv)
  - [`fifo-multi/benchmark-summary.json`](./evidence/week3/quan/b1-2026-10-24/fifo-multi/benchmark-summary.json) & [`fifo-multi/benchmark-results.csv`](./evidence/week3/quan/b1-2026-10-24/fifo-multi/benchmark-results.csv)

---

## 2. Isolated Benchmark Queue Configuration

Both isolated benchmark queues were created in `us-east-1` during Phase B1 with zero Lambda event source mappings (`0` ESMs) and no DLQ redrive policy, ensuring complete isolation from production `orders-queue` and `orders-dlq`:

| Queue Name | Queue Type | ARN (Redacted) | CreatedTimestamp | VisibilityTimeout | MessageRetentionPeriod | SSE | FIFO Attributes | ESMs | Retained Post-Run |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `orders-benchmark-standard` | Standard | `arn:aws:sqs:us-east-1:<ACCOUNT_ID>:orders-benchmark-standard` | `1792820500` | `30` s | `345600` s (4 days) | `SqsManagedSseEnabled=true` | N/A | `0` | Yes (`0/0/0` counts) |
| `orders-benchmark.fifo` | FIFO | `arn:aws:sqs:us-east-1:<ACCOUNT_ID>:orders-benchmark.fifo` | `1792820581` | `30` s | `345600` s (4 days) | `SqsManagedSseEnabled=true` | `FifoQueue=true`, `ContentBasedDeduplication=false`, `DeduplicationScope=queue`, `FifoThroughputLimit=perQueue` | `0` | Yes (`0/0/0` counts) |

- **Queue Retention & Cleanup Safety**: Neither `PurgeQueue` nor `DeleteQueue` was called. Every received message was verified by `runId`, `orderId`, and `sqsMessageId` ownership inside `scripts/benchmark_sqs.py` and deleted individually via `DeleteMessage` (`60` sends, `60` run-owned deletes).

---

## 3. Exact CLI Invocations

All three scenarios ran sequentially using `scripts/benchmark_sqs.py` with `--message-count 20 --batch-size 1 --rate 20 --timeout 15 --max-polls 25 --execute`:

1. **Scenario 1 — Standard Queue (`standard`)**:
   ```text
   python scripts/benchmark_sqs.py --queue-type standard --queue-url https://sqs.us-east-1.amazonaws.com/<ACCOUNT_ID>/orders-benchmark-standard --message-count 20 --batch-size 1 --rate 20 --timeout 15 --max-polls 25 --run-id b1-std-20261024T054259Z-01 --output-dir <output-dir>/standard --execute --confirm-target orders-benchmark-standard
   ```
2. **Scenario 2 — FIFO Single-Group (`fifo-single`, `groupCount=1`, `dedup=explicit`)**:
   ```text
   python scripts/benchmark_sqs.py --queue-type fifo --queue-url https://sqs.us-east-1.amazonaws.com/<ACCOUNT_ID>/orders-benchmark.fifo --message-count 20 --batch-size 1 --rate 20 --timeout 15 --max-polls 25 --group-count 1 --dedup-mode explicit --run-id b1-fifo-g1-20261024T054259Z-02 --output-dir <output-dir>/fifo-single --execute --confirm-target orders-benchmark.fifo
   ```
3. **Scenario 3 — FIFO Multi-Group (`fifo-multi`, `groupCount=5`, `dedup=explicit`)**:
   ```text
   python scripts/benchmark_sqs.py --queue-type fifo --queue-url https://sqs.us-east-1.amazonaws.com/<ACCOUNT_ID>/orders-benchmark.fifo --message-count 20 --batch-size 1 --rate 20 --timeout 15 --max-polls 25 --group-count 5 --dedup-mode explicit --run-id b1-fifo-g5-20261024T054259Z-03 --output-dir <output-dir>/fifo-multi --execute --confirm-target orders-benchmark.fifo
   ```

---

## 4. Measured Phase B1 Benchmark Results

### 4.1 Delivery Completeness, Throughput, and Timing

| Scenario | Run ID | Queue Name | Groups | Dedup Mode | Attempted / Accepted / Failed | Unique Received / Duplicates / Completeness | Polls | Send Elapsed (s) | Receive Elapsed (s) | Total Elapsed (s) | Send Throughput (msg/s) | Receive Throughput (msg/s) | Pre -> Post Queue (`vis/notVis/del`) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Standard** | `b1-std-20261024T054259Z-01` | `orders-benchmark-standard` | `1` | `not_applicable` | `20 / 20 / 0` | `20 / 0 / 1.0` | `20` | `6.9454` | `10.3678` | `17.3132` | `2.88` | `1.929` | `0/0/0` -> `0/0/0` |
| **2. FIFO Single-Group** | `b1-fifo-g1-20261024T054259Z-02` | `orders-benchmark.fifo` | `1` | `explicit` | `20 / 20 / 0` | `20 / 0 / 1.0` | `20` | `7.3151` | `10.4616` | `17.7768` | `2.734` | `1.912` | `0/0/0` -> `0/0/0` |
| **3. FIFO Multi-Group** | `b1-fifo-g5-20261024T054259Z-03` | `orders-benchmark.fifo` | `5` | `explicit` | `20 / 20 / 0` | `20 / 0 / 1.0` | `20` | `9.9641` | `12.7654` | `22.7295` | `2.007` | `1.567` | `0/0/0` -> `0/0/0` |

### 4.2 Per-Call SQS Send and Receive-Poll Latency (`ms`)

| Scenario | `sendLatencyMs` (min / median / mean / p95 / max) | `receivePollLatencyMs` (min / median / mean / p95 / max) | Observed Per-Sequence Latency Distribution |
| :--- | :--- | :--- | :--- |
| **1. Standard** | `242.342 / 243.891 / 299.421 / 260.606 / 1321.362` | `240.809 / 243.346 / 276.38 / 550.847 / 582.248` | Send sequence `#1` recorded `1321.362 ms` (first-call connection/TLS overhead is inferred, not directly measured); sends `#2–#20` ranged from `242.342 ms` to `260.606 ms`. |
| **2. FIFO Single-Group** | `244.293 / 246.461 / 317.977 / 254.454 / 1667.827` | `243.629 / 245.667 / 276.029 / 547.561 / 548.105` | Send sequence `#1` recorded `1667.827 ms` (inferred first-call overhead); sends `#2–#20` ranged from `244.293 ms` to `254.454 ms`. |
| **3. FIFO Multi-Group** | `295.639 / 298.031 / 450.362 / 957.534 / 1870.541` | `247.647 / 249.615 / 376.387 / 689.208 / 1484.711` | Send sequence `#1` recorded `1870.541 ms` (inferred first-call overhead), with higher observed send latencies on sequences `#9–#11` (`826.551–957.534 ms`). |

### 4.3 Ordering Verification (`ordering`)

| Scenario | Evaluated Groups | `allGroupsInOrder` | `outOfOrderGroups` | `totalOutOfOrderTransitions` | Observed Sequence(s) by Group |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Standard** | `1` (`bench-group-01`) | `false` | `1` | `5` | `bench-group-01`: `[17, 1, 3, 10, 11, 2, 4, 5, 6, 7, 14, 15, 16, 12, 13, 19, 8, 9, 20, 18]` |
| **2. FIFO Single-Group** | `1` (`bench-group-01`) | `true` | `0` | `0` | `bench-group-01`: `[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]` |
| **3. FIFO Multi-Group** | `5` (`bench-group-01` .. `05`) | `true` | `0` | `0` | `bench-group-01`: `[1, 6, 11, 16]`<br>`bench-group-02`: `[2, 7, 12, 17]`<br>`bench-group-03`: `[3, 8, 13, 18]`<br>`bench-group-04`: `[4, 9, 14, 19]`<br>`bench-group-05`: `[5, 10, 15, 20]` |

---

## 5. Production Invariant Verification (Before and After Phase B1)

Production resources were verified before (`2026-10-24T05:39:19Z` in Step A and `05:42:54Z` in Step C) and after (`2026-10-24T05:44:02Z`) Phase B1 execution. Zero production writes or reads of DLQ payloads were performed:

| Resource | Pre-B1 State (`05:39:19Z` / `05:42:54Z`) | Post-B1 State (`05:44:02Z`) | Status |
| :--- | :--- | :--- | :--- |
| `orders-queue` | `visible=0, notVisible=0, delayed=0` (`LastModifiedTimestamp=1792060948`) | `visible=0, notVisible=0, delayed=0` (`LastModifiedTimestamp=1792060948`) | Untouched |
| `orders-dlq` | `visible=2, notVisible=0, delayed=0` (`LastModifiedTimestamp=1791692962`) | `visible=2, notVisible=0, delayed=0` (`LastModifiedTimestamp=1791692962`) | Untouched (`2` historical messages preserved; bodies never read) |
| `order-consumer` ESM (`ab1f7f06-157c-429b-bfcf-5cb15689f47f`) | `State=Disabled` (`LastModified=2026-10-15T16:38:40Z`) | `State=Disabled` (`LastModified=2026-10-15T16:38:40Z`) | Untouched |
| `order-processor` ESM (`7812ff9b-4000-47e1-9e27-6805670c7cc6`) | `State=Disabled` (`LastModified=2026-10-11T15:18:23Z`) | `State=Disabled` (`LastModified=2026-10-11T15:18:23Z`) | Untouched |

---

## 6. Non-Executed Scope & Known Limitations (`Phase B2` Not Executed)

1. **Sequential Single-Client Execution**: Because `scripts/benchmark_sqs.py` executes single-message (`--batch-size 1`) synchronous `SendMessage` and `ReceiveMessage` (`MaxNumberOfMessages=1`) calls sequentially from a single client outside `us-east-1`, measured send/receive latencies (`~243–298 ms` median) and throughput (`1.567–2.88 msg/s`) reflect sequential client-to-region round-trip execution rather than SQS service capacity ceilings or parallel multi-client load.
2. **Standard vs FIFO Ordering Trade-off**: Even at a `20`-message sample size, `orders-benchmark-standard` exhibited best-effort ordering (`5` out-of-order transitions: `[17, 1, 3, 10, 11, 2, ...]`), whereas `orders-benchmark.fifo` preserved strict FIFO order within `bench-group-01` (`[1..20]`) and within each of the 5 observed message groups (`bench-group-01..05`, sent round-robin by the single sequential client).
3. **Phase B2 End-to-End & CloudWatch Metrics Not Collected**:
   - Phase B2 (`order-consumer` ESM activation, live API Gateway `POST /orders` load test via `scripts/load_test_orders.py`, DynamoDB `Orders` `GetItem` reconciliation, and live CloudWatch metric harvesting via `scripts/collect_cloudwatch_metrics.py`) was **not authorized and not executed** in this job.
   - All live end-to-end API/Lambda/SQS/DynamoDB CloudWatch metrics for this session remain **not collected / missing** (never fabricated as zero).
4. **Pre-Existing Environment Drift Observed in Read-Only Preflight (Job `2026-10-24-002`)**:
   - **Deployed `order-producer` Drift (`MISMATCH`)**: Live `order-producer` (`LastModified=2026-10-15T11:09:32.000+0000`, `lambda_function.py` `1421` bytes, 60 lines, SHA-256 `c78867dbb8b2e4de4a5440223576c1f6431353794c7a59379049a8bf0ec420b8`, git blob `b4dde269947530d441efae797ca5b1ad452cc773`) predates PR #7 on `main` (`src/producer/lambda_function.py` `2071` bytes LF, 68 lines, SHA-256 `54d8014411164db8c43e7adee60867a1e6167be7ccbc00f103bffb7cba64bc1b`, git blob `5496fbc6c88615db99800fd1e98c3ede6d5297c6`). Specifically, the deployed function lacks `_validate(event)` and never returns HTTP `400`: on missing fields it defaults `customerId="UNKNOWN"`, `productId="UNKNOWN"`, and `quantity=1` and still enqueues to `orders-queue` returning HTTP `202`, while on malformed JSON `json.loads` falls into `except Exception` returning HTTP `500` instead of HTTP `400`. For valid requests (`customerId`, `productId`, positive integer `quantity`), both deployed code and `main` construct the same 6-field SQS payload (`orderId`, `customerId`, `productId`, `quantity`, `status="PENDING"`, `createdAt`) and return HTTP `202` with `orderId` and `order`, which is compatible with valid-request E2E testing via `scripts/load_test_orders.py`.
   - **Deployed `order-consumer` Equivalence (`MATCH_NORMALIZED`)**: Live `order-consumer` (`LastModified=2026-10-15T10:54:23.000+0000`, `lambda_function.py` `8463` bytes LF without trailing newline, SHA-256 `ce0064872be11c05dbf497f91f307383eeab21e8845071ba96bbf05a3414b308`, git blob `a924066971fe516a9a009045317ada3f055c8310`) is 100% AST-identical (`233` stripped lines equal) to `main` `src/consumer/lambda_function.py` (`8464` bytes LF with trailing newline, SHA-256 `a4f54eb6df0a6da36e40b1fa0dff69c1de339b454f39d4909556e1066ae8e4b7`, git blob `112937e0bc17a94f6c40b4e965582143706a4e2f`), differing only by line-ending/final-newline formatting.
   - **Disabled Consumer ESM Provenance (`UNKNOWN`)**: `order-consumer` ESM `ab1f7f06-157c-429b-bfcf-5cb15689f47f` has `State=Disabled`, `StateTransitionReason=USER_INITIATED`, `LastModified=2026-10-15T16:38:40Z`. Bounded read-only CloudTrail `LookupEvents` over the explicit window `2026-10-10T00:00:00Z` to `2026-10-24T05:39:19Z` (`1` page each, `hasMorePages=false`) returned `0` events for `UpdateEventSourceMapping` and `CreateEventSourceMapping`. The root cause of zero returned CloudTrail events and the human owner intent for leaving `ab1f7f06-157c-429b-bfcf-5cb15689f47f` `Disabled` are `UNKNOWN` and require explicit user confirmation before any Phase B2 execution.
