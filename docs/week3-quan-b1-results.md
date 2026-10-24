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

| Scenario | `sendLatencyMs` (min / median / mean / p95 / max) | `receivePollLatencyMs` (min / median / mean / p95 / max) | Notes on First-Call / Network Variance |
| :--- | :--- | :--- | :--- |
| **1. Standard** | `242.342 / 243.891 / 299.421 / 260.606 / 1321.362` | `240.809 / 243.346 / 276.38 / 550.847 / 582.248` | Sequence `#1` incurred initial TLS/connection setup (`1321.362 ms`); subsequent sends clustered at `~242–261 ms` from client to `us-east-1`. |
| **2. FIFO Single-Group** | `244.293 / 246.461 / 317.977 / 254.454 / 1667.827` | `243.629 / 245.667 / 276.029 / 547.561 / 548.105` | Sequence `#1` incurred initial TLS/connection setup (`1667.827 ms`); median send (`246.461 ms`) and receive (`245.667 ms`) matched Standard within `~2.5 ms`. |
| **3. FIFO Multi-Group** | `295.639 / 298.031 / 450.362 / 957.534 / 1870.541` | `247.647 / 249.615 / 376.387 / 689.208 / 1484.711` | Sequence `#1` incurred initial TLS/connection setup (`1870.541 ms`) plus transient WAN jitter on sequences `#9–#11` (`826–958 ms`). |

### 4.3 Ordering Verification (`ordering`)

| Scenario | Evaluated Groups | `allGroupsInOrder` | `outOfOrderGroups` | `totalOutOfOrderTransitions` | Observed Sequence(s) by Group |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Standard** | `1` (`bench-group-01`) | `false` | `1` | `5` | `bench-group-01`: `[17, 1, 3, 10, 11, 2, 4, 5, 6, 7, 14, 15, 16, 12, 13, 19, 8, 9, 20, 18]` |
| **2. FIFO Single-Group** | `1` (`bench-group-01`) | `true` | `0` | `0` | `bench-group-01`: `[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]` |
| **3. FIFO Multi-Group** | `5` (`bench-group-01` .. `05`) | `true` | `0` | `0` | `bench-group-01`: `[1, 6, 11, 16]`<br>`bench-group-02`: `[2, 7, 12, 17]`<br>`bench-group-03`: `[3, 8, 13, 18]`<br>`bench-group-04`: `[4, 9, 14, 19]`<br>`bench-group-05`: `[5, 10, 15, 20]` |

---

## 5. Production Invariant Verification (Before and After Phase B1)

Production resources were verified before (`2026-10-24T05:42:52Z`) and after (`2026-10-24T05:44:02Z`) Phase B1 execution. Zero production writes or reads of DLQ payloads were performed:

| Resource | Pre-B1 State (`05:42:52Z`) | Post-B1 State (`05:44:02Z`) | Status |
| :--- | :--- | :--- | :--- |
| `orders-queue` | `visible=0, notVisible=0, delayed=0` (`LastModifiedTimestamp=1792060948`) | `visible=0, notVisible=0, delayed=0` (`LastModifiedTimestamp=1792060948`) | Untouched |
| `orders-dlq` | `visible=2, notVisible=0, delayed=0` (`LastModifiedTimestamp=1791692962`) | `visible=2, notVisible=0, delayed=0` (`LastModifiedTimestamp=1791692962`) | Untouched (`2` historical messages preserved; bodies never read) |
| `order-consumer` ESM (`ab1f7f06-157c-429b-bfcf-5cb15689f47f`) | `State=Disabled` | `State=Disabled` | Untouched |
| `order-processor` ESM (`7812ff9b-4000-47e1-9e27-6805670c7cc6`) | `State=Disabled` | `State=Disabled` | Untouched |

---

## 6. Non-Executed Scope & Known Limitations (`Phase B2` Not Executed)

1. **Sequential Client RTT Dominance**: Because `scripts/benchmark_sqs.py` executes single-message (`--batch-size 1`) synchronous `SendMessage` and `ReceiveMessage` (`MaxNumberOfMessages=1`) calls sequentially from a remote client outside `us-east-1`, measured send/receive latencies (`~243–298 ms` median) and throughput (`1.567–2.88 msg/s`) are dominated by WAN round-trip time rather than SQS service capacity ceilings.
2. **Standard vs FIFO Ordering Trade-off**: Even at a `20`-message sample size, `orders-benchmark-standard` exhibited best-effort ordering (`5` out-of-order transitions: `[17, 1, 3, 10, 11, 2, ...]`), whereas `orders-benchmark.fifo` preserved strict FIFO order within `bench-group-01` (`[1..20]`) and within each of the 5 parallel message groups (`bench-group-01..05`).
3. **Phase B2 End-to-End & CloudWatch Metrics Not Collected**:
   - Phase B2 (`order-consumer` ESM activation, live API Gateway `POST /orders` load test, DynamoDB `Orders` `GetItem` reconciliation, and live CloudWatch metric harvesting via `scripts/collect_cloudwatch_metrics.py`) was **not authorized and not executed** in this job.
   - All live end-to-end API/Lambda/SQS/DynamoDB CloudWatch metrics for this session remain **not collected / missing** (never fabricated as zero).
4. **Pre-Existing Environment Drift Observed in Read-Only Preflight (Job `2026-10-24-002`)**:
   - **Deployed `order-producer` Drift**: Live `order-producer` (`LastModified=2026-10-15T10:15:36.000+0000`, normalized SHA-256 `b4dde2696c00ec31090624739a834597b6260b2163b149746809bd0254a1bf31`) predates PR #7 (`main` `src/producer/handler.py` normalized SHA-256 `5496fbc6f039ba1a559014c0aa06eb2ddcd264b5f1e72b90c6403c4e24989fc5`). It lacks PR #7 deep `items` validation (`customer_id` / `items` list / `quantity`), though valid `scripts/load_test.py` payloads (`{"userId": "user-load-XXXX", "itemId": "item-load-XX"}`) satisfy both deployed and `main` schemas.
   - **Deployed `order-consumer` Match**: Live `order-consumer` (`LastModified=2026-10-15T10:13:51.000+0000`, normalized SHA-256 `a92406694a4f96a694bc4523b385a77eb51ec43c214231896a388bd4b946a190`) matches `main` `src/consumer/handler.py` (`112937e01fc87710a274106392853ad3a7dbda6234e49334d3996215c227b69d`) in executable AST/runtime logic (differing only by docstring/comments).
   - **Disabled Consumer ESM Provenance**: Explicit-window CloudTrail lookup (`2026-10-10T00:00:00Z` to `2026-10-24T05:39:19Z`) returned `0` events (`hasMorePages=false`) for `UpdateEventSourceMapping` and `CreateEventSourceMapping` due to Learner Lab CloudTrail Event History visibility boundaries; owner intent for keeping `ab1f7f06-157c-429b-bfcf-5cb15689f47f` `Disabled` remains `UNKNOWN` and requires explicit user confirmation before Phase B2.
